#!/usr/bin/env bash
# Bootstraps GPU worker with ComfyUI + Cloudflare Tunnel. Idempotent.
set -euo pipefail

COMFYUI_IMAGE="${COMFYUI_IMAGE:-ghcr.io/comfyanonymous/comfyui:latest}"
COMFYUI_CONTAINER="${COMFYUI_CONTAINER:-comfyui}"
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
COMFYUI_VOLUME="${COMFYUI_VOLUME:-/opt/comfyui-data}"
NVIDIA_VISIBLE_DEVICES="${NVIDIA_VISIBLE_DEVICES:-all}"
CLOUDFLARED_TOKEN="${CLOUDFLARED_TOKEN:-}"
TUNNEL_HOSTNAME="${TUNNEL_HOSTNAME:-}"

if [[ -z "$CLOUDFLARED_TOKEN" || -z "$TUNNEL_HOSTNAME" ]]; then
  echo "CLOUDFLARED_TOKEN and TUNNEL_HOSTNAME are required." >&2
  exit 1
fi

echo "[1/6] Installing Docker if missing"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

echo "[2/6] Installing cloudflared if missing"
if ! command -v cloudflared >/dev/null 2>&1; then
  wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb
  dpkg -i /tmp/cloudflared.deb
  rm -f /tmp/cloudflared.deb
fi

echo "[3/6] Auth tunnel token"
mkdir -p /etc/cloudflared
cat <<EOF >/etc/cloudflared/cert.pem
$CLOUDFLARED_TOKEN
EOF

cat <<EOF >/etc/cloudflared/config.yml
tunnel: gpu-comfyui
credentials-file: /etc/cloudflared/cert.pem
ingress:
  - hostname: $TUNNEL_HOSTNAME
    service: http://localhost:$COMFYUI_PORT
  - service: http_status:404
EOF

echo "[4/6] Start/enable cloudflared systemd service"
cloudflared service install
systemctl enable --now cloudflared || systemctl restart cloudflared

echo "[5/6] Pull and run ComfyUI with GPU"
docker pull "$COMFYUI_IMAGE"
docker stop "$COMFYUI_CONTAINER" >/dev/null 2>&1 || true
docker rm "$COMFYUI_CONTAINER" >/dev/null 2>&1 || true
mkdir -p "$COMFYUI_VOLUME"
docker run -d \
  --gpus "$NVIDIA_VISIBLE_DEVICES" \
  -p "$COMFYUI_PORT:8188" \
  --name "$COMFYUI_CONTAINER" \
  --restart unless-stopped \
  -v "$COMFYUI_VOLUME:/root/comfyui" \
  "$COMFYUI_IMAGE"

echo "[6/6] Done. Exposed via https://$TUNNEL_HOSTNAME"
echo "Set COMFYUI_URL=https://$TUNNEL_HOSTNAME in Fly/Render secrets."
#!/usr/bin/env bash
#
# Bootstraps a GPU worker that runs ComfyUI behind a Cloudflare Tunnel.
# Designed for Ubuntu/Debian hosts with Docker and systemd.
# Required env vars:
#   - CLOUDFLARED_TOKEN: Cloudflare tunnel token (from Zero Trust dashboard)
#   - TUNNEL_HOSTNAME: Public hostname routed to the tunnel (e.g., comfy.example.com)
# Optional env vars:
#   - COMFYUI_IMAGE (default: ghcr.io/comfyanonymous/comfyui:latest)
#   - COMFYUI_PORT (default: 8188)
#   - COMFYUI_VOLUME (default: /opt/comfyui)
#   - NVIDIA_VISIBLE_DEVICES (default: all)
set -euo pipefail

COMFYUI_IMAGE="${COMFYUI_IMAGE:-ghcr.io/comfyanonymous/comfyui:latest}"
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
COMFYUI_VOLUME="${COMFYUI_VOLUME:-/opt/comfyui}"
NVIDIA_VISIBLE_DEVICES="${NVIDIA_VISIBLE_DEVICES:-all}"

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root (sudo)." >&2
    exit 1
  fi
}

require_var() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Missing required env var: $name" >&2
    exit 1
  fi
}

install_prereqs() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found; installing..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  fi

  if ! command -v cloudflared >/dev/null 2>&1; then
    echo "cloudflared not found; installing..."
    curl -fsSL https://developers.cloudflare.com/cloudflare-one/static/documentation/connections/CloudflareTunnel.pkg -o /tmp/cloudflared.pkg
    dpkg -i /tmp/cloudflared.pkg || apt-get -f install -y
  fi
}

ensure_comfyui_container() {
  docker pull "$COMFYUI_IMAGE"
  docker rm -f comfyui || true
  docker run -d \
    --gpus all \
    --env NVIDIA_VISIBLE_DEVICES="$NVIDIA_VISIBLE_DEVICES" \
    -p "${COMFYUI_PORT}:${COMFYUI_PORT}" \
    -v "${COMFYUI_VOLUME}:/opt/comfyui" \
    --name comfyui \
    --restart unless-stopped \
    "$COMFYUI_IMAGE" \
    python main.py --port "${COMFYUI_PORT}"
}

write_systemd_unit() {
  cat >/etc/systemd/system/comfyui.service <<EOF
[Unit]
Description=ComfyUI GPU worker
After=network.target docker.service
Requires=docker.service

[Service]
Restart=always
RestartSec=5s
ExecStart=/usr/bin/docker start -a comfyui
ExecStop=/usr/bin/docker stop comfyui

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable --now comfyui
}

install_cloudflared_service() {
  # Requires CLOUDFLARED_TOKEN from Zero Trust "Tunnel Token"
  cloudflared service uninstall || true
  cloudflared service install "$CLOUDFLARED_TOKEN"

  if [ -n "${TUNNEL_HOSTNAME:-}" ]; then
    echo "cloudflared tunnel will expose https://${TUNNEL_HOSTNAME} -> http://localhost:${COMFYUI_PORT}"
  fi

  systemctl enable --now cloudflared
}

main() {
  require_root
  require_var CLOUDFLARED_TOKEN
  require_var TUNNEL_HOSTNAME

  install_prereqs
  ensure_comfyui_container
  write_systemd_unit
  install_cloudflared_service

  echo "GPU worker ready. Point COMFYUI_URL to https://${TUNNEL_HOSTNAME}"
}

main "$@"

# Online (Mostly-Free) Deployment — Browser-Only, No Human Steps After Setup

Goal: make AInfluencer run fully online, controllable from a browser (MacBook-friendly) with zero manual ops after initial setup. We use free CPU hosting plus your own GPU via a secure tunnel. Once wired, Cursor/CI can redeploy automatically.

## What “free” means (truth)
- No provider gives you a permanent free NVIDIA GPU. The free pattern: free CPU host (web/API) + your GPU via tunnel. Ephemeral free GPUs (Colab/Kaggle) are for demos only.
- Quality stays identical if models + seeds + sampler/steps + precision match. Performance varies with GPU class and precision.

## Target architecture (automatable)
- Web + API: free CPU host (Fly.io free App VM or Render free web service).
- GPU worker: your 4080 (or any GPU) running ComfyUI, exposed via Cloudflare Tunnel (no open ports).
- Storage: Postgres/Redis on CPU host (docker-compose).
- Frontend → Backend → GPU (`COMFYUI_URL`), all over HTTPS.

## One-time bootstrap (then automate)
1) Fork/push repo to GitHub.  
2) Create a free Fly.io account (https://fly.io/docs/hands-on/). From a browser shell (Codespaces/Devbox/Fly Launch UI), run:
   ```bash
   cp deployment/env.example .env
   # edit with strong secrets and URLs
   # required:
   # NEXT_PUBLIC_API_URL=https://<your-fly-app>.fly.dev
   # COMFYUI_URL=https://<your-tunnel-hostname>
   # POSTGRES_PASSWORD=...
   # REDIS_PASSWORD=...
   # SECRET_KEY=...
   # JWT_SECRET_KEY=...
   # GRAFANA_PASSWORD=...
   fly launch --copy-config --no-deploy
   fly deploy
   ```
3) (Optional) Render path: create a Web Service from the repo; deploy via Docker; set env vars from `.env`; expose 3000 (web) or 8000 (API); set `NEXT_PUBLIC_API_URL` to Render URL and keep `COMFYUI_URL` pointing to your tunnel.

## GPU endpoint with Cloudflare Tunnel (no port-forwarding)
1) On the GPU box (Windows/Linux with 4080), install cloudflared.  
2) Run ComfyUI with GPU:
   ```bash
   docker run -d --gpus all -p 8188:8188 --name comfyui --restart unless-stopped ghcr.io/comfyanonymous/comfyui:latest
   ```
3) Start the tunnel to ComfyUI:
   ```bash
   cloudflared tunnel run <your-tunnel-name>
   # tunnel maps https://<your-tunnel-hostname> -> http://localhost:8188
   ```
4) Set `COMFYUI_URL=https://<your-tunnel-hostname>` in `.env` for the backend. Backend now reaches your GPU securely; home router stays closed.

## Make it push-button for Cursor/CI (scripted flow)
- Add a CI job (GitHub Actions) that on push to `main`:
  - Builds and deploys to Fly: `fly deploy --remote-only` (requires `FLY_API_TOKEN` secret).
  - Syncs `.env` values via Fly secrets: `fly secrets set KEY=VALUE` (stored as repo secrets).
- Add a GPU bootstrap script (run once on the GPU box, then on reboot via systemd):
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  docker pull ghcr.io/comfyanonymous/comfyui:latest
  docker stop comfyui || true
  docker rm comfyui || true
  docker run -d --gpus all -p 8188:8188 --name comfyui --restart unless-stopped ghcr.io/comfyanonymous/comfyui:latest
  systemctl enable --now cloudflared
  ```
- Store model checkpoints/LoRAs on the GPU box under the ComfyUI volume so outputs match your laptop.

## One-click automation (shipped in repo)
- CI deploy: `.github/workflows/online-free-deploy.yml`
  - Triggers on `main` changes to backend/web/deployment files.
  - Requires repo secrets: `FLY_API_TOKEN`, `FLY_APP_NAME`, `NEXT_PUBLIC_API_URL`, `COMFYUI_URL`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `SECRET_KEY`, `JWT_SECRET_KEY`, `GRAFANA_PASSWORD`.
  - Action flow: validate secrets → install Flyctl → set Fly secrets → `flyctl deploy --remote-only --app $FLY_APP_NAME`.
- GPU+tunnel bootstrap: `deployment/scripts/gpu_tunnel_bootstrap.sh`
  - Run as root on the GPU host: `sudo CLOUDFLARED_TOKEN=<token> TUNNEL_HOSTNAME=<host> bash gpu_tunnel_bootstrap.sh`
  - Installs Docker + cloudflared (if missing), starts ComfyUI on GPU with restart policy, installs Cloudflare Tunnel as a systemd service, and prints the HTTPS endpoint for `COMFYUI_URL`.
  - Optional envs: `COMFYUI_IMAGE`, `COMFYUI_PORT`, `COMFYUI_VOLUME`, `NVIDIA_VISIBLE_DEVICES`.
  - Set `COMFYUI_URL=https://<TUNNEL_HOSTNAME>` in Fly secrets; backend will reach the GPU worker securely.
- Fly secrets sync helper: `deployment/scripts/fly_secrets_set.sh`
  - Usage: `FLY_APP_NAME=<app> ./deployment/scripts/fly_secrets_set.sh .env` (expects `flyctl` auth).
  - Reads key=value pairs from the env file (skips comments/blank lines) and sets them in Fly secrets in one call.

## Running from a MacBook (browser-only)
- Open `https://<your-fly-app>.fly.dev` (or Render URL). All heavy lifting stays on your GPU via the tunnel; no local installs.

## Model parity (match your laptop outputs)
- Copy your checkpoints/LoRAs/embeddings to the GPU box.  
- Keep sampler/steps/CFG/resolution/seed and precision identical.  
- Use similar PyTorch/CUDA to minimize numeric drift.

## Cost/UX options
- $0 infra: free CPU host + your home GPU via tunnel (depends on your home uptime/bandwidth; adds latency).  
- $0 but unstable: free Colab/Kaggle GPU + free CPU host (ephemeral; not for production).  
- Low-cost/stable: cheap hourly GPU (RunPod/Vast/Paperspace) + Cloudflare Tunnel + free CPU host.

## Security checklist (must do)
- Strong secrets for all keys/passwords.  
- Restrict `ALLOWED_HOSTS`/`CORS_ORIGINS` to your domains.  
- Keep tunnel URL private; add Cloudflare Access if possible.  
- Rotate secrets; update images regularly; keep HTTPS end to end.

## Quick verification (can be scripted in CI)
- Backend health: `curl https://<your-fly-app>.fly.dev/api/health`  
- Web: open site and run a generation; confirm backend hits `COMFYUI_URL`.  
- Logs: `fly logs` (or provider logs) to see requests reaching the GPU.

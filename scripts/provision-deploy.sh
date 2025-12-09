#!/usr/bin/env bash
# Last-mile provisioning automation for Render + Vercel.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/env.deploy"
STATE_DIR="$ROOT_DIR/.deploy"
STATE_FILE="$STATE_DIR/state.json"

SERVICE_NAME="${RENDER_SERVICE_NAME:-ainfluencer-backend}"
PROJECT_NAME="${VERCEL_PROJECT_NAME:-ainfluencer-web}"
SCOPE_ARG=""

mkdir -p "$STATE_DIR"

load_env_file() {
  local file="$1"
  if [ -f "$file" ]; then
    echo "Loading env from $file"
    set -a
    # shellcheck disable=SC1090
    . "$file"
    set +a
  fi
}

load_env_file "$ENV_FILE"

if [ -z "${VERCEL_TOKEN:-}" ]; then
  echo "❌ Missing VERCEL_TOKEN. Run: vercel login (to create token) then export VERCEL_TOKEN."
  exit 1
fi
if [ -z "${RENDER_API_KEY:-}" ]; then
  echo "❌ Missing RENDER_API_KEY. Create a Render API key and export RENDER_API_KEY."
  exit 1
fi

if ! command -v vercel >/dev/null 2>&1; then
  echo "❌ Vercel CLI not found. Install: npm i -g vercel"
  exit 1
fi

if [ -n "${VERCEL_ORG_ID:-}" ]; then
  SCOPE_ARG="--scope $VERCEL_ORG_ID"
fi

write_state() {
  local key="$1"; shift
  local value="$1"; shift
  python - "$STATE_FILE" "$key" "$value" <<'PY'
import json, os, sys
path, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
data = {}
if os.path.exists(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        data = {}
data[key] = value
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    json.dump(data, f, indent=2)
print(f"state[{key}] = {value}")
PY
}

read_state() {
  local key="$1"; shift
  python - "$STATE_FILE" "$key" <<'PY'
import json, os, sys
path, key = sys.argv[1], sys.argv[2]
if not os.path.exists(path):
    sys.exit(1)
try:
    with open(path) as f:
        data = json.load(f)
    val = data.get(key)
    if val:
        print(val)
except Exception:
    sys.exit(1)
PY
}

render_env_keys=(
  NEXT_PUBLIC_API_URL NEXT_PUBLIC_COMFYUI_URL NEXT_PUBLIC_DEMO_MODE NEXT_PUBLIC_ENABLE_ADVANCED
  NEXT_PUBLIC_ENABLE_UPSCALE NEXT_PUBLIC_ENABLE_FACE_RESTORE NEXT_PUBLIC_ENABLE_BATCH
  NEXT_PUBLIC_ENABLE_HIGH_RES NEXT_PUBLIC_DEMO_MAX_WIDTH NEXT_PUBLIC_DEMO_MAX_HEIGHT NEXT_PUBLIC_DEMO_MAX_BATCH
  API_HOST API_PORT ALLOWED_ORIGINS COMFYUI_SERVER DATABASE_URL REDIS_URL REDIS_PASSWORD
  DEMO_MODE ENABLE_ADVANCED ENABLE_UPSCALE ENABLE_FACE_RESTORE ENABLE_BATCH ENABLE_HIGH_RES
  DEMO_MAX_WIDTH DEMO_MAX_HEIGHT DEMO_MAX_BATCH RATE_LIMIT_PER_MINUTE RATE_LIMIT_PER_HOUR
  MAX_REQUEST_SIZE_MB REQUEST_TIMEOUT_SECONDS MAX_CONCURRENT_JOBS
)

get_env_val() {
  local key="$1"
  # prefer exported env over file to allow overrides
  if env | grep -q "^${key}="; then
    printf '%s' "${!key}"
    return
  fi
  if [ -f "$ENV_FILE" ]; then
    local val
    val=$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d '=' -f2-)
    printf '%s' "$val"
  fi
}

get_service_details() {
  local service_id="$1"
  curl -sS -H "Authorization: Bearer $RENDER_API_KEY" \
    "https://api.render.com/v1/services/${service_id}"
}

is_backend_service() {
  local service_json="$1"
  local type env runtime build start rootDir
  type=$(printf '%s' "$service_json" | python - <<'PY'
import json,sys
data=json.loads(sys.stdin.read() or "{}")
print(data.get("type") or (data.get("service") or {}).get("type") or "")
PY
)
  env=$(printf '%s' "$service_json" | python - <<'PY'
import json,sys
data=json.loads(sys.stdin.read() or "{}")
svc=data.get("serviceDetails") or {}
print(data.get("env") or svc.get("env") or "")
PY
)
  runtime=$(printf '%s' "$service_json" | python - <<'PY'
import json,sys
data=json.loads(sys.stdin.read() or "{}")
svc=data.get("serviceDetails") or {}
print(data.get("runtime") or svc.get("runtime") or "")
PY
)
  build=$(printf '%s' "$service_json" | python - <<'PY'
import json,sys
data=json.loads(sys.stdin.read() or "{}")
print((data.get("serviceDetails") or {}).get("buildCommand") or "")
PY
)
  start=$(printf '%s' "$service_json" | python - <<'PY'
import json,sys
data=json.loads(sys.stdin.read() or "{}")
print((data.get("serviceDetails") or {}).get("startCommand") or "")
PY
)
  rootDir=$(printf '%s' "$service_json" | python - <<'PY'
import json,sys
data=json.loads(sys.stdin.read() or "{}")
print((data.get("serviceDetails") or {}).get("rootDir") or "")
PY
)

  local is_web is_python has_uvicorn root_ok build_ok
  is_web=false
  [ "$type" = "web" ] || [ "$type" = "web_service" ] && is_web=true
  is_python=false
  [ "$env" = "python" ] || [ "$runtime" = "python" ] && is_python=true
  has_uvicorn=false
  if printf '%s' "$start" | grep -qi "uvicorn" && printf '%s' "$start" | grep -qi "main:app"; then
    has_uvicorn=true
  fi
  root_ok=true
  if [ -n "$rootDir" ]; then
    if printf '%s' "$rootDir" | grep -q "backend"; then
      root_ok=true
    else
      root_ok=false
    fi
  fi
  build_ok=false
  if [ -n "$build" ]; then
    if printf '%s' "$build" | grep -qi "requirements.txt"; then
      build_ok=true
    fi
    if $root_ok && printf '%s' "$build" | grep -qi "pip install"; then
      build_ok=true
    fi
  fi

  $is_web && $is_python && $has_uvicorn && $build_ok
}

backend_url_guess() {
  local service_json="$1"
  python - <<'PY'
import json,sys
data=json.loads(sys.stdin.read() or "{}")
candidates=[]
svc=data.get("serviceDetails") or {}
for key in ("defaultSubdomain","url"):
    val=svc.get(key)
    if val: candidates.append(val)
custom=svc.get("customDomains")
if isinstance(custom,list):
    candidates.extend(custom)
for key in ("defaultSubdomain","slug","name"):
    val=data.get(key)
    if val: candidates.append(val)
for cand in candidates:
    if not cand: continue
    c=str(cand)
    if c.startswith("http"):
        print(c); sys.exit(0)
    if ".onrender.com" in c:
        print(f"https://{c}"); sys.exit(0)
print("")
PY
}

echo "==> Render: discover or create service '$SERVICE_NAME'"
SERVICE_ID="${RENDER_SERVICE_ID:-$(read_state RENDER_SERVICE_ID || true)}"
if [ -z "$SERVICE_ID" ]; then
  services_json=$(curl -sS -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services)
  SERVICE_ID=$(python - "$SERVICE_NAME" <<'PY'
import json, sys
data = json.loads(sys.stdin.read() or "[]")
name = sys.argv[1]
for svc in data:
    if svc.get("name") == name:
        print(svc.get("id") or "")
        sys.exit(0)
PY
)
fi

service_json=""
if [ -n "$SERVICE_ID" ]; then
  service_json=$(get_service_details "$SERVICE_ID" || true)
  if ! is_backend_service "$service_json"; then
    echo "⚠️  Service '$SERVICE_NAME' (id: $SERVICE_ID) does not look like the Python backend (type/env/start/root mismatch)."
    echo "    If the Render dashboard shows 'Ruby', this is the same issue."
    echo "    Create a new Render Web Service with:"
    echo "      name=ainfluencer-backend, env=python, rootDir=backend"
    echo "      build='pip install --no-cache-dir -r requirements.txt'"
    echo "      start='uvicorn main:app --host 0.0.0.0 --port \$PORT'"
    echo "    Then set RENDER_SERVICE_ID in env.deploy and rerun."
    exit 1
  fi
fi

if [ -z "$SERVICE_ID" ]; then
  echo "Service not found; attempting creation on Render free plan..."
  create_payload=$(cat <<EOF
{
  "type": "web_service",
  "name": "$SERVICE_NAME",
  "plan": "free",
  "region": "oregon",
  "env": "python",
  "serviceDetails": {
    "env": "python",
    "buildCommand": "pip install --no-cache-dir -r requirements.txt",
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port \$PORT",
    "rootDir": "backend",
    "autoDeploy": false
  }
}
EOF
)
  create_resp=$(echo "$create_payload" | curl -sS -X POST \
    -H "Authorization: Bearer $RENDER_API_KEY" \
    -H "Content-Type: application/json" \
    https://api.render.com/v1/services -d @-)
  SERVICE_ID=$(python - <<'PY'
import json, sys
resp = json.loads(sys.stdin.read() or "{}")
print(resp.get("id",""))
PY
<<<"$create_resp")
  if [ -z "$SERVICE_ID" ]; then
    echo "⚠️  Failed to auto-create Render service. Please create it manually via dashboard using render.yaml, then export RENDER_SERVICE_ID."
    exit 1
  fi
  service_json="$create_resp"
  echo "✅ Render service created: $SERVICE_ID"
else
  echo "✅ Render service found: $SERVICE_ID"
fi
write_state RENDER_SERVICE_ID "$SERVICE_ID"
write_state render_backend_service_id "$SERVICE_ID"

if [ -z "$service_json" ]; then
  service_json=$(get_service_details "$SERVICE_ID" || true)
fi
if ! is_backend_service "$service_json"; then
  echo "⚠️  Service $SERVICE_ID is still not a Python uvicorn backend. Marking state invalid."
  write_state render_backend_service_id ""
  echo "Please create the Python service with the commands above, set RENDER_SERVICE_ID, then rerun."
  exit 1
fi
backend_name=$(printf '%s' "$service_json" | python - <<'PY'
import json,sys
data=json.loads(sys.stdin.read() or "{}")
print(data.get("name",""))
PY
)
[ -n "$backend_name" ] && write_state render_backend_service_name "$backend_name"
backend_url=$(backend_url_guess "$service_json")
if [ -n "$backend_url" ]; then
  write_state render_backend_url "$backend_url"
  if [ -z "${NEXT_PUBLIC_API_URL:-}" ]; then
    export NEXT_PUBLIC_API_URL="$backend_url"
    echo "NEXT_PUBLIC_API_URL set for this run: $NEXT_PUBLIC_API_URL"
  fi
else
  echo "⚠️  Could not derive backend URL automatically; set NEXT_PUBLIC_API_URL to your Render hostname."
fi

# Provide a sane default for ALLOWED_ORIGINS if missing (tighten after deploy)
if [ -z "$(get_env_val ALLOWED_ORIGINS)" ] && [ -n "$PROJECT_NAME" ]; then
  export ALLOWED_ORIGINS="https://$PROJECT_NAME.vercel.app"
  echo "⚠️  ALLOWED_ORIGINS not set; defaulting to $ALLOWED_ORIGINS (tighten once you know the domain)."
fi

echo "==> Render env sync (best effort)"
for key in "${render_env_keys[@]}"; do
  val="$(get_env_val "$key")"
  [ -z "$val" ] && continue
  curl -sS -X POST \
    -H "Authorization: Bearer $RENDER_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"key\":\"$key\",\"value\":\"$val\",\"type\":\"SECRET\"}" \
    "https://api.render.com/v1/services/$SERVICE_ID/env-vars" >/dev/null || true
done

echo "==> Vercel: link project '$PROJECT_NAME'"
if ! vercel link --project "$PROJECT_NAME" --yes --cwd "$ROOT_DIR/web" --token "$VERCEL_TOKEN" $SCOPE_ARG >/dev/null 2>&1; then
  echo "⚠️  Vercel project link may require one interactive command. Run:"
  echo "    vercel link --project $PROJECT_NAME --cwd \"$ROOT_DIR/web\" --token \"$VERCEL_TOKEN\" $SCOPE_ARG"
  exit 1
fi

PROJECT_JSON="$ROOT_DIR/web/.vercel/project.json"
if [ -f "$PROJECT_JSON" ]; then
  PROJECT_ID=$(python - <<'PY'
import json,sys,os
path=sys.argv[1]
with open(path) as f:
    data=json.load(f)
print(data.get("projectId",""))
PY
"$PROJECT_JSON")
  ORG_ID=$(python - <<'PY'
import json,sys
with open(sys.argv[1]) as f:
    data=json.load(f)
print(data.get("orgId",""))
PY
"$PROJECT_JSON")
  [ -n "$PROJECT_ID" ] && write_state VERCEL_PROJECT_ID "$PROJECT_ID"
  [ -n "$ORG_ID" ] && write_state VERCEL_ORG_ID "$ORG_ID"
fi

echo "==> Vercel env sync"
for key in "${render_env_keys[@]}"; do
  val="$(get_env_val "$key")"
  [ -z "$val" ] && continue
  printf '%s\n' "$val" | vercel env add "$key" production --token "$VERCEL_TOKEN" --cwd "$ROOT_DIR/web" $SCOPE_ARG >/dev/null 2>&1 || true
done

echo "==> Trigger Render deploy"
deploy_resp=$(curl -sS -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.render.com/v1/services/$SERVICE_ID/deploys" -d '{}')
echo "Render deploy response: $deploy_resp"

echo "==> Trigger Vercel deploy"
vercel deploy --prod --yes --token "$VERCEL_TOKEN" --cwd "$ROOT_DIR/web" $SCOPE_ARG

echo
echo "================ FINAL SUMMARY ================"
echo "Render service ID: $SERVICE_ID"
[ -n "${PROJECT_ID:-}" ] && echo "Vercel project ID: $PROJECT_ID"
[ -n "${ORG_ID:-}" ] && echo "Vercel org ID: $ORG_ID"
echo "State file: $STATE_FILE"
echo
echo "Render env to set (if UI fallback needed):"
for key in "${render_env_keys[@]}"; do
  val="$(get_env_val "$key")"
  [ -n "$val" ] && echo "$key=$val"
done
echo
echo "Vercel env to set (if CLI add failed):"
for key in "${render_env_keys[@]}"; do
  val="$(get_env_val "$key")"
  [ -n "$val" ] && echo "$key=$val"
done
echo "Push-to-deploy is live once this completes successfully."


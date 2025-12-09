#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

ENV_FILES=(
  "$ROOT_DIR/.env"
  "$ROOT_DIR/env.deploy"
  "$ROOT_DIR/backend/.env"
  "$ROOT_DIR/web/.env.local"
)

for file in "${ENV_FILES[@]}"; do
  load_env_file "$file"
done

export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
export BACKEND_URL="${BACKEND_URL:-$NEXT_PUBLIC_API_URL}"
export COMFYUI_URL="${COMFYUI_URL:-${NEXT_PUBLIC_COMFYUI_URL:-http://localhost:8188}}"
export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-8000}"

echo "==> Checking required environment variables"
REQUIRED=(NEXT_PUBLIC_API_URL BACKEND_URL COMFYUI_URL API_HOST API_PORT)
MISSING=()
for key in "${REQUIRED[@]}"; do
  if [ -z "${!key:-}" ]; then
    MISSING+=("$key")
  fi
done
if [ "${#MISSING[@]}" -ne 0 ]; then
  echo "❌ Missing env vars: ${MISSING[*]}"
  exit 1
fi
echo "✅ Env vars present"
echo "    NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}"
echo "    BACKEND_URL=${BACKEND_URL}"
echo "    COMFYUI_URL=${COMFYUI_URL}"
echo "    API_HOST=${API_HOST} API_PORT=${API_PORT}"

echo "==> Building frontend"
pushd "$ROOT_DIR/web" >/dev/null
npm ci --prefer-offline
npm run build
popd >/dev/null
echo "✅ Frontend build ok"

echo "==> Backend import/syntax check"
pushd "$ROOT_DIR/backend" >/dev/null
python -m compileall .
popd >/dev/null
echo "✅ Backend imports ok"

echo "==> Health check (if backend running locally)"
if curl -fsSL "${BACKEND_URL:-http://localhost:8000}/api/health" >/dev/null 2>&1; then
  echo "✅ /api/health reachable"
else
  echo "⚠️  /api/health not reachable; ensure backend is running or ignore for CI-only runs"
fi

echo "Preflight completed."


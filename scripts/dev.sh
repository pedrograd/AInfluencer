#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting backend (http://localhost:8000)…"
(
  cd "$ROOT_DIR/backend"
  # macOS note: default python3 can be 3.14 which is not supported.
  # Prefer Homebrew python3.13 if available.
  if [[ -z "${PY_BIN:-}" ]] && [[ -x "/opt/homebrew/bin/python3.13" ]]; then
    export PY_BIN="/opt/homebrew/bin/python3.13"
  fi
  bash ./run_dev.sh
) &
BACK_PID=$!

echo "Starting frontend (http://localhost:3000)…"
(
  cd "$ROOT_DIR/frontend"
  if command -v npm >/dev/null 2>&1; then
    npm install
  fi
  npm run dev
) &
FRONT_PID=$!

trap 'echo "Shutting down…"; kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true' INT TERM
wait "$BACK_PID" "$FRONT_PID"

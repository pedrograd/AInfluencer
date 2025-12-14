#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting backend (http://localhost:8000)…"
(
  cd "$ROOT_DIR/backend"
  bash ./run_dev.sh
) &
BACK_PID=$!

echo "Starting frontend (http://localhost:3000)…"
(
  cd "$ROOT_DIR/frontend"
  npm run dev
) &
FRONT_PID=$!

trap 'echo "Shutting down…"; kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true' INT TERM
wait "$BACK_PID" "$FRONT_PID"

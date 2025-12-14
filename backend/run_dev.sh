#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY_BIN="${PY_BIN:-}"
if [[ -z "$PY_BIN" ]]; then
  for cand in python3.13 python3.12 python3.11 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
      PY_BIN="$cand"
      break
    fi
  done
fi

if [[ -z "$PY_BIN" ]]; then
  echo "ERROR: Python not found. Install Python 3.12+ (recommended 3.13)." >&2
  exit 1
fi

PY_VER="$("$PY_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PY_VER" == "3.14" ]]; then
  echo "ERROR: Detected Python 3.14. This project currently requires Python 3.12/3.13 (pydantic-core wheels/build)." >&2
  echo "Install Python 3.13 (recommended) and re-run, or set PY_BIN=python3.13." >&2
  exit 1
fi

# If a venv already exists but was created with the wrong Python, recreate it.
if [[ -x ".venv/bin/python" ]]; then
  VENV_VER="$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [[ "$VENV_VER" != "$PY_VER" ]]; then
    echo "Recreating venv: existing=$VENV_VER desired=$PY_VER"
    rm -rf .venv
  fi
fi

"$PY_BIN" -m venv .venv
source .venv/bin/activate
# Use the venv interpreter for installs (avoids Homebrew PEP 668 restrictions).
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

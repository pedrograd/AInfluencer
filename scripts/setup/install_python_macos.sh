#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "ERROR: Homebrew not found. Install it from https://brew.sh/" >&2
  exit 1
fi

echo "Installing Python 3.13 via Homebrew…"
brew update
brew install python@3.13

echo "Done. Verify:" 
/opt/homebrew/bin/python3.13 --version

echo "Tip: run backend with: PY_BIN=/opt/homebrew/bin/python3.13 bash backend/run_dev.sh" 

#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "ERROR: Homebrew not found. Install it from https://brew.sh/" >&2
  exit 1
fi

echo "Installing Node.js (LTS) via Homebrew…"
brew update
brew install node

echo "Done. Verify:"
node --version
npm --version

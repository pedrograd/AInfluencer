#!/usr/bin/env bash

# Simple healthcheck script for the backend API
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"

echo "Pinging ${API_URL}/api/health ..."
curl -fsSL "${API_URL}/api/health" && echo "✅ Backend healthy"


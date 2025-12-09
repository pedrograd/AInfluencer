#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_URL="$(git -C "$ROOT_DIR" config --get remote.origin.url || echo "")"

echo "=== AInfluencer Deploy Bootstrap (bash) ==="
echo "Repo: ${REPO_URL:-unknown}"

command -v gh >/dev/null 2>&1 || { echo "❌ GitHub CLI (gh) not found. Install: https://cli.github.com/"; exit 1; }
if ! gh auth status >/dev/null 2>&1; then
  echo "❌ gh is not authenticated. Run: gh auth login"
  exit 1
fi

if ! command -v vercel >/dev/null 2>&1; then
  echo "ℹ️  Vercel CLI not found. Install with: npm i -g vercel"
fi

echo
echo "Enter provider tokens (leave blank to skip any secret). Values are written to GitHub Secrets for the current repo."

read -rsp "VERCEL_TOKEN: " VERCEL_TOKEN; echo
read -rp "VERCEL_ORG_ID (optional): " VERCEL_ORG_ID
read -rp "VERCEL_PROJECT_ID (optional): " VERCEL_PROJECT_ID
read -rsp "RENDER_API_KEY: " RENDER_API_KEY; echo
read -rp "RENDER_SERVICE_ID: " RENDER_SERVICE_ID

read -rp "NEXT_PUBLIC_API_URL (e.g., https://your-backend.onrender.com): " NEXT_PUBLIC_API_URL
read -rp "DEMO_MODE (true/false) [true]: " DEMO_MODE_INPUT
DEMO_MODE="${DEMO_MODE_INPUT:-true}"

declare -A secrets=(
  [VERCEL_TOKEN]="$VERCEL_TOKEN"
  [VERCEL_ORG_ID]="$VERCEL_ORG_ID"
  [VERCEL_PROJECT_ID]="$VERCEL_PROJECT_ID"
  [RENDER_API_KEY]="$RENDER_API_KEY"
  [RENDER_SERVICE_ID]="$RENDER_SERVICE_ID"
  [NEXT_PUBLIC_API_URL]="$NEXT_PUBLIC_API_URL"
  [DEMO_MODE]="$DEMO_MODE"
  [ENABLE_ADVANCED]=false
  [ENABLE_UPSCALE]=false
  [ENABLE_FACE_RESTORE]=false
  [ENABLE_BATCH]=false
  [ENABLE_HIGH_RES]=false
  [DEMO_MAX_WIDTH]=1024
  [DEMO_MAX_HEIGHT]=1024
  [DEMO_MAX_BATCH]=1
)

echo
echo "==> Writing GitHub Secrets (gh secret set)"
for key in "${!secrets[@]}"; do
  value="${secrets[$key]}"
  if [ -n "$value" ]; then
    gh secret set "$key" --body "$value" >/dev/null && echo "✅ $key set"
  else
    echo "⚠️  Skipping empty $key"
  fi
done

cat <<'EOF'
Next steps:
- Ensure Vercel project exists (root: /web) and has env vars mirrored from env.deploy.example.
- Ensure Render service exists and RENDER_SERVICE_ID matches the created service (use render.yaml as blueprint).
- Push to main to trigger .github/workflows/deploy.yml.

If you prefer manual secret entry, use:
  gh secret set VERCEL_TOKEN
  gh secret set VERCEL_ORG_ID
  gh secret set VERCEL_PROJECT_ID
  gh secret set RENDER_API_KEY
  gh secret set RENDER_SERVICE_ID
  gh secret set NEXT_PUBLIC_API_URL
  gh secret set DEMO_MODE ENABLE_ADVANCED ENABLE_UPSCALE ENABLE_FACE_RESTORE ENABLE_BATCH ENABLE_HIGH_RES DEMO_MAX_WIDTH DEMO_MAX_HEIGHT DEMO_MAX_BATCH
EOF


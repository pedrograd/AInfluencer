#!/usr/bin/env bash
# Sync key=value pairs from an env file into Fly secrets.
set -euo pipefail

ENV_FILE="${1:-.env}"
APP="${FLY_APP_NAME:-}"

if [[ -z "$APP" ]]; then
  echo "FLY_APP_NAME is required in env." >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

args=()
while IFS='=' read -r key value; do
  # skip blanks and comments
  [[ -z "${key// }" ]] && continue
  [[ "$key" =~ ^# ]] && continue
  args+=("$key=$value")
done < "$ENV_FILE"

if [[ ${#args[@]} -eq 0 ]]; then
  echo "No secrets parsed from $ENV_FILE" >&2
  exit 1
fi

flyctl secrets set "${args[@]}" --app "$APP"
#!/usr/bin/env bash
#
# Syncs secrets from an env file into Fly.io for automated deploys.
# Usage: FLY_APP_NAME=my-app ./deployment/scripts/fly_secrets_set.sh .env
# Requirements: flyctl installed and authenticated.
set -euo pipefail

ENV_FILE="${1:-.env}"

if ! command -v flyctl >/dev/null 2>&1; then
  echo "flyctl is required. Install: https://fly.io/docs/hands-on/install-flyctl/" >&2
  exit 1
fi

if [ -z "${FLY_APP_NAME:-}" ]; then
  echo "Set FLY_APP_NAME env var (your Fly app name)." >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

pairs=()
while IFS= read -r line || [ -n "$line" ]; do
  # Skip comments and blank lines
  trimmed="$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  [ -z "$trimmed" ] && continue
  [[ "$trimmed" =~ ^# ]] && continue

  key="${trimmed%%=*}"
  value="${trimmed#*=}"
  key="$(echo "$key" | xargs)"
  value="$(echo "$value" | xargs)"
  if [ -z "$key" ]; then
    continue
  fi
  pairs+=("${key}=${value}")
done < "$ENV_FILE"

if [ "${#pairs[@]}" -eq 0 ]; then
  echo "No secrets parsed from $ENV_FILE" >&2
  exit 1
fi

echo "Setting ${#pairs[@]} secrets on app ${FLY_APP_NAME}..."
flyctl secrets set "${pairs[@]}" --app "$FLY_APP_NAME"

echo "Done. Verify with: flyctl secrets list --app $FLY_APP_NAME"

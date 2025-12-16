#!/bin/bash
# Set sync role helper (Mac/Linux)
# Usage: ./scripts/sync/set_role.sh WRITER
#        ./scripts/sync/set_role.sh FOLLOWER

set -e

cd "$(dirname "$0")/../.."

ROLE="${1:-}"

if [ -z "$ROLE" ]; then
    echo "Usage: $0 WRITER|FOLLOWER"
    exit 1
fi

ROLE=$(echo "$ROLE" | tr '[:lower:]' '[:upper:]')

if [ "$ROLE" != "WRITER" ] && [ "$ROLE" != "FOLLOWER" ]; then
    echo "ERROR: Role must be WRITER or FOLLOWER"
    exit 1
fi

echo "$ROLE" > .sync-role
echo "✓ Role set to: $ROLE"
echo ""
echo "Next: Run ./sync (or SYNC.bat on Windows)"


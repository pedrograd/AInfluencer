#!/bin/bash
# Switch to writer role
# Usage: ./scripts/sync/switch-to-writer.sh

set -e

cd "$(dirname "$0")/../.."

echo "Switching to WRITER role..."

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "WARNING: Uncommitted changes detected."
    echo "Commit or stash before switching to writer."
    exit 1
fi

# Verify upstream
BRANCH=$(git branch --show-current)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")

if [ -z "$UPSTREAM" ]; then
    echo "Setting upstream to origin/$BRANCH..."
    git branch --set-upstream-to=origin/$BRANCH $BRANCH
    echo "✓ Upstream set"
else
    echo "✓ Upstream: $UPSTREAM"
fi

# Fetch latest
echo "Fetching latest..."
git fetch --all --prune >/dev/null 2>&1

# Check if behind
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
    echo "WARNING: Local branch is behind remote."
    echo "Run: git pull --ff-only"
fi

# Create role marker
echo "writer" > .sync-role
echo "✓ Role marker created"

echo ""
echo "✓ Ready to write. Use ./sync-writer.sh (or ./scripts/sync/writer-sync.sh) after commits."


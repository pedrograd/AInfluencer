#!/bin/bash
# Switch to follower role
# Usage: ./scripts/sync/switch-to-follower.sh

set -e

cd "$(dirname "$0")/../.."

echo "Switching to FOLLOWER role..."

# Ensure no local edits
if ! git diff-index --quiet HEAD --; then
    echo "ERROR: Uncommitted changes detected."
    echo "Commit, stash, or discard changes before switching to follower."
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

# Sync once
echo "Syncing once..."
git fetch --all --prune >/dev/null 2>&1
if git pull --ff-only >/dev/null 2>&1; then
    echo "✓ Synced"
else
    echo "WARNING: Could not fast-forward. Check status."
fi

# Create role marker
echo "follower" > .sync-role
echo "✓ Role marker created"

echo ""
echo "✓ Ready to follow. Run: ./sync-follower.sh"


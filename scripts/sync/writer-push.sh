#!/bin/bash
# Writer push script - Auto push after commit
# Usage: ./scripts/sync/writer-push.sh

set -e

cd "$(dirname "$0")/../.."

# Check if repo is clean or only has committed changes
if ! git diff-index --quiet HEAD --; then
    echo "ERROR: Uncommitted changes detected. Commit first."
    exit 1
fi

# Check if there are commits to push
if ! git rev-parse --verify origin/$(git branch --show-current) >/dev/null 2>&1; then
    echo "ERROR: Upstream branch not found. Set upstream first."
    exit 1
fi

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo "ERROR: Upstream not set. Run: git branch --set-upstream-to=origin/$(git branch --show-current)"
    exit 1
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✓ Already up to date. Nothing to push."
    exit 0
fi

# Push (never force push)
echo "Pushing to origin/$(git branch --show-current)..."
if git push; then
    echo "✓ Push successful"
else
    echo "✗ Push failed"
    exit 1
fi


#!/bin/bash
# Follower pull script - Safe auto-pull loop
# Usage: ./scripts/sync/follower-pull.sh
# Press Ctrl+C to stop

set -e

cd "$(dirname "$0")/../.."

echo "Starting follower pull loop (5s interval)..."
echo "Press Ctrl+C to stop"
echo ""

# Trap Ctrl+C
trap 'echo ""; echo "Stopped."; exit 0' INT

while true; do
    # Fetch all branches and prune
    git fetch --all --prune >/dev/null 2>&1 || true
    
    # Check for local changes
    if ! git diff-index --quiet HEAD --; then
        echo "STOP: Local changes detected. Commit or stash first."
        exit 1
    fi
    
    # Try to pull with --ff-only
    if git pull --ff-only >/dev/null 2>&1; then
        echo "[$(date +%H:%M:%S)] ✓ Synced"
    else
        # Check if it's just already up to date
        LOCAL=$(git rev-parse @)
        REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
        
        if [ -z "$REMOTE" ]; then
            echo "STOP: Upstream not set. Run: git branch --set-upstream-to=origin/$(git branch --show-current)"
            exit 1
        fi
        
        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "STOP: Local changes or diverged history. Cannot fast-forward."
            echo "      Local: $(git rev-parse --short @)"
            echo "      Remote: $(git rev-parse --short @{u})"
            exit 1
        fi
    fi
    
    sleep 5
done


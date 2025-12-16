#!/bin/bash
# Writer sync script - Pull latest then push safely
# Usage: ./scripts/sync/writer-sync.sh

set -e

cd "$(dirname "$0")/../.."

echo "Writer sync: Pulling latest, then pushing..."

# 1) Verify clean tree
if ! git diff-index --quiet HEAD --; then
    echo "ERROR: Uncommitted changes detected. Commit or stash first."
    exit 1
fi

# 2) Fetch all and prune
echo "Fetching latest from origin..."
git fetch --all --prune

# 3) Check upstream
BRANCH=$(git branch --show-current)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")

if [ -z "$UPSTREAM" ]; then
    echo "Setting upstream to origin/$BRANCH..."
    git branch --set-upstream-to=origin/$BRANCH $BRANCH
    UPSTREAM="origin/$BRANCH"
fi

# 4) Check if behind remote
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo "ERROR: Cannot read remote branch. Fetch first."
    exit 1
fi

if [ "$LOCAL" != "$REMOTE" ]; then
    # Check if we're behind (need to pull)
    BEHIND=$(git rev-list --count @..@{u} 2>/dev/null || echo "0")
    AHEAD=$(git rev-list --count @{u}..@ 2>/dev/null || echo "0")
    
    if [ "$BEHIND" -gt 0 ]; then
        echo "Local branch is behind remote by $BEHIND commits."
        echo "Pulling with rebase..."
        
        # Try rebase first (safer for linear history)
        if git pull --rebase >/dev/null 2>&1; then
            echo "✓ Rebased successfully"
        else
            # Rebase conflict - create backup and stop
            echo "✗ Rebase conflict detected!"
            echo "Creating backup branch..."
            BACKUP_BRANCH="backup/$(hostname)-$(date +%Y%m%d-%H%M%S)"
            if git branch "$BACKUP_BRANCH" 2>/dev/null; then
                echo "✓ Backup branch created: $BACKUP_BRANCH"
                echo ""
                echo "Next steps:"
                echo "  1. Resolve conflicts: git rebase --continue"
                echo "  2. Or abort: git rebase --abort"
                echo "  3. To recover: git checkout $BACKUP_BRANCH"
            fi
            exit 1
        fi
    fi
    
    # Check if we're ahead (need to push)
    if [ "$AHEAD" -gt 0 ]; then
        echo "Local branch is ahead by $AHEAD commits."
    fi
fi

# 5) Push (never force push)
if [ "$LOCAL" != "$REMOTE" ] || [ "$AHEAD" -gt 0 ]; then
    echo "Pushing to $UPSTREAM..."
    if git push; then
        echo "✓ Push successful"
    else
        echo "✗ Push failed or rejected"
        echo ""
        echo "If push was rejected, create backup and check for conflicts:"
        BACKUP_BRANCH="backup/$(hostname)-$(date +%Y%m%d-%H%M%S)"
        if git branch "$BACKUP_BRANCH" 2>/dev/null; then
            echo "✓ Backup branch created: $BACKUP_BRANCH"
        fi
        echo "Next: git pull --rebase, resolve conflicts, then push again"
        exit 1
    fi
else
    echo "✓ Already up to date. Nothing to push."
fi


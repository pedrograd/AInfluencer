#!/bin/bash
# Sync status script - Shows current repo state
# Usage: ./scripts/sync/status.sh

set -e

cd "$(dirname "$0")/../.."

echo "═══════════════════════════════════════════════════════════"
echo "SYNC STATUS"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Current branch
BRANCH=$(git branch --show-current)
echo "Branch: $BRANCH"

# HEAD hash
HEAD_HASH=$(git rev-parse HEAD)
HEAD_SHORT=$(git rev-parse --short HEAD)
echo "HEAD: $HEAD_SHORT ($HEAD_HASH)"

# Upstream
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "none")
if [ "$UPSTREAM" != "none" ]; then
    UPSTREAM_HASH=$(git rev-parse @{u} 2>/dev/null || echo "")
    if [ -n "$UPSTREAM_HASH" ]; then
        UPSTREAM_SHORT=$(git rev-parse --short @{u})
        echo "Upstream: $UPSTREAM ($UPSTREAM_SHORT)"
    else
        echo "Upstream: $UPSTREAM (not fetched)"
    fi
else
    echo "Upstream: not set"
fi

# Ahead/behind counts
if [ "$UPSTREAM" != "none" ] && [ -n "$UPSTREAM_HASH" ]; then
    AHEAD=$(git rev-list --count @{u}..@ 2>/dev/null || echo "0")
    BEHIND=$(git rev-list --count @..@{u} 2>/dev/null || echo "0")
    echo "Ahead: $AHEAD commits"
    echo "Behind: $BEHIND commits"
else
    echo "Ahead: ? (no upstream)"
    echo "Behind: ? (no upstream)"
fi

# Working tree status
if git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "Working tree: CLEAN"
else
    echo "Working tree: DIRTY (uncommitted changes)"
fi

# Role detection (check for marker file or env var)
ROLE_FILE=".sync-role"
if [ -f "$ROLE_FILE" ]; then
    ROLE=$(cat "$ROLE_FILE" 2>/dev/null | tr '[:upper:]' '[:lower:]' || echo "")
    if [ "$ROLE" = "writer" ] || [ "$ROLE" = "follower" ]; then
        echo "Role: ${ROLE^^}"
    else
        echo "Role: UNKNOWN (invalid marker)"
    fi
elif [ -n "$SYNC_ROLE" ]; then
    ROLE=$(echo "$SYNC_ROLE" | tr '[:upper:]' '[:lower:]')
    if [ "$ROLE" = "writer" ] || [ "$ROLE" = "follower" ]; then
        echo "Role: ${ROLE^^} (from env)"
    else
        echo "Role: UNKNOWN (invalid env)"
    fi
else
    echo "Role: NOT SET (use switch-to-writer.sh or switch-to-follower.sh)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"


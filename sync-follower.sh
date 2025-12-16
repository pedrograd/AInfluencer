#!/bin/bash
# Entrypoint for follower sync (Mac/Linux)
# Usage: ./sync-follower.sh

cd "$(dirname "$0")"
exec ./scripts/sync/follower-pull.sh


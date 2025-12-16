#!/bin/bash
# DEPRECATED: Use ./sync instead
# Entrypoint for follower sync (Mac/Linux)
# Usage: ./sync-follower.sh

echo "WARNING: This script is DEPRECATED. Use './sync' instead."
cd "$(dirname "$0")"
exec ./scripts/sync/follower-pull.sh


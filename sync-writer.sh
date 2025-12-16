#!/bin/bash
# DEPRECATED: Use ./sync with SYNC_ROLE=WRITER instead
# Entrypoint for writer sync (Mac/Linux)
# Usage: ./sync-writer.sh

echo "WARNING: This script is DEPRECATED. Use 'SYNC_ROLE=WRITER ./sync' instead."
cd "$(dirname "$0")"
exec ./scripts/sync/writer-sync.sh


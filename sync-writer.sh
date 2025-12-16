#!/bin/bash
# Entrypoint for writer sync (Mac/Linux)
# Usage: ./sync-writer.sh

cd "$(dirname "$0")"
exec ./scripts/sync/writer-sync.sh


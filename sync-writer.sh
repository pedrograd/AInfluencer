#!/bin/bash
# Entrypoint for writer push (Mac/Linux)
# Usage: ./sync-writer.sh

cd "$(dirname "$0")"
exec ./scripts/sync/writer-push.sh


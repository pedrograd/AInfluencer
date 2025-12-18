#!/bin/bash
# macOS entry point - double-click friendly launcher
# This file calls the canonical Node.js orchestrator

cd "$(dirname "$0")"
node scripts/one.mjs


#!/usr/bin/env bash
# Linux/macOS entry point - launcher wrapper
# This file calls the canonical Node.js orchestrator

cd "$(dirname "$0")"
node scripts/one.mjs

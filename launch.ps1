# PowerShell entry point - launcher wrapper
# This file calls the canonical Node.js orchestrator (scripts/one.mjs)
# All logic is centralized in one.mjs for cross-platform consistency

$ErrorActionPreference = 'Stop'

$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT_DIR

# Delegate to canonical orchestrator
node scripts/one.mjs

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nPress any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit $LASTEXITCODE
}

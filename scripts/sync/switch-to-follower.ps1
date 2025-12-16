# Switch to follower role
# Usage: .\scripts\sync\switch-to-follower.ps1

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..\..

Write-Host "Switching to FOLLOWER role..." -ForegroundColor Cyan

# Ensure no local edits
$status = git status --porcelain
if ($status) {
    Write-Host "ERROR: Uncommitted changes detected." -ForegroundColor Red
    Write-Host "Commit, stash, or discard changes before switching to follower." -ForegroundColor Red
    exit 1
}

# Verify upstream
$branch = git branch --show-current
$upstream = git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>$null

if (-not $upstream) {
    Write-Host "Setting upstream to origin/$branch..." -ForegroundColor Cyan
    git branch --set-upstream-to=origin/$branch $branch
    Write-Host "✓ Upstream set" -ForegroundColor Green
} else {
    Write-Host "✓ Upstream: $upstream" -ForegroundColor Green
}

# Sync once
Write-Host "Syncing once..." -ForegroundColor Cyan
git fetch --all --prune *>$null
$pullOutput = git pull --ff-only 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Synced" -ForegroundColor Green
} else {
    Write-Host "WARNING: Could not fast-forward. Check status." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✓ Ready to follow. Run: SYNC-FOLLOWER.bat" -ForegroundColor Green


# Switch to writer role
# Usage: .\scripts\sync\switch-to-writer.ps1

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..\..

Write-Host "Switching to WRITER role..." -ForegroundColor Cyan

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "WARNING: Uncommitted changes detected." -ForegroundColor Yellow
    Write-Host "Commit or stash before switching to writer." -ForegroundColor Yellow
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

# Fetch latest
Write-Host "Fetching latest..." -ForegroundColor Cyan
git fetch --all --prune *>$null

# Check if behind
$local = git rev-parse @
$remote = git rev-parse @{u} 2>$null

if ($remote -and $local -ne $remote) {
    Write-Host "WARNING: Local branch is behind remote." -ForegroundColor Yellow
    Write-Host "Run: git pull --ff-only" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✓ Ready to write. Use .\scripts\sync\writer-push.ps1 after commits." -ForegroundColor Green


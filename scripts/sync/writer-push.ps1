# Writer push script - Auto push after commit
# Usage: .\scripts\sync\writer-push.ps1

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..\..

# Check if repo is clean
$status = git status --porcelain
if ($status) {
    Write-Host "ERROR: Uncommitted changes detected. Commit first." -ForegroundColor Red
    exit 1
}

# Get current branch
$branch = git branch --show-current
if (-not $branch) {
    Write-Host "ERROR: Not on a branch" -ForegroundColor Red
    exit 1
}

# Check upstream
$upstream = git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>$null
if (-not $upstream) {
    Write-Host "ERROR: Upstream not set. Run: git branch --set-upstream-to=origin/$branch" -ForegroundColor Red
    exit 1
}

# Check if there are commits to push
$local = git rev-parse @
$remote = git rev-parse @{u} 2>$null

if (-not $remote) {
    Write-Host "ERROR: Cannot read remote branch" -ForegroundColor Red
    exit 1
}

if ($local -eq $remote) {
    Write-Host "✓ Already up to date. Nothing to push." -ForegroundColor Green
    exit 0
}

# Push (never force push)
Write-Host "Pushing to $upstream..." -ForegroundColor Cyan
try {
    git push
    Write-Host "✓ Push successful" -ForegroundColor Green
} catch {
    Write-Host "✗ Push failed" -ForegroundColor Red
    exit 1
}


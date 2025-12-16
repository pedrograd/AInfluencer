# Sync status script - Shows current repo state
# Usage: .\scripts\sync\status.ps1

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..\..

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SYNC STATUS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Current branch
$branch = git branch --show-current
Write-Host "Branch: $branch"

# HEAD hash
$headHash = git rev-parse HEAD
$headShort = git rev-parse --short HEAD
Write-Host "HEAD: $headShort ($headHash)"

# Upstream
$upstream = git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>$null
if ($upstream) {
    $upstreamHash = git rev-parse @{u} 2>$null
    if ($upstreamHash) {
        $upstreamShort = git rev-parse --short @{u}
        Write-Host "Upstream: $upstream ($upstreamShort)"
    } else {
        Write-Host "Upstream: $upstream (not fetched)"
    }
} else {
    Write-Host "Upstream: not set"
}

# Ahead/behind counts
if ($upstream -and $upstreamHash) {
    $ahead = git rev-list --count "@{u}..@" 2>$null
    if (-not $ahead) { $ahead = "0" }
    $behind = git rev-list --count "@..@{u}" 2>$null
    if (-not $behind) { $behind = "0" }
    Write-Host "Ahead: $ahead commits"
    Write-Host "Behind: $behind commits"
} else {
    Write-Host "Ahead: ? (no upstream)"
    Write-Host "Behind: ? (no upstream)"
}

# Working tree status
$status = git status --porcelain
if ($status) {
    Write-Host "Working tree: DIRTY (uncommitted changes)" -ForegroundColor Red
} else {
    Write-Host "Working tree: CLEAN" -ForegroundColor Green
}

# Role detection (check for marker file or env var)
$roleFile = ".sync-role"
if (Test-Path $roleFile) {
    $role = (Get-Content $roleFile -ErrorAction SilentlyContinue | ForEach-Object { $_.ToLower() })
    if ($role -eq "writer" -or $role -eq "follower") {
        Write-Host "Role: $($role.ToUpper())"
    } else {
        Write-Host "Role: UNKNOWN (invalid marker)" -ForegroundColor Yellow
    }
} elseif ($env:SYNC_ROLE) {
    $role = $env:SYNC_ROLE.ToLower()
    if ($role -eq "writer" -or $role -eq "follower") {
        Write-Host "Role: $($role.ToUpper()) (from env)"
    } else {
        Write-Host "Role: UNKNOWN (invalid env)" -ForegroundColor Yellow
    }
} else {
    Write-Host "Role: NOT SET (use switch-to-writer.ps1 or switch-to-follower.ps1)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan


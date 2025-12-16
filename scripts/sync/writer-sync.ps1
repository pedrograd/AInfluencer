# Writer sync script - Pull latest then push safely
# Usage: .\scripts\sync\writer-sync.ps1

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..\..

Write-Host "Writer sync: Pulling latest, then pushing..." -ForegroundColor Cyan

# 1) Verify clean tree
$status = git status --porcelain
if ($status) {
    Write-Host "ERROR: Uncommitted changes detected. Commit or stash first." -ForegroundColor Red
    exit 1
}

# 2) Fetch all and prune
Write-Host "Fetching latest from origin..." -ForegroundColor Cyan
git fetch --all --prune *>$null

# 3) Check upstream
$branch = git branch --show-current
$upstream = git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>$null

if (-not $upstream) {
    Write-Host "Setting upstream to origin/$branch..." -ForegroundColor Cyan
    git branch --set-upstream-to=origin/$branch $branch
    $upstream = "origin/$branch"
}

# 4) Check if behind remote
$local = git rev-parse @
$remote = git rev-parse @{u} 2>$null

if (-not $remote) {
    Write-Host "ERROR: Cannot read remote branch. Fetch first." -ForegroundColor Red
    exit 1
}

if ($local -ne $remote) {
    # Check if we're behind (need to pull)
    $behind = git rev-list --count "@..@{u}" 2>$null
    if (-not $behind) { $behind = "0" }
    $ahead = git rev-list --count "@{u}..@" 2>$null
    if (-not $ahead) { $ahead = "0" }
    
    if ([int]$behind -gt 0) {
        Write-Host "Local branch is behind remote by $behind commits." -ForegroundColor Yellow
        Write-Host "Pulling with rebase..." -ForegroundColor Cyan
        
        # Try rebase first (safer for linear history)
        try {
            git pull --rebase *>$null
            Write-Host "✓ Rebased successfully" -ForegroundColor Green
        } catch {
            # Rebase conflict - create backup and stop
            Write-Host "✗ Rebase conflict detected!" -ForegroundColor Red
            Write-Host "Creating backup branch..." -ForegroundColor Yellow
            $hostname = $env:COMPUTERNAME
            if (-not $hostname) { $hostname = "windows" }
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            $backupBranch = "backup/$hostname-$timestamp"
            try {
                git branch $backupBranch 2>$null
                Write-Host "✓ Backup branch created: $backupBranch" -ForegroundColor Green
                Write-Host ""
                Write-Host "Next steps:" -ForegroundColor Cyan
                Write-Host "  1. Resolve conflicts: git rebase --continue" -ForegroundColor Cyan
                Write-Host "  2. Or abort: git rebase --abort" -ForegroundColor Cyan
                Write-Host "  3. To recover: git checkout $backupBranch" -ForegroundColor Cyan
            } catch {
                Write-Host "✗ Failed to create backup branch" -ForegroundColor Red
            }
            exit 1
        }
    }
    
    # Check if we're ahead (need to push)
    if ([int]$ahead -gt 0) {
        Write-Host "Local branch is ahead by $ahead commits." -ForegroundColor Cyan
    }
}

# 5) Push (never force push)
if ($local -ne $remote -or [int]$ahead -gt 0) {
    Write-Host "Pushing to $upstream..." -ForegroundColor Cyan
    try {
        git push
        Write-Host "✓ Push successful" -ForegroundColor Green
    } catch {
        Write-Host "✗ Push failed or rejected" -ForegroundColor Red
        Write-Host ""
        Write-Host "If push was rejected, create backup and check for conflicts:" -ForegroundColor Yellow
        $hostname = $env:COMPUTERNAME
        if (-not $hostname) { $hostname = "windows" }
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backupBranch = "backup/$hostname-$timestamp"
        try {
            git branch $backupBranch 2>$null
            Write-Host "✓ Backup branch created: $backupBranch" -ForegroundColor Green
        } catch {
            Write-Host "✗ Failed to create backup branch" -ForegroundColor Red
        }
        Write-Host "Next: git pull --rebase, resolve conflicts, then push again" -ForegroundColor Cyan
        exit 1
    }
} else {
    Write-Host "✓ Already up to date. Nothing to push." -ForegroundColor Green
}


# Follower pull script - Safe auto-pull loop
# Usage: .\scripts\sync\follower-pull.ps1
# Press Ctrl+C to stop

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..\..

Write-Host "Starting follower pull loop (5s interval)..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        # Fetch all branches and prune
        git fetch --all --prune *>$null
        
        # Check for local changes
        $status = git status --porcelain
        if ($status) {
            Write-Host "STOP: Local changes detected. Commit or stash first." -ForegroundColor Red
            exit 1
        }
        
        # Try to pull with --ff-only
        $pullOutput = git pull --ff-only 2>&1
        $pullSuccess = $LASTEXITCODE -eq 0
        
        if ($pullSuccess) {
            $time = Get-Date -Format "HH:mm:ss"
            Write-Host "[$time] ✓ Synced" -ForegroundColor Green
        } else {
            # Check if it's just already up to date
            $local = git rev-parse @
            $remote = git rev-parse @{u} 2>$null
            
            if (-not $remote) {
                $branch = git branch --show-current
                Write-Host "STOP: Upstream not set. Run: git branch --set-upstream-to=origin/$branch" -ForegroundColor Red
                exit 1
            }
            
            if ($local -ne $remote) {
                $localShort = git rev-parse --short @
                $remoteShort = git rev-parse --short @{u}
                Write-Host "STOP: Local changes or diverged history. Cannot fast-forward." -ForegroundColor Red
                Write-Host "      Local: $localShort" -ForegroundColor Red
                Write-Host "      Remote: $remoteShort" -ForegroundColor Red
                exit 1
            }
        }
        
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "`nStopped." -ForegroundColor Yellow
    exit 0
}


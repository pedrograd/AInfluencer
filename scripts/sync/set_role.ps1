# Set sync role helper (Windows)
# Usage: .\scripts\sync\set_role.ps1 WRITER
#        .\scripts\sync\set_role.ps1 FOLLOWER

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..\..

$role = $args[0]

if (-not $role) {
    Write-Host "Usage: .\scripts\sync\set_role.ps1 WRITER|FOLLOWER" -ForegroundColor Red
    exit 1
}

$role = $role.ToUpper()

if ($role -ne "WRITER" -and $role -ne "FOLLOWER") {
    Write-Host "ERROR: Role must be WRITER or FOLLOWER" -ForegroundColor Red
    exit 1
}

$role | Out-File -FilePath ".sync-role" -Encoding utf8 -NoNewline
Write-Host "✓ Role set to: $role" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Run SYNC.bat"


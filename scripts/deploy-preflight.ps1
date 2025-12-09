param(
    [string]$BackendUrl = $env:BACKEND_URL
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Import-DotEnv {
    param(
        [string]$Path
    )

    if (-not (Test-Path $Path)) { return }

    Write-Host "Loading env from $Path"
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }

        $pair = $line -split "=", 2
        if ($pair.Count -ne 2) { return }

        $key = $pair[0].Trim()
        $value = $pair[1].Trim().Trim('"')

        $existing = Get-Item "Env:$key" -ErrorAction SilentlyContinue
        if (-not $existing) {
            [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

$envFiles = @(
    "$root\.env",
    "$root\env.deploy",
    "$root\backend\.env",
    "$root\web\.env.local"
)

foreach ($file in $envFiles) { Import-DotEnv -Path $file }

if (-not $env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL = "http://localhost:8000" }
if (-not $env:BACKEND_URL) { $env:BACKEND_URL = $env:NEXT_PUBLIC_API_URL }
if (-not $env:COMFYUI_URL -and $env:NEXT_PUBLIC_COMFYUI_URL) { $env:COMFYUI_URL = $env:NEXT_PUBLIC_COMFYUI_URL }
if (-not $env:COMFYUI_URL) { $env:COMFYUI_URL = "http://localhost:8188" }
if (-not $env:API_HOST) { $env:API_HOST = "0.0.0.0" }
if (-not $env:API_PORT) { $env:API_PORT = "8000" }

if (-not $BackendUrl) { $BackendUrl = $env:BACKEND_URL }

Write-Host "==> Checking required environment variables (public vs server)"
$required = @("NEXT_PUBLIC_API_URL", "BACKEND_URL", "COMFYUI_URL", "API_HOST", "API_PORT")
$missing = @()
foreach ($key in $required) {
    $val = Get-Item "Env:$key" -ErrorAction SilentlyContinue
    if (-not $val) { $missing += $key }
}
if ($missing.Count -gt 0) {
    Write-Host "❌ Missing env vars: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Set them, then rerun. Example for localhost:" -ForegroundColor Yellow
    Write-Host '$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"' -ForegroundColor DarkGray
    Write-Host '$env:BACKEND_URL         = $env:NEXT_PUBLIC_API_URL' -ForegroundColor DarkGray
    Write-Host '$env:COMFYUI_URL         = "http://localhost:8188"' -ForegroundColor DarkGray
    Write-Host '$env:API_HOST            = "0.0.0.0"' -ForegroundColor DarkGray
    Write-Host '$env:API_PORT            = "8000"' -ForegroundColor DarkGray
    exit 1
}
Write-Host "✅ Env vars present"
Write-Host "    NEXT_PUBLIC_API_URL=$($env:NEXT_PUBLIC_API_URL)"
Write-Host "    BACKEND_URL=$($env:BACKEND_URL)"
Write-Host "    COMFYUI_URL=$($env:COMFYUI_URL)"
Write-Host "    API_HOST=$($env:API_HOST) API_PORT=$($env:API_PORT)"

Write-Host "==> Building frontend"
Push-Location "$root\web"
npm ci --prefer-offline
npm run build
Pop-Location
Write-Host "✅ Frontend build ok"

Write-Host "==> Backend import/syntax check"
Push-Location "$root\backend"
python -m compileall .
Pop-Location
Write-Host "✅ Backend imports ok"

$healthUrl = if ($BackendUrl) { "$BackendUrl/api/health" } else { "http://localhost:8000/api/health" }
Write-Host "==> Health check (if backend running): $healthUrl"
try {
    Invoke-WebRequest -UseBasicParsing -Uri $healthUrl | Out-Null
    Write-Host "✅ /api/health reachable"
} catch {
    Write-Warning "⚠️  /api/health not reachable; ensure backend is running or ignore for CI-only runs"
}

Write-Host "Preflight completed."


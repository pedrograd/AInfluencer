# Start Frontend on Port 3001
# Use this if you specifically need port 3001

$ErrorActionPreference = "Continue"

Write-Host "🌐 Starting Frontend on Port 3001..." -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "web" -PathType Container)) {
    Write-Host "❌ Error: Must run from project root directory" -ForegroundColor Red
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path "web\node_modules")) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location web
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    Set-Location ..
}

# Check if port 3001 is available
function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
        return $connection
    } catch {
        return $false
    }
}

if (Test-Port 3001) {
    Write-Host "⚠️  Port 3001 is already in use!" -ForegroundColor Yellow
    Write-Host "   Trying to stop existing process..." -ForegroundColor Yellow
    $processes = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $processes) {
        if ($pid) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
}

# Start frontend
Write-Host "🚀 Starting Next.js on port 3001..." -ForegroundColor Cyan
Set-Location web
Start-Process npm -ArgumentList "run", "dev:3001" -WindowStyle Normal
Set-Location ..

Write-Host ""
Write-Host "✅ Frontend starting on http://localhost:3001" -ForegroundColor Green
Write-Host "   Wait a few seconds for it to compile..." -ForegroundColor Yellow
Write-Host ""

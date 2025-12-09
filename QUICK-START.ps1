# Quick Start Script - Fixes and Starts Everything
# Run this to fix connection issues and start all services

$ErrorActionPreference = "Continue"

Write-Host "🚀 AInfluencer Quick Start" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop existing processes
Write-Host "1️⃣  Stopping existing processes..." -ForegroundColor Yellow
$ports = @(3000, 3001, 8000, 8188)
foreach ($port in $ports) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        foreach ($conn in $connections) {
            if ($conn.OwningProcess) {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                Write-Host "   Stopped process on port $port" -ForegroundColor Gray
            }
        }
    } catch {}
}
Start-Sleep -Seconds 2
Write-Host "   ✅ Done" -ForegroundColor Green
Write-Host ""

# Step 2: Check and create .env.local
Write-Host "2️⃣  Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path "web\.env.local")) {
    Write-Host "   Creating .env.local..." -ForegroundColor Gray
    @"
NEXT_PUBLIC_API_URL=http://localhost:8000
"@ | Out-File -FilePath "web\.env.local" -Encoding UTF8 -Force
    Write-Host "   ✅ Created .env.local" -ForegroundColor Green
} else {
    Write-Host "   ✅ .env.local exists" -ForegroundColor Green
}
Write-Host ""

# Step 3: Check dependencies
Write-Host "3️⃣  Checking dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "web\node_modules")) {
    Write-Host "   Installing frontend dependencies..." -ForegroundColor Gray
    Set-Location web
    npm install --silent
    Set-Location ..
    Write-Host "   ✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ✅ Frontend dependencies OK" -ForegroundColor Green
}
Write-Host ""

# Step 4: Start Backend
Write-Host "4️⃣  Starting Backend API..." -ForegroundColor Yellow
$backendDir = Join-Path $PWD "backend"
$backendScript = @"
@echo off
cd /d "$backendDir"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
"@
$tempBackend = Join-Path $env:TEMP "start-backend-$(Get-Random).bat"
$backendScript | Out-File -FilePath $tempBackend -Encoding ASCII -Force
Start-Process cmd.exe -ArgumentList "/k", "`"$tempBackend`"" -WindowStyle Normal
Write-Host "   ✅ Backend starting in new window" -ForegroundColor Green
Write-Host "   Waiting for backend to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Wait for backend
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}
if ($backendReady) {
    Write-Host "   ✅ Backend ready at http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Backend may still be starting..." -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Start Frontend
Write-Host "5️⃣  Starting Frontend..." -ForegroundColor Yellow
$webDir = Join-Path $PWD "web"
$frontendScript = @"
@echo off
cd /d "$webDir"
npm run dev
pause
"@
$tempFrontend = Join-Path $env:TEMP "start-frontend-$(Get-Random).bat"
$frontendScript | Out-File -FilePath $tempFrontend -Encoding ASCII -Force
Start-Process cmd.exe -ArgumentList "/k", "`"$tempFrontend`"" -WindowStyle Normal
Write-Host "   ✅ Frontend starting in new window" -ForegroundColor Green
Write-Host "   Waiting for frontend to compile..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Wait for frontend
$frontendReady = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $frontendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if ($frontendReady) {
    Write-Host "   ✅ Frontend ready at http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Frontend may still be compiling..." -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "  • API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: Use port 3000, not 3001!" -ForegroundColor Yellow
Write-Host "   The frontend runs on port 3000 by default." -ForegroundColor Yellow
Write-Host ""
Write-Host "Opening browser in 3 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

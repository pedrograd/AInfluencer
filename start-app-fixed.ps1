# Fixed Startup Script for AInfluencer
# This script properly starts backend and frontend with error checking

$ErrorActionPreference = "Continue"

Write-Host "🚀 Starting AInfluencer Application..." -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found! Please install Node.js" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check Backend Dependencies
Write-Host "Checking backend dependencies..." -ForegroundColor Yellow
cd backend
try {
    python -c "import fastapi, uvicorn" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Backend dependencies missing. Installing..." -ForegroundColor Yellow
        pip install -r requirements.txt --quiet
        Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "✅ Backend dependencies OK" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Installing backend dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet
}
cd ..

Write-Host ""

# Check Frontend Dependencies
Write-Host "Checking frontend dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "web\node_modules")) {
    Write-Host "⚠️  Frontend dependencies missing. Installing..." -ForegroundColor Yellow
    cd web
    npm install
    cd ..
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Frontend dependencies OK" -ForegroundColor Green
}

Write-Host ""

# Stop any existing services
Write-Host "Stopping existing services..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*main.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.ProcessName -eq "node" -and $_.CommandLine -like "*next*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Check if ports are available
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
    return $connection
}

if (Test-Port 8000) {
    Write-Host "⚠️  Port 8000 is already in use" -ForegroundColor Yellow
}
if (Test-Port 3000) {
    Write-Host "⚠️  Port 3000 is already in use" -ForegroundColor Yellow
}

Write-Host ""

# Start Backend
Write-Host "Starting Backend API on port 8000..." -ForegroundColor Cyan
cd backend
$backendProcess = Start-Process -FilePath "python" -ArgumentList "main.py" -WindowStyle Normal -PassThru
cd ..
Start-Sleep -Seconds 3

# Wait for backend to be ready
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Backend is running at http://localhost:8000" -ForegroundColor Green
            Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Gray
            $backendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $backendReady) {
    Write-Host "❌ Backend failed to start. Check the backend window for errors." -ForegroundColor Red
}

Write-Host ""

# Start Frontend
Write-Host "Starting Frontend on port 3000..." -ForegroundColor Cyan
cd web
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WindowStyle Normal -PassThru
cd ..
Start-Sleep -Seconds 5

# Wait for frontend to be ready
Write-Host "Waiting for frontend to start..." -ForegroundColor Yellow
$frontendReady = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Frontend is running at http://localhost:3000" -ForegroundColor Green
            $frontendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $frontendReady) {
    Write-Host "⚠️  Frontend may still be starting. Check the frontend window for progress." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Startup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

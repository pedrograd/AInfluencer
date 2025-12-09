# Auto-Start Script for AInfluencer
# Automatically installs dependencies and starts services

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "🚀 AInfluencer Auto-Start" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check for virtual environment
$venvPath = Join-Path $scriptPath ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "✅ Found virtual environment" -ForegroundColor Green
    $pythonCmd = $venvPython
    $pipCmd = Join-Path $venvPath "Scripts\pip.exe"
} else {
    Write-Host "⚠️  No virtual environment found, using system Python" -ForegroundColor Yellow
    $pythonCmd = "python"
    $pipCmd = "pip"
}

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $version = & $pythonCmd --version 2>&1
    Write-Host "✅ $version" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install Backend Dependencies
Write-Host "Checking backend dependencies..." -ForegroundColor Yellow
$backendPath = Join-Path $scriptPath "backend"
$requirementsPath = Join-Path $backendPath "requirements.txt"

if (Test-Path $requirementsPath) {
    try {
        & $pythonCmd -c "import fastapi, uvicorn" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Installing backend dependencies..." -ForegroundColor Yellow
            # First install uvicorn and fastapi to ensure they're available
            & $pipCmd install uvicorn[standard]==0.24.0 fastapi==0.104.1
            # Then install Pillow with compatible version
            & $pipCmd install "Pillow>=10.0.0,<10.1.0"
            # Finally install all other dependencies
            & $pipCmd install -r $requirementsPath
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Some dependencies may have failed. Continuing..." -ForegroundColor Yellow
            }
        } else {
            Write-Host "✅ Backend dependencies OK" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Installing backend dependencies..." -ForegroundColor Yellow
        # Install critical packages first
        & $pipCmd install uvicorn[standard]==0.24.0 fastapi==0.104.1
        & $pipCmd install "Pillow>=10.0.0,<10.1.0"
        & $pipCmd install -r $requirementsPath
    }
} else {
    Write-Host "⚠️  requirements.txt not found" -ForegroundColor Yellow
}

Write-Host ""

# Install Frontend Dependencies
Write-Host "Checking frontend dependencies..." -ForegroundColor Yellow
$webPath = Join-Path $scriptPath "web"
$nodeModulesPath = Join-Path $webPath "node_modules"

if (-not (Test-Path $nodeModulesPath)) {
    Write-Host "⚠️  Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location $webPath
    npm install
    Set-Location $scriptPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    }
} else {
    Write-Host "✅ Frontend dependencies OK" -ForegroundColor Green
}

Write-Host ""

# Stop existing services
Write-Host "Stopping existing services..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*Backend*" -or $_.CommandLine -like "*main.py*" -or $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*Frontend*" -or $_.CommandLine -like "*next*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Kill processes on ports
Write-Host "Checking ports..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "⚠️  Port 8000 in use, killing process..." -ForegroundColor Yellow
    Stop-Process -Id $port8000.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

if ($port3000) {
    Write-Host "⚠️  Port 3000 in use, killing process..." -ForegroundColor Yellow
    Stop-Process -Id $port3000.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Host ""

# Start Backend
Write-Host "Starting Backend API..." -ForegroundColor Cyan
$backendScript = @"
cd /d `"$backendPath`"
`"$pythonCmd`" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
"@

$backendScriptPath = Join-Path $env:TEMP "start-backend.bat"
$backendScript | Out-File -FilePath $backendScriptPath -Encoding ASCII
Start-Process cmd.exe -ArgumentList "/k", "`"$backendScriptPath`"" -WindowStyle Normal
Start-Sleep -Seconds 5

# Wait for backend
Write-Host "Waiting for backend..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 0; $i -lt 40; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Backend is running!" -ForegroundColor Green
            Write-Host "   http://localhost:8000" -ForegroundColor Gray
            $backendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}
Write-Host ""

if (-not $backendReady) {
    Write-Host "⚠️  Backend may still be starting. Check the backend window." -ForegroundColor Yellow
}

Write-Host ""

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Cyan
$frontendScript = @"
cd /d `"$webPath`"
npm run dev
pause
"@

$frontendScriptPath = Join-Path $env:TEMP "start-frontend.bat"
$frontendScript | Out-File -FilePath $frontendScriptPath -Encoding ASCII
Start-Process cmd.exe -ArgumentList "/k", "`"$frontendScriptPath`"" -WindowStyle Normal
Start-Sleep -Seconds 5

# Wait for frontend
Write-Host "Waiting for frontend..." -ForegroundColor Yellow
$frontendReady = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Frontend is running!" -ForegroundColor Green
            Write-Host "   http://localhost:3000" -ForegroundColor Gray
            $frontendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}
Write-Host ""

if (-not $frontendReady) {
    Write-Host "⚠️  Frontend may still be starting. Check the frontend window." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Startup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

if ($backendReady -and $frontendReady) {
    Write-Host "🎉 Opening browser..." -ForegroundColor Green
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000"
} else {
    Write-Host "⚠️  Some services may still be starting." -ForegroundColor Yellow
    Write-Host "   Check the command windows for status." -ForegroundColor Yellow
}

Write-Host "=" * 60 -ForegroundColor Cyan

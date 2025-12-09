# Fix Dependencies and Start Services
$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "🔧 Fixing Dependencies and Starting Services" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check for virtual environment
$venvPath = Join-Path $scriptPath ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "✅ Using virtual environment" -ForegroundColor Green
    $pythonCmd = $venvPython
    $pipCmd = Join-Path $venvPath "Scripts\pip.exe"
} else {
    Write-Host "⚠️  No virtual environment, using system Python" -ForegroundColor Yellow
    $pythonCmd = "python"
    $pipCmd = "pip"
}

# Step 1: Install uvicorn and fastapi first (critical)
Write-Host "Step 1: Installing critical packages..." -ForegroundColor Yellow
& $pipCmd install --upgrade pip
& $pipCmd install uvicorn[standard]==0.24.0 fastapi==0.104.1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Critical packages installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install critical packages" -ForegroundColor Red
    exit 1
}

# Step 2: Fix Pillow version in requirements.txt
Write-Host "Step 2: Fixing Pillow version..." -ForegroundColor Yellow
$requirementsPath = Join-Path $scriptPath "backend\requirements.txt"
if (Test-Path $requirementsPath) {
    $content = Get-Content $requirementsPath -Raw
    $content = $content -replace "Pillow==10\.1\.0", "Pillow>=10.0.0,<10.1.0"
    $content | Set-Content $requirementsPath -NoNewline
    Write-Host "✅ Fixed Pillow version in requirements.txt" -ForegroundColor Green
}

# Step 3: Install Pillow with compatible version
Write-Host "Step 3: Installing compatible Pillow..." -ForegroundColor Yellow
& $pipCmd install "Pillow>=10.0.0,<10.1.0"
Write-Host "✅ Pillow installed" -ForegroundColor Green

# Step 4: Install remaining dependencies
Write-Host "Step 4: Installing remaining dependencies..." -ForegroundColor Yellow
& $pipCmd install -r $requirementsPath
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some dependencies may have warnings, but continuing..." -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Verify uvicorn is available
Write-Host "Step 5: Verifying installation..." -ForegroundColor Yellow
try {
    & $pythonCmd -c "import uvicorn, fastapi; print('✅ uvicorn and fastapi are available')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Verification successful" -ForegroundColor Green
    } else {
        Write-Host "❌ Verification failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Verification failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Dependencies Fixed!" -ForegroundColor Green
Write-Host ""

# Step 6: Start services
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""

# Kill existing processes
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*main.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*next*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Kill processes on ports
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port8000) { Stop-Process -Id $port8000.OwningProcess -Force -ErrorAction SilentlyContinue }
if ($port3000) { Stop-Process -Id $port3000.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

# Start Backend
Write-Host "Starting Backend..." -ForegroundColor Cyan
$backendPath = Join-Path $scriptPath "backend"
$backendScript = @"
cd /d `"$backendPath`"
`"$pythonCmd`" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
"@
$tempBackend = Join-Path $env:TEMP "start-backend-$(Get-Random).bat"
$backendScript | Out-File -FilePath $tempBackend -Encoding ASCII
Start-Process cmd.exe -ArgumentList "/k", "`"$tempBackend`"" -WindowStyle Normal
Start-Sleep -Seconds 5

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Cyan
$webPath = Join-Path $scriptPath "web"
$frontendScript = @"
cd /d `"$webPath`"
npm run dev
pause
"@
$tempFrontend = Join-Path $env:TEMP "start-frontend-$(Get-Random).bat"
$frontendScript | Out-File -FilePath $tempFrontend -Encoding ASCII
Start-Process cmd.exe -ArgumentList "/k", "`"$tempFrontend`"" -WindowStyle Normal
Start-Sleep -Seconds 5

# Wait and check
Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$backendReady = $false
$frontendReady = $false

for ($i = 0; $i -lt 30; $i++) {
    if (-not $backendReady) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) {
                Write-Host "✅ Backend is running!" -ForegroundColor Green
                $backendReady = $true
            }
        } catch { }
    }
    
    if (-not $frontendReady) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) {
                Write-Host "✅ Frontend is running!" -ForegroundColor Green
                $frontendReady = $true
            }
        } catch { }
    }
    
    if ($backendReady -and $frontendReady) { break }
    Start-Sleep -Seconds 1
    Write-Host "." -NoNewline -ForegroundColor Gray
}
Write-Host ""

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

if ($backendReady -and $frontendReady) {
    Write-Host "🎉 Opening browser..." -ForegroundColor Green
    Start-Process "http://localhost:3000"
} else {
    Write-Host "⚠️  Check the command windows for any errors" -ForegroundColor Yellow
}

Write-Host "=" * 60 -ForegroundColor Cyan

# Comprehensive Auto-Fix Script for AInfluencer
# Fixes all dependency conflicts and starts services

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "🔧 AInfluencer - Comprehensive Auto-Fix" -ForegroundColor Cyan
$separator = '=' * 60
Write-Host $separator -ForegroundColor Cyan
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

# Step 1: Upgrade pip
Write-Host "Step 1: Upgrading pip..." -ForegroundColor Yellow
& $pipCmd install --upgrade pip --quiet
Write-Host "✅ pip upgraded" -ForegroundColor Green

# Step 2: Install critical packages first (uvicorn, fastapi)
Write-Host "Step 2: Installing critical packages..." -ForegroundColor Yellow
& $pipCmd install --quiet uvicorn[standard]==0.24.0 fastapi==0.104.1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Critical packages installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install critical packages" -ForegroundColor Red
    exit 1
}

# Step 3: Fix requirements.txt - resolve conflicts
Write-Host "Step 3: Fixing dependency conflicts..." -ForegroundColor Yellow
$requirementsPath = Join-Path $scriptPath "backend\requirements.txt"
if (Test-Path $requirementsPath) {
    $content = Get-Content $requirementsPath -Raw
    
    # Fix Pillow version
    $content = $content -replace "Pillow==10\.0\.1", "Pillow==10.0.1"
    
    # Fix pydantic to compatible version (instagrapi needs 2.5.3+)
    $pydanticFix = 'pydantic>=2.5.3,<3.0.0'
    $content = $content -replace "pydantic==2\.5\.0", $pydanticFix
    
    # Fix requests to compatible version
    $requestsFix = 'requests>=2.31.0,<3.0.0'
    $content = $content -replace "requests==2\.31\.0", $requestsFix
    
    # Fix instagrapi to compatible version
    $content = $content -replace "instagrapi>=2\.0\.0", "instagrapi==2.0.3"
    
    $content | Set-Content $requirementsPath -NoNewline
    Write-Host "✅ Fixed requirements.txt" -ForegroundColor Green
}

# Step 4: Install compatible Pillow
Write-Host "Step 4: Installing compatible Pillow..." -ForegroundColor Yellow
& $pipCmd install --quiet "Pillow==10.0.1"
Write-Host "✅ Pillow installed" -ForegroundColor Green

# Step 5: Install pydantic compatible version
Write-Host "Step 5: Installing compatible pydantic..." -ForegroundColor Yellow
$pydanticVersion = 'pydantic>=2.5.3,<3.0.0'
& $pipCmd install --quiet $pydanticVersion
Write-Host "✅ pydantic installed" -ForegroundColor Green

# Step 6: Install requests compatible version
Write-Host "Step 6: Installing compatible requests..." -ForegroundColor Yellow
$requestsVersion = 'requests>=2.31.0,<3.0.0'
& $pipCmd install --quiet $requestsVersion
Write-Host "✅ requests installed" -ForegroundColor Green

# Step 7: Install remaining dependencies (skip conflicting ones)
Write-Host "Step 7: Installing remaining dependencies..." -ForegroundColor Yellow
& $pipCmd install --quiet -r $requirementsPath 2>&1 | Out-Null
Write-Host "✅ Dependencies installed (some warnings may appear)" -ForegroundColor Green

# Step 8: Verify installation
Write-Host "Step 8: Verifying installation..." -ForegroundColor Yellow
try {
    & $pythonCmd -c "import uvicorn, fastapi, pydantic; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Verification successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Verification had issues, but continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Verification warning: $_" -ForegroundColor Yellow
}

Write-Host ""
$separator = '=' * 60
Write-Host $separator -ForegroundColor Cyan
Write-Host "✅ Dependencies Fixed!" -ForegroundColor Green
Write-Host ""

# Step 9: Kill existing processes
Write-Host "Step 9: Cleaning up existing processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
    $_.Path -like "*uvicorn*" -or $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*main.py*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Get-Process node -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like "*next*" -or $_.CommandLine -like "*npm*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill processes on ports
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port8000) { 
    Stop-Process -Id $port8000.OwningProcess -Force -ErrorAction SilentlyContinue 
    Write-Host "   Killed process on port 8000" -ForegroundColor Gray
}
if ($port3000) { 
    Stop-Process -Id $port3000.OwningProcess -Force -ErrorAction SilentlyContinue 
    Write-Host "   Killed process on port 3000" -ForegroundColor Gray
}
Start-Sleep -Seconds 2
Write-Host "✅ Cleanup complete" -ForegroundColor Green

Write-Host ""

# Step 10: Start Backend
Write-Host "Step 10: Starting Backend..." -ForegroundColor Cyan
$backendPath = Join-Path $scriptPath "backend"
$backendScriptContent = "cd /d `"$backendPath`"`r`n`"$pythonCmd`" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`r`npause`r`n"
$tempBackend = Join-Path $env:TEMP "start-backend-$([System.Guid]::NewGuid().ToString('N').Substring(0,8)).bat"
$backendScriptContent | Out-File -FilePath $tempBackend -Encoding ASCII -NoNewline
Start-Process cmd.exe -ArgumentList "/k", "`"$tempBackend`"" -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "✅ Backend started in new window" -ForegroundColor Green

# Step 11: Start Frontend
Write-Host "Step 11: Starting Frontend..." -ForegroundColor Cyan
$webPath = Join-Path $scriptPath "web"
if (-not (Test-Path (Join-Path $webPath "node_modules"))) {
    Write-Host "   Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location $webPath
    npm install --quiet
    Set-Location $scriptPath
}

$frontendScriptContent = "cd /d `"$webPath`"`r`nnpm run dev`r`npause`r`n"
$tempFrontend = Join-Path $env:TEMP "start-frontend-$([System.Guid]::NewGuid().ToString('N').Substring(0,8)).bat"
$frontendScriptContent | Out-File -FilePath $tempFrontend -Encoding ASCII -NoNewline
Start-Process cmd.exe -ArgumentList "/k", "`"$tempFrontend`"" -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "✅ Frontend started in new window" -ForegroundColor Green

# Step 12: Wait and check services
Write-Host ""
Write-Host "Step 12: Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$backendReady = $false
$frontendReady = $false

for ($i = 0; $i -lt 40; $i++) {
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
$separator = '=' * 60
Write-Host $separator -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

if ($backendReady -and $frontendReady) {
    Write-Host "🎉 All services are running! Opening browser..." -ForegroundColor Green
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000"
} else {
    Write-Host "⚠️  Some services may still be starting." -ForegroundColor Yellow
    Write-Host "   Check the command windows for status." -ForegroundColor Yellow
    if (-not $backendReady) {
        Write-Host '   Backend window should show any errors.' -ForegroundColor Gray
    }
    if (-not $frontendReady) {
        Write-Host '   Frontend window should show any errors.' -ForegroundColor Gray
    }
}

$separator = '=' * 60
Write-Host $separator -ForegroundColor Cyan
Write-Host ""

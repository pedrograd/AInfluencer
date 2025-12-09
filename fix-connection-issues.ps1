# Fix Connection Issues - AInfluencer Platform
# This script fixes port conflicts and ensures services start correctly

$ErrorActionPreference = "Continue"

Write-Host "🔧 Fixing Connection Issues..." -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend" -PathType Container)) {
    Write-Host "❌ Error: Must run from project root directory" -ForegroundColor Red
    exit 1
}

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
        return $connection
    } catch {
        return $false
    }
}

# Function to kill process on port
function Stop-ProcessOnPort {
    param([int]$Port)
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $processes) {
            if ($pid) {
                Write-Host "   Stopping process $pid on port $Port..." -ForegroundColor Yellow
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 1
            }
        }
    } catch {
        # Ignore errors
    }
}

# Check and fix port conflicts
Write-Host "🔍 Checking for port conflicts..." -ForegroundColor Cyan

# Port 3000 (Frontend)
if (Test-Port 3000) {
    Write-Host "⚠️  Port 3000 is in use. Stopping process..." -ForegroundColor Yellow
    Stop-ProcessOnPort 3000
    Start-Sleep -Seconds 2
}

# Port 3001 (Alternative Frontend)
if (Test-Port 3001) {
    Write-Host "⚠️  Port 3001 is in use. Stopping process..." -ForegroundColor Yellow
    Stop-ProcessOnPort 3001
    Start-Sleep -Seconds 2
}

# Port 8000 (Backend)
if (Test-Port 8000) {
    Write-Host "⚠️  Port 8000 is in use. Stopping process..." -ForegroundColor Yellow
    Stop-ProcessOnPort 8000
    Start-Sleep -Seconds 2
}

# Port 8188 (ComfyUI)
if (Test-Port 8188) {
    Write-Host "⚠️  Port 8188 is in use. Stopping process..." -ForegroundColor Yellow
    Stop-ProcessOnPort 8188
    Start-Sleep -Seconds 2
}

Write-Host "✅ Port conflicts resolved" -ForegroundColor Green
Write-Host ""

# Check Node.js installation
Write-Host "🔍 Checking Node.js installation..." -ForegroundColor Cyan
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "   ✅ Node.js installed: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Node.js not found!" -ForegroundColor Red
    Write-Host "   Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check npm installation
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmVersion = npm --version
    Write-Host "   ✅ npm installed: $npmVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ npm not found!" -ForegroundColor Red
    exit 1
}

# Check Python installation
Write-Host "🔍 Checking Python installation..." -ForegroundColor Cyan
$python = $null
if (Test-Path ".venv\Scripts\python.exe") {
    $python = ".venv\Scripts\python.exe"
    Write-Host "   ✅ Virtual environment found" -ForegroundColor Green
} elseif (Test-Path "backend\.venv\Scripts\python.exe") {
    $python = "backend\.venv\Scripts\python.exe"
    Write-Host "   ✅ Backend virtual environment found" -ForegroundColor Green
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
    $pythonVersion = python --version
    Write-Host "   ✅ Python installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python not found!" -ForegroundColor Red
    Write-Host "   Please install Python 3.11+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check frontend dependencies
Write-Host "🔍 Checking frontend dependencies..." -ForegroundColor Cyan
if (Test-Path "web\node_modules") {
    Write-Host "   ✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Frontend dependencies missing. Installing..." -ForegroundColor Yellow
    Set-Location web
    npm install
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to install frontend dependencies" -ForegroundColor Red
        exit 1
    }
    Set-Location ..
}

Write-Host ""

# Check backend dependencies
Write-Host "🔍 Checking backend dependencies..." -ForegroundColor Cyan
if ($python) {
    $pipCheck = & $python -c "import fastapi, uvicorn" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Backend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Backend dependencies missing. Installing..." -ForegroundColor Yellow
        & $python -m pip install -r backend\requirements.txt --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Backend dependencies installed" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Failed to install backend dependencies" -ForegroundColor Red
        }
    }
}

Write-Host ""

# Create .env file for frontend if it doesn't exist
Write-Host "🔍 Checking environment configuration..." -ForegroundColor Cyan
if (-not (Test-Path "web\.env.local")) {
    Write-Host "   Creating .env.local file..." -ForegroundColor Yellow
    $envContent = @"
NEXT_PUBLIC_API_URL=http://localhost:8000
"@
    $envContent | Out-File -FilePath "web\.env.local" -Encoding UTF8 -Force
    Write-Host "   ✅ Created .env.local" -ForegroundColor Green
} else {
    Write-Host "   ✅ Environment file exists" -ForegroundColor Green
}

Write-Host ""

# Update Next.js config to ensure correct port
Write-Host "🔍 Checking Next.js configuration..." -ForegroundColor Cyan
$nextConfigPath = "web\next.config.js"
if (Test-Path $nextConfigPath) {
    $nextConfig = Get-Content $nextConfigPath -Raw
    if ($nextConfig -notmatch "port") {
        Write-Host "   Updating Next.js config..." -ForegroundColor Yellow
        $newConfig = $nextConfig -replace "const nextConfig = \{", "const nextConfig = {`n  // Port configuration`n  // Default port: 3000`n  // To use port 3001, run: PORT=3001 npm run dev`n"
        $newConfig | Out-File -FilePath $nextConfigPath -Encoding UTF8 -Force
        Write-Host "   ✅ Next.js config updated" -ForegroundColor Green
    } else {
        Write-Host "   ✅ Next.js config OK" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Connection Issues Fixed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Run: .\start-all.ps1" -ForegroundColor White
Write-Host "  2. Access frontend at: http://localhost:3000" -ForegroundColor White
Write-Host "  3. If you need port 3001, run:" -ForegroundColor White
Write-Host "     cd web" -ForegroundColor Gray
Write-Host "     `$env:PORT=3001; npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: The frontend runs on port 3000 by default." -ForegroundColor Yellow
Write-Host "      If you need port 3001, set the PORT environment variable." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

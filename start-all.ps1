# Start All Services - AInfluencer Platform
# This script starts ComfyUI, Backend API, Frontend, and optional services

param(
    [switch]$SkipComfyUI,
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$UseDocker,
    [switch]$StartRedis,
    [switch]$StartPostgres
)

$ErrorActionPreference = "Continue"

Write-Host "🚀 Starting AInfluencer Platform..." -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend" -PathType Container)) {
    Write-Host "❌ Error: Must run from project root directory" -ForegroundColor Red
    exit 1
}

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    return $connection.TcpTestSucceeded
}

# Function to wait for service
function Wait-ForService {
    param(
        [string]$Name,
        [string]$Url,
        [int]$MaxWait = 60
    )
    $waited = 0
    while ($waited -lt $MaxWait) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $Name is ready!" -ForegroundColor Green
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds 2
            $waited += 2
            Write-Host "⏳ Waiting for $Name... ($waited/$MaxWait seconds)" -ForegroundColor Yellow
        }
    }
    Write-Host "❌ $Name failed to start within $MaxWait seconds" -ForegroundColor Red
    return $false
}

# Start ComfyUI
if (-not $SkipComfyUI) {
    Write-Host "📦 Starting ComfyUI..." -ForegroundColor Cyan
    
    if (Test-Port 8188) {
        Write-Host "⚠️  Port 8188 already in use. ComfyUI may already be running." -ForegroundColor Yellow
        Write-Host "   Skipping ComfyUI startup. If needed, start manually:" -ForegroundColor Yellow
        Write-Host "   cd ComfyUI; python main.py" -ForegroundColor Gray
    } else {
        if (Test-Path "ComfyUI\main.py") {
            try {
                # Get Python command
                $venvPython = ".venv\Scripts\python.exe"
                if (-not (Test-Path $venvPython)) {
                    if (Get-Command python -ErrorAction SilentlyContinue) {
                        $venvPython = "python"
                    } else {
                        Write-Host "   ❌ Python not found!" -ForegroundColor Red
                        Write-Host "   ⚠️  Skipping ComfyUI startup." -ForegroundColor Yellow
                    }
                }
                
                if ($venvPython) {
                    $comfyPath = Join-Path $PWD "ComfyUI"
                    $comfyuiJob = Start-Job -ScriptBlock {
                        param($ComfyPath, $PythonCmd)
                        Set-Location $ComfyPath
                        & $PythonCmd main.py
                    } -ArgumentList $comfyPath, $venvPython
                    Write-Host "   Started ComfyUI in background (Job ID: $($comfyuiJob.Id))" -ForegroundColor Gray
                    Start-Sleep -Seconds 2
                    
                    # Wait for ComfyUI to be ready
                    if (Wait-ForService "ComfyUI" "http://127.0.0.1:8188/system_stats" -MaxWait 120) {
                        Write-Host "   ComfyUI running at: http://127.0.0.1:8188" -ForegroundColor Green
                    } else {
                        Write-Host "   ⚠️  ComfyUI may still be starting. Check manually." -ForegroundColor Yellow
                    }
                }
            }
            catch {
                Write-Host "   ❌ Error starting ComfyUI: $_" -ForegroundColor Red
                Write-Host "   ⚠️  You can start it manually: cd ComfyUI; python main.py" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ⚠️  ComfyUI not found. Skipping." -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Start Redis (optional)
if ($StartRedis) {
    Write-Host "🔴 Starting Redis..." -ForegroundColor Cyan
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        docker-compose up -d redis
        if (Wait-ForService "Redis" "http://localhost:6379" -MaxWait 30) {
            Write-Host "   Redis running at: localhost:6379" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️  Docker not found. Install Docker or start Redis manually." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Start PostgreSQL (optional)
if ($StartPostgres) {
    Write-Host "🐘 Starting PostgreSQL..." -ForegroundColor Cyan
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        docker-compose up -d postgres
        if (Wait-ForService "PostgreSQL" "http://localhost:5432" -MaxWait 60) {
            Write-Host "   PostgreSQL running at: localhost:5432" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️  Docker not found. Install Docker or start PostgreSQL manually." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Start Backend API
if (-not $SkipBackend) {
    Write-Host "🔧 Starting Backend API..." -ForegroundColor Cyan
    
    if (Test-Port 8000) {
        Write-Host "⚠️  Port 8000 already in use. Backend may already be running." -ForegroundColor Yellow
    } else {
        # Check if virtual environment exists (project root or backend folder)
        $venvPath = ".venv"
        $venvPython = "$venvPath\Scripts\python.exe"
        if (-not (Test-Path $venvPython)) {
            $venvPath = "backend\.venv"
            $venvPython = "$venvPath\Scripts\python.exe"
        }
        
        if (Test-Path $venvPython) {
            $python = $venvPython
            Write-Host "   Using virtual environment" -ForegroundColor Gray
        } else {
            $python = "python"
            Write-Host "   Using system Python" -ForegroundColor Gray
        }
        
        try {
            # Check if uvicorn is installed
            $uvicornCheck = & $python -c "import uvicorn" 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "   ⚠️  uvicorn not installed. Installing..." -ForegroundColor Yellow
                & $python -m pip install uvicorn[standard] fastapi --quiet
            }
            
            # Start backend in a new window
            $backendDir = Join-Path $PWD "backend"
            $line1 = "cd /d `"$backendDir`""
            $line2 = "`"$python`" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
            $line3 = "pause"
            $backendScript = "$line1`r`n$line2`r`n$line3"
            $tempScript = Join-Path $env:TEMP "start-backend-$(Get-Random).bat"
            $backendScript | Out-File -FilePath $tempScript -Encoding ASCII -Force
            Start-Process cmd.exe -ArgumentList "/k", "`"$tempScript`"" -WindowStyle Normal
            Write-Host "   Started Backend API in new window" -ForegroundColor Gray
            Start-Sleep -Seconds 2
            
            # Wait for backend to be ready
            if (Wait-ForService "Backend API" "http://localhost:8000/api/health" -MaxWait 60) {
                Write-Host "   Backend API running at: http://localhost:8000" -ForegroundColor Green
                Write-Host "   API Docs at: http://localhost:8000/docs" -ForegroundColor Gray
            } else {
                Write-Host "   ⚠️  Backend may still be starting. Check the backend window." -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "   ❌ Error starting Backend: $_" -ForegroundColor Red
            Write-Host "   ⚠️  You can start it manually: cd backend; python -m uvicorn main:app --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Start Frontend
if (-not $SkipFrontend) {
    Write-Host "🌐 Starting Frontend..." -ForegroundColor Cyan
    
    if (Test-Port 3000) {
        Write-Host "⚠️  Port 3000 already in use. Frontend may already be running." -ForegroundColor Yellow
    } else {
        if (Test-Path "web\package.json") {
            try {
                # Check if node_modules exists
                if (-not (Test-Path "web\node_modules")) {
                    Write-Host "   📦 Installing frontend dependencies..." -ForegroundColor Yellow
                    Set-Location web
                    npm install
                    Set-Location ..
                }
                
                # Start frontend in a new window
                $webDir = Join-Path $PWD "web"
                $line1 = "cd /d `"$webDir`""
                $line2 = "npm run dev"
                $line3 = "pause"
                $frontendScript = "$line1`r`n$line2`r`n$line3"
                $tempScript = Join-Path $env:TEMP "start-frontend-$(Get-Random).bat"
                $frontendScript | Out-File -FilePath $tempScript -Encoding ASCII -Force
                Start-Process cmd.exe -ArgumentList "/k", "`"$tempScript`"" -WindowStyle Normal
                Write-Host "   Started Frontend in new window" -ForegroundColor Gray
                Start-Sleep -Seconds 2
                
                # Wait for frontend to be ready
                if (Wait-ForService "Frontend" "http://localhost:3000" -MaxWait 90) {
                    Write-Host "   Frontend running at: http://localhost:3000" -ForegroundColor Green
                } else {
                    Write-Host "   ⚠️  Frontend may still be starting. Check manually." -ForegroundColor Yellow
                }
            }
            catch {
                Write-Host "   ❌ Error starting Frontend: $_" -ForegroundColor Red
                Write-Host "   ⚠️  You can start it manually: cd web; npm run dev" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ⚠️  Frontend not found. Skipping." -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Startup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services Status:" -ForegroundColor Cyan
Write-Host "  • ComfyUI:      http://127.0.0.1:8188" -ForegroundColor White
Write-Host "  • Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "  • API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services, run:" -ForegroundColor Yellow
Write-Host "  .\stop-all.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "To check system health, run:" -ForegroundColor Yellow
Write-Host "  .\health-check.ps1" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Write-Host ""
Write-Host "💡 Tip: Services are running in separate windows." -ForegroundColor Cyan
Write-Host "   Check the windows for logs and any errors." -ForegroundColor Gray

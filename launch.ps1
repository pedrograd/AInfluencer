# PowerShell orchestrator for Windows
# Handles service startup, health checks, logging, and browser opening
# Enhanced with PRECHECK summary, explicit failures, and root cause analysis

$ErrorActionPreference = 'Stop'

$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT_DIR

# Create runs/launcher directory structure
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$RUNS_DIR = Join-Path $ROOT_DIR "runs"
$LAUNCHER_DIR = Join-Path $RUNS_DIR "launcher"
$RUN_DIR = Join-Path $LAUNCHER_DIR $TIMESTAMP
$LATEST_FILE = Join-Path $LAUNCHER_DIR "latest.txt"

New-Item -ItemType Directory -Force -Path $RUN_DIR | Out-Null
$LATEST_FILE | Set-Content -Value $TIMESTAMP

$SUMMARY_FILE = Join-Path $RUN_DIR "summary.txt"
$EVENTS_FILE = Join-Path $RUN_DIR "events.jsonl"
$BACKEND_LOG = Join-Path $RUN_DIR "backend.log"
$FRONTEND_LOG = Join-Path $RUN_DIR "frontend.log"
$PIP_LOG = Join-Path $RUN_DIR "pip_install.log"
$NPM_LOG = Join-Path $RUN_DIR "npm_install.log"

$AINFLUENCER_DIR = Join-Path $ROOT_DIR ".ainfluencer"
$BACKEND_PID_FILE = Join-Path $AINFLUENCER_DIR "backend.pid"
$FRONTEND_PID_FILE = Join-Path $AINFLUENCER_DIR "frontend.pid"

New-Item -ItemType Directory -Force -Path $AINFLUENCER_DIR | Out-Null

function Write-Event {
    param(
        [string]$Level,
        [string]$Service,
        [string]$Message,
        [string]$Fix = ""
    )
    $event = @{
        ts = [DateTimeOffset]::Now.ToUnixTimeSeconds()
        level = $Level
        service = $Service
        message = $Message
    }
    if ($Fix) { $event.fix = $Fix }
    $event | ConvertTo-Json -Compress | Add-Content -Path $EVENTS_FILE
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] [$Service] $Message" -ForegroundColor $(if ($Level -eq "error") { "Red" } elseif ($Level -eq "warning") { "Yellow" } else { "White" })
}

function Write-Summary {
    param([string]$Content)
    Add-Content -Path $SUMMARY_FILE -Value $Content
}

function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
        return $connection
    } catch {
        return $false
    }
}

function Wait-ForHealth {
    param(
        [string]$Url,
        [int]$MaxWait = 30,
        [string]$ServiceName
    )
    $elapsed = 0
    $interval = 1
    while ($elapsed -lt $MaxWait) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Event -Level "info" -Service "launcher" -Message "$ServiceName health check passed"
                return $true
            }
        } catch {
            # Continue waiting
        }
        Start-Sleep -Seconds $interval
        $elapsed += $interval
        Write-Event -Level "info" -Service "launcher" -Message "Waiting for $ServiceName... ($elapsed/$MaxWait seconds)"
    }
    return $false
}

function Get-ProcessByPort {
    param([int]$Port)
    try {
        $netstat = netstat -ano | Select-String ":$Port\s"
        if ($netstat) {
            $pid = ($netstat -split '\s+')[-1]
            return [int]$pid
        }
    } catch {}
    return $null
}

function Parse-PipFailure {
    param([string]$LogFile)
    if (-not (Test-Path $LogFile)) {
        return "Log file not found: $LogFile"
    }
    
    $logContent = Get-Content $LogFile -Tail 60
    $errorLines = @()
    $collecting = $false
    
    foreach ($line in $logContent) {
        if ($line -match "ERROR|FAILED|error|failed|Exception|Traceback") {
            $collecting = $true
            $errorLines += $line
        } elseif ($collecting -and ($line -match "^\s{4,}" -or $line -match "^\s*at\s" -or $line -match "^\s*File\s")) {
            $errorLines += $line
        } elseif ($collecting -and $line.Trim() -eq "") {
            # Empty line might end the error block, but continue collecting
        } else {
            $collecting = $false
        }
    }
    
    if ($errorLines.Count -eq 0) {
        $errorLines = $logContent[-20..-1]
    }
    
    return "`nROOT CAUSE (last 60 lines):`n" + ($errorLines -join "`n")
}

# Initialize
Write-Event -Level "info" -Service "launcher" -Message "Starting AI Studio Launcher"
Write-Summary "AI Studio Launcher - Run Summary"
Write-Summary "================================="
Write-Summary "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Summary "Logs: $RUN_DIR"
Write-Summary ""

Write-Host "`n=== AInfluencer Launcher ===" -ForegroundColor Cyan
Write-Host "Logs: $RUN_DIR" -ForegroundColor Gray
Write-Host ""

# PRECHECK Summary
Write-Host "=== PRECHECK Summary ===" -ForegroundColor Yellow
Write-Event -Level "info" -Service "launcher" -Message "Running prechecks..."

# Run doctor script first
$doctorScript = Join-Path $ROOT_DIR "scripts\doctor.ps1"
if (Test-Path $doctorScript) {
    Write-Host "Running doctor checks..." -ForegroundColor Gray
    & $doctorScript
    if ($LASTEXITCODE -ne 0) {
        Write-Event -Level "error" -Service "launcher" -Message "Doctor checks failed. Fix issues before launching."
        Write-Summary "Status: FAILED"
        Write-Summary "Error: Doctor checks failed"
        Write-Host "`n✗ Doctor checks failed. Please fix the issues above before launching." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Event -Level "warning" -Service "launcher" -Message "Doctor script not found, running inline checks"
}

# Check Python (must be 3.11.x 64-bit)
Write-Host "`nChecking Python 3.11.x 64-bit..." -ForegroundColor Gray
$pythonFound = $false
$pythonCmd = $null
$pythonVersion = $null
$pythonArch = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in @("3.11")) {
        try {
            $test = py "-$v" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); print('64bit' if sys.maxsize > 2**32 else '32bit')" 2>&1
            if ($LASTEXITCODE -eq 0) {
                $lines = $test -split "`n"
                $pythonVersion = $lines[0].Trim()
                $pythonArch = $lines[1].Trim()
                if ($pythonVersion -match "^3\.11\." -and $pythonArch -eq "64bit") {
                    $pythonCmd = @("py", "-$v")
                    $pythonFound = $true
                    break
                }
            }
        } catch {}
    }
    if (-not $pythonFound) {
        # Try default py
        try {
            $test = py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); print('64bit' if sys.maxsize > 2**32 else '32bit')" 2>&1
            if ($LASTEXITCODE -eq 0) {
                $lines = $test -split "`n"
                $pythonVersion = $lines[0].Trim()
                $pythonArch = $lines[1].Trim()
                if ($pythonVersion -match "^3\.11\." -and $pythonArch -eq "64bit") {
                    $pythonCmd = @("py")
                    $pythonFound = $true
                }
            }
        } catch {}
    }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    try {
        $test = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); print('64bit' if sys.maxsize > 2**32 else '32bit')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $lines = $test -split "`n"
            $pythonVersion = $lines[0].Trim()
            $pythonArch = $lines[1].Trim()
            if ($pythonVersion -match "^3\.11\." -and $pythonArch -eq "64bit") {
                $pythonCmd = @("python")
                $pythonFound = $true
            }
        }
    } catch {}
}

if (-not $pythonFound) {
    Write-Host "`n✗ FATAL: Python 3.11.x 64-bit not found!" -ForegroundColor Red
    Write-Host "Current Python: $pythonVersion ($pythonArch)" -ForegroundColor Yellow
    Write-Host "`nFIX STEPS:" -ForegroundColor Yellow
    Write-Host "1. Download Python 3.11.x 64-bit from: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "2. During installation, check 'Add Python to PATH'" -ForegroundColor White
    Write-Host "3. Verify: python -c `"import sys; print(sys.version); print('64bit' if sys.maxsize > 2**32 else '32bit')`"" -ForegroundColor White
    Write-Host "4. Re-run launch.bat" -ForegroundColor White
    Write-Event -Level "error" -Service "launcher" -Message "Python 3.11.x 64-bit not found. Current: $pythonVersion ($pythonArch)" -Fix "Install Python 3.11.x 64-bit from python.org"
    Write-Summary "Status: FAILED"
    Write-Summary "Error: Python 3.11.x 64-bit not found"
    exit 1
}

Write-Host "✓ Python: $pythonVersion ($pythonArch)" -ForegroundColor Green
Write-Event -Level "info" -Service "launcher" -Message "Python found: $pythonVersion ($pythonArch)"

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "`n✗ FATAL: Node.js not found!" -ForegroundColor Red
    Write-Host "`nFIX STEPS:" -ForegroundColor Yellow
    Write-Host "1. Download Node.js LTS from: https://nodejs.org/" -ForegroundColor White
    Write-Host "2. Install with default options" -ForegroundColor White
    Write-Host "3. Re-run launch.bat" -ForegroundColor White
    Write-Event -Level "error" -Service "launcher" -Message "Node.js not found" -Fix "Install Node.js LTS from nodejs.org"
    Write-Summary "Status: FAILED"
    Write-Summary "Error: Node.js not found"
    exit 1
}
$nodeVersion = node --version
Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
Write-Event -Level "info" -Service "launcher" -Message "Node.js found: $nodeVersion"

# Check npm
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "`n✗ FATAL: npm not found!" -ForegroundColor Red
    Write-Event -Level "error" -Service "launcher" -Message "npm not found" -Fix "Reinstall Node.js (npm comes with Node.js)"
    Write-Summary "Status: FAILED"
    Write-Summary "Error: npm not found"
    exit 1
}
$npmVersion = npm --version
Write-Host "✓ npm: $npmVersion" -ForegroundColor Green
Write-Event -Level "info" -Service "launcher" -Message "npm found: $npmVersion"

# Check git status
if (Get-Command git -ErrorAction SilentlyContinue) {
    try {
        $gitStatus = git status --porcelain 2>&1
        $gitBranch = git rev-parse --abbrev-ref HEAD 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Git: Branch $gitBranch" -ForegroundColor Green
            Write-Event -Level "info" -Service "launcher" -Message "Git branch: $gitBranch"
        }
    } catch {
        Write-Host "⚠ Git: Not a repository" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Git: Not found" -ForegroundColor Yellow
}

Write-Host ""

# Check if services already running
$backendRunning = Test-Port -Port 8000
$frontendRunning = Test-Port -Port 3000

if ($backendRunning -or $frontendRunning) {
    Write-Event -Level "warning" -Service "launcher" -Message "Services may already be running. Checking..."
    if ($backendRunning) {
        $existingPid = Get-ProcessByPort -Port 8000
        Write-Event -Level "info" -Service "launcher" -Message "Backend appears to be running on port 8000 (PID: $existingPid)"
    }
    if ($frontendRunning) {
        $existingPid = Get-ProcessByPort -Port 3000
        Write-Event -Level "info" -Service "launcher" -Message "Frontend appears to be running on port 3000 (PID: $existingPid)"
    }
}

# Start Backend
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"
if (-not $backendRunning) {
    Write-Host "=== Starting Backend ===" -ForegroundColor Cyan
    Write-Event -Level "info" -Service "launcher" -Message "Starting backend..."
    Set-Location $BACKEND_DIR
    
    # Create venv if needed
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Gray
        Write-Event -Level "info" -Service "backend" -Message "Creating virtual environment..."
        if ($pythonCmd.Length -gt 1) {
            & $pythonCmd[0] $pythonCmd[1] -m venv .venv 2>&1 | Out-Null
        } else {
            & $pythonCmd[0] -m venv .venv 2>&1 | Out-Null
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n✗ FATAL: Failed to create virtual environment!" -ForegroundColor Red
            Write-Event -Level "error" -Service "backend" -Message "Failed to create virtual environment"
            Write-Summary "Status: FAILED"
            Write-Summary "Error: Failed to create virtual environment"
            exit 1
        }
    }
    
    # Activate venv and upgrade pip/setuptools/wheel
    $activateScript = Join-Path $BACKEND_DIR ".venv\Scripts\Activate.ps1"
    $venvPython = Join-Path $BACKEND_DIR ".venv\Scripts\python.exe"
    if (Test-Path $activateScript) {
        . $activateScript
        Write-Host "Upgrading pip, setuptools, wheel..." -ForegroundColor Gray
        python -m pip install --upgrade pip setuptools wheel --quiet 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n✗ FATAL: Failed to upgrade pip/setuptools/wheel!" -ForegroundColor Red
            Write-Event -Level "error" -Service "backend" -Message "Failed to upgrade pip/setuptools/wheel"
            Write-Summary "Status: FAILED"
            Write-Summary "Error: Failed to upgrade pip/setuptools/wheel"
            exit 1
        }
        
        # Install backend requirements with verbose logging
        Write-Host "Installing backend requirements (this may take a while)..." -ForegroundColor Gray
        Write-Host "Logs: $PIP_LOG" -ForegroundColor Gray
        Write-Event -Level "info" -Service "backend" -Message "Installing backend requirements..."
        
        python -m pip install -r requirements.txt --verbose 2>&1 | Tee-Object -FilePath $PIP_LOG
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n✗ FATAL: Failed to install backend requirements!" -ForegroundColor Red
            $rootCause = Parse-PipFailure -LogFile $PIP_LOG
            Write-Host $rootCause -ForegroundColor Yellow
            Write-Host "`nNEXT COMMANDS:" -ForegroundColor Yellow
            Write-Host "1. Check the full log: $PIP_LOG" -ForegroundColor White
            Write-Host "2. Try manual install: cd backend && .venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor White
            Write-Host "3. If specific package fails, check for Windows wheel availability" -ForegroundColor White
            Write-Event -Level "error" -Service "backend" -Message "Failed to install backend requirements" -Fix "Check $PIP_LOG for details"
            Write-Summary "Status: FAILED"
            Write-Summary "Error: Failed to install backend requirements"
            Write-Summary "Log: $PIP_LOG"
            exit 1
        }
        Write-Host "✓ Backend requirements installed" -ForegroundColor Green
    } else {
        Write-Host "`n✗ FATAL: Virtual environment activation script not found!" -ForegroundColor Red
        Write-Event -Level "error" -Service "backend" -Message "Virtual environment activation script not found"
        Write-Summary "Status: FAILED"
        Write-Summary "Error: Virtual environment activation script not found"
        exit 1
    }
    
    # Start backend in background using venv python
    if (Test-Path $venvPython) {
        Write-Host "Starting backend server..." -ForegroundColor Gray
        $backendProcess = Start-Process -FilePath $venvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $BACKEND_DIR -PassThru -NoNewWindow -RedirectStandardOutput $BACKEND_LOG -RedirectStandardError $BACKEND_LOG
    } else {
        Write-Host "`n✗ FATAL: Virtual environment Python not found!" -ForegroundColor Red
        Write-Event -Level "error" -Service "backend" -Message "Virtual environment Python not found"
        Write-Summary "Status: FAILED"
        Write-Summary "Error: Virtual environment Python not found"
        exit 1
    }
    
    # Wait for health check
    Write-Host "Waiting for backend health check..." -ForegroundColor Gray
    if (Wait-ForHealth -Url "http://localhost:8000/api/health" -ServiceName "Backend") {
        $backendPid = $backendProcess.Id
        $backendPid | Set-Content -Path $BACKEND_PID_FILE
        Write-Host "✓ Backend started (PID: $backendPid, Port: 8000)" -ForegroundColor Green
        Write-Event -Level "info" -Service "backend" -Message "Backend started (PID: $backendPid, Port: 8000)"
        Write-Summary "- Backend: RUNNING (PID $backendPid, Port 8000) ✓"
    } else {
        Write-Host "`n✗ FATAL: Backend failed to start or health check timed out!" -ForegroundColor Red
        Write-Host "Check logs: $BACKEND_LOG" -ForegroundColor Yellow
        Write-Event -Level "error" -Service "backend" -Message "Backend failed to start or health check timed out"
        Write-Summary "- Backend: FAILED ✗"
        Write-Summary "Log: $BACKEND_LOG"
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    Write-Host "Backend already running, skipping start" -ForegroundColor Yellow
    Write-Event -Level "info" -Service "launcher" -Message "Backend already running, skipping start"
    Write-Summary "- Backend: ALREADY RUNNING ✓"
}

# Start Frontend
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"
if (-not $frontendRunning) {
    Write-Host "`n=== Starting Frontend ===" -ForegroundColor Cyan
    Write-Event -Level "info" -Service "launcher" -Message "Starting frontend..."
    Set-Location $FRONTEND_DIR
    
    # Install deps if needed
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Gray
        Write-Host "Logs: $NPM_LOG" -ForegroundColor Gray
        Write-Event -Level "info" -Service "frontend" -Message "Installing frontend dependencies..."
        npm ci 2>&1 | Tee-Object -FilePath $NPM_LOG
        if ($LASTEXITCODE -ne 0) {
            Write-Host "npm ci failed, trying npm install..." -ForegroundColor Yellow
            npm install 2>&1 | Tee-Object -FilePath $NPM_LOG -Append
            if ($LASTEXITCODE -ne 0) {
                Write-Host "`n✗ FATAL: Failed to install frontend dependencies!" -ForegroundColor Red
                Write-Host "Check logs: $NPM_LOG" -ForegroundColor Yellow
                Write-Event -Level "error" -Service "frontend" -Message "Failed to install frontend dependencies" -Fix "Check $NPM_LOG for details"
                Write-Summary "Status: FAILED"
                Write-Summary "Error: Failed to install frontend dependencies"
                Write-Summary "Log: $NPM_LOG"
                exit 1
            }
        }
        Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
    }
    
    # Start frontend in background
    Write-Host "Starting frontend server..." -ForegroundColor Gray
    $frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FRONTEND_DIR -PassThru -NoNewWindow -RedirectStandardOutput $FRONTEND_LOG -RedirectStandardError $FRONTEND_LOG
    
    # Wait for health check
    Write-Host "Waiting for frontend health check..." -ForegroundColor Gray
    if (Wait-ForHealth -Url "http://localhost:3000" -ServiceName "Frontend") {
        $frontendPid = $frontendProcess.Id
        $frontendPid | Set-Content -Path $FRONTEND_PID_FILE
        Write-Host "✓ Frontend started (PID: $frontendPid, Port: 3000)" -ForegroundColor Green
        Write-Event -Level "info" -Service "frontend" -Message "Frontend started (PID: $frontendPid, Port: 3000)"
        Write-Summary "- Frontend: RUNNING (PID $frontendPid, Port 3000) ✓"
    } else {
        Write-Host "`n✗ FATAL: Frontend failed to start or health check timed out!" -ForegroundColor Red
        Write-Host "Check logs: $FRONTEND_LOG" -ForegroundColor Yellow
        Write-Event -Level "error" -Service "frontend" -Message "Frontend failed to start or health check timed out"
        Write-Summary "- Frontend: FAILED ✗"
        Write-Summary "Log: $FRONTEND_LOG"
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    Write-Host "Frontend already running, skipping start" -ForegroundColor Yellow
    Write-Event -Level "info" -Service "launcher" -Message "Frontend already running, skipping start"
    Write-Summary "- Frontend: ALREADY RUNNING ✓"
}

# Optional ComfyUI check
Write-Host "`n=== Optional Services ===" -ForegroundColor Cyan
$comfyRunning = Test-Port -Port 8188
if ($comfyRunning) {
    Write-Host "✓ ComfyUI: Running on port 8188" -ForegroundColor Green
    Write-Event -Level "info" -Service "launcher" -Message "ComfyUI detected on port 8188"
} else {
    Write-Host "⚠ ComfyUI: Not running (optional, skipping)" -ForegroundColor Yellow
    Write-Event -Level "info" -Service "launcher" -Message "ComfyUI not running (optional)"
}

# Open browser
Write-Host "`n=== Opening Browser ===" -ForegroundColor Cyan
Write-Event -Level "info" -Service "launcher" -Message "Opening dashboard in browser..."
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

# Final summary
Write-Summary ""
Write-Summary "Status: SUCCESS"
Write-Summary ""
Write-Summary "Next Steps:"
Write-Summary "- Dashboard: http://localhost:3000"
Write-Summary "- Backend API: http://localhost:8000"
Write-Summary ""
Write-Summary "Logs: $RUN_DIR"

Write-Event -Level "info" -Service "launcher" -Message "All services started successfully"
Write-Host ""
Write-Host "✓ AI Studio is running!" -ForegroundColor Green
Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Logs: $RUN_DIR" -ForegroundColor Gray
Write-Host ""

# Cleanup function
function Stop-Services {
    Write-Event -Level "info" -Service "launcher" -Message "Shutting down services..."
    
    # Stop backend
    if (Test-Path $BACKEND_PID_FILE) {
        $pid = Get-Content $BACKEND_PID_FILE -ErrorAction SilentlyContinue
        if ($pid) {
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Event -Level "info" -Service "backend" -Message "Backend stopped (PID: $pid)"
            } catch {}
        }
        Remove-Item $BACKEND_PID_FILE -ErrorAction SilentlyContinue
    }
    
    # Stop frontend
    if (Test-Path $FRONTEND_PID_FILE) {
        $pid = Get-Content $FRONTEND_PID_FILE -ErrorAction SilentlyContinue
        if ($pid) {
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Event -Level "info" -Service "frontend" -Message "Frontend stopped (PID: $pid)"
            } catch {}
        }
        Remove-Item $FRONTEND_PID_FILE -ErrorAction SilentlyContinue
    }
    
    Write-Summary "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Event -Level "info" -Service "launcher" -Message "Launcher stopped"
}

# Register cleanup on exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Stop-Services } | Out-Null
[Console]::TreatControlCAsInput = $false

Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Gray
Write-Host ""

# Wait for user interrupt
try {
    while ($true) {
        Start-Sleep -Seconds 1
        # Check if services are still running
        if (-not (Test-Port -Port 8000) -and -not (Test-Port -Port 3000)) {
            Write-Event -Level "warning" -Service "launcher" -Message "Services stopped unexpectedly"
            break
        }
    }
} catch {
    # Ctrl+C or other interrupt
} finally {
    Stop-Services
}

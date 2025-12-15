# PowerShell orchestrator for Windows
# Handles service startup, health checks, logging, and browser opening

$ErrorActionPreference = 'Stop'

$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT_DIR

# Create runs directory structure
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$RUNS_DIR = Join-Path $ROOT_DIR "runs"
$RUN_DIR = Join-Path $RUNS_DIR $TIMESTAMP
$LATEST_FILE = Join-Path $RUNS_DIR "latest.txt"

New-Item -ItemType Directory -Force -Path $RUN_DIR | Out-Null
$LATEST_FILE | Set-Content -Value $TIMESTAMP

$SUMMARY_FILE = Join-Path $RUN_DIR "summary.txt"
$EVENTS_FILE = Join-Path $RUN_DIR "events.jsonl"
$BACKEND_LOG = Join-Path $RUN_DIR "backend.log"
$FRONTEND_LOG = Join-Path $RUN_DIR "frontend.log"

$AINFLUENCER_DIR = Join-Path $ROOT_DIR ".ainfluencer"
$BACKEND_PID_FILE = Join-Path $AINFLUENCER_DIR "backend.pid"
$FRONTEND_PID_FILE = Join-Path $AINFLUENCER_DIR "frontend.pid"

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

# Initialize
Write-Event -Level "info" -Service "launcher" -Message "Starting AI Studio Launcher"
Write-Summary "AI Studio Launcher - Run Summary"
Write-Summary "================================="
Write-Summary "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Summary ""

# Check prerequisites
Write-Event -Level "info" -Service "launcher" -Message "Checking prerequisites..."

# Check Python
$pythonFound = $false
$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in @("3.13", "3.12", "3.11")) {
        try {
            $test = py "-$v" -c "import sys; print(sys.version)" 2>&1
            if ($LASTEXITCODE -eq 0) {
                $pythonCmd = @("py", "-$v")
                $pythonFound = $true
                break
            }
        } catch {}
    }
    if (-not $pythonFound) {
        $pythonCmd = @("py")
        $pythonFound = $true
    }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = @("python")
    $pythonFound = $true
}

if (-not $pythonFound) {
    Write-Event -Level "error" -Service "launcher" -Message "Python not found. Install Python 3.12+ (recommended 3.13)." -Fix "Install Python from python.org or use installer service"
    Write-Summary "Status: FAILED"
    Write-Summary "Error: Python not found"
    exit 1
}
Write-Event -Level "info" -Service "launcher" -Message "Python found: $($pythonCmd -join ' ')"

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Event -Level "error" -Service "launcher" -Message "Node.js not found. Install Node.js LTS." -Fix "Install Node.js from nodejs.org or use installer service"
    Write-Summary "Status: FAILED"
    Write-Summary "Error: Node.js not found"
    exit 1
}
$nodeVersion = node --version
Write-Event -Level "info" -Service "launcher" -Message "Node.js found: $nodeVersion"

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
    Write-Event -Level "info" -Service "launcher" -Message "Starting backend..."
    Set-Location $BACKEND_DIR
    
    # Create venv if needed
    if (-not (Test-Path ".venv")) {
        Write-Event -Level "info" -Service "backend" -Message "Creating virtual environment..."
        if ($pythonCmd.Length -gt 1) {
            & $pythonCmd[0] $pythonCmd[1] -m venv .venv
        } else {
            & $pythonCmd[0] -m venv .venv
        }
    }
    
    # Activate venv and install deps
    $activateScript = Join-Path $BACKEND_DIR ".venv\Scripts\Activate.ps1"
    $venvPython = Join-Path $BACKEND_DIR ".venv\Scripts\python.exe"
    if (Test-Path $activateScript) {
        . $activateScript
        python -m pip install --upgrade pip --quiet
        python -m pip install -r requirements.txt --quiet
    }
    
    # Start backend in background using venv python
    if (Test-Path $venvPython) {
        $backendProcess = Start-Process -FilePath $venvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $BACKEND_DIR -PassThru -NoNewWindow -RedirectStandardOutput $BACKEND_LOG -RedirectStandardError $BACKEND_LOG
    } else {
        # Fallback to system python
        $backendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $BACKEND_DIR -PassThru -NoNewWindow -RedirectStandardOutput $BACKEND_LOG -RedirectStandardError $BACKEND_LOG
    }
    
    # Wait for health check
    if (Wait-ForHealth -Url "http://localhost:8000/api/health" -ServiceName "Backend") {
        $backendPid = $backendProcess.Id
        $backendPid | Set-Content -Path $BACKEND_PID_FILE
        Write-Event -Level "info" -Service "backend" -Message "Backend started (PID: $backendPid, Port: 8000)"
        Write-Summary "- Backend: RUNNING (PID $backendPid, Port 8000) ✓"
    } else {
        Write-Event -Level "error" -Service "backend" -Message "Backend failed to start or health check timed out"
        Write-Summary "- Backend: FAILED ✗"
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    Write-Event -Level "info" -Service "launcher" -Message "Backend already running, skipping start"
    Write-Summary "- Backend: ALREADY RUNNING ✓"
}

# Start Frontend
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"
if (-not $frontendRunning) {
    Write-Event -Level "info" -Service "launcher" -Message "Starting frontend..."
    Set-Location $FRONTEND_DIR
    
    # Install deps if needed
    if (-not (Test-Path "node_modules")) {
        Write-Event -Level "info" -Service "frontend" -Message "Installing frontend dependencies..."
        npm install 2>&1 | Tee-Object -FilePath $FRONTEND_LOG -Append
    }
    
    # Start frontend in background
    $frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FRONTEND_DIR -PassThru -NoNewWindow -RedirectStandardOutput $FRONTEND_LOG -RedirectStandardError $FRONTEND_LOG
    
    # Wait for health check
    if (Wait-ForHealth -Url "http://localhost:3000" -ServiceName "Frontend") {
        $frontendPid = $frontendProcess.Id
        $frontendPid | Set-Content -Path $FRONTEND_PID_FILE
        Write-Event -Level "info" -Service "frontend" -Message "Frontend started (PID: $frontendPid, Port: 3000)"
        Write-Summary "- Frontend: RUNNING (PID $frontendPid, Port 3000) ✓"
    } else {
        Write-Event -Level "error" -Service "frontend" -Message "Frontend failed to start or health check timed out"
        Write-Summary "- Frontend: FAILED ✗"
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    Write-Event -Level "info" -Service "launcher" -Message "Frontend already running, skipping start"
    Write-Summary "- Frontend: ALREADY RUNNING ✓"
}

# Open browser
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
Write-Host "Press Ctrl+C to stop all services..."

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


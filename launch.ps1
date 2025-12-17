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
Set-Content -Path $LATEST_FILE -Value $TIMESTAMP

$SUMMARY_FILE = Join-Path $RUN_DIR "summary.txt"
$EVENTS_FILE = Join-Path $RUN_DIR "events.jsonl"
$BACKEND_STDOUT_LOG = Join-Path $RUN_DIR "backend.stdout.log"
$BACKEND_STDERR_LOG = Join-Path $RUN_DIR "backend.stderr.log"
$FRONTEND_STDOUT_LOG = Join-Path $RUN_DIR "frontend.stdout.log"
$FRONTEND_STDERR_LOG = Join-Path $RUN_DIR "frontend.stderr.log"
$PIP_LOG = Join-Path $RUN_DIR "pip_install.log"
$NPM_LOG = Join-Path $RUN_DIR "npm_install.log"
$PORTS_FILE = Join-Path $RUN_DIR "ports.json"
$RUN_SUMMARY_JSON = Join-Path $RUN_DIR "run_summary.json"
$ERROR_ROOT_CAUSE_FILE = Join-Path $RUN_DIR "error_root_cause.txt"

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
        [int]$MaxWait = 60,
        [string]$ServiceName,
        [string]$StderrLog = ""
    )
    $elapsed = 0
    $interval = 2
    $attempt = 0
    while ($elapsed -lt $MaxWait) {
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Event -Level "info" -Service "launcher" -Message "$ServiceName health check passed (attempt $attempt)"
                return $true
            }
        } catch {
            # Continue waiting
        }
        if ($attempt % 5 -eq 0) {
            Write-Event -Level "info" -Service "launcher" -Message "Waiting for $ServiceName... ($elapsed/$MaxWait seconds, attempt $attempt)"
        }
        Start-Sleep -Seconds $interval
        $elapsed += $interval
    }
    
    # Health check failed - show last 80 lines of stderr if available
    if ($StderrLog -and (Test-Path $StderrLog)) {
        Write-Host "`nLast 80 lines of $ServiceName stderr:" -ForegroundColor Yellow
        Get-Content $StderrLog -Tail 80 | Write-Host
    }
    
    return $false
}

function Get-PortPid {
    param([int]$Port)
    try {
        # Use Get-NetTCPConnection (most reliable on Windows)
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($conn -and $conn.OwningProcess) {
            return $conn.OwningProcess
        }
    } catch {}
    
    # Fallback to netstat parsing
    try {
        $netstat = netstat -ano | Select-String ":$Port\s"
        if ($netstat) {
            $parts = ($netstat -split '\s+')
            $pidStr = $parts[-1]
            if ($pidStr -match '^\d+$') {
                return [int]$pidStr
            }
        }
    } catch {}
    return $null
}

function Resolve-ProcessInfo {
    param([int]$Pid)
    try {
        $proc = Get-Process -Id $Pid -ErrorAction SilentlyContinue
        if ($proc) {
            return @{
                Name = $proc.ProcessName
                Path = $proc.Path
                CommandLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $Pid").CommandLine
            }
        }
    } catch {}
    return $null
}

function Get-AvailablePort {
    param(
        [int[]]$Ports,
        [string]$ServiceName
    )
    foreach ($port in $Ports) {
        $pid = Get-PortPid -Port $port
        if (-not $pid) {
            return @{ Port = $port; Pid = $null; Reused = $false }
        }
        
        # Check if it's our process and healthy
        $procInfo = Resolve-ProcessInfo -Pid $pid
        $isOurProcess = $false
        
        if ($ServiceName -eq "backend" -and $procInfo) {
            $isOurProcess = ($procInfo.Name -eq "python" -or $procInfo.Name -eq "python.exe") -or 
                           ($procInfo.CommandLine -like "*uvicorn*" -or $procInfo.CommandLine -like "*app.main:app*")
        } elseif ($ServiceName -eq "frontend" -and $procInfo) {
            $isOurProcess = ($procInfo.Name -eq "node" -or $procInfo.Name -eq "node.exe") -or
                           ($procInfo.CommandLine -like "*next*" -or $procInfo.CommandLine -like "*npm*")
        }
        
        if ($isOurProcess) {
            # Test health
            $healthUrl = if ($ServiceName -eq "backend") { "http://localhost:$port/api/health" } else { "http://localhost:$port" }
            try {
                $response = Invoke-WebRequest -Uri $healthUrl -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Event -Level "info" -Service "launcher" -Message "Reusing existing $ServiceName on port $port (PID: $pid, healthy)"
                    return @{ Port = $port; Pid = $pid; Reused = $true }
                }
            } catch {
                # Process exists but unhealthy, will try next port
            }
        }
    }
    
    # No available port found
    return $null
}

function Save-Ports {
    param([hashtable]$Ports)
    $Ports | ConvertTo-Json | Set-Content -Path $PORTS_FILE
}

function Get-ProcessByPort {
    param([int]$Port)
    return Get-PortPid -Port $Port
}

function Write-ErrorRootCause {
    param(
        [string]$Category,
        [string]$Message
    )
    
    $errorInfo = @{
        category = $Category
        message = $Message
        timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }
    
    # Map categories to fix steps
    $fixSteps = @{
        "PORT_IN_USE" = @(
            "1. Check which process is using the port: Get-NetTCPConnection -LocalPort <port>",
            "2. Stop the conflicting process or change the port in launcher",
            "3. Re-run launch.bat"
        )
        "BACKEND_PROCESS_START_FAILED" = @(
            "1. Check backend virtual environment: cd backend && .venv\Scripts\python.exe --version",
            "2. Check backend dependencies: pip list",
            "3. Review log: $BACKEND_STDERR_LOG",
            "4. Try manual start: cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
        )
        "BACKEND_HEALTHCHECK_TIMEOUT" = @(
            "1. Check backend stderr log: $BACKEND_STDERR_LOG",
            "2. Verify backend is listening: Test-NetConnection localhost -Port $BACKEND_PORT",
            "3. Check for import errors or missing dependencies",
            "4. Review last 80 lines of stderr (shown above)"
        )
        "FRONTEND_PROCESS_START_FAILED" = @(
            "1. Check Node.js version: node --version",
            "2. Reinstall dependencies: cd frontend && npm install",
            "3. Review log: $FRONTEND_STDERR_LOG",
            "4. Try manual start: cd frontend && npm run dev"
        )
        "FRONTEND_HEALTHCHECK_TIMEOUT" = @(
            "1. Check frontend stderr log: $FRONTEND_STDERR_LOG",
            "2. Verify frontend is listening: Test-NetConnection localhost -Port $FRONTEND_PORT",
            "3. Check for build errors or missing dependencies",
            "4. Review last 80 lines of stderr (shown above)"
        )
        "PIP_INSTALL_FAILED" = @(
            "1. Check Python version (must be 3.11.x 64-bit): python --version",
            "2. Upgrade pip: python -m pip install --upgrade pip",
            "3. Review log: $PIP_LOG",
            "4. Try manual install: cd backend && .venv\Scripts\activate && pip install -r requirements.core.txt"
        )
        "NPM_INSTALL_FAILED" = @(
            "1. Check Node.js version: node --version",
            "2. Clear npm cache: npm cache clean --force",
            "3. Review log: $NPM_LOG",
            "4. Try manual install: cd frontend && npm install"
        )
        "ENV_MISSING" = @(
            "1. Verify Python virtual environment exists: Test-Path backend\.venv",
            "2. Recreate venv: cd backend && python -m venv .venv",
            "3. Check Python installation: python --version"
        )
    }
    
    $errorInfo.fix_steps = if ($fixSteps.ContainsKey($Category)) { $fixSteps[$Category] } else { @("Review logs in $RUN_DIR") }
    $errorInfo.log_file = $RUN_DIR
    
    $errorInfo | ConvertTo-Json -Depth 3 | Set-Content -Path $ERROR_ROOT_CAUSE_FILE
    
    Write-Host "`nROOT CAUSE: $Category" -ForegroundColor Red
    Write-Host $Message -ForegroundColor Yellow
    Write-Host "`nFIX STEPS:" -ForegroundColor Yellow
    foreach ($step in $errorInfo.fix_steps) {
        Write-Host "  $step" -ForegroundColor White
    }
    Write-Host "`nLogs: $RUN_DIR" -ForegroundColor Gray
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
    & $doctorScript 2>&1 | Tee-Object -FilePath (Join-Path $RUN_DIR "doctor.log")
    if ($LASTEXITCODE -ne 0) {
        Write-Event -Level "error" -Service "launcher" -Message "Doctor checks failed. Fix issues before launching."
        Write-Summary "Status: FAILED"
        Write-Summary "Error: Doctor checks failed"
        Write-Host "`n✗ Doctor checks failed. Please fix the issues above before launching." -ForegroundColor Red
        Write-Host "Logs: $RUN_DIR" -ForegroundColor Gray
        exit 1
    }
} else {
    Write-Event -Level "warning" -Service "launcher" -Message "Doctor script not found, running inline checks"
}

# Check and create .env file if missing
$envExample = Join-Path $ROOT_DIR ".env.example"
$envFile = Join-Path $ROOT_DIR ".env"
if (Test-Path $envExample) {
    if (-not (Test-Path $envFile)) {
        Write-Host "Creating .env file from .env.example..." -ForegroundColor Gray
        Copy-Item -Path $envExample -Destination $envFile
        Write-Event -Level "info" -Service "launcher" -Message "Created .env file from .env.example"
        Write-Host "✓ Created .env file (please configure it if needed)" -ForegroundColor Green
    } else {
        Write-Host "✓ .env file exists" -ForegroundColor Green
    }
} else {
    Write-Event -Level "warning" -Service "launcher" -Message ".env.example not found, skipping .env creation"
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

# Port management: find available ports with fallback
$backendPorts = @(8000, 8001)
$frontendPorts = @(3000, 3001, 3002)

$backendPortInfo = Get-AvailablePort -Ports $backendPorts -ServiceName "backend"
$frontendPortInfo = Get-AvailablePort -Ports $frontendPorts -ServiceName "frontend"

$BACKEND_PORT = if ($backendPortInfo) { $backendPortInfo.Port } else { $backendPorts[0] }
$FRONTEND_PORT = if ($frontendPortInfo) { $frontendPortInfo.Port } else { $frontendPorts[0] }

$backendRunning = $backendPortInfo -and $backendPortInfo.Reused
$frontendRunning = $frontendPortInfo -and $frontendPortInfo.Reused

# Save port configuration
Save-Ports -Ports @{
    backend = $BACKEND_PORT
    frontend = $FRONTEND_PORT
    backend_reused = $backendRunning
    frontend_reused = $frontendRunning
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
        
        # Install backend core requirements with verbose logging
        Write-Host "Installing backend core requirements (this may take a while)..." -ForegroundColor Gray
        Write-Host "Logs: $PIP_LOG" -ForegroundColor Gray
        Write-Event -Level "info" -Service "backend" -Message "Installing backend core requirements..."
        
        $requirementsFile = Join-Path $BACKEND_DIR "requirements.core.txt"
        if (-not (Test-Path $requirementsFile)) {
            Write-Host "⚠ requirements.core.txt not found, falling back to requirements.txt" -ForegroundColor Yellow
            $requirementsFile = Join-Path $BACKEND_DIR "requirements.txt"
        }
        
        python -m pip install -r $requirementsFile --verbose 2>&1 | Tee-Object -FilePath $PIP_LOG
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n✗ FATAL: Failed to install backend core requirements!" -ForegroundColor Red
            $rootCause = Parse-PipFailure -LogFile $PIP_LOG
            Write-Host $rootCause -ForegroundColor Yellow
            Write-ErrorRootCause -Category "PIP_INSTALL_FAILED" -Message "Backend core dependencies failed to install. Check $PIP_LOG for details."
            Write-Event -Level "error" -Service "backend" -Message "Failed to install backend core requirements" -Fix "Check $PIP_LOG for details"
            Write-Summary "Status: FAILED"
            Write-Summary "Error: Failed to install backend core requirements"
            Write-Summary "Log: $PIP_LOG"
            exit 1
        }
        Write-Host "✓ Backend core requirements installed" -ForegroundColor Green
        Write-Event -Level "info" -Service "backend" -Message "Backend core requirements installed successfully"
    } else {
        Write-Host "`n✗ FATAL: Virtual environment activation script not found!" -ForegroundColor Red
        Write-Event -Level "error" -Service "backend" -Message "Virtual environment activation script not found"
        Write-Summary "Status: FAILED"
        Write-Summary "Error: Virtual environment activation script not found"
        exit 1
    }
    
    # Start backend in background using venv python
    if (Test-Path $venvPython) {
        Write-Host "Starting backend server on port $BACKEND_PORT..." -ForegroundColor Gray
        $backendProcess = Start-Process -FilePath $venvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$BACKEND_PORT" -WorkingDirectory $BACKEND_DIR -PassThru -NoNewWindow -RedirectStandardOutput $BACKEND_STDOUT_LOG -RedirectStandardError $BACKEND_STDERR_LOG
    } else {
        Write-Host "`n✗ FATAL: Virtual environment Python not found!" -ForegroundColor Red
        Write-Event -Level "error" -Service "backend" -Message "Virtual environment Python not found"
        Write-Summary "Status: FAILED"
        Write-Summary "Error: Virtual environment Python not found"
        Write-ErrorRootCause -Category "ENV_MISSING" -Message "Virtual environment Python not found at $venvPython"
        exit 1
    }
    
    # Wait for health check
    Write-Host "Waiting for backend health check..." -ForegroundColor Gray
    $healthUrl = "http://localhost:$BACKEND_PORT/api/health"
    if (Wait-ForHealth -Url $healthUrl -ServiceName "Backend" -StderrLog $BACKEND_STDERR_LOG) {
        $backendPid = $backendProcess.Id
        $backendPid | Set-Content -Path $BACKEND_PID_FILE
        Write-Host "✓ Backend started (PID: $backendPid, Port: $BACKEND_PORT)" -ForegroundColor Green
        Write-Event -Level "info" -Service "backend" -Message "Backend started (PID: $backendPid, Port: $BACKEND_PORT)"
        Write-Summary "- Backend: RUNNING (PID $backendPid, Port $BACKEND_PORT) ✓"
    } else {
        Write-Host "`n✗ FATAL: Backend failed to start or health check timed out!" -ForegroundColor Red
        Write-Host "Check logs: $BACKEND_STDERR_LOG" -ForegroundColor Yellow
        Write-Event -Level "error" -Service "backend" -Message "Backend failed to start or health check timed out"
        Write-Summary "- Backend: FAILED ✗"
        Write-Summary "Log: $BACKEND_STDERR_LOG"
        Write-ErrorRootCause -Category "BACKEND_HEALTHCHECK_TIMEOUT" -Message "Backend health check failed after 60s. Check $BACKEND_STDERR_LOG for errors."
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
                Write-ErrorRootCause -Category "NPM_INSTALL_FAILED" -Message "Frontend dependencies failed to install. Check $NPM_LOG for details."
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
    Write-Host "Starting frontend server on port $FRONTEND_PORT..." -ForegroundColor Gray
    # Set PORT environment variable for Next.js
    $env:PORT = "$FRONTEND_PORT"
    $frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FRONTEND_DIR -PassThru -NoNewWindow -RedirectStandardOutput $FRONTEND_STDOUT_LOG -RedirectStandardError $FRONTEND_STDERR_LOG
    
    # Wait for health check
    Write-Host "Waiting for frontend health check..." -ForegroundColor Gray
    $healthUrl = "http://localhost:$FRONTEND_PORT"
    if (Wait-ForHealth -Url $healthUrl -ServiceName "Frontend" -StderrLog $FRONTEND_STDERR_LOG) {
        $frontendPid = $frontendProcess.Id
        $frontendPid | Set-Content -Path $FRONTEND_PID_FILE
        Write-Host "✓ Frontend started (PID: $frontendPid, Port: $FRONTEND_PORT)" -ForegroundColor Green
        Write-Event -Level "info" -Service "frontend" -Message "Frontend started (PID: $frontendPid, Port: $FRONTEND_PORT)"
        Write-Summary "- Frontend: RUNNING (PID $frontendPid, Port $FRONTEND_PORT) ✓"
    } else {
        Write-Host "`n✗ FATAL: Frontend failed to start or health check timed out!" -ForegroundColor Red
        Write-Host "Check logs: $FRONTEND_STDERR_LOG" -ForegroundColor Yellow
        Write-Event -Level "error" -Service "frontend" -Message "Frontend failed to start or health check timed out"
        Write-Summary "- Frontend: FAILED ✗"
        Write-Summary "Log: $FRONTEND_STDERR_LOG"
        Write-ErrorRootCause -Category "FRONTEND_HEALTHCHECK_TIMEOUT" -Message "Frontend health check failed after 60s. Check $FRONTEND_STDERR_LOG for errors."
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
Start-Process "http://localhost:$FRONTEND_PORT"

# Final summary
Write-Summary ""
Write-Summary "Status: SUCCESS"
Write-Summary ""
Write-Summary "Next Steps:"
Write-Summary "- Dashboard: http://localhost:$FRONTEND_PORT"
Write-Summary "- Backend API: http://localhost:$BACKEND_PORT"
Write-Summary ""
Write-Summary "Logs: $RUN_DIR"

# Write run summary JSON
$runSummary = @{
    status = "SUCCESS"
    timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    backend = @{
        port = $BACKEND_PORT
        pid = if (Test-Path $BACKEND_PID_FILE) { (Get-Content $BACKEND_PID_FILE) } else { $null }
        reused = $backendRunning
    }
    frontend = @{
        port = $FRONTEND_PORT
        pid = if (Test-Path $FRONTEND_PID_FILE) { (Get-Content $FRONTEND_PID_FILE) } else { $null }
        reused = $frontendRunning
    }
    logs = $RUN_DIR
}
$runSummary | ConvertTo-Json -Depth 3 | Set-Content -Path $RUN_SUMMARY_JSON

Write-Event -Level "info" -Service "launcher" -Message "All services started successfully"
Write-Host ""
Write-Host "✓ SUCCESS: AInfluencer is running!" -ForegroundColor Green
Write-Host "  Dashboard: http://localhost:$FRONTEND_PORT" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:$BACKEND_PORT" -ForegroundColor Cyan
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
        if (-not (Test-Port -Port $BACKEND_PORT) -and -not (Test-Port -Port $FRONTEND_PORT)) {
            Write-Event -Level "warning" -Service "launcher" -Message "Services stopped unexpectedly"
            break
        }
    }
} catch {
    # Ctrl+C or other interrupt
} finally {
    Stop-Services
}

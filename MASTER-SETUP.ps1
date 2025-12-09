# ============================================
# AInfluencer - MASTER SETUP SCRIPT
# ============================================
# One script to do everything:
# - Check system prerequisites
# - Setup environment
# - Download/install everything
# - Run tests
# - Start all services
# - Open web interface
# ============================================

param(
    [switch]$SkipTests,
    [switch]$SkipModels,
    [switch]$SkipServices,
    [switch]$SkipBrowser,
    [switch]$ForceReinstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# UTF-8 encoding
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try { 
    chcp 65001 | Out-Null 
} catch {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}

# Path resolution
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = $scriptRoot
Set-Location $Root

# Logging functions
function Write-Info { param([string]$Msg) Write-Host "[INFO] $Msg" -ForegroundColor Cyan }
function Write-Success { param([string]$Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
function Write-Warning { param([string]$Msg) Write-Host "[WARN] $Msg" -ForegroundColor Yellow }
function Write-Error { param([string]$Msg) Write-Host "[ERROR] $Msg" -ForegroundColor Red }
function Write-Step { param([int]$Num, [int]$Total, [string]$Msg) Write-Host "`n[$Num/$Total] $Msg" -ForegroundColor Magenta }

# Helper: Get Python command
function Get-PythonCmd {
    $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        return $venvPy
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $version = py --version 2>&1
            if ($version -match "Python \d+\.\d+" -and $LASTEXITCODE -eq 0) {
                return "py"
            }
        } catch { }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try {
            $version = python --version 2>&1
            if ($version -match "Python \d+\.\d+" -and $LASTEXITCODE -eq 0) {
                return "python"
            }
        } catch { }
    }
    return $null
}

# Helper: Test port availability
function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
        return $connection
    } catch {
        return $false
    }
}

# Helper: Wait for service
function Wait-ForService {
    param([string]$Name, [string]$Url, [int]$MaxWait = 60)
    $waited = 0
    while ($waited -lt $MaxWait) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 2
            $waited += 2
            if ($waited % 10 -eq 0) {
                Write-Info "Waiting for $Name... ($waited/$MaxWait seconds)"
            }
        }
    }
    return $false
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  AInfluencer - MASTER SETUP" -ForegroundColor Cyan
Write-Host "  Complete Automated Setup & Launch" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$startTime = Get-Date
$stepCount = 0
$totalSteps = 10
$setupErrors = @()

# ============================================
# STEP 1: System Prerequisites Check
# ============================================
$stepCount++
Write-Step $stepCount $totalSteps "Checking System Prerequisites"

$prerequisitesOk = $true

# Python
Write-Info "Checking Python..."
$pythonCmd = Get-PythonCmd
if ($pythonCmd) {
    $version = & $pythonCmd --version 2>&1
    Write-Success "Python found: $version"
} else {
    Write-Error "Python not found! Please install Python 3.10+ from https://www.python.org/downloads/"
    $prerequisitesOk = $false
}

# Node.js
Write-Info "Checking Node.js..."
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Success "Node.js found: $nodeVersion"
} else {
    Write-Error "Node.js not found! Please install from https://nodejs.org/"
    $prerequisitesOk = $false
}

# Git
Write-Info "Checking Git..."
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitVersion = git --version
    Write-Success "Git found: $gitVersion"
} else {
    Write-Warning "Git not found (needed for ComfyUI). Install from https://git-scm.com/"
}

# GPU Check
Write-Info "Checking GPU..."
try {
    $gpu = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" } | Select-Object -First 1
    if ($gpu) {
        Write-Success "NVIDIA GPU found: $($gpu.Name)"
    } else {
        Write-Warning "No NVIDIA GPU detected (CPU mode will be slower)"
    }
} catch {
    Write-Warning "Could not check GPU status"
}

if (-not $prerequisitesOk) {
    Write-Error "Prerequisites check failed. Please install missing software and run again."
    exit 1
}

# ============================================
# STEP 2: Create Virtual Environment
# ============================================
$stepCount++
Write-Step $stepCount $totalSteps "Setting Up Python Virtual Environment"

$venvPath = Join-Path $Root ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython) -or $ForceReinstall) {
    if ($ForceReinstall -and (Test-Path $venvPath)) {
        Write-Info "Removing existing virtual environment..."
        Remove-Item $venvPath -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Write-Info "Creating virtual environment..."
    & $pythonCmd -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
    Write-Success "Virtual environment created"
} else {
    Write-Success "Virtual environment already exists"
}

# Upgrade pip
Write-Info "Upgrading pip..."
& $venvPython -m pip install --upgrade pip --quiet
Write-Success "pip upgraded"

# ============================================
# STEP 3: Setup ComfyUI
# ============================================
$stepCount++
Write-Step $stepCount $totalSteps "Setting Up ComfyUI"

$comfyPath = Join-Path $Root "ComfyUI"
$comfyMainPy = Join-Path $comfyPath "main.py"

if (-not (Test-Path $comfyMainPy)) {
    Write-Info "ComfyUI not found. Cloning from GitHub..."
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "Git required to clone ComfyUI. Please install Git first."
        exit 1
    }
    
    Push-Location $Root
    try {
        git clone https://github.com/comfyanonymous/ComfyUI.git
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to clone ComfyUI"
            exit 1
        }
        Write-Success "ComfyUI cloned successfully"
    } catch {
        Write-Error "Error cloning ComfyUI: $_"
        exit 1
    } finally {
        Pop-Location
    }
} else {
    Write-Success "ComfyUI already installed"
}

# Install ComfyUI requirements
Write-Info "Installing ComfyUI dependencies..."
$comfyRequirements = Join-Path $comfyPath "requirements.txt"
if (Test-Path $comfyRequirements) {
    & $venvPython -m pip install -r $comfyRequirements --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Success "ComfyUI dependencies installed"
    } else {
        Write-Warning "Some ComfyUI dependencies may have failed (continuing...)"
    }
}

# ============================================
# STEP 4: Install Backend Dependencies
# ============================================
$stepCount++
Write-Step $stepCount $totalSteps "Installing Backend Dependencies"

$backendRequirements = Join-Path $Root "backend\requirements.txt"
if (Test-Path $backendRequirements) {
    Write-Info "Installing backend Python packages..."
    & $venvPython -m pip install -r $backendRequirements --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Backend dependencies installed"
    } else {
        Write-Warning "Some backend dependencies may have failed (continuing...)"
    }
} else {
    Write-Warning "backend/requirements.txt not found"
}

# Install base requirements
$baseRequirements = Join-Path $Root "requirements-base.txt"
if (Test-Path $baseRequirements) {
    Write-Info "Installing base requirements..."
    & $venvPython -m pip install -r $baseRequirements --quiet
}

# ============================================
# STEP 5: Install Frontend Dependencies
# ============================================
$stepCount++
Write-Step $stepCount $totalSteps "Installing Frontend Dependencies"

$webPath = Join-Path $Root "web"
$nodeModules = Join-Path $webPath "node_modules"

if (Test-Path (Join-Path $webPath "package.json")) {
    if (-not (Test-Path $nodeModules) -or $ForceReinstall) {
        Write-Info "Installing frontend dependencies (this may take a few minutes)..."
        Push-Location $webPath
        try {
            npm install
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Frontend dependencies installed"
            } else {
                Write-Warning "Frontend installation may have issues (continuing...)"
            }
        } catch {
            Write-Warning "Frontend installation error: $_"
        } finally {
            Pop-Location
        }
    } else {
        Write-Success "Frontend dependencies already installed"
    }
} else {
    Write-Warning "web/package.json not found"
}

# ============================================
# STEP 6: Create Required Directories
# ============================================
$stepCount++
Write-Step $stepCount $totalSteps "Creating Required Directories"

$requiredDirs = @(
    "characters",
    (Join-Path "ComfyUI" "output"),
    (Join-Path "ComfyUI" "output_processed"),
    (Join-Path "ComfyUI" "output_final"),
    "runs"
)

foreach ($dir in $requiredDirs) {
    $fullPath = Join-Path $Root $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Info "Created directory: $dir"
    }
}
Write-Success "All required directories ready"

# ============================================
# STEP 7: Download Models
# ============================================
if (-not $SkipModels) {
    $stepCount++
    Write-Step $stepCount $totalSteps "Downloading AI Models"
    
    $downloadScript = Join-Path $Root "download-models-auto.ps1"
    if (Test-Path $downloadScript) {
        Write-Info "Running model download script..."
        Write-Warning "This may take 10-30 minutes depending on your internet speed"
        & $downloadScript
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Model download completed"
        } else {
            Write-Warning "Model download had issues (you can run download-models-auto.ps1 manually later)"
        }
    } else {
        Write-Warning "download-models-auto.ps1 not found - skipping model downloads"
    }
} else {
    Write-Info "Skipping model downloads (--SkipModels flag)"
    $stepCount++
}

# ============================================
# STEP 8: Run Tests
# ============================================
if (-not $SkipTests) {
    $stepCount++
    Write-Step $stepCount $totalSteps "Running Tests"
    
    $testScript = Join-Path $Root "test-all.ps1"
    if (Test-Path $testScript) {
        Write-Info "Running test suite..."
        try {
            & $testScript 2>&1 | Out-Host
            if ($LASTEXITCODE -eq 0) {
                Write-Success "All tests passed"
            } else {
                Write-Warning "Some tests failed (check output above) - continuing anyway..."
            }
        } catch {
            Write-Warning "Test execution error: $_ - continuing anyway..."
        }
    } else {
        Write-Info "test-all.ps1 not found - skipping tests"
    }
} else {
    Write-Info "Skipping tests (--SkipTests flag)"
    $stepCount++
}

# ============================================
# STEP 9: Start Services
# ============================================
if (-not $SkipServices) {
    $stepCount++
    Write-Step $stepCount $totalSteps "Starting All Services"
    
    Write-Info "Checking if services are already running..."
    
    # Check ports
    $comfyuiRunning = Test-Port 8188
    $backendRunning = Test-Port 8000
    $frontendRunning = Test-Port 3000
    
    if ($comfyuiRunning -or $backendRunning -or $frontendRunning) {
        Write-Warning "Some services appear to be running already"
        if ($comfyuiRunning) { Write-Info "  ComfyUI (port 8188) is in use" }
        if ($backendRunning) { Write-Info "  Backend (port 8000) is in use" }
        if ($frontendRunning) { Write-Info "  Frontend (port 3000) is in use" }
        Write-Info "Starting only missing services..."
    }
    
    # Start ComfyUI
    if (-not $comfyuiRunning) {
        Write-Info "Starting ComfyUI..."
        if (Test-Path $comfyMainPy) {
            try {
                $comfyuiJob = Start-Job -ScriptBlock {
                    Set-Location $using:comfyPath
                    & $using:venvPython main.py
                }
                Write-Info "ComfyUI started in background (Job ID: $($comfyuiJob.Id))"
                Start-Sleep -Seconds 3
                
                if (Wait-ForService "ComfyUI" "http://127.0.0.1:8188/system_stats" -MaxWait 120) {
                    Write-Success "ComfyUI is ready at http://127.0.0.1:8188"
                } else {
                    Write-Warning "ComfyUI may still be starting (check manually at http://127.0.0.1:8188)"
                }
            } catch {
                Write-Warning "Failed to start ComfyUI: $_"
                Write-Info "You can start it manually: cd ComfyUI && python main.py"
            }
        } else {
            Write-Warning "ComfyUI main.py not found - skipping"
        }
    } else {
        Write-Success "ComfyUI already running"
    }
    
    # Start Backend
    if (-not $backendRunning) {
        Write-Info "Starting Backend API..."
        try {
            $backendScript = @"
cd /d `"$Root\backend`"
`"$venvPython`" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
"@
            $tempScript = Join-Path $env:TEMP "start-backend-$(Get-Random).bat"
            $backendScript | Out-File -FilePath $tempScript -Encoding ASCII
            Start-Process cmd.exe -ArgumentList "/k", "`"$tempScript`"" -WindowStyle Normal
            Write-Info "Backend started in new window"
            Start-Sleep -Seconds 3
            
            if (Wait-ForService "Backend API" "http://localhost:8000/api/health" -MaxWait 60) {
                Write-Success "Backend API is ready at http://localhost:8000"
            } else {
                Write-Warning "Backend may still be starting (check the backend window or visit http://localhost:8000)"
            }
        } catch {
            Write-Warning "Failed to start Backend: $_"
            Write-Info "You can start it manually: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
        }
    } else {
        Write-Success "Backend already running"
    }
    
    # Start Frontend
    if (-not $frontendRunning) {
        Write-Info "Starting Frontend..."
        if (Test-Path (Join-Path $webPath "package.json")) {
            try {
                $frontendScript = @"
cd /d `"$Root\web`"
npm run dev
pause
"@
                $tempScript = Join-Path $env:TEMP "start-frontend-$(Get-Random).bat"
                $frontendScript | Out-File -FilePath $tempScript -Encoding ASCII
                Start-Process cmd.exe -ArgumentList "/k", "`"$tempScript`"" -WindowStyle Normal
                Write-Info "Frontend started in new window"
                Start-Sleep -Seconds 3
                
                if (Wait-ForService "Frontend" "http://localhost:3000" -MaxWait 90) {
                    Write-Success "Frontend is ready at http://localhost:3000"
                } else {
                    Write-Warning "Frontend may still be starting (check the frontend window or visit http://localhost:3000)"
                }
            } catch {
                Write-Warning "Failed to start Frontend: $_"
                Write-Info "You can start it manually: cd web && npm run dev"
            }
        } else {
            Write-Warning "Frontend package.json not found - skipping"
        }
    } else {
        Write-Success "Frontend already running"
    }
} else {
    Write-Info "Skipping service startup (--SkipServices flag)"
    $stepCount++
}

# ============================================
# STEP 10: Open Browser
# ============================================
if (-not $SkipBrowser) {
    $stepCount++
    Write-Step $stepCount $totalSteps "Opening Web Interface"
    
    Start-Sleep -Seconds 3
    
    Write-Info "Opening web interface in browser..."
    try {
        Start-Process "http://localhost:3000"
        Write-Success "Browser opened"
    } catch {
        Write-Warning "Could not open browser automatically. Please visit: http://localhost:3000"
    }
} else {
    Write-Info "Skipping browser launch (--SkipBrowser flag)"
    $stepCount++
}

# ============================================
# SUMMARY
# ============================================
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Setup completed in $([math]::Round($duration.TotalMinutes, 1)) minutes" -ForegroundColor White
Write-Host ""

Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  • Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "  • Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • ComfyUI:      http://127.0.0.1:8188" -ForegroundColor White
Write-Host ""

Write-Host "Useful Commands:" -ForegroundColor Cyan
Write-Host "  • Stop services:    .\stop-all.ps1" -ForegroundColor Gray
Write-Host "  • Health check:     .\health-check.ps1" -ForegroundColor Gray
Write-Host "  • Run tests:        .\test-all.ps1" -ForegroundColor Gray
Write-Host "  • Download models:  .\download-models-auto.ps1" -ForegroundColor Gray
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Create a character: .\create-character-config.ps1" -ForegroundColor White
Write-Host "  2. Generate images:   .\gen.ps1 CharacterName -count 10" -ForegroundColor White
Write-Host "  3. Read documentation: See SETUP.md and docs/ folder" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Note about InsightFace model (if it failed)
Write-Host "Note: If InsightFace model download failed, you may need to:" -ForegroundColor Yellow
Write-Host "  1. Visit: https://huggingface.co/deepinsight/antelopev2" -ForegroundColor Gray
Write-Host "  2. Download models manually to: ComfyUI\models\insightface\" -ForegroundColor Gray
Write-Host "  3. Or authenticate with HuggingFace: huggingface-cli login" -ForegroundColor Gray
Write-Host ""

# Always show service URLs
Write-Host "If services didn't start automatically, run:" -ForegroundColor Yellow
Write-Host "  .\start-all.ps1" -ForegroundColor Gray
Write-Host ""

# Exit successfully (even if there were errors, we want to show the summary)
exit 0

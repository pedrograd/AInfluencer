# PowerShell doctor script - runs all prechecks and prints actionable fixes
# Usage: .\scripts\doctor.ps1

$ErrorActionPreference = 'Stop'

$ROOT_DIR = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ROOT_DIR

$issues = @()
$warnings = @()

function Write-Precheck {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Details = "",
        [string]$Fix = ""
    )
    $color = if ($Status -eq "PASS") { "Green" } elseif ($Status -eq "FAIL") { "Red" } else { "Yellow" }
    Write-Host "[$Status] $Name" -ForegroundColor $color
    if ($Details) {
        Write-Host "  $Details" -ForegroundColor Gray
    }
    if ($Fix) {
        Write-Host "  FIX: $Fix" -ForegroundColor Yellow
    }
}

Write-Host "`n=== AInfluencer Doctor - Precheck Summary ===" -ForegroundColor Cyan
Write-Host ""

# 1. Python version check (must be 3.11.x 64-bit)
Write-Host "1. Python Version Check" -ForegroundColor White
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
    Write-Precheck -Name "Python 3.11.x 64-bit" -Status "FAIL" -Details "Python 3.11.x 64-bit not found" -Fix "Install Python 3.11.x 64-bit from python.org/downloads. Ensure you select 'Add Python to PATH' during installation."
    $issues += "Python 3.11.x 64-bit not found. Current: $pythonVersion ($pythonArch)"
} else {
    Write-Precheck -Name "Python 3.11.x 64-bit" -Status "PASS" -Details "$pythonVersion ($pythonArch)"
}

# 2. Node.js version check
Write-Host "`n2. Node.js Version Check" -ForegroundColor White
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Precheck -Name "Node.js" -Status "PASS" -Details $nodeVersion
} else {
    Write-Precheck -Name "Node.js" -Status "FAIL" -Details "Node.js not found" -Fix "Install Node.js LTS from nodejs.org or run: .\scripts\setup\install_node_windows.ps1"
    $issues += "Node.js not found"
}

# 3. npm version check
Write-Host "`n3. npm Version Check" -ForegroundColor White
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmVersion = npm --version
    Write-Precheck -Name "npm" -Status "PASS" -Details $npmVersion
} else {
    Write-Precheck -Name "npm" -Status "FAIL" -Details "npm not found" -Fix "npm should come with Node.js. Reinstall Node.js from nodejs.org"
    $issues += "npm not found"
}

# 4. Git status check
Write-Host "`n4. Git Status Check" -ForegroundColor White
if (Get-Command git -ErrorAction SilentlyContinue) {
    try {
        $gitStatus = git status --porcelain 2>&1
        $gitBranch = git rev-parse --abbrev-ref HEAD 2>&1
        if ($LASTEXITCODE -eq 0) {
            $statusText = if ($gitStatus) { "Modified files present" } else { "Clean working tree" }
            Write-Precheck -Name "Git" -Status "PASS" -Details "Branch: $gitBranch, Status: $statusText"
        } else {
            Write-Precheck -Name "Git" -Status "WARN" -Details "Not a git repository"
            $warnings += "Not a git repository"
        }
    } catch {
        Write-Precheck -Name "Git" -Status "WARN" -Details "Git check failed: $_"
        $warnings += "Git check failed"
    }
} else {
    Write-Precheck -Name "Git" -Status "WARN" -Details "Git not found" -Fix "Install Git from git-scm.com or run: .\scripts\setup\install_git_windows.ps1"
    $warnings += "Git not found"
}

# 5. Backend virtual environment check
Write-Host "`n5. Backend Virtual Environment Check" -ForegroundColor White
$backendVenv = Join-Path $ROOT_DIR "backend\.venv"
if (Test-Path $backendVenv) {
    $venvPython = Join-Path $backendVenv "Scripts\python.exe"
    if (Test-Path $venvPython) {
        try {
            $venvVersion = & $venvPython --version 2>&1
            Write-Precheck -Name "Backend .venv" -Status "PASS" -Details "Virtual environment exists at $backendVenv"
        } catch {
            Write-Precheck -Name "Backend .venv" -Status "WARN" -Details "Virtual environment exists but Python not accessible"
            $warnings += "Backend .venv Python not accessible"
        }
    } else {
        Write-Precheck -Name "Backend .venv" -Status "WARN" -Details "Virtual environment directory exists but incomplete"
        $warnings += "Backend .venv incomplete"
    }
} else {
    Write-Precheck -Name "Backend .venv" -Status "WARN" -Details "Virtual environment not found" -Fix "Will be created automatically on launch"
    $warnings += "Backend .venv not found (will be created)"
}

# 6. Frontend node_modules check
Write-Host "`n6. Frontend Dependencies Check" -ForegroundColor White
$frontendNodeModules = Join-Path $ROOT_DIR "frontend\node_modules"
if (Test-Path $frontendNodeModules) {
    Write-Precheck -Name "Frontend node_modules" -Status "PASS" -Details "Dependencies installed"
} else {
    Write-Precheck -Name "Frontend node_modules" -Status "WARN" -Details "Dependencies not installed" -Fix "Will be installed automatically on launch"
    $warnings += "Frontend node_modules not found (will be installed)"
}

# 7. Backend dependencies compatibility check
Write-Host "`n7. Backend Dependencies Compatibility Check" -ForegroundColor White
$requirementsFile = Join-Path $ROOT_DIR "backend\requirements.txt"
if (Test-Path $requirementsFile) {
    try {
        $requirements = Get-Content $requirementsFile | Where-Object { $_ -match "^\s*[^#]" -and $_ -notmatch "^\s*$" }
        $invalidDeps = @()
        
        # Known incompatible versions (add more as needed)
        $knownIssues = @{
            "tweepy==5.0.0" = "tweepy 5.0.0 does not exist on PyPI. Latest valid version is 4.16.0"
        }
        
        foreach ($req in $requirements) {
            $req = $req.Trim()
            if ($knownIssues.ContainsKey($req)) {
                $invalidDeps += "$req - $($knownIssues[$req])"
            }
        }
        
        if ($invalidDeps.Count -gt 0) {
            Write-Precheck -Name "Backend Dependencies" -Status "FAIL" -Details "Invalid or incompatible dependency pins found" -Fix "Fix invalid dependencies in backend/requirements.txt"
            foreach ($dep in $invalidDeps) {
                Write-Host "  ✗ $dep" -ForegroundColor Red
            }
            $issues += "Invalid dependencies in requirements.txt: $($invalidDeps -join '; ')"
        } else {
            Write-Precheck -Name "Backend Dependencies" -Status "PASS" -Details "No known incompatible dependencies detected"
        }
    } catch {
        Write-Precheck -Name "Backend Dependencies" -Status "WARN" -Details "Could not parse requirements.txt: $_"
        $warnings += "Could not parse requirements.txt"
    }
} else {
    Write-Precheck -Name "Backend Dependencies" -Status "WARN" -Details "requirements.txt not found"
    $warnings += "Backend requirements.txt not found"
}

# 8. Port availability check
Write-Host "`n8. Port Availability Check" -ForegroundColor White
function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
        return $connection
    } catch {
        return $false
    }
}

$port8000 = Test-Port -Port 8000
$port3000 = Test-Port -Port 3000
$port8188 = Test-Port -Port 8188

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

$port8000Pid = Get-PortPid -Port 8000
if ($port8000) {
    $pidDetails = if ($port8000Pid) { " (PID: $port8000Pid)" } else { " (PID: unknown)" }
    Write-Precheck -Name "Port 8000 (Backend)" -Status "WARN" -Details "Port 8000 is in use$pidDetails" -Fix "Stop the process using port 8000 or change backend port"
    $warnings += "Port 8000 in use"
} else {
    Write-Precheck -Name "Port 8000 (Backend)" -Status "PASS" -Details "Available"
}

$port3000Pid = Get-PortPid -Port 3000
if ($port3000) {
    $pidDetails = if ($port3000Pid) { " (PID: $port3000Pid)" } else { " (PID: unknown)" }
    Write-Precheck -Name "Port 3000 (Frontend)" -Status "WARN" -Details "Port 3000 is in use$pidDetails" -Fix "Stop the process using port 3000 or change frontend port"
    $warnings += "Port 3000 in use"
} else {
    Write-Precheck -Name "Port 3000 (Frontend)" -Status "PASS" -Details "Available"
}

if ($port8188) {
    Write-Precheck -Name "Port 8188 (ComfyUI)" -Status "INFO" -Details "Port 8188 is in use (optional)"
} else {
    Write-Precheck -Name "Port 8188 (ComfyUI)" -Status "INFO" -Details "Not in use (optional service)"
}

# 9. Environment file check
Write-Host "`n9. Environment File Check" -ForegroundColor White
$envExample = Join-Path $ROOT_DIR ".env.example"
$envFile = Join-Path $ROOT_DIR ".env"
if (Test-Path $envExample) {
    if (Test-Path $envFile) {
        Write-Precheck -Name ".env file" -Status "PASS" -Details ".env file exists"
    } else {
        Write-Precheck -Name ".env file" -Status "WARN" -Details ".env file not found" -Fix "Will be created automatically from .env.example on launch"
        $warnings += ".env file not found (will be created on launch)"
    }
} else {
    Write-Precheck -Name ".env file" -Status "INFO" -Details ".env.example not found (optional)"
}

# 10. Python package installation test (if venv exists)
Write-Host "`n10. Python Package Installation Test" -ForegroundColor White
$backendVenv = Join-Path $ROOT_DIR "backend\.venv"
$venvPython = Join-Path $backendVenv "Scripts\python.exe"
if (Test-Path $venvPython) {
    try {
        # Try to import critical packages to detect missing dependencies
        $testResult = & $venvPython -c "import sys; sys.path.insert(0, ''); import fastapi; import uvicorn; print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0 -and $testResult -match "OK") {
            Write-Precheck -Name "Python Packages" -Status "PASS" -Details "Critical packages importable"
        } else {
            Write-Precheck -Name "Python Packages" -Status "WARN" -Details "Some packages may be missing. Run: pip install -r backend/requirements.core.txt"
            $warnings += "Python packages may be missing"
        }
    } catch {
        Write-Precheck -Name "Python Packages" -Status "WARN" -Details "Could not test package imports: $_"
        $warnings += "Could not test Python packages"
    }
} else {
    Write-Precheck -Name "Python Packages" -Status "INFO" -Details "Virtual environment not found (will be created on launch)"
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✓ All checks passed!" -ForegroundColor Green
    exit 0
} elseif ($issues.Count -eq 0) {
    Write-Host "⚠ Some warnings (non-critical):" -ForegroundColor Yellow
    foreach ($w in $warnings) {
        Write-Host "  - $w" -ForegroundColor Yellow
    }
    exit 0
} else {
    Write-Host "✗ Critical issues found:" -ForegroundColor Red
    foreach ($i in $issues) {
        Write-Host "  - $i" -ForegroundColor Red
    }
    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠ Warnings:" -ForegroundColor Yellow
        foreach ($w in $warnings) {
            Write-Host "  - $w" -ForegroundColor Yellow
        }
    }
    exit 1
}


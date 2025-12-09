# Health Check Script - AInfluencer Platform
# Checks the status of all services and system health

$ErrorActionPreference = "Continue"

Write-Host "🏥 AInfluencer Platform Health Check" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$allHealthy = $true

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$Timeout = 5
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec $Timeout -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ $Name" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  ⚠️  $Name (Status: $($response.StatusCode))" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "  ❌ $Name (Error: $($_.Exception.Message))" -ForegroundColor Red
        return $false
    }
}

# Function to test port
function Test-Port {
    param([int]$Port, [string]$ServiceName)
    
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($connection) {
            Write-Host "  ✅ $ServiceName (Port $Port)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  ❌ $ServiceName (Port $Port not accessible)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  ❌ $ServiceName (Port $Port check failed)" -ForegroundColor Red
        return $false
    }
}

# 1. Core Services
Write-Host "📦 Core Services" -ForegroundColor Yellow
Write-Host ""

$comfyuiHealthy = Test-HttpEndpoint "ComfyUI" "http://127.0.0.1:8188/system_stats"
$backendHealthy = Test-HttpEndpoint "Backend API" "http://localhost:8000/api/health"
$frontendHealthy = Test-HttpEndpoint "Frontend" "http://localhost:3000"

if (-not $comfyuiHealthy) { $allHealthy = $false }
if (-not $backendHealthy) { $allHealthy = $false }
if (-not $frontendHealthy) { $allHealthy = $false }

Write-Host ""

# 2. Optional Services
Write-Host "🔧 Optional Services" -ForegroundColor Yellow
Write-Host ""

$redisHealthy = Test-Port 6379 "Redis"
$postgresHealthy = Test-Port 5432 "PostgreSQL"

Write-Host ""

# 3. Backend API Endpoints
if ($backendHealthy) {
    Write-Host "🔌 Backend API Endpoints" -ForegroundColor Yellow
    Write-Host ""
    
    $endpoints = @(
        @{Name = "Health Check"; Url = "http://localhost:8000/api/health"},
        @{Name = "ComfyUI Status"; Url = "http://localhost:8000/api/setup/comfyui"},
        @{Name = "System Stats"; Url = "http://localhost:8000/api/system/stats"},
        @{Name = "Models List"; Url = "http://localhost:8000/api/models"}
    )
    
    foreach ($endpoint in $endpoints) {
        Test-HttpEndpoint -Name $endpoint.Name -Url $endpoint.Url -Timeout 3 | Out-Null
    }
    
    Write-Host ""
}

# 4. System Resources
Write-Host "💻 System Resources" -ForegroundColor Yellow
Write-Host ""

# Disk Space
$disk = Get-PSDrive C
$freeSpaceGB = [math]::Round($disk.Free / 1GB, 2)
$usedSpaceGB = [math]::Round(($disk.Used / 1GB), 2)
$totalSpaceGB = [math]::Round(($disk.Free + $disk.Used) / 1GB, 2)
$freePercent = [math]::Round(($disk.Free / ($disk.Free + $disk.Used)) * 100, 1)

if ($freePercent -gt 20) {
    Write-Host "  ✅ Disk Space: $freeSpaceGB GB free / $totalSpaceGB GB total ($freePercent% free)" -ForegroundColor Green
} elseif ($freePercent -gt 10) {
    Write-Host "  ⚠️  Disk Space: $freeSpaceGB GB free / $totalSpaceGB GB total ($freePercent% free) - Low!" -ForegroundColor Yellow
    $allHealthy = $false
} else {
    Write-Host "  ❌ Disk Space: $freeSpaceGB GB free / $totalSpaceGB GB total ($freePercent% free) - Critical!" -ForegroundColor Red
    $allHealthy = $false
}

# Memory
$memory = Get-CimInstance Win32_OperatingSystem
$freeMemoryGB = [math]::Round($memory.FreePhysicalMemory / 1MB, 2)
$totalMemoryGB = [math]::Round($memory.TotalVisibleMemorySize / 1MB, 2)
$usedMemoryGB = $totalMemoryGB - $freeMemoryGB
$freeMemoryPercent = [math]::Round(($freeMemoryGB / $totalMemoryGB) * 100, 1)

Write-Host "  ℹ️  Memory: $freeMemoryGB GB free / $totalMemoryGB GB total ($freeMemoryPercent% free)" -ForegroundColor White

# GPU Check
Write-Host ""
Write-Host "🎮 GPU Status" -ForegroundColor Yellow
Write-Host ""

try {
    $gpu = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" -or $_.Name -like "*AMD*" -or $_.Name -like "*Intel*" } | Select-Object -First 1
    if ($gpu) {
        Write-Host "  ✅ GPU Found: $($gpu.Name)" -ForegroundColor Green
        Write-Host "     Driver Version: $($gpu.DriverVersion)" -ForegroundColor Gray
        Write-Host "     Adapter RAM: $([math]::Round($gpu.AdapterRAM / 1GB, 2)) GB" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  No GPU detected (CPU mode only)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Could not check GPU status" -ForegroundColor Yellow
}

# Python Check
Write-Host ""
Write-Host "🐍 Python Environment" -ForegroundColor Yellow
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion) {
        Write-Host "  ✅ Python: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Python not found" -ForegroundColor Red
        $allHealthy = $false
    }
} catch {
    Write-Host "  ❌ Python not found" -ForegroundColor Red
    $allHealthy = $false
}

# Node.js Check
Write-Host ""
Write-Host "📦 Node.js Environment" -ForegroundColor Yellow
Write-Host ""

try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion) {
        Write-Host "  ✅ Node.js: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Node.js not found" -ForegroundColor Red
        $allHealthy = $false
    }
} catch {
    Write-Host "  ❌ Node.js not found" -ForegroundColor Red
    $allHealthy = $false
}

# Database Check
Write-Host ""
Write-Host "💾 Database Status" -ForegroundColor Yellow
Write-Host ""

$dbPath = "backend\ainfluencer.db"
if (Test-Path $dbPath) {
    $dbSize = [math]::Round((Get-Item $dbPath).Length / 1MB, 2)
    Write-Host "  ✅ SQLite Database: $dbPath ($dbSize MB)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  SQLite Database not found (will be created on first use)" -ForegroundColor Yellow
}

# ComfyUI Check
Write-Host ""
Write-Host "🎨 ComfyUI Status" -ForegroundColor Yellow
Write-Host ""

if (Test-Path "ComfyUI\main.py") {
    Write-Host "  ✅ ComfyUI installation found" -ForegroundColor Green
} else {
    Write-Host "  ❌ ComfyUI not found" -ForegroundColor Red
    $allHealthy = $false
}

# Models Check
Write-Host ""
Write-Host "📚 Models Status" -ForegroundColor Yellow
Write-Host ""

$modelDirs = @(
    @{Path = "ComfyUI\models\checkpoints"; Name = "Checkpoint Models"},
    @{Path = "ComfyUI\models\vae"; Name = "VAE Models"},
    @{Path = "ComfyUI\models\ip-adapter"; Name = "IP-Adapter Models"}
)

foreach ($dir in $modelDirs) {
    if (Test-Path $dir.Path) {
        $files = (Get-ChildItem $dir.Path -File -ErrorAction SilentlyContinue).Count
        if ($files -gt 0) {
            Write-Host "  ✅ $($dir.Name): $files files" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  $($dir.Name): No files found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️  $($dir.Name): Directory not found" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if ($allHealthy) {
    Write-Host "✅ Overall Status: HEALTHY" -ForegroundColor Green
    Write-Host ""
    Write-Host "All critical services are running and accessible." -ForegroundColor White
} else {
    Write-Host "⚠️  Overall Status: ISSUES DETECTED" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Some services are not running or have issues." -ForegroundColor White
    Write-Host "Check the details above and:" -ForegroundColor Yellow
    Write-Host "  • Start services: .\start-all.ps1" -ForegroundColor Gray
    Write-Host "  • Check logs for errors" -ForegroundColor Gray
    Write-Host "  • Verify configuration" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  • ComfyUI:      http://127.0.0.1:8188" -ForegroundColor White
Write-Host "  • Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "  • API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Exit with appropriate code
if ($allHealthy) {
    exit 0
} else {
    exit 1
}

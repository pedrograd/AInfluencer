# Run All Tests - AInfluencer Platform
# Runs backend tests, frontend tests, and integration tests

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$IntegrationOnly,
    [switch]$Coverage,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

Write-Host "🧪 Running AInfluencer Platform Tests" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$testResults = @{
    Backend = $null
    Frontend = $null
    Integration = $null
}

$allPassed = $true

# Backend Tests
if (-not $FrontendOnly -and -not $IntegrationOnly) {
    Write-Host "🔧 Running Backend Tests..." -ForegroundColor Yellow
    Write-Host ""
    
    if (Test-Path "backend\tests") {
        Set-Location backend
        
        # Check if pytest is installed
        $pytestCheck = python -c "import pytest" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   Installing pytest..." -ForegroundColor Yellow
            python -m pip install pytest pytest-asyncio pytest-cov
        }
        
        $pytestArgs = @("tests", "-v")
        if ($Coverage) {
            $pytestArgs += @("--cov=.", "--cov-report=html", "--cov-report=term")
        }
        if ($Verbose) {
            $pytestArgs += "-vv"
        }
        
        try {
            python -m pytest $pytestArgs
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "   ✅ Backend tests passed!" -ForegroundColor Green
                $testResults.Backend = $true
            } else {
                Write-Host ""
                Write-Host "   ❌ Backend tests failed!" -ForegroundColor Red
                $testResults.Backend = $false
                $allPassed = $false
            }
        } catch {
            Write-Host ""
            Write-Host "   ❌ Error running backend tests: $_" -ForegroundColor Red
            $testResults.Backend = $false
            $allPassed = $false
        }
        
        Set-Location ..
    } else {
        Write-Host "   ⚠️  Backend tests directory not found" -ForegroundColor Yellow
        $testResults.Backend = $null
    }
    Write-Host ""
}

# Frontend Tests
if (-not $BackendOnly -and -not $IntegrationOnly) {
    Write-Host "🌐 Running Frontend Tests..." -ForegroundColor Yellow
    Write-Host ""
    
    if (Test-Path "web\package.json") {
        Set-Location web
        
        # Check if test script exists
        $packageJson = Get-Content package.json | ConvertFrom-Json
        if ($packageJson.scripts.test) {
            try {
                npm test
                if ($LASTEXITCODE -eq 0) {
                    Write-Host ""
                    Write-Host "   ✅ Frontend tests passed!" -ForegroundColor Green
                    $testResults.Frontend = $true
                } else {
                    Write-Host ""
                    Write-Host "   ❌ Frontend tests failed!" -ForegroundColor Red
                    $testResults.Frontend = $false
                    $allPassed = $false
                }
            } catch {
                Write-Host ""
                Write-Host "   ⚠️  Frontend tests not configured or failed: $_" -ForegroundColor Yellow
                $testResults.Frontend = $null
            }
        } else {
            Write-Host "   ⚠️  Frontend test script not configured in package.json" -ForegroundColor Yellow
            $testResults.Frontend = $null
        }
        
        Set-Location ..
    } else {
        Write-Host "   ⚠️  Frontend package.json not found" -ForegroundColor Yellow
        $testResults.Frontend = $null
    }
    Write-Host ""
}

# Integration Tests
if (-not $BackendOnly -and -not $FrontendOnly) {
    Write-Host "🔌 Running Integration Tests..." -ForegroundColor Yellow
    Write-Host ""
    
    # Check if services are running
    Write-Host "   Checking service availability..." -ForegroundColor Gray
    
    $servicesRunning = $true
    
    # Check ComfyUI
    try {
        $comfyuiResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8188/system_stats" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "   ✅ ComfyUI is running" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  ComfyUI is not running (some tests may be skipped)" -ForegroundColor Yellow
        $servicesRunning = $false
    }
    
    # Check Backend
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "   ✅ Backend API is running" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Backend API is not running (some tests may be skipped)" -ForegroundColor Yellow
        $servicesRunning = $false
    }
    
    if ($servicesRunning) {
        # Run integration tests if they exist
        if (Test-Path "backend\tests\integration") {
            Set-Location backend
            try {
                python -m pytest tests/integration -v
                if ($LASTEXITCODE -eq 0) {
                    Write-Host ""
                    Write-Host "   ✅ Integration tests passed!" -ForegroundColor Green
                    $testResults.Integration = $true
                } else {
                    Write-Host ""
                    Write-Host "   ❌ Integration tests failed!" -ForegroundColor Red
                    $testResults.Integration = $false
                    $allPassed = $false
                }
            } catch {
                Write-Host ""
                Write-Host "   ⚠️  Error running integration tests: $_" -ForegroundColor Yellow
                $testResults.Integration = $null
            }
            Set-Location ..
        } else {
            Write-Host "   ⚠️  Integration tests directory not found" -ForegroundColor Yellow
            $testResults.Integration = $null
        }
    } else {
        Write-Host ""
        Write-Host "   ⚠️  Skipping integration tests (services not running)" -ForegroundColor Yellow
        Write-Host "   Start services with: .\start-all.ps1" -ForegroundColor Gray
        $testResults.Integration = $null
    }
    Write-Host ""
}

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 Test Results Summary" -ForegroundColor Cyan
Write-Host ""

$statusSymbol = @{
    $true = "✅ PASSED"
    $false = "❌ FAILED"
    $null = "⚠️  SKIPPED"
}

Write-Host "  Backend:      $($statusSymbol[$testResults.Backend])" -ForegroundColor $(if ($testResults.Backend) { "Green" } elseif ($testResults.Backend -eq $false) { "Red" } else { "Yellow" })
Write-Host "  Frontend:     $($statusSymbol[$testResults.Frontend])" -ForegroundColor $(if ($testResults.Frontend) { "Green" } elseif ($testResults.Frontend -eq $false) { "Red" } else { "Yellow" })
Write-Host "  Integration:  $($statusSymbol[$testResults.Integration])" -ForegroundColor $(if ($testResults.Integration) { "Green" } elseif ($testResults.Integration -eq $false) { "Red" } else { "Yellow" })

Write-Host ""

if ($allPassed) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
    if ($Coverage) {
        Write-Host ""
        Write-Host "📊 Coverage report generated in backend/htmlcov/index.html" -ForegroundColor Cyan
    }
    exit 0
} else {
    Write-Host "❌ Some tests failed. Check output above for details." -ForegroundColor Red
    exit 1
}

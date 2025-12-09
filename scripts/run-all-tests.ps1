# Complete Anti-Detection Test Suite Runner
# Runs all tests and generates comprehensive report

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete Anti-Detection Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "..\backend"

# Step 1: Check environment
Write-Host "Step 1: Checking environment..." -ForegroundColor Green
$envFile = Join-Path $backendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "  Creating .env file from .env.example..." -ForegroundColor Yellow
    $envExample = Join-Path $backendDir ".env.example"
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
    }
}

# Step 2: Generate test image
Write-Host ""
Write-Host "Step 2: Generating test image..." -ForegroundColor Green
Set-Location $backendDir
python ..\scripts\generate-test-image.py --output test_output\test_image.png --width 1024 --height 1024 --complexity medium
if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARNING: Test image generation failed, continuing anyway..." -ForegroundColor Yellow
}

# Step 3: Run anti-detection tests
Write-Host ""
Write-Host "Step 3: Running anti-detection tests..." -ForegroundColor Green
python test_anti_detection.py
$testExitCode = $LASTEXITCODE

# Step 4: Check API connection (if backend is running)
Write-Host ""
Write-Host "Step 4: Checking API connection..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✓ Backend API is running" -ForegroundColor Green
    
    # Get detection stats
    Write-Host ""
    Write-Host "Step 5: Fetching detection statistics..." -ForegroundColor Green
    $statsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/anti-detection/stats" -Method Get
    if ($statsResponse.success) {
        $stats = $statsResponse.data
        Write-Host "  Total Tests: $($stats.total_tests)" -ForegroundColor Cyan
        Write-Host "  Pass Rate: $([math]::Round($stats.pass_rate, 1))%" -ForegroundColor Cyan
        Write-Host "  Average Score: $([math]::Round($stats.average_score * 100, 1))%" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ⚠ Backend API is not running (this is OK if you're only testing locally)" -ForegroundColor Yellow
}

# Step 5: Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Suite Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($testExitCode -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed. Review the output above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review test results in backend/test_output/" -ForegroundColor White
Write-Host "  2. Check API keys in backend/.env if tests failed" -ForegroundColor White
Write-Host "  3. Run 'python scripts/monitor-detection-stats.py' to monitor statistics" -ForegroundColor White
Write-Host ""

exit $testExitCode

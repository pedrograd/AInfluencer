# Anti-Detection Testing Script for PowerShell
# Automatically tests all anti-detection features

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Anti-Detection Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
$envFile = Join-Path $PSScriptRoot "..\backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "WARNING: .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    
    $envExample = Join-Path $PSScriptRoot "..\backend\.env.example"
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "Created .env file. Please fill in your API keys." -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: .env.example not found. Cannot create .env file." -ForegroundColor Red
        exit 1
    }
}

# Load environment variables
Write-Host "Loading environment variables..." -ForegroundColor Green
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        if ($value -and $value -ne "your_hive_api_key_here" -and $value -ne "your_sensity_api_key_here" -and $value -ne "your_ai_or_not_api_key_here") {
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Check API keys
Write-Host ""
Write-Host "Checking API keys..." -ForegroundColor Green
$hiveKey = [Environment]::GetEnvironmentVariable("HIVE_API_KEY", "Process")
$sensityKey = [Environment]::GetEnvironmentVariable("SENSITY_API_KEY", "Process")
$aiOrNotKey = [Environment]::GetEnvironmentVariable("AI_OR_NOT_API_KEY", "Process")

$missingKeys = @()
if (-not $hiveKey -or $hiveKey -eq "your_hive_api_key_here") {
    $missingKeys += "HIVE_API_KEY"
}
if (-not $sensityKey -or $sensityKey -eq "your_sensity_api_key_here") {
    $missingKeys += "SENSITY_API_KEY"
}
if (-not $aiOrNotKey -or $aiOrNotKey -eq "your_ai_or_not_api_key_here") {
    $missingKeys += "AI_OR_NOT_API_KEY"
}

if ($missingKeys.Count -gt 0) {
    Write-Host "WARNING: Missing API keys: $($missingKeys -join ', ')" -ForegroundColor Yellow
    Write-Host "Some detection tools may not work without API keys." -ForegroundColor Yellow
    Write-Host "Edit backend\.env file to add your API keys." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "✓ All API keys configured" -ForegroundColor Green
    Write-Host ""
}

# Change to backend directory
$backendDir = Join-Path $PSScriptRoot "..\backend"
Set-Location $backendDir

# Run the test script
Write-Host "Running anti-detection tests..." -ForegroundColor Green
Write-Host ""

python test_anti_detection.py

$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✓ Test suite completed successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed. Check the output above." -ForegroundColor Red
}

exit $exitCode

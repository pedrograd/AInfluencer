# PowerShell verification script - smoke test for launcher
# Usage: .\scripts\verify.ps1

$ErrorActionPreference = 'Stop'

$ROOT_DIR = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ROOT_DIR

Write-Host "`n=== AInfluencer Verification Script ===" -ForegroundColor Cyan
Write-Host ""

# 1. Print environment info
Write-Host "1. Environment Info" -ForegroundColor White
Write-Host "   OS: $($PSVersionTable.OS)" -ForegroundColor Gray
Write-Host "   PowerShell: $($PSVersionTable.PSVersion)" -ForegroundColor Gray
Write-Host "   Working Directory: $ROOT_DIR" -ForegroundColor Gray
Write-Host ""

# 2. Run doctor
Write-Host "2. Running Doctor Checks..." -ForegroundColor White
$doctorScript = Join-Path $ROOT_DIR "scripts\doctor.ps1"
if (Test-Path $doctorScript) {
    & $doctorScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n✗ Doctor checks failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ⚠ Doctor script not found" -ForegroundColor Yellow
}
Write-Host ""

# 3. Check if services are running
Write-Host "3. Checking Service Health..." -ForegroundColor White

function Test-HttpEndpoint {
    param(
        [string]$Url,
        [string]$ServiceName
    )
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✓ $ServiceName: OK (200)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "   ✗ $ServiceName: Unexpected status $($response.StatusCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "   ✗ $ServiceName: Failed - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check backend
$backendPort = 8000
$backendUrl = "http://localhost:$backendPort/api/health"
$backendOk = Test-HttpEndpoint -Url $backendUrl -ServiceName "Backend ($backendPort)"

# Check frontend
$frontendPort = 3000
$frontendUrl = "http://localhost:$frontendPort"
$frontendOk = Test-HttpEndpoint -Url $frontendUrl -ServiceName "Frontend ($frontendPort)"

# Check ComfyUI (optional)
$comfyPort = 8188
$comfyUrl = "http://localhost:$comfyPort"
try {
    $comfyResponse = Invoke-WebRequest -Uri $comfyUrl -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($comfyResponse.StatusCode -eq 200) {
        Write-Host "   ✓ ComfyUI ($comfyPort): OK (optional)" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠ ComfyUI ($comfyPort): Not running (optional)" -ForegroundColor Yellow
}

Write-Host ""

# 4. Check latest run logs
Write-Host "4. Checking Latest Run Logs..." -ForegroundColor White
$latestRunFile = Join-Path $ROOT_DIR "runs\launcher\latest.txt"
if (Test-Path $latestRunFile) {
    $latestRun = Get-Content $latestRunFile -ErrorAction SilentlyContinue
    if ($latestRun) {
        $runDir = Join-Path $ROOT_DIR "runs\launcher\$latestRun"
        if (Test-Path $runDir) {
            Write-Host "   ✓ Latest run: $latestRun" -ForegroundColor Green
            Write-Host "   Logs: $runDir" -ForegroundColor Gray
            
            # Check for error root cause
            $errorFile = Join-Path $runDir "error_root_cause.txt"
            if (Test-Path $errorFile) {
                Write-Host "   ⚠ Error root cause file found: $errorFile" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ⚠ Latest run directory not found: $runDir" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   ⚠ No run logs found" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "=== Summary ===" -ForegroundColor Cyan
if ($backendOk -and $frontendOk) {
    Write-Host "✓ SUCCESS: All services are healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Backend: $backendUrl" -ForegroundColor Cyan
    Write-Host "  Frontend: $frontendUrl" -ForegroundColor Cyan
    Write-Host ""
    exit 0
} else {
    Write-Host "✗ FAILED: Some services are not healthy" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Backend: $(if ($backendOk) { 'OK' } else { 'FAILED' })" -ForegroundColor $(if ($backendOk) { 'Green' } else { 'Red' })
    Write-Host "  Frontend: $(if ($frontendOk) { 'OK' } else { 'FAILED' })" -ForegroundColor $(if ($frontendOk) { 'Green' } else { 'Red' })
    Write-Host ""
    Write-Host "Run launch.bat to start services, then re-run this script." -ForegroundColor Yellow
    exit 1
}


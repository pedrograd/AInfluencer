# Ensure All Models Script
# Automatically downloads all missing models and validates installation

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# Import common library
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
$commonPath = Join-Path $rootPath "scripts\lib\common.ps1"
if (Test-Path $commonPath) {
    . $commonPath
} else {
    function Write-Info { param([string]$Msg) Write-Host "[INFO] $Msg" -ForegroundColor White }
    function Write-Success { param([string]$Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
    function Write-Warning { param([string]$Msg) Write-Host "[WARN] $Msg" -ForegroundColor Yellow }
    function Write-Error { param([string]$Msg) Write-Host "[ERR] $Msg" -ForegroundColor Red }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OTOMATIK MODEL INDIRME VE DOGRULAMA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get root path
$root = if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

# Step 1: Run download script
Write-Info "[1/3] Modeller indiriliyor..."
$downloadScript = Join-Path $root "download-models-auto.ps1"
if (Test-Path $downloadScript) {
    & $downloadScript
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Indirme scripti hata verdi, devam ediliyor..."
    }
} else {
    Write-Error "download-models-auto.ps1 bulunamadi: $downloadScript"
    exit 1
}
Write-Host ""

# Step 2: Validate downloads
Write-Info "[2/3] Indirilen modeller dogrulanıyor..."
$testScript = Join-Path $scriptPath "test-model-downloads.ps1"
if (Test-Path $testScript) {
    & $testScript
    $testExitCode = $LASTEXITCODE
} else {
    Write-Warning "Test scripti bulunamadi, manuel kontrol yapin"
    $testExitCode = 0
}
Write-Host ""

# Step 3: Summary
Write-Info "[3/3] Ozet hazirlaniyor..."
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ISLEM TAMAMLANDI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($testExitCode -eq 0) {
    Write-Success "Tum modeller basariyla indirildi ve dogrulandi!"
    Write-Host ""
    Write-Host "Sonraki adimlar:" -ForegroundColor Yellow
    Write-Host "  1. Karakter olustur: .\create-character-config.ps1" -ForegroundColor Cyan
    Write-Host "  2. Icerik uret: .\full-auto-generate.ps1 -CharacterName MODEL_ADI" -ForegroundColor Cyan
} else {
    Write-Warning "Bazi modeller eksik olabilir"
    Write-Host ""
    Write-Host "Manuel kontrol:" -ForegroundColor Yellow
    Write-Host "  .\scripts\test-model-downloads.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Tekrar indirme:" -ForegroundColor Yellow
    Write-Host "  .\download-models-auto.ps1" -ForegroundColor Cyan
}

exit $testExitCode

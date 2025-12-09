# Master Automation Script
# Tum sureci otomatik olarak yonetir

# PHASE 1: UTF-8 encoding enforcement
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try { 
    chcp 65001 | Out-Null 
} catch {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}

# Simple path resolution
$Root = $PSScriptRoot
if (-not $Root) {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# PHASE 2: Get-PythonCmd pattern (prefer .venv)
function Get-PythonCmd {
    $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        return $venvPy
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    Write-Error "Python bulunamadi!"
    exit 1
}

param(
    [string]$Action = "all",
    [string]$CharacterName = "",
    [int]$ImageCount = 10
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ULTRA REALISTIC ONLYFANS - MASTER AUTOMATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Action'a gore islem yap
$actionLower = $Action.ToLower()

if ($actionLower -eq "setup") {
    Write-Host "[SETUP] Kurulum basliyor..." -ForegroundColor Yellow
    & ".\auto-install-missing-tools.ps1"
    & ".\download-models-auto.ps1"
    Write-Host ""
    Write-Host "[OK] Kurulum tamamlandi!" -ForegroundColor Green
}
elseif ($actionLower -eq "create-character") {
    Write-Host "[CREATE CHARACTER] Karakter olusturuluyor..." -ForegroundColor Yellow
    & ".\create-character-config.ps1"
}
elseif ($actionLower -eq "generate-prompts") {
    if (-not $CharacterName) {
        Write-Host "HATA: Karakter adi gerekli!" -ForegroundColor Red
        Write-Host "Kullanim: .\master-automation.ps1 -Action generate-prompts -CharacterName Model1" -ForegroundColor Yellow
        exit 1
    }
    $configFile = "characters\$CharacterName\config.json"
    if (-not (Test-Path $configFile)) {
        Write-Host "HATA: $configFile bulunamadi!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[GENERATE PROMPTS] Prompt'lar olusturuluyor..." -ForegroundColor Yellow
    $pythonCmd = Get-PythonCmd
    & $pythonCmd "generate-prompt-auto.py" $configFile
}
elseif ($actionLower -eq "post-process") {
    Write-Host "[POST-PROCESS] Post-processing basliyor..." -ForegroundColor Yellow
    $pythonCmd = Get-PythonCmd
    & $pythonCmd "post_process_pipeline.py"
}
elseif ($actionLower -eq "generate") {
    if (-not $CharacterName) {
        Write-Host "HATA: Karakter adi gerekli!" -ForegroundColor Red
        Write-Host "Kullanim: .\master-automation.ps1 -Action generate -CharacterName Model1 -ImageCount 10" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[GENERATE] Tam otomatik goruntu uretimi basliyor..." -ForegroundColor Yellow
    & ".\full-auto-generate.ps1" -CharacterName $CharacterName -ImageCount $ImageCount
}
elseif ($actionLower -eq "all") {
    Write-Host "[FULL AUTOMATION] Tum surec basliyor..." -ForegroundColor Yellow
    Write-Host ""
    
    # 1. Setup
    Write-Host "[1/5] Kurulum kontrol ediliyor..." -ForegroundColor Cyan
    & ".\quick-start-guide.ps1"
    Write-Host ""
    
    # 2. Eksik araclari kur
    Write-Host "[2/5] Eksik araclar kuruluyor..." -ForegroundColor Cyan
    & ".\auto-install-missing-tools.ps1"
    Write-Host ""
    
    # 3. Modelleri kontrol et
    Write-Host "[3/5] Modeller kontrol ediliyor..." -ForegroundColor Cyan
    & ".\download-models-auto.ps1"
    Write-Host ""
    
    # 4. Karakter yoksa olustur
    if (-not $CharacterName) {
        Write-Host "[4/5] Karakter konfigurasyonu olusturuluyor..." -ForegroundColor Cyan
        Write-Host "  (Interaktif mod - bilgileri girin)" -ForegroundColor Yellow
        & ".\create-character-config.ps1"
    } else {
        Write-Host "[4/5] Karakter konfigurasyonu kullaniliyor: $CharacterName" -ForegroundColor Cyan
    }
    Write-Host ""
    
    # 5. Prompt'lar olustur
    if ($CharacterName) {
        Write-Host "[5/5] Prompt'lar olusturuluyor..." -ForegroundColor Cyan
        $configFile = "characters\$CharacterName\config.json"
        if (Test-Path $configFile) {
            $pythonCmd = Get-PythonCmd
            & $pythonCmd "generate-prompt-auto.py" $configFile
        }
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "AUTOMATION TAMAMLANDI!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "SONRAKI ADIMLAR:" -ForegroundColor Yellow
    Write-Host "1. ComfyUI'i baslatin ve workflow olusturun" -ForegroundColor White
    Write-Host "2. Olusturulan prompt'lari kullanarak goruntu uretin" -ForegroundColor White
    Write-Host "3. Post-processing uygulayin: .\master-automation.ps1 -Action post-process" -ForegroundColor White
    Write-Host ""
}
else {
    Write-Host "Kullanim:" -ForegroundColor Yellow
    Write-Host "  .\master-automation.ps1 -Action setup" -ForegroundColor Cyan
    Write-Host "  .\master-automation.ps1 -Action create-character" -ForegroundColor Cyan
    Write-Host "  .\master-automation.ps1 -Action generate-prompts -CharacterName Model1" -ForegroundColor Cyan
    Write-Host "  .\master-automation.ps1 -Action post-process" -ForegroundColor Cyan
    Write-Host "  .\master-automation.ps1 -Action generate -CharacterName Model1 -ImageCount 10" -ForegroundColor Cyan
    Write-Host "  .\master-automation.ps1 -Action all" -ForegroundColor Cyan
    Write-Host ""
}

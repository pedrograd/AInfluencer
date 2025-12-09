# ============================================
# AInfluencer - Tam Otomatik Kurulum
# ============================================
# Bu script tum kurulum ve hazirlik islemlerini otomatik yapar

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Simple path resolution
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = $scriptRoot

# Simple logging functions (ASCII only)
function Write-Info { param([string]$Msg) Write-Host "[AInfluencer] $Msg" -ForegroundColor White }
function Write-Success { param([string]$Msg) Write-Host "[AInfluencer] OK  $Msg" -ForegroundColor Green }
function Write-Warning { param([string]$Msg) Write-Host "[AInfluencer] !   $Msg" -ForegroundColor Yellow }
function Write-Error { param([string]$Msg) Write-Host "[AInfluencer] ERR $Msg" -ForegroundColor Red }

# Simple helper functions
function Get-ComfyUIPath { return Join-Path $Root "ComfyUI" }
function Ensure-PythonInstalled {
    # Helper to test if a Python command actually works
    function Test-PythonCommand {
        param([string]$Cmd)
        try {
            $process = Start-Process -FilePath $Cmd -ArgumentList "--version" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$env:TEMP\py_test_stdout.txt" -RedirectStandardError "$env:TEMP\py_test_stderr.txt"
            $stdout = if (Test-Path "$env:TEMP\py_test_stdout.txt") { Get-Content "$env:TEMP\py_test_stdout.txt" -Raw } else { "" }
            $stderr = if (Test-Path "$env:TEMP\py_test_stderr.txt") { Get-Content "$env:TEMP\py_test_stderr.txt" -Raw } else { "" }
            $output = "$stdout$stderr"
            
            # Cleanup
            if (Test-Path "$env:TEMP\py_test_stdout.txt") { Remove-Item "$env:TEMP\py_test_stdout.txt" -ErrorAction SilentlyContinue }
            if (Test-Path "$env:TEMP\py_test_stderr.txt") { Remove-Item "$env:TEMP\py_test_stderr.txt" -ErrorAction SilentlyContinue }
            
            # Check if it's Windows Store alias
            if ($output -match "Microsoft Store" -or $output -match "App execution aliases" -or $output -match "run without arguments") {
                return $false
            }
            
            # Check if it's a valid Python version
            if ($output -match "Python \d+\.\d+" -and $process.ExitCode -eq 0) {
                return $true
            }
            
            return $false
        } catch {
            return $false
        }
    }
    
    # Try py launcher first (more reliable on Windows)
    if (Get-Command py -ErrorAction SilentlyContinue) {
        if (Test-PythonCommand "py") {
            return "py"
        }
    }
    
    # Try python command, but verify it actually works
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-PythonCommand "python") {
            return "python"
        } else {
            Write-Warning "Python komutu Windows Store alias'ina isaret ediyor veya calismiyor"
        }
    }
    
    # If we get here, neither worked
    Write-Error "Python bulunamadi veya calismiyor!"
    Write-Host ""
    Write-Host "Cozum:" -ForegroundColor Yellow
    Write-Host "  1. Python'i kurun: https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "     Kurulum sirasinda 'Add Python to PATH' secenegini isaretleyin" -ForegroundColor Cyan
    Write-Host "  2. Windows Store alias'ini devre disi birakin:" -ForegroundColor Cyan
    Write-Host "     Ayarlar > Uygulamalar > Uygulama yoneticisi > Python > Gelişmiş seçenekler > Sıfırla" -ForegroundColor White
    Write-Host ""
    throw "Python bulunamadi. Lutfen Python'i kurun veya Windows Store alias'ini devre disi birakin."
}
function Test-GitInstalled {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        try {
            $version = git --version 2>&1
            if ($version -match "git version") {
                return $true
            }
        } catch {
            return $false
        }
    }
    return $false
}

function Ensure-ComfyUI { 
    param([bool]$AutoClone = $true)
    $path = Get-ComfyUIPath
    
    # Check if ComfyUI already exists
    if (Test-Path $path) {
        $mainPy = Join-Path $path "main.py"
        if (Test-Path $mainPy) {
            Write-Success "ComfyUI bulundu: $path"
            return $path
        } else {
            Write-Warning "ComfyUI klasoru var ancak main.py bulunamadi: $path"
            # Check if there's a nested ComfyUI directory
            $nestedPath = Join-Path $path "ComfyUI"
            $nestedMainPy = Join-Path $nestedPath "main.py"
            if (Test-Path $nestedMainPy) {
                Write-Info "Icice ComfyUI klasoru bulundu, duzeltiliyor..."
                try {
                    # Move contents from nested to parent
                    Get-ChildItem -Path $nestedPath | Move-Item -Destination $path -Force
                    Remove-Item -Path $nestedPath -Force -ErrorAction SilentlyContinue
                    Write-Success "Icice klasor duzeltildi"
                    if (Test-Path $mainPy) {
                        Write-Success "ComfyUI bulundu: $path"
                        return $path
                    }
                } catch {
                    Write-Warning "Icice klasor duzeltilemedi: $_"
                }
            }
        }
    }
    
    # Try to auto-clone if enabled
    if ($AutoClone) {
        if (-not (Test-GitInstalled)) {
            Write-Error "Git bulunamadi. ComfyUI'i manuel olarak kurmaniz gerekiyor."
            throw "Git gerekli ancak bulunamadi"
        }
        
        # Check if directory exists but is incomplete
        if (Test-Path $path) {
            Write-Warning "ComfyUI klasoru zaten var ancak eksik gorunuyor: $path"
            $mainPy = Join-Path $path "main.py"
            if (-not (Test-Path $mainPy)) {
                Write-Info "Eksik klasor temizleniyor..."
                try {
                    Remove-Item -Path $path -Recurse -Force -ErrorAction Stop
                    Write-Info "Eksik klasor temizlendi"
                } catch {
                    Write-Error "Eksik klasor temizlenemedi: $_"
                    Write-Host "Lutfen manuel olarak $path klasorunu silin ve tekrar deneyin" -ForegroundColor Yellow
                    throw "ComfyUI klasoru eksik ve temizlenemedi"
                }
            }
        }
        
        Write-Info "ComfyUI bulunamadi, otomatik klonlaniyor..."
        Write-Info "Bu islem birkaç dakika surebilir..."
        
        try {
            Push-Location $Root
            
            # Run git clone and capture output separately
            $gitStdout = ""
            $gitStderr = ""
            $process = Start-Process -FilePath "git" -ArgumentList "clone", "https://github.com/comfyanonymous/ComfyUI.git" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$env:TEMP\git_stdout.txt" -RedirectStandardError "$env:TEMP\git_stderr.txt"
            
            if ($process.ExitCode -eq 0) {
                # Wait a moment for file system to sync
                Start-Sleep -Seconds 2
                
                # Verify the clone completed successfully
                if (Test-Path $path) {
                    $mainPy = Join-Path $path "main.py"
                    if (Test-Path $mainPy) {
                        Write-Success "ComfyUI basariyla klonlandi: $path"
                        
                        # Install Python requirements
                        Write-Info "Python requirements kuruluyor..."
                        $pythonCmd = Ensure-PythonInstalled
                        $requirementsFile = Join-Path $path "requirements.txt"
                        if (Test-Path $requirementsFile) {
                            try {
                                Push-Location $path
                                & $pythonCmd -m pip install -r requirements.txt --quiet 2>&1 | Out-Null
                                if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
                                    Write-Success "Python requirements kuruldu"
                                } else {
                                    Write-Warning "Python requirements kurulumunda hata olustu (devam ediliyor)"
                                }
                            } catch {
                                Write-Warning "Python requirements kurulumunda hata: $_"
                            } finally {
                                Pop-Location
                            }
                        }
                        
                        Pop-Location
                        return $path
                    } else {
                        Write-Error "ComfyUI klonlandi ancak main.py bulunamadi. Klonlama eksik olabilir."
                    }
                } else {
                    Write-Error "ComfyUI klonlandi ancak klasor bulunamadi: $path"
                }
            } else {
                # Check if it's because directory already exists
                if (Test-Path "$env:TEMP\git_stderr.txt") {
                    $stderrContent = Get-Content "$env:TEMP\git_stderr.txt" -Raw
                    if ($stderrContent -match "already exists") {
                        Write-Warning "ComfyUI klasoru zaten var. Mevcut klasor kullaniliyor..."
                        if (Test-Path $path) {
                            $mainPy = Join-Path $path "main.py"
                            if (Test-Path $mainPy) {
                                Write-Success "Mevcut ComfyUI kullaniliyor: $path"
                                Pop-Location
                                return $path
                            }
                        }
                    }
                    Write-Error "ComfyUI klonlanamadi. Git cikis kodu: $($process.ExitCode)"
                    Write-Host $stderrContent -ForegroundColor Red
                } else {
                    Write-Error "ComfyUI klonlanamadi. Git cikis kodu: $($process.ExitCode)"
                }
            }
            
            # Cleanup temp files
            if (Test-Path "$env:TEMP\git_stdout.txt") { Remove-Item "$env:TEMP\git_stdout.txt" -ErrorAction SilentlyContinue }
            if (Test-Path "$env:TEMP\git_stderr.txt") { Remove-Item "$env:TEMP\git_stderr.txt" -ErrorAction SilentlyContinue }
            
        } catch {
            Write-Error "ComfyUI klonlanamadi: $_"
        } finally {
            Pop-Location
        }
    }
    
    # If we get here, ComfyUI is not available
    Write-Error "ComfyUI bulunamadi: $path"
    throw "ComfyUI bulunamadi: $path"
}
function Test-RequiredFolders { 
    $folders = @(
        "characters",
        (Join-Path "ComfyUI" "output"),
        (Join-Path "ComfyUI" "output_processed"),
        (Join-Path "ComfyUI" "output_final")
    )
    foreach ($folder in $folders) {
        $fullPath = Join-Path $Root $folder
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Info "Klasor olusturuldu: $folder"
        }
    }
    return $true
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TAM OTOMATIK KURULUM BASLIYOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$comfyPath = Get-ComfyUIPath

try {
    # 1. Sistem Kontrolleri
    Write-Info "[1/8] Sistem kontrolleri yapiliyor..."
    
    try {
        $comfyPath = Ensure-ComfyUI -AutoClone $true
        Write-Success "ComfyUI hazir"
    } catch {
        Write-Error "ComfyUI kurulumu basarisiz: $_"
        Write-Host ""
        Write-Host "ComfyUI'i manuel olarak kurmak icin:" -ForegroundColor Yellow
        Write-Host "  1. Git ile klonlayin:" -ForegroundColor Cyan
        Write-Host "     git clone https://github.com/comfyanonymous/ComfyUI.git" -ForegroundColor White
        Write-Host "     cd ComfyUI" -ForegroundColor White
        $pythonCmd = Ensure-PythonInstalled
        Write-Host "     $pythonCmd -m pip install -r requirements.txt" -ForegroundColor White
        Write-Host ""
        exit 1
    }
    
    # PHASE 3: Use Get-PythonCmd pattern (prefer .venv)
    function Get-PythonCmd {
        $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
        if (Test-Path $venvPy) {
            return $venvPy
        }
        # Fallback to system Python
        return Ensure-PythonInstalled
    }
    
    # Python kontrolu
    try {
        $pythonCmd = Get-PythonCmd
        Write-Success "Python bulundu: $pythonCmd"
    } catch {
        Write-Error "Python bulunamadi: $_"
        Write-Host ""
        Write-Host "Python'i otomatik olarak kurmak ister misiniz? (E/H)" -ForegroundColor Yellow
        $response = Read-Host
        if ($response -eq "E" -or $response -eq "e" -or $response -eq "Y" -or $response -eq "y") {
            Write-Info "Python otomatik kurulum baslatiliyor..."
            $installScript = Join-Path $Root "auto-install-python.ps1"
            if (Test-Path $installScript) {
                try {
                    & $installScript
                    Write-Host ""
                    Write-Info "Python kurulumu tamamlandi. Lutfen PowerShell'i yeniden baslatin ve scripti tekrar calistirin."
                    Write-Host ""
                    exit 0
                } catch {
                    Write-Error "Python otomatik kurulumu basarisiz: $_"
                    Write-Host ""
                    Write-Host "Manuel kurulum:" -ForegroundColor Yellow
                    Write-Host "  1. https://www.python.org/downloads/ adresinden Python indirin" -ForegroundColor Cyan
                    Write-Host "  2. Kurulum sirasinda 'Add Python to PATH' secenegini isaretleyin" -ForegroundColor Cyan
                    Write-Host ""
                    exit 1
                }
            } else {
                Write-Error "auto-install-python.ps1 bulunamadi!"
                Write-Host ""
                Write-Host "Manuel kurulum:" -ForegroundColor Yellow
                Write-Host "  1. https://www.python.org/downloads/ adresinden Python indirin" -ForegroundColor Cyan
                Write-Host "  2. Kurulum sirasinda 'Add Python to PATH' secenegini isaretleyin" -ForegroundColor Cyan
                Write-Host ""
                exit 1
            }
        } else {
            Write-Host ""
            Write-Host "Python kurulumu atlandi. Lutfen Python'i manuel olarak kurun." -ForegroundColor Yellow
            Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
            Write-Host ""
            exit 1
        }
    }
    
    Write-Host ""
    
    # 2. Eksik Araclari Kur
    Write-Info "[2/8] Eksik araclar kuruluyor..."
    $installToolsPath = Join-Path $Root "auto-install-missing-tools.ps1"
    if (Test-Path $installToolsPath) {
        try {
            & $installToolsPath
            Write-Success "Araclar kontrol edildi"
        } catch {
            Write-Warning "Arac kurulumunda hata: $_"
        }
    } else {
        Write-Warning "auto-install-missing-tools.ps1 bulunamadi, atlaniyor"
    }
    Write-Host ""
    
    # 3. Klasor Yapisi Olustur
    Write-Info "[3/8] Klasor yapisi olusturuluyor..."
    try {
        Test-RequiredFolders
        Write-Success "Klasor yapisi hazir"
    } catch {
        Write-Error "Klasor olusturulamadi: $_"
        exit 1
    }
    Write-Host ""
    
    # 4. Karakter Template Kopyala
    Write-Info "[4/8] Karakter template hazirlaniyor..."
    $templatePath = Join-Path $Root "character_template.json"
    if (Test-Path $templatePath) {
        Write-Success "Template mevcut"
    } else {
        Write-Warning "Template bulunamadi: $templatePath"
    }
    Write-Host ""
    
    # 5. Python Scriptleri Kontrol Et
    Write-Info "[5/8] Python scriptleri kontrol ediliyor..."
    $scripts = @(
        "post_process_pipeline.py",
        "generate-prompt-auto.py",
        "comfyui-workflow-generator.py"
    )
    
    $missingScripts = @()
    foreach ($script in $scripts) {
        $scriptPath = Join-Path $Root $script
        if (Test-Path $scriptPath) {
            Write-Success "$script mevcut"
        } else {
            Write-Warning "$script bulunamadi"
            $missingScripts += $script
        }
    }
    Write-Host ""
    
    # 6. Model Kontrolleri
    Write-Info "[6/8] Model kontrolleri yapiliyor..."
    $models = @{
        "Checkpoint" = Join-Path $comfyPath "models\checkpoints\*.safetensors"
        "InstantID" = Join-Path $comfyPath "models\instantid\ip-adapter.bin"
        "RealESRGAN" = Join-Path $comfyPath "models\upscale_models\RealESRGAN_x4plus.pth"
        "GFPGAN" = Join-Path $comfyPath "models\face_restore\GFPGANv1.4.pth"
    }
    
    $missingModels = @()
    foreach ($modelName in $models.Keys) {
        $modelPath = $models[$modelName]
        try {
            $found = Get-ChildItem -Path $modelPath -ErrorAction SilentlyContinue
            if ($found) {
                Write-Success "$modelName modeli bulundu"
            } else {
                Write-Warning "$modelName modeli bulunamadi"
                $missingModels += $modelName
            }
        } catch {
            Write-Warning "$modelName modeli kontrol edilemedi: $_"
            $missingModels += $modelName
        }
    }
    Write-Host ""
    
    # 7. Ozet
    Write-Info "[7/8] Ozet hazirlaniyor..."
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "KURULUM DURUMU" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($missingModels.Count -eq 0) {
        Write-Success "Tum modeller mevcut!"
    } else {
        Write-Warning "Eksik modeller:"
        foreach ($model in $missingModels) {
            Write-Host "  - $model" -ForegroundColor Yellow
        }
        Write-Host ""
        $downloadScript = Join-Path $Root "download-models-auto.ps1"
        if (Test-Path $downloadScript) {
            Write-Host "Modelleri indirmek icin: .\download-models-auto.ps1" -ForegroundColor Cyan
        }
    }
    Write-Host ""
    
    # 8. Sonraki Adimlar
    Write-Info "[8/8] Sonraki adimlar gosteriliyor..."
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "SONRAKI ADIMLAR" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Karakter olustur:" -ForegroundColor White
    Write-Host "   .\create-character-config.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Prompt'lar olustur:" -ForegroundColor White
    Write-Host "   $pythonCmd generate-prompt-auto.py characters\MODEL_ADI\config.json" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. ComfyUI workflow olustur:" -ForegroundColor White
    Write-Host "   $pythonCmd comfyui-workflow-generator.py characters\MODEL_ADI\config.json" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "4. ComfyUI'i baslat ve workflow'u yukle" -ForegroundColor White
    Write-Host ""
    Write-Host "5. Goruntu uret ve post-processing uygula:" -ForegroundColor White
    Write-Host "   $pythonCmd post_process_pipeline.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "HAZIR!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Error "Kurulum sirasinda kritik hata: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}

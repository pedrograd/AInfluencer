# ============================================
# AInfluencer - Tam Otomatik Görüntü Üretim Scripti
# ============================================
# Tüm süreci otomatik yapar: karakter -> prompt -> workflow -> üretim -> post-processing

param(
    [Parameter(Mandatory=$false)]
    [string]$CharacterName = "",
    
    [Parameter(Mandatory=$false)]
    [int]$ImageCount = 10,
    
    [Parameter(Mandatory=$false)]
    [string]$ComfyUIServer = "127.0.0.1:8188",
    
    [switch]$SkipSetup,
    
    [switch]$SkipPostProcess,
    
    [switch]$SmokeTest,
    
    [switch]$NonInteractive  # PHASE 7: Non-interactive mode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# PHASE 1: UTF-8 encoding enforcement
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try { 
    chcp 65001 | Out-Null 
} catch {
    # Fallback if chcp fails
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}

# Simple path resolution
$Root = $PSScriptRoot
if (-not $Root) {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# PHASE 0: Lock Python to .venv
function Get-PythonCmd {
    $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        return $venvPy
    }
    # Fallback to system Python
    return Ensure-PythonInstalled
}

# PHASE 1: Cross-version safe environment variable wrapper
# Works on both PowerShell 5.1 and PowerShell 7.x
function Invoke-WithEnv {
    param(
        [Parameter(Mandatory=$true)][hashtable]$Vars,
        [Parameter(Mandatory=$true)][scriptblock]$Block
    )
    
    $backup = @{}
    foreach ($k in $Vars.Keys) {
        # Get current value using Env: drive
        $envItem = Get-Item "Env:$k" -ErrorAction SilentlyContinue
        $backup[$k] = if ($envItem) { $envItem.Value } else { $null }
        # Set new value using Set-Item
        Set-Item "Env:$k" -Value ([string]$Vars[$k]) -ErrorAction Stop
    }
    
    try {
        & $Block
    }
    finally {
        foreach ($k in $Vars.Keys) {
            if ($null -eq $backup[$k]) {
                Remove-Item "Env:$k" -ErrorAction SilentlyContinue
            } else {
                Set-Item "Env:$k" -Value $backup[$k] -ErrorAction Stop
            }
        }
    }
}

# Simple logging functions (ASCII only)
function Write-Info { param([string]$Msg) Write-Host "[AInfluencer] $Msg" -ForegroundColor White }
function Write-Success { param([string]$Msg) Write-Host "[AInfluencer] OK  $Msg" -ForegroundColor Green }
function Write-Warning { param([string]$Msg) Write-Host "[AInfluencer] !   $Msg" -ForegroundColor Yellow }
function Write-Error { param([string]$Msg) Write-Host "[AInfluencer] ERR $Msg" -ForegroundColor Red }
function Get-ComfyUIPath { return Join-Path $Root "ComfyUI" }
function Get-CharactersPath { return Join-Path $Root "characters" }
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

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TAM OTOMATIK GORUNTU URETIMI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ensure we're in the right directory
if (-not (Test-Path (Join-Path $Root "full-auto-generate.ps1"))) {
    Write-Warning "Script yanlis dizinde calistiriliyor olabilir."
    Write-Host "  Mevcut dizin: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "  Beklenen dizin: $Root" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Dogru kullanim:" -ForegroundColor Cyan
    Write-Host "  cd $Root" -ForegroundColor White
    Write-Host "  .\full-auto-generate.ps1 -CharacterName `"Model1`" -ImageCount 1" -ForegroundColor White
    Write-Host ""
}

try {
    # PHASE 0: Use .venv Python if available
    $pythonCmd = Get-PythonCmd
    Write-Success "Python bulundu: $pythonCmd"
    
    # 0. ComfyUI Kontrolü (kritik - önce kontrol et)
    Write-Info "[0/7] ComfyUI kontrol ediliyor..."
    try {
        $comfyPath = Ensure-ComfyUI -AutoClone $true
        Write-Success "ComfyUI hazir: $comfyPath"
    } catch {
        Write-Error "ComfyUI kurulumu basarisiz: $_"
        Write-Host ""
        Write-Host "ComfyUI'i manuel olarak kurmak icin:" -ForegroundColor Yellow
        Write-Host "  1. Git ile klonlayin:" -ForegroundColor Cyan
        Write-Host "     git clone https://github.com/comfyanonymous/ComfyUI.git" -ForegroundColor White
        Write-Host "     cd ComfyUI" -ForegroundColor White
        Write-Host "     $pythonCmd -m pip install -r requirements.txt" -ForegroundColor White
        Write-Host ""
        Write-Host "  2. Veya otomatik kurulum scriptini calistirin:" -ForegroundColor Cyan
        Write-Host "     .\auto-complete-setup.ps1" -ForegroundColor White
        Write-Host ""
        exit 1
    }
    Write-Host ""
    
    # 1. Kurulum Kontrolü
    if (-not $SkipSetup) {
        Write-Info "[1/7] Kurulum kontrol ediliyor..."
        $setupScript = Join-Path $Root "auto-complete-setup.ps1"
        if (Test-Path $setupScript) {
            try {
                # Capture output but don't fail on warnings
                $setupOutput = & $setupScript 2>&1
                $setupExitCode = $LASTEXITCODE
                if ($setupExitCode -eq 0 -or $setupExitCode -eq $null) {
                    Write-Success "Kurulum kontrolu tamamlandi"
                } else {
                    Write-Warning "Kurulum kontrolunde bazı uyarilar var (devam ediliyor)"
                }
            } catch {
                Write-Warning "Kurulum kontrolunde hata: $_ (devam ediliyor)"
            }
        } else {
            Write-Warning "auto-complete-setup.ps1 bulunamadi, atlaniyor"
        }
        Write-Host ""
    }
    
    # 2. Karakter Kontrolü
    Write-Info "[2/7] Karakter kontrol ediliyor..."
    
    $charactersPath = Get-CharactersPath
    
    # Karakter klasörünü oluştur
    if (-not (Test-Path $charactersPath)) {
        New-Item -ItemType Directory -Path $charactersPath -Force | Out-Null
        Write-Info "Karakter klasoru olusturuldu: $charactersPath"
    }
    
    if ([string]::IsNullOrWhiteSpace($CharacterName)) {
        Write-Warning "Karakter adi belirtilmedi"
        Write-Host "  Mevcut karakterler:" -ForegroundColor White
        
        $characters = Get-ChildItem -Path $charactersPath -Directory -ErrorAction SilentlyContinue
        if ($characters) {
            foreach ($char in $characters) {
                Write-Host "    - $($char.Name)" -ForegroundColor Cyan
            }
            Write-Host ""
            $CharacterName = Read-Host "Karakter adini girin (veya yeni karakter olusturmak icin Enter)"
        } else {
            Write-Warning "Karakter klasoru bos"
            Write-Host "  Yeni karakter olusturulacak..." -ForegroundColor Yellow
            $CharacterName = Read-Host "Karakter adini girin"
        }
    }
    
    $configFile = Join-Path $charactersPath "$CharacterName\config.json"
    
    # Karakter config yoksa oluştur
    if (-not (Test-Path $configFile)) {
        Write-Warning "Karakter config bulunamadi: $configFile"
        Write-Host "  Yeni karakter olusturuluyor..." -ForegroundColor Yellow
        
        $createScript = Join-Path $Root "create-character-config.ps1"
        if (Test-Path $createScript) {
            try {
                # PHASE 7: Pass CharacterName and NonInteractive flag
                if ($SmokeTest -or $NonInteractive) {
                    # In smoke test or non-interactive mode, use defaults
                    & $createScript -CharacterName $CharacterName -NonInteractive
                } else {
                    # Pass name but allow interactive prompts for other fields
                    & $createScript -CharacterName $CharacterName
                }
                
                # Oluşturulan karakteri bul
                $characters = Get-ChildItem -Path $charactersPath -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
                if ($characters) {
                    $CharacterName = $characters[0].Name
                    $configFile = Join-Path $charactersPath "$CharacterName\config.json"
                    Write-Success "Karakter olusturuldu: $CharacterName"
                } else {
                    Write-Error "Karakter olusturulamadi!"
                    Write-Host "  Manuel olarak karakter olusturmak icin:" -ForegroundColor Yellow
                    Write-Host "    .\create-character-config.ps1" -ForegroundColor Cyan
                    exit 1
                }
            } catch {
                Write-Error "Karakter olusturma hatasi: $_"
                Write-Host "  Manuel olarak karakter olusturmak icin:" -ForegroundColor Yellow
                Write-Host "    .\create-character-config.ps1" -ForegroundColor Cyan
                exit 1
            }
        } else {
            Write-Error "create-character-config.ps1 bulunamadi!"
            Write-Host "  Lutfen once karakter config dosyasini olusturun." -ForegroundColor Yellow
            exit 1
        }
    }
    
    if (-not (Test-Path $configFile)) {
        Write-Error "Karakter config hala bulunamadi: $configFile"
        Write-Host "  Lutfen karakter config dosyasini olusturun:" -ForegroundColor Yellow
        Write-Host "    .\create-character-config.ps1" -ForegroundColor Cyan
        exit 1
    }
    
    Write-Success "Karakter bulundu: $CharacterName"
    Write-Host ""
    
    # 2.5. Checkpoint Model Kontrolü (kritik - workflow için gerekli)
    Write-Info "[2.5/7] Checkpoint model kontrol ediliyor..."
    $comfyPath = Get-ComfyUIPath
    $checkpointDir = Join-Path $comfyPath "models\checkpoints"
    $checkpointDirAbsolute = (Resolve-Path $checkpointDir -ErrorAction SilentlyContinue).Path
    if (-not $checkpointDirAbsolute) {
        $checkpointDirAbsolute = (New-Item -ItemType Directory -Path $checkpointDir -Force).FullName
    }
    Write-Info "Checkpoint scan dir: $checkpointDirAbsolute"
    $checkpointFound = $false
    
    # Klasörü oluştur yoksa
    if (-not (Test-Path $checkpointDir)) {
        New-Item -ItemType Directory -Path $checkpointDir -Force | Out-Null
        Write-Info "Checkpoint klasoru olusturuldu: $checkpointDir"
    }
    
    # Checkpoint dosyalarını ara (daha güvenilir yöntem)
    $checkpointFiles = @()
    
    # .safetensors dosyalarını ara
    $safetensorsFiles = Get-ChildItem -Path $checkpointDir -Filter "*.safetensors" -ErrorAction SilentlyContinue
    if ($safetensorsFiles) {
        if ($safetensorsFiles -is [array]) {
            $checkpointFiles += $safetensorsFiles
        } else {
            $checkpointFiles += $safetensorsFiles
        }
    }
    
    # .ckpt dosyalarını ara
    $ckptFiles = Get-ChildItem -Path $checkpointDir -Filter "*.ckpt" -ErrorAction SilentlyContinue
    if ($ckptFiles) {
        if ($ckptFiles -is [array]) {
            $checkpointFiles += $ckptFiles
        } else {
            $checkpointFiles += $ckptFiles
        }
    }
    
    # Sonuçları kontrol et
    if ($checkpointFiles.Count -gt 0) {
        $checkpointFound = $true
        $firstCheckpoint = $checkpointFiles[0]
        $checkpointName = $firstCheckpoint.Name
        if ($firstCheckpoint.Length) {
            $fileSizeMB = [math]::Round($firstCheckpoint.Length / 1MB, 2)
            $fileSizeGB = [math]::Round($firstCheckpoint.Length / 1GB, 2)
            if ($fileSizeGB -ge 1) {
                Write-Success "Checkpoint modeli bulundu: $checkpointName ($fileSizeGB GB)"
            } else {
                Write-Success "Checkpoint modeli bulundu: $checkpointName ($fileSizeMB MB)"
            }
        } else {
            Write-Success "Checkpoint modeli bulundu: $checkpointName"
        }
    } else {
        # Daha detaylı hata mesajı
        Write-Error "Checkpoint model bulunamadi - workflow olusturulamaz!"
        Write-Host ""
        Write-Host "  Kontrol edilen klasor: $checkpointDir" -ForegroundColor Yellow
        if (Test-Path $checkpointDir) {
            $allFiles = Get-ChildItem -Path $checkpointDir -File -ErrorAction SilentlyContinue
            if ($allFiles) {
                Write-Host "  Klasorde bulunan dosyalar:" -ForegroundColor Yellow
                foreach ($file in $allFiles) {
                    if ($file.PSIsContainer -eq $false -and $file.Length) {
                        $fileSizeMB = [math]::Round($file.Length / 1MB, 2)
                        $fileSizeGB = [math]::Round($file.Length / 1GB, 2)
                        if ($fileSizeGB -ge 1) {
                            Write-Host "    - $($file.Name) ($fileSizeGB GB)" -ForegroundColor White
                        } else {
                            Write-Host "    - $($file.Name) ($fileSizeMB MB)" -ForegroundColor White
                        }
                    } else {
                        Write-Host "    - $($file.Name) (dizin veya boyut bilinmiyor)" -ForegroundColor White
                    }
                }
                Write-Host ""
                Write-Host "  NOT: Checkpoint dosyalari .safetensors veya .ckpt uzantili olmalidir" -ForegroundColor Yellow
            } else {
                Write-Host "  Klasor bos" -ForegroundColor Yellow
            }
        }
        Write-Host ""
        Write-Host "  Cozum:" -ForegroundColor Yellow
        Write-Host "    Otomatik indirme deneniyor..." -ForegroundColor Cyan
        Write-Host ""
        
        # Try to automatically download checkpoint
        $downloadScript = Join-Path $Root "download-models-auto.ps1"
        $ensureScript = Join-Path $Root "scripts\ensure-all-models.ps1"
        
        if (Test-Path $ensureScript) {
            Write-Info "Otomatik model indirme baslatiliyor..."
            try {
                & $ensureScript
                $downloadExitCode = $LASTEXITCODE
                
                # Check again after download attempt
                $checkpointFilesAfter = Get-ChildItem -Path $checkpointDir -Include "*.safetensors", "*.ckpt" -ErrorAction SilentlyContinue
                if ($checkpointFilesAfter) {
                    $count = if ($checkpointFilesAfter -is [array]) { $checkpointFilesAfter.Count } else { 1 }
                    if ($count -gt 0) {
                        Write-Success "Checkpoint model basariyla indirildi!"
                        $checkpointFound = $true
                    }
                }
            } catch {
                Write-Warning "Otomatik indirme basarisiz: $_"
            }
        } elseif (Test-Path $downloadScript) {
            Write-Info "Model indirme scripti calistiriliyor..."
            try {
                & $downloadScript
                # Check again after download attempt
                $checkpointFilesAfter = Get-ChildItem -Path $checkpointDir -Include "*.safetensors", "*.ckpt" -ErrorAction SilentlyContinue
                if ($checkpointFilesAfter) {
                    $count = if ($checkpointFilesAfter -is [array]) { $checkpointFilesAfter.Count } else { 1 }
                    if ($count -gt 0) {
                        Write-Success "Checkpoint model basariyla indirildi!"
                        $checkpointFound = $true
                    }
                }
            } catch {
                Write-Warning "Indirme scripti basarisiz: $_"
            }
        }
        
        if (-not $checkpointFound) {
            Write-Error "Checkpoint model hala bulunamadi!"
            Write-Host ""
            Write-Host "  Manuel indirme:" -ForegroundColor Yellow
            Write-Host "    1. Bir checkpoint model indirin (ornek: Realistic Vision V6.0)" -ForegroundColor Cyan
            Write-Host "    2. Dosyayi su klasore koyun: $checkpointDir" -ForegroundColor Cyan
            Write-Host "    3. Indirme: https://civitai.com/models/4201/realistic-vision-v60-b1" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  Veya otomatik indirme scriptini tekrar calistirin:" -ForegroundColor Yellow
            Write-Host "    .\scripts\ensure-all-models.ps1" -ForegroundColor Cyan
            Write-Host "    .\download-models-auto.ps1" -ForegroundColor Cyan
            Write-Host ""
            exit 1
        }
    }
    Write-Host ""
    
    # 3. Prompt'ları Oluştur
    Write-Info "[3/7] Prompt'lar olusturuluyor..."
    $promptFile = Join-Path $Root "generated_prompts.txt"
    $generatePromptScript = Join-Path $Root "generate-prompt-auto.py"
    
    if (-not (Test-Path $generatePromptScript)) {
        Write-Error "generate-prompt-auto.py bulunamadi: $generatePromptScript"
        exit 1
    }
    
    try {
        # PHASE 0: Use .venv Python
        $pythonCmd = Get-PythonCmd
        & $pythonCmd $generatePromptScript $configFile
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            throw "Python script cikis kodu: $LASTEXITCODE"
        }
    } catch {
        Write-Error "Prompt olusturma hatasi: $_"
        exit 1
    }
    
    if (-not (Test-Path $promptFile)) {
        Write-Error "Prompt dosyasi olusturulamadi: $promptFile"
        exit 1
    }
    
    Write-Success "Prompt'lar olusturuldu: $promptFile"
    Write-Host ""
    
    # 4. Workflow Oluştur
    Write-Info "[4/7] Workflow olusturuluyor..."
    $workflowFile = Join-Path $Root "comfyui_workflow.json"
    $workflowGeneratorScript = Join-Path $Root "comfyui-workflow-generator.py"
    
    if (-not (Test-Path $workflowGeneratorScript)) {
        Write-Error "comfyui-workflow-generator.py bulunamadi: $workflowGeneratorScript"
        exit 1
    }
    
    # PHASE 5: Validate-only step before generation
    Write-Info "Workflow validation yapiliyor..."
    try {
        $pythonCmd = Get-PythonCmd
        $validateOutput = & $pythonCmd $workflowGeneratorScript $configFile --server $ComfyUIServer --validate-only 2>&1
        $validateExitCode = $LASTEXITCODE
        if ($validateExitCode -ne 0 -and $validateExitCode -ne $null) {
            Write-Error "Workflow validation basarisiz!"
            Write-Host $validateOutput
            Write-Host ""
            Write-Host "  Cozum:" -ForegroundColor Yellow
            Write-Host "    - ComfyUI server'in calistigindan emin olun: http://$ComfyUIServer/system_stats" -ForegroundColor Cyan
            Write-Host "    - Checkpoint model'in ComfyUI/models/checkpoints/ klasorunde oldugunu kontrol edin" -ForegroundColor Cyan
            Write-Host ""
            exit 1
        }
        Write-Success "Workflow validation basarili"
    } catch {
        Write-Warning "Workflow validation atlandi: $_"
    }
    Write-Host ""
    
    # PHASE 3: Check server capabilities before generating workflow
    Write-Info "ComfyUI server capability kontrolu yapiliyor..."
    $capabilityScript = Join-Path $Root "comfyui_capabilities.py"
    if (Test-Path $capabilityScript) {
        try {
            $pythonCmd = Get-PythonCmd
            $capabilityOutput = & $pythonCmd $capabilityScript --server $ComfyUIServer --check-instantid 2>&1
            if ($capabilityOutput -match "YES") {
                Write-Success "InstantID nodes available on server"
            } else {
                Write-Warning "InstantID nodes not available on server - will use base workflow"
            }
        } catch {
            Write-Warning "Capability check failed, proceeding with workflow generation"
        }
    }
    
    try {
        # PHASE 0: Use .venv Python
        $pythonCmd = Get-PythonCmd
        # PHASE 3: Use Invoke-WithEnv for cross-version compatibility (PS 5.1 + PS 7.x)
        # Direct invocation with output capture - no Start-Process with -Environment
        $workflowExitCode = 0
        $stdout = ""
        $stderr = ""
        
        # Use Invoke-WithEnv to set environment variable, then capture output
        Invoke-WithEnv @{"COMFYUI_SERVER" = $ComfyUIServer} {
            # Capture both stdout and stderr
            $allOutput = & $pythonCmd $workflowGeneratorScript $configFile --server $ComfyUIServer 2>&1
            $workflowExitCode = $LASTEXITCODE
            
            # Separate stdout and stderr from mixed output
            foreach ($line in $allOutput) {
                if ($line -is [System.Management.Automation.ErrorRecord]) {
                    $stderr += $line.ToString() + "`r`n"
                } else {
                    $stdout += [string]$line + "`r`n"
                }
            }
        }
        
        # Display output
        if ($stdout) {
            Write-Host $stdout
        }
        if ($stderr) {
            Write-Host $stderr -ForegroundColor Yellow
        }
        
        # Check exit code
        if ($workflowExitCode -ne 0) {
            # Check if it's a checkpoint missing error (already shown by Python script)
            $combinedOutput = "$stdout$stderr"
            if ($combinedOutput -match "Checkpoint model bulunamadi") {
                # Error message already displayed by Python script
                Write-Host ""
                Write-Error "Workflow olusturulamadi: Checkpoint model gerekli"
                Write-Host ""
                Write-Host "  Cozum:" -ForegroundColor Yellow
                Write-Host "    1. Bir checkpoint model indirin (ornek: Realistic Vision V6.0)" -ForegroundColor Cyan
                $checkpointDir = Join-Path (Get-ComfyUIPath) "models\checkpoints"
                Write-Host "    2. Dosyayi su klasore koyun: $checkpointDir" -ForegroundColor Cyan
                Write-Host "    3. Indirme: https://civitai.com/models/4201/realistic-vision-v60-b1" -ForegroundColor Cyan
                Write-Host ""
                exit 1
            } else {
                # Other error - show the output and exit
                if ($combinedOutput) {
                    Write-Host ""
                    Write-Error "Workflow olusturma hatasi (cikis kodu: $workflowExitCode)"
                } else {
                    Write-Error "Workflow olusturma hatasi: Python script cikis kodu: $workflowExitCode"
                }
                exit 1
            }
        }
    } catch {
        Write-Error "Workflow olusturma hatasi: $_"
        exit 1
    }
    
    if (-not (Test-Path $workflowFile)) {
        Write-Error "Workflow dosyasi olusturulamadi: $workflowFile"
        exit 1
    }
    
    Write-Success "Workflow olusturuldu: $workflowFile"
    Write-Host ""
    
    # 5. ComfyUI Servis Kontrolü
    Write-Info "[5/7] ComfyUI servis kontrol ediliyor..."
    
    # ComfyUI çalışıyor mu kontrol et
    $comfyUrl = "http://$ComfyUIServer/system_stats"
    try {
        $response = Invoke-WebRequest -Uri $comfyUrl -TimeoutSec 5 -ErrorAction Stop
        Write-Success "ComfyUI calisiyor: $ComfyUIServer"
    } catch {
        Write-Error "ComfyUI calismiyor veya erisilemiyor: $ComfyUIServer"
        Write-Host ""
        Write-Host "ComfyUI'i baslatmak icin:" -ForegroundColor Yellow
        $comfyPath = Get-ComfyUIPath
        Write-Host "  cd `"$comfyPath`"" -ForegroundColor Cyan
        Write-Host "  $pythonCmd main.py" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "ComfyUI basladiktan sonra bu scripti tekrar calistirin." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    
    # 6. Görüntü Üretimi
    Write-Info "[6/7] Goruntu uretimi basliyor..."
    
    # Pre-flight Validation (Non-blocking warnings)
    Write-Info "Pre-flight kontrolu yapiliyor..."
    $comfyPath = Get-ComfyUIPath
    
    # Check for critical models (warn but don't fail)
    $missingModels = @()
    
    # Check for Checkpoint models (multiple file patterns) - use same logic as earlier check
    $checkpointDir = Join-Path $comfyPath "models\checkpoints"
    $checkpointFound = $false
    if (Test-Path $checkpointDir) {
        # Use same method as the earlier successful check
        $safetensorsFiles = Get-ChildItem -Path $checkpointDir -Filter "*.safetensors" -ErrorAction SilentlyContinue
        $ckptFiles = Get-ChildItem -Path $checkpointDir -Filter "*.ckpt" -ErrorAction SilentlyContinue
        
        $checkpointFiles = @()
        if ($safetensorsFiles) {
            if ($safetensorsFiles -is [array]) {
                $checkpointFiles += $safetensorsFiles
            } else {
                $checkpointFiles += $safetensorsFiles
            }
        }
        if ($ckptFiles) {
            if ($ckptFiles -is [array]) {
                $checkpointFiles += $ckptFiles
            } else {
                $checkpointFiles += $ckptFiles
            }
        }
        
        if ($checkpointFiles.Count -gt 0) {
            $checkpointFound = $true
        }
    }
    if (-not $checkpointFound) {
        $missingModels += "Checkpoint"
    }
    
    # PHASE 4: Check InstantID using server capability detection (not just file existence)
    $instantIdPath = Join-Path $comfyPath "models\instantid\ip-adapter.bin"
    $instantIdNodesAvailable = $false
    $instantIdFolderExists = Test-Path $instantIdPath
    
    $capabilityScript = Join-Path $Root "comfyui_capabilities.py"
    if (Test-Path $capabilityScript) {
        try {
            $pythonCmd = Get-PythonCmd
            $capabilityOutput = & $pythonCmd $capabilityScript --server $ComfyUIServer --check-instantid 2>&1
            if ($capabilityOutput -match "YES") {
                $instantIdNodesAvailable = $true
            }
        } catch {
            Write-Warning "InstantID capability check failed, assuming not available"
        }
    }
    
    if (-not $instantIdFolderExists) {
        $missingModels += "InstantID"
    }
    
    if ($missingModels.Count -gt 0) {
        Write-Warning "Bazi kritik modeller bulunamadi:"
        foreach ($model in $missingModels) {
            Write-Host "  - $model" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # PHASE 4: Stop if checkpoint is missing (critical)
        if ($missingModels -contains "Checkpoint") {
            Write-Error "Checkpoint model bulunamadi - bu kritik!"
            Write-Host ""
            Write-Host "  Cozum:" -ForegroundColor Yellow
            Write-Host "    1. Bir checkpoint model indirin (ornek: Realistic Vision V6.0)" -ForegroundColor Cyan
            Write-Host "    2. Dosyayi su klasore koyun: $checkpointDir" -ForegroundColor Cyan
            Write-Host "    3. Indirme: https://civitai.com/models/4201/realistic-vision-v60-b1" -ForegroundColor Cyan
            Write-Host ""
            exit 1
        }
        
        # PHASE 4: For InstantID, check both file and server nodes
        if ($missingModels -contains "InstantID" -or -not $instantIdNodesAvailable) {
            if ($instantIdFolderExists -and -not $instantIdNodesAvailable) {
                Write-Warning "  InstantID folder present but nodes NOT registered in server. Base workflow will be used."
            } elseif (-not $instantIdNodesAvailable) {
                Write-Warning "  InstantID nodes not registered in server - base workflow will be used"
            } else {
                Write-Warning "  InstantID model file bulunamadi - base workflow kullanilacak (yuz tutarliligi olmayacak)"
            }
            Write-Host "  InstantID model indirmek icin: .\download-models-auto.ps1" -ForegroundColor Cyan
        }
        Write-Host ""
    } else {
        Write-Success "Kritik modeller mevcut"
        if ($instantIdNodesAvailable) {
            Write-Success "InstantID nodes available on server"
        }
    }
    
    Write-Info "Goruntu uretimi hazirliklari tamamlandi..."
    Write-Host "  -> Toplam goruntu: $ImageCount" -ForegroundColor White
    $outputPath = Join-Path $comfyPath "output"
    Write-Host "  -> Cikis klasoru: $outputPath" -ForegroundColor White
    Write-Host ""
    
    # WebSocket kütüphanesi kontrolü
    Write-Info "Gerekli Python paketleri kontrol ediliyor..."
    try {
        # PHASE 0: Use .venv Python
        $pythonCmd = Get-PythonCmd
        $null = & $pythonCmd -c "import websocket; import requests" 2>&1
        $checkExitCode = $LASTEXITCODE
        if ($checkExitCode -ne 0 -and $checkExitCode -ne $null) {
            throw "Paketler bulunamadi"
        }
        # Additional check: try to actually import
        $importTest = & $pythonCmd -c "try:
    import websocket
    import requests
    print('OK')
except ImportError as e:
    print('MISSING')
    exit(1)" 2>&1
        if ($importTest -match "MISSING" -or $LASTEXITCODE -ne 0) {
            throw "Paketler bulunamadi"
        }
        Write-Success "Gerekli paketler mevcut"
    } catch {
        Write-Info "Gerekli paketler kuruluyor (websocket-client, requests)..."
        try {
            $installOutput = & $pythonCmd -m pip install --upgrade websocket-client requests 2>&1
            if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
                Write-Success "Paketler kuruldu"
            } else {
                Write-Warning "Paket kurulumunda hata olustu (devam ediliyor): $($installOutput -join ' ')"
            }
        } catch {
            Write-Warning "Paket kurulumunda hata: $_ (devam ediliyor)"
        }
    }
    
    # API ile görüntü üret
    $apiGeneratorScript = Join-Path $Root "comfyui-api-generator.py"
    if (-not (Test-Path $apiGeneratorScript)) {
        Write-Error "comfyui-api-generator.py bulunamadi: $apiGeneratorScript"
        exit 1
    }
    
    try {
        Write-Info "API generator calistiriliyor..."
        
        # PHASE 5: Create run directory for artifacts
        $runStamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $runDir = Join-Path $Root ("runs\" + $runStamp)
        New-Item -ItemType Directory -Force -Path $runDir | Out-Null
        Write-Info "Run artifacts directory: $runDir"
        
        # Build arguments array
        $scriptArgs = @(
            $apiGeneratorScript,
            "--workflow", $workflowFile,
            "--prompts", $promptFile,
            "--output", $outputPath,
            "--count", $ImageCount.ToString(),
            "--server", $ComfyUIServer,
            "--run-dir", $runDir
        )
        
        # Execute with proper output capture
        $stdoutFile = Join-Path $env:TEMP "comfyui_api_stdout_$(Get-Date -Format 'yyyyMMddHHmmss').txt"
        $stderrFile = Join-Path $env:TEMP "comfyui_api_stderr_$(Get-Date -Format 'yyyyMMddHHmmss').txt"
        
        try {
            # PHASE 0: Use .venv Python
            $pythonCmd = Get-PythonCmd
            $process = Start-Process -FilePath $pythonCmd -ArgumentList $scriptArgs `
                -NoNewWindow -Wait -PassThru `
                -RedirectStandardOutput $stdoutFile `
                -RedirectStandardError $stderrFile
            
            $apiExitCode = $process.ExitCode
            
            # Read output files
            $stdout = if (Test-Path $stdoutFile) { Get-Content $stdoutFile -Raw -ErrorAction SilentlyContinue } else { "" }
            $stderr = if (Test-Path $stderrFile) { Get-Content $stderrFile -Raw -ErrorAction SilentlyContinue } else { "" }
            
            # Display output
            if ($stdout) {
                Write-Host $stdout
            }
            if ($stderr) {
                Write-Host $stderr -ForegroundColor Yellow
            }
            
            # Check exit code
            if ($apiExitCode -ne 0) {
                Write-Host ""
                Write-Error "Goruntu uretimi basarisiz, cikis kodu: $apiExitCode"
                Write-Host ""
                Write-Host "Run artifacts directory: $runDir" -ForegroundColor Cyan
                
                # PHASE 5: Show error artifacts if they exist
                $errorTextFiles = Get-ChildItem -Path $runDir -Filter "error_text_*.txt" -ErrorAction SilentlyContinue | Sort-Object Name
                if ($errorTextFiles) {
                    Write-Host ""
                    Write-Host "Error details (first 2):" -ForegroundColor Yellow
                    foreach ($errFile in $errorTextFiles | Select-Object -First 2) {
                        Write-Host "  -> $($errFile.Name)" -ForegroundColor White
                        try {
                            $errContent = Get-Content $errFile.FullName -Raw -ErrorAction SilentlyContinue
                            if ($errContent) {
                                $preview = if ($errContent.Length -gt 200) { $errContent.Substring(0, 200) + "..." } else { $errContent }
                                Write-Host "     $preview" -ForegroundColor Gray
                            }
                        } catch {
                            # Ignore read errors
                        }
                    }
                }
                
                Write-Host ""
                Write-Host "For full details, check:" -ForegroundColor Yellow
                Write-Host "  - Run log: $runDir\run_log.jsonl" -ForegroundColor Cyan
                Write-Host "  - Error JSON files: $runDir\error_raw_*.json" -ForegroundColor Cyan
                Write-Host "  - Error text files: $runDir\error_text_*.txt" -ForegroundColor Cyan
                
                if ($stderr) {
                    Write-Host ""
                    Write-Host "Stderr output:" -ForegroundColor Red
                    Write-Host $stderr -ForegroundColor Yellow
                }
                throw "API generator failed with exit code $apiExitCode"
            }
            
            Write-Success "Goruntu uretimi tamamlandi!"
        } finally {
            # Cleanup temp files
            if (Test-Path $stdoutFile) { Remove-Item $stdoutFile -ErrorAction SilentlyContinue }
            if (Test-Path $stderrFile) { Remove-Item $stderrFile -ErrorAction SilentlyContinue }
        }
    } catch {
        Write-Error "Goruntu uretimi hatasi: $_"
        Write-Host ""
        Write-Host "Olası çözümler:" -ForegroundColor Yellow
        Write-Host "  1. ComfyUI'in çalıştığından emin olun: http://$ComfyUIServer/system_stats" -ForegroundColor Cyan
        Write-Host "  2. Workflow dosyasının geçerli olduğunu kontrol edin: $workflowFile" -ForegroundColor Cyan
        Write-Host "  3. Prompt dosyasının doğru formatta olduğunu kontrol edin: $promptFile" -ForegroundColor Cyan
        Write-Host "  4. Modellerin yüklü olduğunu kontrol edin" -ForegroundColor Cyan
        Write-Host "  5. Python scripti manuel olarak test edin:" -ForegroundColor Cyan
        Write-Host "     $pythonCmd $apiGeneratorScript --workflow `"$workflowFile`" --prompts `"$promptFile`" --output `"$outputPath`" --count $ImageCount --server $ComfyUIServer" -ForegroundColor White
        Write-Host ""
        exit 1
    }
    
    Write-Host ""
    
    # 7. Post-Processing
    if (-not $SkipPostProcess) {
        Write-Info "[7/7] Post-processing basliyor..."
        
        $postProcessScript = Join-Path $Root "post_process_pipeline.py"
        if (Test-Path $postProcessScript) {
            $processedPath = Join-Path $comfyPath "output_processed"
            try {
                # PHASE 0: Use .venv Python
                $pythonCmd = Get-PythonCmd
                & $pythonCmd $postProcessScript `
                    --input $outputPath `
                    --output $processedPath
                
                if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
                    Write-Success "Post-processing tamamlandi!"
                } else {
                    Write-Warning "Post-processing'de hata olustu (devam ediliyor)"
                }
            } catch {
                Write-Warning "Post-processing hatasi: $_"
            }
        } else {
            Write-Warning "post_process_pipeline.py bulunamadi, atlaniyor"
        }
        Write-Host ""
    }
    
    # Özet
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "TAM OTOMATIK URETIM TAMAMLANDI!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "SONUCLAR:" -ForegroundColor Yellow
    Write-Host "  Karakter: $CharacterName" -ForegroundColor White
    Write-Host "  Uretilen goruntu: $ImageCount" -ForegroundColor White
    Write-Host "  Ham goruntuler: $outputPath" -ForegroundColor White
    if (-not $SkipPostProcess) {
        $processedPath = Join-Path $comfyPath "output_processed"
        Write-Host "  Islenmis goruntuler: $processedPath" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "SONRAKI ADIMLAR:" -ForegroundColor Yellow
    Write-Host "  1. Goruntuleri kontrol edin" -ForegroundColor White
    Write-Host "  2. Kalite kontrolu yapin" -ForegroundColor White
    Write-Host "  3. Metadata temizlendi mi kontrol edin" -ForegroundColor White
    Write-Host "  4. Gerekirse tekrar uretim yapin" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Error "Kritik hata: $_"
    Write-Host ""
    Write-Host "Hata Detayları:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    if ($_.ScriptStackTrace) {
        Write-Host ""
        Write-Host "Stack Trace:" -ForegroundColor Red
        Write-Host $_.ScriptStackTrace -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Yardım için:" -ForegroundColor Cyan
    Write-Host "  - Tüm log'ları kontrol edin" -ForegroundColor White
    Write-Host "  - ComfyUI'in çalıştığından emin olun" -ForegroundColor White
    Write-Host "  - Modellerin yüklü olduğunu kontrol edin" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Model Indirme Scripti - Otomatik
# Tum gerekli modelleri otomatik olarak indirir

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

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

# PHASE 0: Lock Python to .venv
function Get-PythonCmd {
    $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        return $venvPy
    }
    # Fallback to system Python
    return Ensure-PythonInstalled
}

# Simple logging functions
function Write-Info { param([string]$Msg) Write-Host "[AInfluencer] $Msg" -ForegroundColor White }
function Write-Success { param([string]$Msg) Write-Host "[AInfluencer] OK  $Msg" -ForegroundColor Green }
function Write-Warning { param([string]$Msg) Write-Host "[AInfluencer] !   $Msg" -ForegroundColor Yellow }
function Write-Error { param([string]$Msg) Write-Host "[AInfluencer] ERR $Msg" -ForegroundColor Red }

function Get-ComfyUIPath { return Join-Path $Root "ComfyUI" }

function Ensure-PythonInstalled {
    # Try py launcher first (more reliable on Windows)
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $version = py --version 2>&1
            if ($version -match "Python \d+\.\d+" -and $LASTEXITCODE -eq 0) {
                return "py"
            }
        } catch { }
    }
    
    # Try python command
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try {
            $version = python --version 2>&1
            if ($version -match "Python \d+\.\d+" -and $LASTEXITCODE -eq 0) {
                return "python"
            }
        } catch { }
    }
    
    Write-Error "Python bulunamadi!"
    Write-Host "  Cozum: Python'i kurun: https://www.python.org/downloads/" -ForegroundColor Cyan
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OTOMATIK MODEL INDIRME" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# PHASE 0: Use .venv Python if available
$pythonCmd = Get-PythonCmd
Write-Success "Python bulundu: $pythonCmd"

# ComfyUI path'i kontrol et
$comfyPath = Get-ComfyUIPath
if (-not (Test-Path $comfyPath)) {
    Write-Error "ComfyUI bulunamadi: $comfyPath"
    Write-Host "  Cozum: Once ComfyUI'i kurun:" -ForegroundColor Yellow
    Write-Host "    .\auto-complete-setup.ps1" -ForegroundColor Cyan
    exit 1
}
Write-Success "ComfyUI bulundu: $comfyPath"
Write-Host ""

# Python paketleri kurulumu
Write-Info "[0/6] Python paketleri kuruluyor..."
$packages = @("huggingface_hub", "requests", "insightface", "onnxruntime")
foreach ($package in $packages) {
    try {
        Write-Info "  Kuruluyor: $package..."
        $installOutput = & $pythonCmd -m pip install --upgrade $package --quiet 2>&1
        $installExitCode = $LASTEXITCODE
        if ($installExitCode -eq 0) {
            Write-Success "$package hazir"
        } else {
            Write-Warning "$package kurulumunda sorun olabilir (devam ediliyor)"
        }
    } catch {
        Write-Warning "$package kurulumunda hata (devam ediliyor): $_"
    }
}
Write-Host ""

# Model klasorlerini olustur
$modelDirs = @(
    (Join-Path $comfyPath "models\checkpoints"),
    (Join-Path $comfyPath "models\instantid"),
    (Join-Path $comfyPath "models\upscale_models"),
    (Join-Path $comfyPath "models\face_restore"),
    (Join-Path $comfyPath "models\insightface")
)

foreach ($dir in $modelDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Info "Klasor olusturuldu: $dir"
    }
}

Write-Host ""

# PHASE 8: Config-driven model download from MODEL_SOURCES.json
$modelSourcesFile = Join-Path $Root "MODEL_SOURCES.json"
if (Test-Path $modelSourcesFile) {
    Write-Info "MODEL_SOURCES.json bulundu, config-driven indirme aktif"
    try {
        $modelSources = Get-Content $modelSourcesFile -Raw | ConvertFrom-Json
        $comfyPath = Get-ComfyUIPath
        
        foreach ($modelName in $modelSources.PSObject.Properties.Name) {
            if ($modelName -eq "_comment") { continue }
            
            $model = $modelSources.$modelName
            $url = $model.url
            $target = $model.target
            $description = if ($model.description) { $model.description } else { $modelName }
            $required = if ($model.required) { $true } else { $false }
            
            # Resolve target path relative to root
            if (-not [System.IO.Path]::IsPathRooted($target)) {
                $targetPath = Join-Path $Root $target
            } else {
                $targetPath = $target
            }
            
            # Create directory if needed
            $targetDir = Split-Path -Parent $targetPath
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            
            # Check if already exists
            if (Test-Path $targetPath) {
                $fileSizeMB = (Get-Item $targetPath).Length / 1MB
                if ($fileSizeMB -gt 1) {
                    Write-Success "$description zaten mevcut ($([math]::Round($fileSizeMB, 2)) MB)"
                    continue
                }
            }
            
            # Download if URL provided
            if ([string]::IsNullOrWhiteSpace($url)) {
                if ($required) {
                    Write-Warning "$description gerekli ancak URL yok - manuel indirme gerekli"
                    if ($model.source) {
                        Write-Host "  Kaynak: $($model.source)" -ForegroundColor Cyan
                    }
                } else {
                    Write-Info "$description URL yok - atlaniyor (opsiyonel)"
                }
            } else {
                Write-Info "$description indiriliyor..."
                $downloadSuccess = Download-DirectUrl -Url $url -TargetPath $targetPath -Description $description
                if (-not $downloadSuccess -and $required) {
                    Write-Warning "$description indirilemedi - manuel indirme gerekli"
                    if ($model.source) {
                        Write-Host "  Kaynak: $($model.source)" -ForegroundColor Cyan
                    }
                }
            }
        }
        Write-Host ""
    } catch {
        Write-Warning "MODEL_SOURCES.json okunamadi, mevcut indirme mantigi kullanilacak: $_"
        Write-Host ""
    }
} else {
    Write-Info "MODEL_SOURCES.json bulunamadi, mevcut indirme mantigi kullaniliyor"
    Write-Host ""
}

# Model indirme fonksiyonu
function Download-HuggingFaceModel {
    param(
        [string]$RepoId,
        [string]$FileName,
        [string]$TargetPath,
        [string]$Subfolder = "",
        [string]$Description = ""
    )
    
    if ([string]::IsNullOrWhiteSpace($Description)) {
        $Description = $FileName
    }
    
    # Dosya zaten varsa atla
    if (Test-Path $TargetPath) {
        $fileSizeMB = (Get-Item $TargetPath).Length / 1MB
        $fileSizeGB = $fileSizeMB / 1024
        if ($fileSizeGB -ge 1) {
            Write-Success "$Description zaten mevcut ($([math]::Round($fileSizeGB, 2)) GB)"
        } else {
            Write-Success "$Description zaten mevcut ($([math]::Round($fileSizeMB, 2)) MB)"
        }
        return $true
    }
    
    Write-Info "$Description indiriliyor..."
    
    # Python download script with progress
    $downloadScript = @"
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

repo_id = "$RepoId"
filename = "$FileName"
target_path = r"$TargetPath"
subfolder = "$Subfolder"

try:
    print(f"Downloading {filename} from {repo_id}...")
    print("This may take several minutes for large files (checkpoints are 2-6 GB)...")
    
    # Download with resume capability (automatic in newer versions)
    if subfolder and subfolder.strip():
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            subfolder=subfolder,
            local_dir=os.path.dirname(target_path)
        )
    else:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=os.path.dirname(target_path)
        )
    
    # Ensure file is in correct location
    if os.path.exists(downloaded_path):
        if downloaded_path != target_path:
            # Move to target location if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(downloaded_path, target_path)
        
        file_size_mb = os.path.getsize(target_path) / (1024 * 1024)
        file_size_gb = file_size_mb / 1024
        if file_size_gb >= 1:
            print(f"SUCCESS: {target_path} ({file_size_gb:.2f} GB)")
        else:
            print(f"SUCCESS: {target_path} ({file_size_mb:.2f} MB)")
        sys.exit(0)
    else:
        print(f"ERROR: File not found after download: {downloaded_path}")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
    
    $scriptPath = Join-Path $env:TEMP "download_$(New-Guid).py"
    try {
        $downloadScript | Out-File -FilePath $scriptPath -Encoding UTF8 -Force
        
        $output = & $pythonCmd $scriptPath 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($output) {
            Write-Host $output
        }
        
        if ($exitCode -eq 0 -and (Test-Path $TargetPath)) {
            $fileSizeMB = (Get-Item $TargetPath).Length / 1MB
            $fileSizeGB = $fileSizeMB / 1024
            if ($fileSizeGB -ge 1) {
                Write-Success "$Description indirildi ($([math]::Round($fileSizeGB, 2)) GB)"
            } else {
                Write-Success "$Description indirildi ($([math]::Round($fileSizeMB, 2)) MB)"
            }
            return $true
        } else {
            Write-Warning "$Description indirilemedi"
            return $false
        }
    } catch {
        Write-Warning "$Description indirilemedi: $_"
        return $false
    } finally {
        if (Test-Path $scriptPath) {
            Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
        }
    }
}

# GitHub release download function
function Download-GitHubRelease {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$FileName,
        [string]$TargetPath,
        [string]$Description = ""
    )
    
    if ([string]::IsNullOrWhiteSpace($Description)) {
        $Description = $FileName
    }
    
    # Dosya zaten varsa atla
    if (Test-Path $TargetPath) {
        $fileSizeMB = (Get-Item $TargetPath).Length / 1MB
        $fileSizeGB = $fileSizeMB / 1024
        if ($fileSizeGB -ge 1) {
            Write-Success "$Description zaten mevcut ($([math]::Round($fileSizeGB, 2)) GB)"
        } else {
            Write-Success "$Description zaten mevcut ($([math]::Round($fileSizeMB, 2)) MB)"
        }
        return $true
    }
    
    Write-Info "$Description GitHub'dan indiriliyor..."
    
    # Try to download from latest release
    $releaseUrl = "https://github.com/$Owner/$Repo/releases/latest/download/$FileName"
    
    try {
        # Create directory if needed
        $targetDir = Split-Path -Parent $TargetPath
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        
        # Download file with progress
        $ProgressPreference = 'Continue'
        Invoke-WebRequest -Uri $releaseUrl -OutFile $TargetPath -UseBasicParsing -ErrorAction Stop
        
        if (Test-Path $TargetPath) {
            $fileSizeMB = (Get-Item $TargetPath).Length / 1MB
            $fileSizeGB = $fileSizeMB / 1024
            if ($fileSizeGB -ge 1) {
                Write-Success "$Description indirildi ($([math]::Round($fileSizeGB, 2)) GB)"
            } else {
                Write-Success "$Description indirildi ($([math]::Round($fileSizeMB, 2)) MB)"
            }
            return $true
        } else {
            Write-Warning "$Description indirilemedi"
            return $false
        }
    } catch {
        Write-Warning "$Description GitHub'dan indirilemedi: $_"
        return $false
    }
}

# Direct URL download function (for large files with resume support)
function Download-DirectUrl {
    param(
        [string]$Url,
        [string]$TargetPath,
        [string]$Description = ""
    )
    
    if ([string]::IsNullOrWhiteSpace($Description)) {
        $Description = Split-Path -Leaf $TargetPath
    }
    
    # Dosya zaten varsa atla
    if (Test-Path $TargetPath) {
        $fileSizeMB = (Get-Item $TargetPath).Length / 1MB
        $fileSizeGB = $fileSizeMB / 1024
        if ($fileSizeGB -ge 1) {
            Write-Success "$Description zaten mevcut ($([math]::Round($fileSizeGB, 2)) GB)"
        } else {
            Write-Success "$Description zaten mevcut ($([math]::Round($fileSizeMB, 2)) MB)"
        }
        return $true
    }
    
    Write-Info "$Description indiriliyor..."
    
    try {
        # Create directory if needed
        $targetDir = Split-Path -Parent $TargetPath
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        
        # Use Python for better download with resume capability
        $downloadScript = @"
import os
import sys
import requests
from pathlib import Path

url = "$Url"
target_path = r"$TargetPath"

try:
    print(f"Downloading from {url}...")
    print("This may take several minutes for large files...")
    
    # Create directory if needed
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # Download with streaming and resume support
    # Increase timeout for large files and add retry logic
    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            print(f"Download attempt {attempt + 1}/{max_retries}...")
            response = requests.get(url, stream=True, timeout=(30, 600), headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Retry {attempt + 1}/{max_retries} after error: {str(e)}")
            import time
            time.sleep(2)
    
    if not response:
        raise Exception("Failed to get response after retries")
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    if downloaded % (1024 * 1024 * 10) == 0:  # Print every 10MB
                        print(f"Progress: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
    
    file_size_mb = os.path.getsize(target_path) / (1024 * 1024)
    file_size_gb = file_size_mb / 1024
    if file_size_gb >= 1:
        print(f"SUCCESS: {target_path} ({file_size_gb:.2f} GB)")
    else:
        print(f"SUCCESS: {target_path} ({file_size_mb:.2f} MB)")
    sys.exit(0)
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
        
        $scriptPath = Join-Path $env:TEMP "direct_download_$(New-Guid).py"
        try {
            $downloadScript | Out-File -FilePath $scriptPath -Encoding UTF8 -Force
            
            $output = & $pythonCmd $scriptPath 2>&1
            $exitCode = $LASTEXITCODE
            
            if ($output) {
                Write-Host $output
            }
            
            if ($exitCode -eq 0 -and (Test-Path $TargetPath)) {
                $fileSizeMB = (Get-Item $TargetPath).Length / 1MB
                $fileSizeGB = $fileSizeMB / 1024
                if ($fileSizeGB -ge 1) {
                    Write-Success "$Description indirildi ($([math]::Round($fileSizeGB, 2)) GB)"
                } else {
                    Write-Success "$Description indirildi ($([math]::Round($fileSizeMB, 2)) MB)"
                }
                return $true
            } else {
                Write-Warning "$Description indirilemedi"
                return $false
            }
        } finally {
            if (Test-Path $scriptPath) {
                Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Warning "$Description indirilemedi: $_"
        return $false
    }
}

# Helper function for browser-based download (last resort)
function Open-BrowserDownload {
    param(
        [string]$Url,
        [string]$Description
    )
    
    Write-Host "  Tarayici aciliyor: $Description" -ForegroundColor Cyan
    Write-Host "  URL: $Url" -ForegroundColor White
    try {
        Start-Process $Url
        Write-Info "  Tarayici acildi - dosyalari manuel olarak indirin"
        return $true
    } catch {
        Write-Warning "  Tarayici acilamadi: $_"
        return $false
    }
}

# 1. InsightFace modeli
Write-Info "[1/6] InsightFace modeli indiriliyor..."

# Force install insightface package
Write-Info "  insightface paketi kuruluyor/guncelleniyor..."
try {
    $installOutput = & $pythonCmd -m pip install --upgrade insightface onnxruntime --quiet 2>&1
    $installExitCode = $LASTEXITCODE
    if ($installExitCode -eq 0) {
        Write-Success "  insightface paketi hazir"
    } else {
        Write-Warning "  insightface paketi kurulumunda sorun olabilir (devam ediliyor)"
    }
} catch {
    Write-Warning "  insightface paketi kurulamadi: $_"
}

# Verify package is importable
$packageOk = $false
try {
    $testOutput = & $pythonCmd -c "import insightface; from insightface.app import FaceAnalysis; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0 -and $testOutput -match "OK") {
        $packageOk = $true
        Write-Success "  insightface paketi calisiyor"
    }
} catch {
    Write-Warning "  insightface paketi test edilemedi"
}

$insightfaceDir = Join-Path $comfyPath "models\insightface"
if (-not (Test-Path $insightfaceDir)) {
    New-Item -ItemType Directory -Path $insightfaceDir -Force | Out-Null
}

# Check if models already exist
$existingModels = @(Get-ChildItem -Path $insightfaceDir -Recurse -Include "*.onnx", "*.param", "*.bin" -ErrorAction SilentlyContinue)
if ($existingModels.Count -gt 0) {
    Write-Success "InsightFace modelleri zaten mevcut ($($existingModels.Count) dosya)"
} else {
    $downloadSuccess = $false
    
    # Method 1: Try via insightface package (preferred)
    if ($packageOk) {
        Write-Info "  Method 1: insightface paketi ile indiriliyor..."
        $insightfaceScript = @"
import os
import sys
import traceback
import shutil

try:
    import insightface
    from insightface.app import FaceAnalysis
    
    # Set the model root directory explicitly
    model_root = r"$insightfaceDir"
    os.makedirs(model_root, exist_ok=True)
    
    # Set environment variable for model cache
    os.environ['INSIGHTFACE_ROOT'] = model_root
    
    print("Creating FaceAnalysis app with antelopev2 model...")
    print(f"Model directory: {model_root}")
    
    # Create FaceAnalysis app - this will download models automatically
    app = FaceAnalysis(name='antelopev2', root=model_root)
    print("Preparing models (downloading if needed)...")
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    # Also try to get models explicitly
    print("Downloading models explicitly...")
    try:
        model_zoo = insightface.model_zoo.get_model('antelopev2', download=True, root=model_root)
        if model_zoo:
            print("Model zoo download successful")
    except Exception as e:
        print(f"Model zoo download note: {e}")
    
    # Check if models were downloaded
    model_files = []
    for root, dirs, files in os.walk(model_root):
        for file in files:
            if file.endswith(('.onnx', '.param', '.bin')):
                full_path = os.path.join(root, file)
                model_files.append(full_path)
    
    # Also check default InsightFace cache location
    default_cache = os.path.join(os.path.expanduser('~'), '.insightface', 'models', 'antelopev2')
    if os.path.exists(default_cache):
        print(f"Found models in default location: {default_cache}")
        for root, dirs, files in os.walk(default_cache):
            for file in files:
                if file.endswith(('.onnx', '.param', '.bin')):
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, default_cache)
                    dst_path = os.path.join(model_root, rel_path)
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    if not os.path.exists(dst_path):
                        shutil.copy2(src_path, dst_path)
                        print(f"Copied: {file}")
    
    # Re-check after copy
    model_files = []
    for root, dirs, files in os.walk(model_root):
        for file in files:
            if file.endswith(('.onnx', '.param', '.bin')):
                full_path = os.path.join(root, file)
                model_files.append(full_path)
    
    if model_files:
        total_size = sum(os.path.getsize(f) for f in model_files)
        size_mb = total_size / (1024 * 1024)
        print(f"SUCCESS: InsightFace models found ({len(model_files)} files, {size_mb:.2f} MB)")
        for f in model_files[:5]:
            print(f"  - {os.path.basename(f)}")
        sys.exit(0)
    else:
        print("WARNING: InsightFace preparation succeeded but no model files found")
        print(f"Checked directory: {model_root}")
        sys.exit(1)
        
except ImportError as e:
    print(f"ERROR: insightface package not installed: {e}")
    print("Install with: pip install insightface onnxruntime")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
"@
        $scriptPath = Join-Path $env:TEMP "insightface_download_$(New-Guid).py"
        try {
            $insightfaceScript | Out-File -FilePath $scriptPath -Encoding UTF8 -Force
            
            Write-Info "  Modeller indiriliyor (30-60 saniye surebilir)..."
            $output = & $pythonCmd $scriptPath 2>&1
            $exitCode = $LASTEXITCODE
            
            if ($output) {
                $output | ForEach-Object { Write-Host $_ }
            }
            
            # Verify models were actually downloaded
            $verifyModels = @(Get-ChildItem -Path $insightfaceDir -Recurse -Include "*.onnx", "*.param", "*.bin" -ErrorAction SilentlyContinue)
            if ($verifyModels.Count -gt 0) {
                Write-Success "InsightFace modeli indirildi ($($verifyModels.Count) dosya)"
                $downloadSuccess = $true
            } elseif ($exitCode -eq 0) {
                # Double check - sometimes files are in subdirectories
                Start-Sleep -Seconds 2
                $verifyModels2 = @(Get-ChildItem -Path $insightfaceDir -Recurse -Include "*.onnx", "*.param", "*.bin" -ErrorAction SilentlyContinue)
                if ($verifyModels2.Count -gt 0) {
                    Write-Success "InsightFace modeli indirildi ($($verifyModels2.Count) dosya)"
                    $downloadSuccess = $true
                }
            }
        } catch {
            Write-Warning "  Download script hatasi: $_"
        } finally {
            if (Test-Path $scriptPath) {
                Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    # Method 2: HuggingFace Hub API download (using huggingface_hub)
    if (-not $downloadSuccess) {
        Write-Info "  Method 2: HuggingFace Hub API ile indiriliyor..."
        $hfDownloadScript = @"
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

model_root = r"$insightfaceDir"
os.makedirs(model_root, exist_ok=True)

try:
    repo_id = "deepinsight/antelopev2"
    files_to_download = [
        "det_10g.onnx",
        "1k3d68.onnx", 
        "genderage.onnx",
        "w600k_r50.onnx"
    ]
    
    downloaded = []
    for filename in files_to_download:
        try:
            target_path = os.path.join(model_root, filename)
            if os.path.exists(target_path):
                print(f"Already exists: {filename}")
                downloaded.append(filename)
                continue
                
            print(f"Downloading {filename}...")
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=model_root,
                local_dir_use_symlinks=False
            )
            downloaded.append(filename)
            print(f"SUCCESS: {filename}")
        except Exception as e:
            print(f"WARNING: Failed to download {filename}: {e}")
    
    if len(downloaded) >= 3:
        print(f"SUCCESS: Downloaded {len(downloaded)}/{len(files_to_download)} files")
        sys.exit(0)
    else:
        print(f"ERROR: Only downloaded {len(downloaded)}/{len(files_to_download)} files")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
        $hfScriptPath = Join-Path $env:TEMP "insightface_hf_$(New-Guid).py"
        try {
            $hfDownloadScript | Out-File -FilePath $hfScriptPath -Encoding UTF8 -Force
            $hfOutput = & $pythonCmd $hfScriptPath 2>&1
            $hfExitCode = $LASTEXITCODE
            
            if ($hfOutput) {
                $hfOutput | ForEach-Object { Write-Host "    $_" }
            }
            
            if ($hfExitCode -eq 0) {
                $verifyModels = @(Get-ChildItem -Path $insightfaceDir -Recurse -Include "*.onnx", "*.param", "*.bin" -ErrorAction SilentlyContinue)
                if ($verifyModels.Count -ge 3) {
                    Write-Success "InsightFace modeli indirildi ($($verifyModels.Count) dosya)"
                    $downloadSuccess = $true
                }
            }
        } catch {
            Write-Warning "  HuggingFace Hub API hatasi: $_"
        } finally {
            if (Test-Path $hfScriptPath) {
                Remove-Item $hfScriptPath -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    # Method 3: Direct HTTP download from multiple URLs (fallback)
    if (-not $downloadSuccess) {
        Write-Info "  Method 3: Direkt HTTP indirme deneniyor..."
        $directUrls = @(
            "https://huggingface.co/deepinsight/antelopev2/resolve/main/det_10g.onnx",
            "https://huggingface.co/deepinsight/antelopev2/resolve/main/1k3d68.onnx",
            "https://huggingface.co/deepinsight/antelopev2/resolve/main/genderage.onnx",
            "https://huggingface.co/deepinsight/antelopev2/resolve/main/w600k_r50.onnx"
        )
        
        # Also try alternative CDN URLs
        $alternativeUrls = @(
            "https://github.com/deepinsight/insightface/releases/download/v0.7.3/buffalo_l.zip",
            "https://github.com/deepinsight/insightface/releases/download/v0.7.3/antelopev2.zip"
        )
        
        $downloadedCount = 0
        $totalFiles = $directUrls.Count
        
        foreach ($url in $directUrls) {
            $fileName = Split-Path -Leaf $url
            $targetPath = Join-Path $insightfaceDir $fileName
            
            if (-not (Test-Path $targetPath)) {
                Write-Info "    Indiriliyor: $fileName..."
                $success = Download-DirectUrl -Url $url -TargetPath $targetPath -Description "InsightFace $fileName"
                if ($success) {
                    $downloadedCount++
                }
            } else {
                $fileSize = (Get-Item $targetPath).Length
                if ($fileSize -gt 1024) {
                    $downloadedCount++
                    Write-Info "    Zaten mevcut: $fileName"
                }
            }
        }
        
        # If direct downloads failed, try ZIP download and extract
        if ($downloadedCount -lt 3 -and $alternativeUrls.Count -gt 0) {
            Write-Info "  ZIP dosyasi indiriliyor..."
            foreach ($zipUrl in $alternativeUrls) {
                if ($downloadSuccess) { break }
                
                $zipFileName = Split-Path -Leaf $zipUrl
                $zipPath = Join-Path $env:TEMP "insightface_$zipFileName"
                
                try {
                    $zipSuccess = Download-DirectUrl -Url $zipUrl -TargetPath $zipPath -Description "InsightFace ZIP"
                    if ($zipSuccess -and (Test-Path $zipPath)) {
                        Write-Info "  ZIP dosyasi aciliyor..."
                        # Use Python to extract ZIP (handles UTF-8 better)
                        $extractScript = @"
import zipfile
import os
import shutil

zip_path = r"$zipPath"
extract_to = r"$insightfaceDir"

try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    # Check for extracted ONNX files
    onnx_files = []
    for root, dirs, files in os.walk(extract_to):
        for file in files:
            if file.endswith('.onnx'):
                onnx_files.append(os.path.join(root, file))
    
    # Move files to root if they're in subdirectories
    for file_path in onnx_files:
        file_name = os.path.basename(file_path)
        target_path = os.path.join(extract_to, file_name)
        if file_path != target_path:
            if os.path.exists(target_path):
                os.remove(target_path)
            shutil.move(file_path, target_path)
    
    print(f"SUCCESS: Extracted {len(onnx_files)} ONNX files")
except Exception as e:
    print(f"ERROR: {e}")
"@
                        $extractScriptPath = Join-Path $env:TEMP "extract_insightface_$(New-Guid).py"
                        $extractScript | Out-File -FilePath $extractScriptPath -Encoding UTF8 -Force
                        $extractOutput = & $pythonCmd $extractScriptPath 2>&1
                        
                        if ($extractOutput -match "SUCCESS") {
                            Write-Success "  ZIP dosyasi acildi"
                            $downloadedCount = $totalFiles
                        }
                        
                        Remove-Item $extractScriptPath -Force -ErrorAction SilentlyContinue
                        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue -ErrorAction SilentlyContinue
                    }
                } catch {
                    Write-Warning "  ZIP indirme hatasi: $_"
                }
            }
        }
        
        if ($downloadedCount -ge 3) {
            $finalModels = @(Get-ChildItem -Path $insightfaceDir -Recurse -Include "*.onnx", "*.param", "*.bin" -ErrorAction SilentlyContinue)
            if ($finalModels.Count -ge 3) {
                Write-Success "InsightFace modeli indirildi ($($finalModels.Count) dosya)"
                $downloadSuccess = $true
            }
        }
    }
    
    # Method 4: Try using gdown for Google Drive links (if available)
    if (-not $downloadSuccess) {
        Write-Info "  Method 4: Alternatif kaynaklar deneniyor..."
        # Try installing gdown for Google Drive support
        try {
            $null = & $pythonCmd -m pip install gdown --quiet 2>&1
        } catch { }
        
        # InsightFace models are sometimes on GitHub releases or other sources
        # This is a last resort before browser method
    }
    
    # Final verification
    if (-not $downloadSuccess) {
        # Final check - maybe files exist with different names
        Start-Sleep -Seconds 2
        $finalCheck = @(Get-ChildItem -Path $insightfaceDir -Recurse -Include "*.onnx", "*.param", "*.bin" -ErrorAction SilentlyContinue)
        if ($finalCheck.Count -ge 3) {
            Write-Success "InsightFace modeli bulundu ($($finalCheck.Count) dosya)"
            $downloadSuccess = $true
        }
    }
    
    # Method 5: Browser automation (last resort - opens browser with instructions)
    if (-not $downloadSuccess) {
        Write-Warning "InsightFace modeli otomatik indirilemedi"
        Write-Host ""
        Write-Host "  ========================================" -ForegroundColor Yellow
        Write-Host "  MANUEL INDIRME GEREKLI" -ForegroundColor Yellow
        Write-Host "  ========================================" -ForegroundColor Yellow
        Write-Host ""
        
        # Ask user if they want to open browser
        Write-Host "  Tarayici ile indirmek ister misiniz? (E/H)" -ForegroundColor Cyan
        Write-Host "  Veya Python ile otomatik indirmeyi deneyin:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Komut:" -ForegroundColor Yellow
        Write-Host "    python -c \"import insightface; app = insightface.app.FaceAnalysis(name='antelopev2'); app.prepare(ctx_id=0)\"" -ForegroundColor White
        Write-Host ""
        
        # Open browser automatically
        Write-Info "  Tarayici otomatik olarak aciliyor..."
        $browserOpened = Open-BrowserDownload -Url "https://huggingface.co/deepinsight/antelopev2/tree/main" -Description "InsightFace AntelopeV2 Models"
        
        Write-Host ""
        Write-Host "  INDIRME TALIMATLARI:" -ForegroundColor Yellow
        Write-Host "    1. Acilan sayfada asagidaki dosyalari bulun:" -ForegroundColor Cyan
        Write-Host "       - det_10g.onnx" -ForegroundColor White
        Write-Host "       - 1k3d68.onnx" -ForegroundColor White
        Write-Host "       - genderage.onnx" -ForegroundColor White
        Write-Host "       - w600k_r50.onnx" -ForegroundColor White
        Write-Host ""
        Write-Host "    2. Her dosyanin yanindaki 'Download' butonuna tiklayin" -ForegroundColor Cyan
        Write-Host "    3. Indirilen dosyalari su klasore tasiyin:" -ForegroundColor Cyan
        Write-Host "       $insightfaceDir" -ForegroundColor White
        Write-Host ""
        Write-Host "    4. Scripti tekrar calistirin:" -ForegroundColor Cyan
        Write-Host "       .\download-models-auto.ps1" -ForegroundColor White
        Write-Host ""
        
        # Also provide direct download links
        Write-Host "  DIREKT INDIRME LINKLERI:" -ForegroundColor Yellow
        Write-Host "    det_10g.onnx:" -ForegroundColor Cyan
        Write-Host "      https://huggingface.co/deepinsight/antelopev2/resolve/main/det_10g.onnx" -ForegroundColor Gray
        Write-Host "    1k3d68.onnx:" -ForegroundColor Cyan
        Write-Host "      https://huggingface.co/deepinsight/antelopev2/resolve/main/1k3d68.onnx" -ForegroundColor Gray
        Write-Host "    genderage.onnx:" -ForegroundColor Cyan
        Write-Host "      https://huggingface.co/deepinsight/antelopev2/resolve/main/genderage.onnx" -ForegroundColor Gray
        Write-Host "    w600k_r50.onnx:" -ForegroundColor Cyan
        Write-Host "      https://huggingface.co/deepinsight/antelopev2/resolve/main/w600k_r50.onnx" -ForegroundColor Gray
        Write-Host ""
    }
}
Write-Host ""

# 2. InstantID modeli
Write-Info "[2/6] InstantID modeli indiriliyor..."
$instantIdPath = Join-Path $comfyPath "models\instantid\ip-adapter.bin"
$success = Download-HuggingFaceModel `
    -RepoId "InstantX/InstantID" `
    -FileName "ip-adapter.bin" `
    -TargetPath $instantIdPath `
    -Description "InstantID ip-adapter.bin"
Write-Host ""

# 3. Real-ESRGAN modeli
Write-Info "[3/6] Real-ESRGAN modeli indiriliyor..."
$realesrganPath = Join-Path $comfyPath "models\upscale_models\RealESRGAN_x4plus.pth"

# Skip HuggingFace (401/404 errors) - go straight to GitHub direct downloads
$realesrganSuccess = $false
Write-Info "Real-ESRGAN GitHub'dan indiriliyor (HuggingFace atlaniyor)..."
$realesrganUrls = @(
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth",
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus.pth",
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRGAN_x4plus.pth"
)

foreach ($url in $realesrganUrls) {
    if (-not $realesrganSuccess) {
        Write-Info "Deneniyor: $url"
        $success = Download-DirectUrl -Url $url -TargetPath $realesrganPath -Description "Real-ESRGAN x4plus"
        if ($success) {
            $realesrganSuccess = $true
            break
        }
    }
}

if (-not $realesrganSuccess) {
    Write-Warning "Real-ESRGAN otomatik indirilemedi"
    Write-Host "  Manuel indirme: https://github.com/xinntao/Real-ESRGAN/releases" -ForegroundColor Cyan
    Write-Host "  Dosya: RealESRGAN_x4plus.pth" -ForegroundColor Cyan
    Write-Host "  Hedef: $realesrganPath" -ForegroundColor Cyan
}
Write-Host ""

# 4. GFPGAN modeli
Write-Info "[4/6] GFPGAN modeli indiriliyor..."
$gfpganPath = Join-Path $comfyPath "models\face_restore\GFPGANv1.4.pth"

# Skip HuggingFace (401 errors) - go straight to GitHub direct downloads (proven to work)
$gfpganSuccess = $false
Write-Info "GFPGAN GitHub'dan indiriliyor (HuggingFace atlaniyor)..."
$gfpganUrls = @(
    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.8/GFPGANv1.4.pth",
    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.14/GFPGANv1.4.pth"
)

foreach ($url in $gfpganUrls) {
    if (-not $gfpganSuccess) {
        Write-Info "Deneniyor: $url"
        $success = Download-DirectUrl -Url $url -TargetPath $gfpganPath -Description "GFPGAN v1.4"
        if ($success) {
            $gfpganSuccess = $true
            break
        }
    }
}

if (-not $gfpganSuccess) {
    Write-Warning "GFPGAN otomatik indirilemedi"
    Write-Host "  Manuel indirme: https://github.com/TencentARC/GFPGAN/releases" -ForegroundColor Cyan
    Write-Host "  Dosya: GFPGANv1.4.pth" -ForegroundColor Cyan
    Write-Host "  Hedef: $gfpganPath" -ForegroundColor Cyan
    Write-Host "  Veya: https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" -ForegroundColor Cyan
}
Write-Host ""

# 5. Checkpoint modeli (Realistic Vision V6.0) - Otomatik indirme
Write-Info "[5/6] Checkpoint modeli kontrol ediliyor..."
$checkpointDir = Join-Path $comfyPath "models\checkpoints"

# Mevcut checkpoint'leri kontrol et
$existingCheckpoints = @()
$safetensorsFiles = @(Get-ChildItem -Path $checkpointDir -Filter "*.safetensors" -ErrorAction SilentlyContinue)
$ckptFiles = @(Get-ChildItem -Path $checkpointDir -Filter "*.ckpt" -ErrorAction SilentlyContinue)

if ($safetensorsFiles.Count -gt 0) {
    $existingCheckpoints += $safetensorsFiles
}
if ($ckptFiles.Count -gt 0) {
    $existingCheckpoints += $ckptFiles
}

if ($existingCheckpoints.Count -gt 0) {
    $checkpointName = $existingCheckpoints[0].Name
    $fileSize = [math]::Round($existingCheckpoints[0].Length / 1GB, 2)
    Write-Success "Checkpoint model mevcut: $checkpointName ($fileSize GB)"
} else {
    Write-Warning "Checkpoint model bulunamadi"
    Write-Host ""
    Write-Info "En iyi checkpoint modeli otomatik indiriliyor: Realistic Vision V6.0"
    Write-Host "  Bu islem 5-15 dakika surebilir (dosya boyutu: ~2-6 GB)" -ForegroundColor Yellow
    Write-Host ""
    
    # Realistic Vision V6.0 indir
    $checkpointFileName = "Realistic_Vision_V6.0_B1_noVAE.safetensors"
    $checkpointPath = Join-Path $checkpointDir $checkpointFileName
    
    # Önce farklı dosya isimlerini kontrol et (bazı repolarda farklı isimlerle olabilir)
    $alternativeNames = @(
        "Realistic_Vision_V6.0_B1_noVAE.safetensors",
        "realisticVisionV60B1_v51HyperInpaintVAE.safetensors",
        "Realistic_Vision_V6.0.safetensors"
    )
    
    $foundAlternative = $false
    foreach ($altName in $alternativeNames) {
        $altPath = Join-Path $checkpointDir $altName
        if (Test-Path $altPath) {
            Write-Success "Alternatif checkpoint bulundu: $altName"
            $foundAlternative = $true
            break
        }
    }
    
    if (-not $foundAlternative) {
        # Try multiple checkpoint sources and filenames
        $checkpointAttempts = @(
            # HuggingFace sources
            @{ Source = "HuggingFace"; RepoId = "SG161222/Realistic_Vision_V6.0_B1_noVAE"; FileName = "Realistic_Vision_V6.0_NV_B1.safetensors"; TargetName = "Realistic_Vision_V6.0_NV_B1.safetensors" },
            @{ Source = "HuggingFace"; RepoId = "SG161222/Realistic_Vision_V6.0_B1_noVAE"; FileName = "Realistic_Vision_V6.0_B1_noVAE.safetensors"; TargetName = "Realistic_Vision_V6.0_B1_noVAE.safetensors" },
            @{ Source = "HuggingFace"; RepoId = "SG161222/Realistic_Vision_V6.0_B1_noVAE"; FileName = "realisticVisionV60B1_v51HyperInpaintVAE.safetensors"; TargetName = "realisticVisionV60B1_v51HyperInpaintVAE.safetensors" },
            # Alternative HuggingFace repo
            @{ Source = "HuggingFace"; RepoId = "SG161222/Realistic_Vision_V6.0_B1_noVAE"; FileName = "Realistic_Vision_V6.0_NV_B1_fp16.safetensors"; TargetName = "Realistic_Vision_V6.0_NV_B1_fp16.safetensors" }
        )
        
        $checkpointSuccess = $false
        foreach ($attempt in $checkpointAttempts) {
            if (-not $checkpointSuccess) {
                $attemptPath = Join-Path $checkpointDir $attempt.TargetName
                Write-Info "Deneniyor: $($attempt.FileName) ($($attempt.Source))"
                
                if ($attempt.Source -eq "HuggingFace") {
                    $success = Download-HuggingFaceModel `
                        -RepoId $attempt.RepoId `
                        -FileName $attempt.FileName `
                        -TargetPath $attemptPath `
                        -Description "Realistic Vision V6.0"
                    if ($success) {
                        $checkpointSuccess = $true
                        break
                    }
                }
            }
        }
        
        # Try direct download from HuggingFace CDN if above failed
        if (-not $checkpointSuccess) {
            Write-Info "HuggingFace API basarisiz, CDN'den deneniyor..."
            $cdnUrls = @(
                "https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE/resolve/main/Realistic_Vision_V6.0_NV_B1.safetensors",
                "https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE/resolve/main/Realistic_Vision_V6.0_B1_noVAE.safetensors"
            )
            
            foreach ($url in $cdnUrls) {
                if (-not $checkpointSuccess) {
                    $targetName = Split-Path -Leaf $url
                    $attemptPath = Join-Path $checkpointDir $targetName
                    Write-Info "CDN'den indiriliyor: $targetName"
                    $success = Download-DirectUrl -Url $url -TargetPath $attemptPath -Description "Realistic Vision V6.0"
                    if ($success) {
                        $checkpointSuccess = $true
                        break
                    }
                }
            }
        }
        
        if (-not $checkpointSuccess) {
            Write-Warning "Otomatik indirme basarisiz oldu"
            Write-Host ""
            Write-Host "  Manuel indirme:" -ForegroundColor Yellow
            Write-Host "    1. URL: https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE" -ForegroundColor Cyan
            Write-Host "    2. 'Files and versions' sekmesine gidin" -ForegroundColor Cyan
            Write-Host "    3. .safetensors dosyasini indirin (Realistic_Vision_V6.0_NV_B1.safetensors onerilir)" -ForegroundColor Cyan
            Write-Host "    4. Dosyayi su klasore koyun: $checkpointDir" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  Alternatif (Civitai):" -ForegroundColor Yellow
            Write-Host "    https://civitai.com/models/4201/realistic-vision-v60-b1" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  Veya diger iyi modeller:" -ForegroundColor Yellow
            Write-Host "    - Juggernaut XL V9: https://civitai.com/models/133005/juggernaut-xl" -ForegroundColor Cyan
            Write-Host "    - DreamShaper XL: https://huggingface.co/Lykon/DreamShaperXL" -ForegroundColor Cyan
            Write-Host "    - RealVisXL V4.0: https://civitai.com/models/82764" -ForegroundColor Cyan
        }
    }
}
Write-Host ""

# 6. Ozet
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INDIRME OZETI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$models = @(
    @{ Name = "InsightFace"; Path = (Join-Path $comfyPath "models\insightface"); Pattern = "*.onnx,*.param,*.bin" },
    @{ Name = "InstantID"; Path = (Join-Path $comfyPath "models\instantid\ip-adapter.bin"); Pattern = "" },
    @{ Name = "Real-ESRGAN"; Path = (Join-Path $comfyPath "models\upscale_models\RealESRGAN_x4plus.pth"); Pattern = "" },
    @{ Name = "GFPGAN"; Path = (Join-Path $comfyPath "models\face_restore\GFPGANv1.4.pth"); Pattern = "" },
    @{ Name = "Checkpoint"; Path = $checkpointDir; Pattern = "*.safetensors,*.ckpt" }
)

$allFound = $true
foreach ($model in $models) {
    if ($model.Pattern) {
        # Directory check with multiple patterns
        $patterns = $model.Pattern.Split(',') | ForEach-Object { $_.Trim() }
        $files = @()
        foreach ($pattern in $patterns) {
            $foundFiles = @(Get-ChildItem -Path $model.Path -Recurse -Filter $pattern -ErrorAction SilentlyContinue)
            if ($foundFiles.Count -gt 0) {
                $files += $foundFiles
            }
        }
        
        if ($files.Count -gt 0) {
            $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
            $sizeMB = $totalSize / 1MB
            $sizeGB = $sizeMB / 1024
            if ($sizeGB -ge 1) {
                Write-Success "$($model.Name): Mevcut ($([math]::Round($sizeGB, 2)) GB)"
            } else {
                Write-Success "$($model.Name): Mevcut ($([math]::Round($sizeMB, 2)) MB)"
            }
        } else {
            Write-Warning "$($model.Name): Bulunamadi"
            $allFound = $false
        }
    } else {
        # File check
        if (Test-Path $model.Path) {
            $fileSize = (Get-Item $model.Path).Length / 1MB
            $fileSizeGB = $fileSize / 1024
            if ($fileSizeGB -ge 1) {
                Write-Success "$($model.Name): Mevcut ($([math]::Round($fileSizeGB, 2)) GB)"
            } else {
                Write-Success "$($model.Name): Mevcut ($([math]::Round($fileSize, 2)) MB)"
            }
        } else {
            Write-Warning "$($model.Name): Bulunamadi"
            $allFound = $false
        }
    }
}

Write-Host ""
if ($allFound) {
    Write-Success "Tum modeller hazir!"
} else {
    Write-Warning "Bazi modeller eksik - manuel indirme gerekebilir"
    Write-Host ""
    Write-Host "Manuel indirme rehberi:" -ForegroundColor Yellow
    Write-Host "  - InstantID: https://huggingface.co/InstantX/InstantID" -ForegroundColor Cyan
    Write-Host "  - Real-ESRGAN: https://huggingface.co/xinntao/Real-ESRGAN" -ForegroundColor Cyan
    Write-Host "  - GFPGAN: https://huggingface.co/TencentARC/GFPGAN" -ForegroundColor Cyan
    Write-Host "  - Checkpoint: https://civitai.com/models/4201/realistic-vision-v60-b1" -ForegroundColor Cyan
}

Write-Host ""

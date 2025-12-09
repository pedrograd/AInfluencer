# =========================================
# Auto-Fixed Model Download Script
# Simplified and robust version
# =========================================

$ErrorActionPreference = "Continue"
Set-StrictMode -Off  # More forgiving for compatibility

# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Get script directory
$Root = $PSScriptRoot
if (-not $Root) {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if (-not $Root) {
    $Root = Get-Location
}

Set-Location $Root

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MODEL DOWNLOAD SYSTEM - AUTO FIXED" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find Python
$pythonCmd = $null
$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    $pythonCmd = $venvPy
    Write-Host "[OK] Using venv Python: $pythonCmd" -ForegroundColor Green
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
    Write-Host "[OK] Using py launcher" -ForegroundColor Green
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    Write-Host "[OK] Using system Python" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Please install Python or activate your virtual environment" -ForegroundColor Yellow
    exit 1
}

# Check ComfyUI
$comfyPath = Join-Path $Root "ComfyUI"
if (-not (Test-Path $comfyPath)) {
    Write-Host "[ERROR] ComfyUI not found: $comfyPath" -ForegroundColor Red
    Write-Host "Please run auto-complete-setup.ps1 first" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] ComfyUI found: $comfyPath" -ForegroundColor Green
Write-Host ""

# Install required packages
Write-Host "[1/5] Installing Python packages..." -ForegroundColor Cyan
$packages = @("huggingface_hub", "requests", "tqdm")
foreach ($package in $packages) {
    try {
        & $pythonCmd -m pip install --upgrade $package --quiet 2>&1 | Out-Null
        Write-Host "  [OK] $package" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] $package - continuing anyway" -ForegroundColor Yellow
    }
}
Write-Host ""

# Create directories
Write-Host "[2/5] Creating model directories..." -ForegroundColor Cyan
$modelDirs = @(
    "ComfyUI\models\checkpoints",
    "ComfyUI\models\controlnet",
    "ComfyUI\models\upscale_models",
    "ComfyUI\models\face_restore",
    "ComfyUI\models\ipadapter",
    "ComfyUI\models\instantid",
    "ComfyUI\models\insightface",
    "ComfyUI\models\animatediff"
)

foreach ($dir in $modelDirs) {
    $fullPath = Join-Path $Root $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  [OK] Created: $dir" -ForegroundColor Green
    }
}
Write-Host ""

# Download function
function Download-Model {
    param(
        [string]$Url,
        [string]$TargetPath,
        [string]$Description
    )
    
    if ([string]::IsNullOrWhiteSpace($Description)) {
        $Description = Split-Path -Leaf $TargetPath
    }
    
    # Check if already exists
    if (Test-Path $TargetPath) {
        $size = (Get-Item $TargetPath).Length / 1MB
        if ($size -gt 1) {
            Write-Host "  [OK] $Description already exists ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
            return $true
        }
    }
    
    Write-Host "  [INFO] Downloading $Description..." -ForegroundColor Cyan
    
    # Create directory
    $targetDir = Split-Path -Parent $TargetPath
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    # Use Python for download with progress
    $downloadScript = @"
import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

url = "$Url"
target_path = r"$TargetPath"

try:
    print(f"Downloading from {url}...")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    response = requests.get(url, stream=True, timeout=(30, 600), headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(target_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0 and downloaded % (1024 * 1024 * 10) == 0:
                    percent = (downloaded / total_size) * 100
                    print(f"Progress: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
    
    file_size_mb = os.path.getsize(target_path) / (1024 * 1024)
    print(f"SUCCESS: {target_path} ({file_size_mb:.2f} MB)")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
"@
    
    $scriptPath = Join-Path $env:TEMP "download_$(New-Guid).py"
    try {
        $downloadScript | Out-File -FilePath $scriptPath -Encoding UTF8 -Force
        $output = & $pythonCmd $scriptPath 2>&1
        
        if ($LASTEXITCODE -eq 0 -and (Test-Path $TargetPath)) {
            $size = (Get-Item $TargetPath).Length / 1MB
            Write-Host "  [OK] $Description downloaded ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
            return $true
        } else {
            Write-Host $output
            Write-Host "  [WARN] $Description download failed" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "  [ERROR] $Description download error: $_" -ForegroundColor Red
        return $false
    } finally {
        if (Test-Path $scriptPath) {
            Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
        }
    }
}

# Download HuggingFace model
function Download-HFModel {
    param(
        [string]$RepoId,
        [string]$FileName,
        [string]$TargetPath,
        [string]$Description
    )
    
    if ([string]::IsNullOrWhiteSpace($Description)) {
        $Description = $FileName
    }
    
    if (Test-Path $TargetPath) {
        $size = (Get-Item $TargetPath).Length / 1MB
        Write-Host "  [OK] $Description already exists ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
        return $true
    }
    
    Write-Host "  [INFO] Downloading $Description from HuggingFace..." -ForegroundColor Cyan
    
    $downloadScript = @"
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

repo_id = "$RepoId"
filename = "$FileName"
target_path = r"$TargetPath"

try:
    print(f"Downloading {filename} from {repo_id}...")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=os.path.dirname(target_path),
        local_dir_use_symlinks=False
    )
    
    if os.path.exists(downloaded_path):
        if downloaded_path != target_path:
            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(downloaded_path, target_path)
        
        file_size_mb = os.path.getsize(target_path) / (1024 * 1024)
        print(f"SUCCESS: {target_path} ({file_size_mb:.2f} MB)")
        sys.exit(0)
    else:
        print("ERROR: File not found after download")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
"@
    
    $scriptPath = Join-Path $env:TEMP "hf_download_$(New-Guid).py"
    try {
        $downloadScript | Out-File -FilePath $scriptPath -Encoding UTF8 -Force
        $output = & $pythonCmd $scriptPath 2>&1
        
        if ($LASTEXITCODE -eq 0 -and (Test-Path $TargetPath)) {
            $size = (Get-Item $TargetPath).Length / 1MB
            Write-Host "  [OK] $Description downloaded ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
            return $true
        } else {
            Write-Host $output
            Write-Host "  [WARN] $Description download failed" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "  [ERROR] $Description download error: $_" -ForegroundColor Red
        return $false
    } finally {
        if (Test-Path $scriptPath) {
            Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
        }
    }
}

# Start downloading essential models
Write-Host "[3/5] Downloading essential models..." -ForegroundColor Cyan
Write-Host ""

# Realistic Vision V6.0 (Essential)
$realisticPath = Join-Path $Root "ComfyUI\models\checkpoints\Realistic_Vision_V6.0.safetensors"
Download-HFModel -RepoId "SG161222/Realistic_Vision_V6.0_B1_noVAE" -FileName "Realistic_Vision_V6.0_NV_B1.safetensors" -TargetPath $realisticPath -Description "Realistic Vision V6.0"

# InstantID
$instantIdPath = Join-Path $Root "ComfyUI\models\instantid\ip-adapter.bin"
Download-HFModel -RepoId "InstantX/InstantID" -FileName "ip-adapter.bin" -TargetPath $instantIdPath -Description "InstantID"

# Real-ESRGAN
$realesrganPath = Join-Path $Root "ComfyUI\models\upscale_models\RealESRGAN_x4plus.pth"
Download-Model -Url "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth" -TargetPath $realesrganPath -Description "Real-ESRGAN x4plus"

# GFPGAN
$gfpganPath = Join-Path $Root "ComfyUI\models\face_restore\GFPGANv1.4.pth"
Download-Model -Url "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" -TargetPath $gfpganPath -Description "GFPGAN v1.4"

Write-Host ""

# InsightFace setup
Write-Host "[4/5] Setting up InsightFace..." -ForegroundColor Cyan
$insightfaceDir = Join-Path $Root "ComfyUI\models\insightface"
try {
    & $pythonCmd -m pip install insightface onnxruntime --quiet 2>&1 | Out-Null
    $insightfaceScript = @"
import os
import sys
import insightface
from insightface.app import FaceAnalysis

model_root = r"$insightfaceDir"
os.makedirs(model_root, exist_ok=True)
os.environ['INSIGHTFACE_ROOT'] = model_root

try:
    app = FaceAnalysis(name='antelopev2', root=model_root)
    app.prepare(ctx_id=0, det_size=(640, 640))
    print("SUCCESS: InsightFace models downloaded")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
"@
    $scriptPath = Join-Path $env:TEMP "insightface_$(New-Guid).py"
    $insightfaceScript | Out-File -FilePath $scriptPath -Encoding UTF8 -Force
    $output = & $pythonCmd $scriptPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] InsightFace setup complete" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] InsightFace setup may have issues" -ForegroundColor Yellow
    }
    if (Test-Path $scriptPath) {
        Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
    }
} catch {
    Write-Host "  [WARN] InsightFace setup error: $_" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "[5/5] Generating summary..." -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DOWNLOAD SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$models = @(
    @{ Name = "Realistic Vision V6.0"; Path = $realisticPath },
    @{ Name = "InstantID"; Path = $instantIdPath },
    @{ Name = "Real-ESRGAN"; Path = $realesrganPath },
    @{ Name = "GFPGAN"; Path = $gfpganPath }
)

$downloaded = 0
foreach ($model in $models) {
    if (Test-Path $model.Path) {
        $size = (Get-Item $model.Path).Length / 1MB
        Write-Host "[OK] $($model.Name) - $([math]::Round($size, 2)) MB" -ForegroundColor Green
        $downloaded++
    } else {
        Write-Host "[MISSING] $($model.Name)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Downloaded: $downloaded / $($models.Count) essential models" -ForegroundColor $(if ($downloaded -eq $models.Count) { "Green" } else { "Yellow" })
Write-Host ""
Write-Host "For more models, run: .\download-all-models-complete.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

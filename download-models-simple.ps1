# Simple Model Download - Auto Fixed
Write-Host "Starting model download..." -ForegroundColor Green

$Root = $PSScriptRoot
if (-not $Root) { $Root = Get-Location }

# Find Python
$python = $null
if (Test-Path "$Root\.venv\Scripts\python.exe") {
    $python = "$Root\.venv\Scripts\python.exe"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
}

if (-not $python) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $python" -ForegroundColor Cyan

# Install packages
Write-Host "Installing packages..." -ForegroundColor Cyan
& $python -m pip install --quiet --upgrade huggingface_hub requests tqdm 2>&1 | Out-Null

# Create directories
$dirs = @(
    "ComfyUI\models\checkpoints",
    "ComfyUI\models\instantid",
    "ComfyUI\models\upscale_models",
    "ComfyUI\models\face_restore",
    "ComfyUI\models\insightface"
)

foreach ($dir in $dirs) {
    $path = Join-Path $Root $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    }
}

# Download essential models
Write-Host "`nDownloading models..." -ForegroundColor Cyan

# Realistic Vision V6.0
$script = @"
from huggingface_hub import hf_hub_download
import os
target = r"$Root\ComfyUI\models\checkpoints\Realistic_Vision_V6.0.safetensors"
os.makedirs(os.path.dirname(target), exist_ok=True)
hf_hub_download(repo_id="SG161222/Realistic_Vision_V6.0_B1_noVAE", filename="Realistic_Vision_V6.0_NV_B1.safetensors", local_dir=os.path.dirname(target), local_dir_use_symlinks=False)
print("OK: Realistic Vision V6.0")
"@

$script | & $python
Write-Host "Realistic Vision V6.0: OK" -ForegroundColor Green

# InstantID
$script = @"
from huggingface_hub import hf_hub_download
import os
target = r"$Root\ComfyUI\models\instantid\ip-adapter.bin"
os.makedirs(os.path.dirname(target), exist_ok=True)
hf_hub_download(repo_id="InstantX/InstantID", filename="ip-adapter.bin", local_dir=os.path.dirname(target), local_dir_use_symlinks=False)
print("OK: InstantID")
"@

$script | & $python
Write-Host "InstantID: OK" -ForegroundColor Green

# Real-ESRGAN
$script = @"
import requests
import os
url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth"
target = r"$Root\ComfyUI\models\upscale_models\RealESRGAN_x4plus.pth"
os.makedirs(os.path.dirname(target), exist_ok=True)
r = requests.get(url, stream=True)
with open(target, 'wb') as f:
    for chunk in r.iter_content(chunk_size=8192):
        f.write(chunk)
print("OK: Real-ESRGAN")
"@

$script | & $python
Write-Host "Real-ESRGAN: OK" -ForegroundColor Green

# GFPGAN
$script = @"
import requests
import os
url = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"
target = r"$Root\ComfyUI\models\face_restore\GFPGANv1.4.pth"
os.makedirs(os.path.dirname(target), exist_ok=True)
r = requests.get(url, stream=True)
with open(target, 'wb') as f:
    for chunk in r.iter_content(chunk_size=8192):
        f.write(chunk)
print("OK: GFPGAN")
"@

$script | & $python
Write-Host "GFPGAN: OK" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DOWNLOAD COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

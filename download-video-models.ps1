# Download Video Generation Models
# Automatically downloads AnimateDiff and SVD models using huggingface-hub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Downloading Video Generation Models" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if huggingface-hub is installed
Write-Host "[1/4] Checking huggingface-hub..." -ForegroundColor Yellow
try {
    python -c "import huggingface_hub" 2>&1 | Out-Null
    Write-Host "✓ huggingface-hub installed" -ForegroundColor Green
} catch {
    Write-Host "Installing huggingface-hub..." -ForegroundColor Gray
    python -m pip install huggingface-hub
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ huggingface-hub installed" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install huggingface-hub" -ForegroundColor Red
        exit 1
    }
}

$comfyuiPath = Join-Path $PSScriptRoot "ComfyUI"
if (-not (Test-Path $comfyuiPath)) {
    Write-Host "✗ ComfyUI directory not found" -ForegroundColor Red
    exit 1
}

# Setup directories
$animatediffModelsPath = Join-Path $comfyuiPath "models\animatediff"
$svdModelsPath = Join-Path $comfyuiPath "models\svd"

New-Item -ItemType Directory -Path $animatediffModelsPath -Force | Out-Null
New-Item -ItemType Directory -Path $svdModelsPath -Force | Out-Null

# Download AnimateDiff model
Write-Host ""
Write-Host "[2/4] Downloading AnimateDiff model..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

$animatediffModel = "mm_sd_v15_v2.safetensors"
$animatediffModelPath = Join-Path $animatediffModelsPath $animatediffModel

if (Test-Path $animatediffModelPath) {
    Write-Host "✓ AnimateDiff model already exists: $animatediffModel" -ForegroundColor Green
} else {
    try {
        python -c @"
from huggingface_hub import hf_hub_download
import os

model_path = hf_hub_download(
    repo_id='guoyww/animatediff-motion-adapter-v1-5-2',
    filename='mm_sd_v15_v2.safetensors',
    local_dir=r'$animatediffModelsPath',
    local_dir_use_symlinks=False
)
print(f'Downloaded to: {model_path}')
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ AnimateDiff model downloaded" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to download AnimateDiff model" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Error downloading AnimateDiff model: $_" -ForegroundColor Red
        Write-Host "  You can download manually from:" -ForegroundColor Yellow
        Write-Host "  https://huggingface.co/guoyww/animatediff-motion-adapter-v1-5-2" -ForegroundColor Gray
    }
}

# Download SVD model (checkpoint)
Write-Host ""
Write-Host "[3/4] Downloading SVD model..." -ForegroundColor Yellow
Write-Host "This may take several minutes (model is large)..." -ForegroundColor Gray

$svdCheckpoint = "svd.safetensors"
$svdCheckpointPath = Join-Path $svdModelsPath $svdCheckpoint

if (Test-Path $svdCheckpointPath) {
    Write-Host "✓ SVD model already exists: $svdCheckpoint" -ForegroundColor Green
} else {
    try {
        Write-Host "Downloading SVD checkpoint..." -ForegroundColor Gray
        python -c @"
from huggingface_hub import snapshot_download
import os

try:
    snapshot_download(
        repo_id='stabilityai/stable-video-diffusion-img2vid',
        local_dir=r'$svdModelsPath',
        local_dir_use_symlinks=False,
        ignore_patterns=['*.md', '*.txt', '*.json']  # Skip non-model files
    )
    print('SVD model downloaded successfully')
except Exception as e:
    print(f'Error: {e}')
    print('Note: SVD model is very large. You may need to download manually.')
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ SVD model downloaded" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to download SVD model" -ForegroundColor Yellow
            Write-Host "  SVD model is very large. Consider downloading manually:" -ForegroundColor Yellow
            Write-Host "  https://huggingface.co/stabilityai/stable-video-diffusion-img2vid" -ForegroundColor Gray
        }
    } catch {
        Write-Host "✗ Error downloading SVD model: $_" -ForegroundColor Red
    }
}

# Verify downloads
Write-Host ""
Write-Host "[4/4] Verifying downloads..." -ForegroundColor Yellow

$animatediffFiles = Get-ChildItem -Path $animatediffModelsPath -Filter "*.safetensors","*.ckpt" -ErrorAction SilentlyContinue
$svdFiles = Get-ChildItem -Path $svdModelsPath -Filter "*.safetensors","*.ckpt" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Download Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "AnimateDiff Models: $($animatediffFiles.Count) files" -ForegroundColor $(if ($animatediffFiles.Count -gt 0) { "Green" } else { "Yellow" })
if ($animatediffFiles.Count -gt 0) {
    foreach ($file in $animatediffFiles) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "  - $($file.Name) ($sizeMB MB)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "SVD Models: $($svdFiles.Count) files" -ForegroundColor $(if ($svdFiles.Count -gt 0) { "Green" } else { "Yellow" })
if ($svdFiles.Count -gt 0) {
    foreach ($file in $svdFiles) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "  - $($file.Name) ($sizeMB MB)" -ForegroundColor Gray
    }
}

Write-Host ""
if ($animatediffFiles.Count -gt 0 -or $svdFiles.Count -gt 0) {
    Write-Host "✓ Models ready for video generation!" -ForegroundColor Green
} else {
    Write-Host "⚠ No models downloaded. Please download manually or check errors above." -ForegroundColor Yellow
}

Write-Host ""

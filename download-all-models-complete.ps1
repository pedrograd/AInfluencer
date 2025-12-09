# =========================================
# Complete Model Download Script
# Implements all models from docs/33-MODELS-AND-CHECKPOINTS-COMPLETE-GUIDE.md
# =========================================

Set-StrictMode -Off  # More forgiving for compatibility
$ErrorActionPreference = "Continue"

# UTF-8 encoding (multiple methods)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try { 
    chcp 65001 | Out-Null 
} catch {
    # Fallback - encoding already set above
}

# Path resolution (multiple fallbacks)
$Root = $PSScriptRoot
if (-not $Root) {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if (-not $Root) {
    $Root = Get-Location
}
Set-Location $Root

# Python command
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
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

# Logging functions
function Write-Info { param([string]$Msg) Write-Host "[INFO] $Msg" -ForegroundColor Cyan }
function Write-Success { param([string]$Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
function Write-Warning { param([string]$Msg) Write-Host "[WARN] $Msg" -ForegroundColor Yellow }
function Write-Error { param([string]$Msg) Write-Host "[ERROR] $Msg" -ForegroundColor Red }

$pythonCmd = Get-PythonCmd
$comfyPath = Join-Path $Root "ComfyUI"

if (-not (Test-Path $comfyPath)) {
    Write-Error "ComfyUI not found: $comfyPath"
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "COMPLETE MODEL DOWNLOAD SYSTEM" -ForegroundColor Cyan
Write-Host "Based on docs/33-MODELS-AND-CHECKPOINTS-COMPLETE-GUIDE.md" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Install required packages
Write-Info "Installing required Python packages..."
$packages = @("huggingface_hub", "requests", "insightface", "onnxruntime", "tqdm")
foreach ($package in $packages) {
    try {
        & $pythonCmd -m pip install --upgrade $package --quiet 2>&1 | Out-Null
        Write-Success "$package installed"
    } catch {
        Write-Warning "$package installation issue (continuing)"
    }
}
Write-Host ""

# Create all model directories
$modelDirs = @(
    "models\checkpoints",
    "models\controlnet",
    "models\upscale_models",
    "models\face_restore",
    "models\ipadapter",
    "models\instantid",
    "models\insightface",
    "models\animatediff",
    "models\vae"
)

foreach ($dir in $modelDirs) {
    $fullPath = Join-Path $comfyPath $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Info "Created directory: $dir"
    }
}
Write-Host ""

# Download function for HuggingFace
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
    
    if (Test-Path $TargetPath) {
        $sizeMB = (Get-Item $TargetPath).Length / 1MB
        $sizeGB = $sizeMB / 1024
        if ($sizeGB -ge 1) {
            Write-Success "$Description already exists ($([math]::Round($sizeGB, 2)) GB)"
        } else {
            Write-Success "$Description already exists ($([math]::Round($sizeMB, 2)) MB)"
        }
        return $true
    }
    
    Write-Info "Downloading $Description..."
    
    $downloadScript = @"
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download
from tqdm import tqdm

repo_id = "$RepoId"
filename = "$FileName"
target_path = r"$TargetPath"
subfolder = "$Subfolder"

try:
    print(f"Downloading {filename} from {repo_id}...")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    if subfolder and subfolder.strip():
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            subfolder=subfolder,
            local_dir=os.path.dirname(target_path),
            local_dir_use_symlinks=False
        )
    else:
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
        file_size_gb = file_size_mb / 1024
        if file_size_gb >= 1:
            print(f"SUCCESS: {target_path} ({file_size_gb:.2f} GB)")
        else:
            print(f"SUCCESS: {target_path} ({file_size_mb:.2f} MB)")
        sys.exit(0)
    else:
        print(f"ERROR: File not found after download")
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
                Write-Success "$Description downloaded ($([math]::Round($fileSizeGB, 2)) GB)"
            } else {
                Write-Success "$Description downloaded ($([math]::Round($fileSizeMB, 2)) MB)"
            }
            return $true
        } else {
            Write-Warning "$Description download failed"
            return $false
        }
    } catch {
        Write-Warning "$Description download error: $_"
        return $false
    } finally {
        if (Test-Path $scriptPath) {
            Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
        }
    }
}

# Direct URL download function
function Download-DirectUrl {
    param(
        [string]$Url,
        [string]$TargetPath,
        [string]$Description = ""
    )
    
    if ([string]::IsNullOrWhiteSpace($Description)) {
        $Description = Split-Path -Leaf $TargetPath
    }
    
    if (Test-Path $TargetPath) {
        $fileSizeMB = (Get-Item $TargetPath).Length / 1MB
        $fileSizeGB = $fileSizeMB / 1024
        if ($fileSizeGB -ge 1) {
            Write-Success "$Description already exists ($([math]::Round($fileSizeGB, 2)) GB)"
        } else {
            Write-Success "$Description already exists ($([math]::Round($fileSizeMB, 2)) MB)"
        }
        return $true
    }
    
    Write-Info "Downloading $Description..."
    
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
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    if downloaded % (1024 * 1024 * 10) == 0:
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
                Write-Success "$Description downloaded ($([math]::Round($fileSizeGB, 2)) GB)"
            } else {
                Write-Success "$Description downloaded ($([math]::Round($fileSizeMB, 2)) MB)"
            }
            return $true
        } else {
            Write-Warning "$Description download failed"
            return $false
        }
    } finally {
        if (Test-Path $scriptPath) {
            Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
        }
    }
}

# =========================================
# TIER 1: ULTRA-REALISTIC IMAGE MODELS
# =========================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "TIER 1: ULTRA-REALISTIC IMAGE MODELS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 1. Flux.1 [dev] - Highest Quality
Write-Info "[1/4] Flux.1 [dev] - Highest Quality (10/10)"
$fluxDevPath = Join-Path $comfyPath "models\checkpoints\flux1-dev.safetensors"
# Note: Flux models are very large (~24GB), downloading main file
$fluxDevSuccess = Download-HuggingFaceModel `
    -RepoId "black-forest-labs/FLUX.1-dev" `
    -FileName "diffusion_pytorch_model.safetensors" `
    -TargetPath $fluxDevPath `
    -Description "Flux.1 [dev] - Ultimate Quality"

# 2. Realistic Vision V6.0 - Best General Purpose
Write-Info "[2/4] Realistic Vision V6.0 - Best General Purpose (9.5/10)"
$realisticVisionPath = Join-Path $comfyPath "models\checkpoints\Realistic_Vision_V6.0.safetensors"
$realisticVisionSuccess = Download-HuggingFaceModel `
    -RepoId "SG161222/Realistic_Vision_V6.0_B1_noVAE" `
    -FileName "Realistic_Vision_V6.0_NV_B1.safetensors" `
    -TargetPath $realisticVisionPath `
    -Description "Realistic Vision V6.0"

# 3. Juggernaut XL V9 - Professional Quality
Write-Info "[3/4] Juggernaut XL V9 - Professional Quality (9.5/10)"
Write-Warning "Juggernaut XL V9 requires Civitai download (manual or API key)"
$juggernautPath = Join-Path $comfyPath "models\checkpoints\juggernautXL_v9.safetensors"
if (-not (Test-Path $juggernautPath)) {
    Write-Host "  Source: https://civitai.com/models/133005/juggernaut-xl-v9" -ForegroundColor Cyan
}

# 4. DreamShaper XL - Artistic Realism
Write-Info "[4/4] DreamShaper XL - Artistic Realism (9/10)"
$dreamshaperPath = Join-Path $comfyPath "models\checkpoints\DreamShaperXL.safetensors"
$dreamshaperSuccess = Download-HuggingFaceModel `
    -RepoId "Lykon/DreamShaperXL" `
    -FileName "DreamShaperXL_turboDpmppSDE.safetensors" `
    -TargetPath $dreamshaperPath `
    -Description "DreamShaper XL"

Write-Host ""

# =========================================
# TIER 2: HIGH QUALITY FAST MODELS
# =========================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "TIER 2: HIGH QUALITY FAST MODELS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 5. Flux.1 [schnell] - Fast Generation
Write-Info "[1/3] Flux.1 [schnell] - Fast Generation (9/10)"
$fluxSchnellPath = Join-Path $comfyPath "models\checkpoints\flux1-schnell.safetensors"
$fluxSchnellSuccess = Download-HuggingFaceModel `
    -RepoId "black-forest-labs/FLUX.1-schnell" `
    -FileName "diffusion_pytorch_model.safetensors" `
    -TargetPath $fluxSchnellPath `
    -Description "Flux.1 [schnell] - Fast"

# 6. SDXL Turbo - Very Fast
Write-Info "[2/3] SDXL Turbo - Very Fast (8.5/10)"
$sdxlTurboPath = Join-Path $comfyPath "models\checkpoints\sdxl_turbo.safetensors"
$sdxlTurboSuccess = Download-HuggingFaceModel `
    -RepoId "stabilityai/sdxl-turbo" `
    -FileName "sd_xl_turbo_1.0_fp16.safetensors" `
    -TargetPath $sdxlTurboPath `
    -Description "SDXL Turbo"

# 7. SDXL Base - Foundation Model
Write-Info "[3/3] SDXL Base 1.0 - Foundation Model (8/10)"
$sdxlBasePath = Join-Path $comfyPath "models\checkpoints\sd_xl_base_1.0.safetensors"
$sdxlBaseSuccess = Download-HuggingFaceModel `
    -RepoId "stabilityai/stable-diffusion-xl-base-1.0" `
    -FileName "sd_xl_base_1.0.safetensors" `
    -TargetPath $sdxlBasePath `
    -Description "SDXL Base 1.0"

Write-Host ""

# =========================================
# TIER 3: CLASSIC & COMPATIBLE MODELS
# =========================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "TIER 3: CLASSIC & COMPATIBLE MODELS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 8. Stable Diffusion 1.5 - Classic
Write-Info "[1/3] Stable Diffusion 1.5 - Classic (7.5/10)"
$sd15Path = Join-Path $comfyPath "models\checkpoints\v1-5-pruned.safetensors"
$sd15Success = Download-HuggingFaceModel `
    -RepoId "runwayml/stable-diffusion-v1-5" `
    -FileName "v1-5-pruned.safetensors" `
    -TargetPath $sd15Path `
    -Description "Stable Diffusion 1.5"

# 9. Stable Diffusion 2.1 - Enhanced
Write-Info "[2/3] Stable Diffusion 2.1 (8/10)"
$sd21Path = Join-Path $comfyPath "models\checkpoints\v2-1_768-ema-pruned.safetensors"
$sd21Success = Download-HuggingFaceModel `
    -RepoId "stabilityai/stable-diffusion-2-1" `
    -FileName "v2-1_768-ema-pruned.safetensors" `
    -TargetPath $sd21Path `
    -Description "Stable Diffusion 2.1 768-EMA"

# 10. Stable Cascade - High Detail
Write-Info "[3/3] Stable Cascade - High Detail (9/10)"
$cascadePath = Join-Path $comfyPath "models\checkpoints\stable_cascade_stage_c.safetensors"
$cascadeSuccess = Download-HuggingFaceModel `
    -RepoId "stabilityai/stable-cascade" `
    -FileName "stage_c.safetensors" `
    -TargetPath $cascadePath `
    -Description "Stable Cascade Stage C"

Write-Host ""

# =========================================
# VIDEO GENERATION MODELS
# =========================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "VIDEO GENERATION MODELS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 1. Stable Video Diffusion (SVD)
Write-Info "[1/3] Stable Video Diffusion (SVD) - Best Quality (9.5/10)"
$svdPath = Join-Path $comfyPath "models\checkpoints\svd.safetensors"
$svdSuccess = Download-HuggingFaceModel `
    -RepoId "stabilityai/stable-video-diffusion-img2vid-xt" `
    -FileName "svd_xt.safetensors" `
    -TargetPath $svdPath `
    -Description "Stable Video Diffusion"

# 2. AnimateDiff
Write-Info "[2/3] AnimateDiff - Character Animation (9/10)"
$animatediffPath = Join-Path $comfyPath "models\animatediff\animatediff_motion_adapter_v1_5_2.safetensors"
$animatediffSuccess = Download-HuggingFaceModel `
    -RepoId "guoyww/animatediff-motion-adapter-v1-5-2" `
    -FileName "diffusion_pytorch_model.safetensors" `
    -TargetPath $animatediffPath `
    -Description "AnimateDiff Motion Adapter"

# 3. SVD XT Extended
Write-Info "[3/3] SVD XT Extended - Longer Videos (9.5/10)"
$svdXtPath = Join-Path $comfyPath "models\checkpoints\svd_xt_1_1.safetensors"
$svdXtSuccess = Download-HuggingFaceModel `
    -RepoId "stabilityai/stable-video-diffusion-img2vid-xt-1-1" `
    -FileName "svd_xt_1_1.safetensors" `
    -TargetPath $svdXtPath `
    -Description "SVD XT Extended"

# 4. ModelScope Text-to-Video
Write-Info "[4/5] ModelScope T2V (8.5/10)"
$modelScopePath = Join-Path $comfyPath "models\checkpoints\modelscope_t2v.safetensors"
$modelScopeSuccess = Download-HuggingFaceModel `
    -RepoId "damo-vilab/modelscope-damo-text-to-video-synthesis" `
    -FileName "modelscope-damo-text-to-video-synthesis.safetensors" `
    -TargetPath $modelScopePath `
    -Description "ModelScope Text-to-Video"

# 5. HunyuanVideo
Write-Info "[5/5] HunyuanVideo (9/10)"
$hunyuanVideoPath = Join-Path $comfyPath "models\checkpoints\hunyuan_video.safetensors"
$hunyuanVideoSuccess = Download-HuggingFaceModel `
    -RepoId "Tencent/HunyuanVideo" `
    -FileName "hunyuan_video.safetensors" `
    -TargetPath $hunyuanVideoPath `
    -Description "HunyuanVideo"

Write-Host ""

# =========================================
# FACE CONSISTENCY MODELS
# =========================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "FACE CONSISTENCY MODELS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 1. InstantID
Write-Info "[1/3] InstantID - Best Face Consistency (10/10)"
$instantIdPath = Join-Path $comfyPath "models\instantid\ip-adapter.bin"
$instantIdSuccess = Download-HuggingFaceModel `
    -RepoId "InstantX/InstantID" `
    -FileName "ip-adapter.bin" `
    -TargetPath $instantIdPath `
    -Description "InstantID IP-Adapter"

# 2. InsightFace (Required for InstantID)
Write-Info "[2/3] InsightFace - Face Analysis (Required for InstantID)"
$insightfaceDir = Join-Path $comfyPath "models\insightface"
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
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
$insightfaceScriptPath = Join-Path $env:TEMP "insightface_$(New-Guid).py"
try {
    $insightfaceScript | Out-File -FilePath $insightfaceScriptPath -Encoding UTF8 -Force
    $output = & $pythonCmd $insightfaceScriptPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "InsightFace models downloaded"
    } else {
        Write-Warning "InsightFace download may have issues"
        Write-Host $output
    }
} finally {
    if (Test-Path $insightfaceScriptPath) {
        Remove-Item $insightfaceScriptPath -Force -ErrorAction SilentlyContinue
    }
}

# 3. IP-Adapter Plus
Write-Info "[3/3] IP-Adapter Plus - Universal Compatibility (9/10)"
$ipadapterPath = Join-Path $comfyPath "models\ipadapter\ip-adapter-plus_sd15.safetensors"
$ipadapterSuccess = Download-HuggingFaceModel `
    -RepoId "lllyasviel/sd-controlnet" `
    -FileName "ip-adapter-plus_sd15.safetensors" `
    -TargetPath $ipadapterPath `
    -Description "IP-Adapter Plus"

Write-Host ""

# =========================================
# POST-PROCESSING MODELS
# =========================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "POST-PROCESSING MODELS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 1. Real-ESRGAN x4plus
Write-Info "[1/4] Real-ESRGAN x4plus - General Upscaling (9.5/10)"
$realesrganPath = Join-Path $comfyPath "models\upscale_models\RealESRGAN_x4plus.pth"
$realesrganSuccess = Download-DirectUrl `
    -Url "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth" `
    -TargetPath $realesrganPath `
    -Description "Real-ESRGAN x4plus"

# 2. 4x-UltraSharp
Write-Info "[2/4] 4x-UltraSharp - Maximum Quality Upscaling (10/10)"
Write-Warning "4x-UltraSharp requires manual download from GitHub"
$ultrasharpPath = Join-Path $comfyPath "models\upscale_models\4x-UltraSharp.pth"
if (-not (Test-Path $ultrasharpPath)) {
    Write-Host "  Source: https://github.com/tsurumeso/4x-UltraSharp" -ForegroundColor Cyan
}

# 3. GFPGAN
Write-Info "[3/4] GFPGAN - Face Restoration (9.5/10)"
$gfpganPath = Join-Path $comfyPath "models\face_restore\GFPGANv1.4.pth"
$gfpganSuccess = Download-DirectUrl `
    -Url "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" `
    -TargetPath $gfpganPath `
    -Description "GFPGAN v1.4"

# 4. CodeFormer
Write-Info "[4/4] CodeFormer - Best Quality Face Restoration (10/10)"
Write-Warning "CodeFormer requires manual download from GitHub"
$codeformerPath = Join-Path $comfyPath "models\face_restore\codeformer.pth"
if (-not (Test-Path $codeformerPath)) {
    Write-Host "  Source: https://github.com/sczhou/CodeFormer" -ForegroundColor Cyan
}

Write-Host ""

# =========================================
# CONTROLNET MODELS
# =========================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "CONTROLNET MODELS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 1. ControlNet OpenPose
Write-Info "[1/3] ControlNet OpenPose - Pose Control"
$openposePath = Join-Path $comfyPath "models\controlnet\control_v11p_sd15_openpose.pth"
$openposeSuccess = Download-HuggingFaceModel `
    -RepoId "lllyasviel/sd-controlnet-openpose" `
    -FileName "diffusion_pytorch_model.safetensors" `
    -TargetPath $openposePath `
    -Description "ControlNet OpenPose"

# 2. ControlNet Depth
Write-Info "[2/3] ControlNet Depth - Depth Control"
$depthPath = Join-Path $comfyPath "models\controlnet\control_v11f1p_sd15_depth.pth"
$depthSuccess = Download-HuggingFaceModel `
    -RepoId "lllyasviel/sd-controlnet-depth" `
    -FileName "diffusion_pytorch_model.safetensors" `
    -TargetPath $depthPath `
    -Description "ControlNet Depth"

# 3. ControlNet Canny
Write-Info "[3/3] ControlNet Canny - Edge Control"
$cannyPath = Join-Path $comfyPath "models\controlnet\control_v11p_sd15_canny.pth"
$cannySuccess = Download-HuggingFaceModel `
    -RepoId "lllyasviel/sd-controlnet-canny" `
    -FileName "diffusion_pytorch_model.safetensors" `
    -TargetPath $cannyPath `
    -Description "ControlNet Canny"

Write-Host ""

# =========================================
# SUMMARY
# =========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DOWNLOAD SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$models = @(
    @{ Name = "Flux.1 [dev]"; Path = $fluxDevPath; Category = "Image - Tier 1" },
    @{ Name = "Realistic Vision V6.0"; Path = $realisticVisionPath; Category = "Image - Tier 1" },
    @{ Name = "Juggernaut XL V9"; Path = $juggernautPath; Category = "Image - Tier 1" },
    @{ Name = "DreamShaper XL"; Path = $dreamshaperPath; Category = "Image - Tier 1" },
    @{ Name = "Flux.1 [schnell]"; Path = $fluxSchnellPath; Category = "Image - Tier 2" },
    @{ Name = "SDXL Turbo"; Path = $sdxlTurboPath; Category = "Image - Tier 2" },
    @{ Name = "SDXL Base"; Path = $sdxlBasePath; Category = "Image - Tier 2" },
    @{ Name = "Stable Diffusion 1.5"; Path = $sd15Path; Category = "Image - Tier 3" },
    @{ Name = "Stable Diffusion 2.1"; Path = $sd21Path; Category = "Image - Tier 3" },
    @{ Name = "Stable Cascade"; Path = $cascadePath; Category = "Image - Tier 3" },
    @{ Name = "Stable Video Diffusion"; Path = $svdPath; Category = "Video" },
    @{ Name = "AnimateDiff"; Path = $animatediffPath; Category = "Video" },
    @{ Name = "SVD XT Extended"; Path = $svdXtPath; Category = "Video" },
    @{ Name = "ModelScope T2V"; Path = $modelScopePath; Category = "Video" },
    @{ Name = "HunyuanVideo"; Path = $hunyuanVideoPath; Category = "Video" },
    @{ Name = "InstantID"; Path = $instantIdPath; Category = "Face Consistency" },
    @{ Name = "InsightFace"; Path = $insightfaceDir; Category = "Face Consistency" },
    @{ Name = "IP-Adapter Plus"; Path = $ipadapterPath; Category = "Face Consistency" },
    @{ Name = "Real-ESRGAN"; Path = $realesrganPath; Category = "Post-Processing" },
    @{ Name = "4x-UltraSharp"; Path = $ultrasharpPath; Category = "Post-Processing" },
    @{ Name = "GFPGAN"; Path = $gfpganPath; Category = "Post-Processing" },
    @{ Name = "CodeFormer"; Path = $codeformerPath; Category = "Post-Processing" },
    @{ Name = "ControlNet OpenPose"; Path = $openposePath; Category = "ControlNet" },
    @{ Name = "ControlNet Depth"; Path = $depthPath; Category = "ControlNet" },
    @{ Name = "ControlNet Canny"; Path = $cannyPath; Category = "ControlNet" }
)

$downloaded = 0
$total = $models.Count

foreach ($model in $models) {
    if (Test-Path $model.Path) {
        $size = (Get-Item $model.Path -ErrorAction SilentlyContinue).Length
        if ($size -gt 0) {
            $downloaded++
            $sizeGB = $size / (1024**3)
            $sizeMB = $size / (1024**2)
            if ($sizeGB -ge 1) {
                Write-Success "$($model.Name) - $($model.Category) ($([math]::Round($sizeGB, 2)) GB)"
            } else {
                Write-Success "$($model.Name) - $($model.Category) ($([math]::Round($sizeMB, 2)) MB)"
            }
        } else {
            Write-Warning "$($model.Name) - $($model.Category) (exists but empty)"
        }
    } else {
        Write-Warning "$($model.Name) - $($model.Category) (not found)"
    }
}

Write-Host ""
Write-Host "Downloaded: $downloaded / $total models" -ForegroundColor $(if ($downloaded -eq $total) { "Green" } else { "Yellow" })
Write-Host ""

if ($downloaded -lt $total) {
    Write-Host "Some models require manual download:" -ForegroundColor Yellow
    Write-Host "  - Juggernaut XL V9: https://civitai.com/models/133005/juggernaut-xl-v9" -ForegroundColor Cyan
    Write-Host "  - 4x-UltraSharp: https://github.com/tsurumeso/4x-UltraSharp" -ForegroundColor Cyan
    Write-Host "  - CodeFormer: https://github.com/sczhou/CodeFormer" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DOWNLOAD COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

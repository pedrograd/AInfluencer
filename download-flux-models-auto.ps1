# Automatic Flux Model Download Script
# Downloads Flux.1 [dev] and Flux.1 [schnell] models automatically
# Based on Phase 1 priorities from roadmap

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Automatic Flux Model Download" -ForegroundColor Cyan
Write-Host "Phase 1: Quality & Realism Enhancement" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get root directory
$Root = $PSScriptRoot
if (-not $Root) {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# Paths
$ComfyUIPath = Join-Path $Root "ComfyUI"
$ModelsPath = Join-Path $ComfyUIPath "models"
$CheckpointsPath = Join-Path $ModelsPath "checkpoints"

# Ensure directories exist
if (-not (Test-Path $CheckpointsPath)) {
    New-Item -ItemType Directory -Path $CheckpointsPath -Force | Out-Null
}

# Get Python from venv
$PythonCmd = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonCmd)) {
    Write-Host "[ERROR] Python not found in .venv. Please run setup first." -ForegroundColor Red
    exit 1
}

Write-Host "Installing/Updating huggingface_hub..." -ForegroundColor Yellow
& $PythonCmd -m pip install --upgrade huggingface_hub hf-transfer --quiet 2>&1 | Out-Null
Write-Host "[OK] Ready" -ForegroundColor Green
Write-Host ""

# Check Hugging Face authentication
Write-Host "Checking Hugging Face authentication..." -ForegroundColor Yellow
$AuthCheckScript = @"
import os
from huggingface_hub import HfApi, login
from pathlib import Path

try:
    api = HfApi()
    # Try to get current user info
    try:
        user = api.whoami()
        print(f"AUTHENTICATED: Logged in as {user.get('name', 'user')}")
        exit(0)
    except Exception as e:
        # Check if token exists in environment or cache
        token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN')
        if token:
            print("TOKEN_FOUND: Hugging Face token found in environment")
            exit(0)
        
        # Check cache directory for token
        cache_dir = Path.home() / ".cache" / "huggingface"
        if cache_dir.exists():
            print("CACHE_FOUND: Hugging Face cache directory exists")
            exit(1)  # Token might exist but not authenticated
        else:
            print("NOT_AUTHENTICATED: No authentication found")
            exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
"@

$TempAuthCheck = Join-Path $env:TEMP "check_hf_auth_$([guid]::NewGuid()).py"
$AuthCheckScript | Out-File -FilePath $TempAuthCheck -Encoding UTF8
$AuthCheckResult = & $PythonCmd $TempAuthCheck 2>&1
$AuthCheckExitCode = $LASTEXITCODE
Remove-Item $TempAuthCheck -Force -ErrorAction SilentlyContinue

$IsAuthenticated = $false
if ($AuthCheckResult -match "AUTHENTICATED|TOKEN_FOUND") {
    Write-Host "[OK] Hugging Face authentication found" -ForegroundColor Green
    $IsAuthenticated = $true
} else {
    Write-Host "[WARNING] Hugging Face authentication not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Flux models require Hugging Face authentication because they are gated repositories." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To authenticate:" -ForegroundColor Cyan
    Write-Host "  1. Get your Hugging Face token from: https://huggingface.co/settings/tokens" -ForegroundColor White
    Write-Host "  2. Request access to Flux models:" -ForegroundColor White
    Write-Host "     - https://huggingface.co/black-forest-labs/FLUX.1-schnell" -ForegroundColor Gray
    Write-Host "     - https://huggingface.co/black-forest-labs/FLUX.1-dev" -ForegroundColor Gray
    Write-Host "  3. Run: huggingface-cli login" -ForegroundColor White
    Write-Host "     Or set environment variable: `$env:HF_TOKEN='your_token_here'" -ForegroundColor White
    Write-Host ""
    Write-Host "The script will attempt downloads, but they will fail if you're not authenticated." -ForegroundColor Yellow
    Write-Host "You can skip Flux models and use other models instead." -ForegroundColor Yellow
    Write-Host ""
}
Write-Host ""

# Flux models to download
$ModelsToDownload = @(
    @{
        Name = "Flux.1 [schnell]"
        FileName = "flux1-schnell.safetensors"
        Repo = "black-forest-labs/FLUX.1-schnell"
        FilePath = "flux1-schnell.safetensors"
        Priority = "HIGH"
        Required = $false
        SizeGB = 24
        Description = "Fast generation with excellent quality (9/10 quality, very fast)"
    },
    @{
        Name = "Flux.1 [dev]"
        FileName = "flux1-dev.safetensors"
        Repo = "black-forest-labs/FLUX.1-dev"
        FilePath = "flux1-dev.safetensors"
        Priority = "HIGH"
        Required = $false
        SizeGB = 24
        Description = "Highest quality generation (10/10 quality, slow)"
    }
)

$Downloaded = 0
$Skipped = 0
$Failed = 0

foreach ($Model in $ModelsToDownload) {
    $OutputPath = Join-Path $CheckpointsPath $Model.FileName
    
    Write-Host "[$($Model.Priority)] $($Model.Name)" -ForegroundColor Cyan
    Write-Host "  Description: $($Model.Description)" -ForegroundColor Gray
    Write-Host "  Size: ~$($Model.SizeGB) GB" -ForegroundColor Gray
    Write-Host ""
    
    # Check if already downloaded
    if (Test-Path $OutputPath) {
        $FileSize = (Get-Item $OutputPath).Length / 1GB
        if ($FileSize -gt 20) {  # Rough check - files should be >20GB
            Write-Host "  [SKIP] Already downloaded ($([math]::Round($FileSize, 2)) GB)" -ForegroundColor Green
            $Skipped++
            Write-Host ""
            continue
        } else {
            Write-Host "  [WARNING] File exists but seems incomplete, re-downloading..." -ForegroundColor Yellow
            Remove-Item $OutputPath -Force -ErrorAction SilentlyContinue
        }
    }
    
    Write-Host "  [DOWNLOAD] Starting download..." -ForegroundColor Yellow
    Write-Host "    Repository: $($Model.Repo)" -ForegroundColor Gray
    Write-Host "    Destination: $OutputPath" -ForegroundColor Gray
    Write-Host ""
    
    # Create Python download script
    $DownloadScript = @"
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download, HfApi
from huggingface_hub.utils import GatedRepoError
import traceback

try:
    repo_id = "$($Model.Repo)"
    filename = "$($Model.FilePath)"
    local_dir = r"$CheckpointsPath"
    
    print(f"Downloading {repo_id}/{filename}...")
    print(f"Destination: {local_dir}")
    
    # Check authentication first
    try:
        api = HfApi()
        api.whoami()
        print("Authentication verified")
    except Exception as auth_err:
        print("WARNING: Authentication check failed. Attempting download anyway...")
    
    # Use hf-transfer for faster downloads if available
    try:
        os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
        print("Using hf-transfer for faster downloads...")
    except:
        pass
    
    # Download with resume support
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        # Verify file exists and has reasonable size
        file_path = Path(downloaded_path)
        if file_path.exists():
            size_gb = file_path.stat().st_size / (1024**3)
            print(f"Download complete: {file_path.name}")
            print(f"Size: {size_gb:.2f} GB")
            if size_gb < 20:
                print(f"WARNING: File size ({size_gb:.2f} GB) seems too small for Flux model")
                sys.exit(1)
            sys.exit(0)
        else:
            print("ERROR: File not found after download")
            sys.exit(1)
    except GatedRepoError as gated_err:
        print(f"ERROR: Gated repository - authentication required")
        print(f"Please:")
        print(f"  1. Request access at: https://huggingface.co/{repo_id}")
        print(f"  2. Authenticate with: huggingface-cli login")
        print(f"  3. Or set HF_TOKEN environment variable")
        sys.exit(1)
    except Exception as download_err:
        # Check if it's an authentication error
        error_str = str(download_err).lower()
        if "401" in error_str or "unauthorized" in error_str or "gated" in error_str:
            print(f"ERROR: Authentication required for gated repository")
            print(f"Please:")
            print(f"  1. Request access at: https://huggingface.co/{repo_id}")
            print(f"  2. Authenticate with: huggingface-cli login")
            print(f"  3. Or set HF_TOKEN environment variable")
        else:
            print(f"ERROR: {download_err}")
        traceback.print_exc()
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
"@
    
    # Save temporary script
    $TempScript = Join-Path $env:TEMP "download_flux_$([guid]::NewGuid()).py"
    $DownloadScript | Out-File -FilePath $TempScript -Encoding UTF8
    
    # Run download
    $Process = Start-Process -FilePath $PythonCmd -ArgumentList $TempScript -NoNewWindow -Wait -PassThru
    
    # Cleanup
    Remove-Item $TempScript -Force -ErrorAction SilentlyContinue
    
    if ($Process.ExitCode -eq 0) {
        if (Test-Path $OutputPath) {
            $FileSize = (Get-Item $OutputPath).Length / 1GB
            Write-Host "  [OK] Download complete ($([math]::Round($FileSize, 2)) GB)" -ForegroundColor Green
            $Downloaded++
        } else {
            Write-Host "  [ERROR] Download reported success but file not found" -ForegroundColor Red
            $Failed++
        }
    } else {
        # Check if it's an authentication error
        $ErrorOutput = $Process.StandardError
        if ($ErrorOutput -match "401|unauthorized|gated|authentication required") {
            Write-Host "  [SKIP] Authentication required for gated repository" -ForegroundColor Yellow
            Write-Host "    This model requires:" -ForegroundColor Gray
            Write-Host "    1. Access request at: https://huggingface.co/$($Model.Repo)" -ForegroundColor Gray
            Write-Host "    2. Hugging Face authentication (huggingface-cli login)" -ForegroundColor Gray
            Write-Host "    Skipping this model for now..." -ForegroundColor Gray
            $Skipped++
        } else {
            Write-Host "  [ERROR] Download failed (exit code: $($Process.ExitCode))" -ForegroundColor Red
            $Failed++
        }
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Download Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Downloaded: $Downloaded" -ForegroundColor Green
Write-Host "Skipped: $Skipped" -ForegroundColor Yellow
Write-Host "Failed: $Failed" -ForegroundColor $(if ($Failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

Write-Host ""
if ($Downloaded -gt 0) {
    Write-Host "Successfully downloaded $Downloaded Flux model(s)!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Models are now available in ComfyUI" -ForegroundColor White
    Write-Host "2. Use Flux.1 [schnell] for fast generation" -ForegroundColor White
    Write-Host "3. Use Flux.1 [dev] for highest quality" -ForegroundColor White
}

if ($Skipped -gt 0 -or $Failed -gt 0) {
    Write-Host ""
    if ($Skipped -gt 0) {
        Write-Host "Note: $Skipped model(s) were skipped (authentication required)" -ForegroundColor Yellow
    }
    if ($Failed -gt 0) {
        Write-Host "Warning: $Failed model(s) failed to download" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "To download Flux models:" -ForegroundColor Cyan
    Write-Host "1. Request access at:" -ForegroundColor White
    Write-Host "   - https://huggingface.co/black-forest-labs/FLUX.1-schnell" -ForegroundColor Gray
    Write-Host "   - https://huggingface.co/black-forest-labs/FLUX.1-dev" -ForegroundColor Gray
    Write-Host "2. Authenticate with Hugging Face:" -ForegroundColor White
    Write-Host "   huggingface-cli login" -ForegroundColor Gray
    Write-Host "3. Re-run this script" -ForegroundColor White
    Write-Host ""
    Write-Host "You can continue using other models (SDXL, Realistic Vision, etc.)" -ForegroundColor Green
    Write-Host "while setting up Flux model access." -ForegroundColor Green
}

# Exit with 0 if we downloaded at least one model or skipped due to auth (not a critical failure)
if ($Downloaded -gt 0 -or ($Failed -eq 0 -and $Skipped -gt 0)) {
    exit 0
} else {
    exit 1
}
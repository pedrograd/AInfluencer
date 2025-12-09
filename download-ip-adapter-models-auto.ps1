# Automatic IP-Adapter Model Download Script
# Uses correct Hugging Face file paths

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Automatic IP-Adapter Model Download" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Paths
$modelsPath = "C:\Users\vandan\Desktop\Data\Models"
$ipAdapterPath = "$modelsPath\ip-adapter"
$pythonPath = "C:\Users\vandan\Desktop\Data\Assets\Python310\python.exe"

# Create directory
if (-not (Test-Path $ipAdapterPath)) {
    New-Item -ItemType Directory -Path $ipAdapterPath -Force | Out-Null
}

Write-Host "Installing huggingface_hub..." -ForegroundColor Yellow
& $pythonPath -m pip install --upgrade huggingface_hub --quiet 2>&1 | Out-Null
Write-Host "[OK] Ready" -ForegroundColor Green
Write-Host ""

# Correct file paths based on Hugging Face structure
$modelsToDownload = @(
    @{
        Name="ip-adapter_sdxl.safetensors"
        Repo="h94/IP-Adapter"
        Subfolder="sdxl_models"
        Priority="HIGH"
        Required=$true
    },
    @{
        Name="ip-adapter_sd15.safetensors"
        Repo="h94/IP-Adapter"
        Subfolder="models"
        Priority="MEDIUM"
        Required=$false
    }
)

Write-Host "Downloading models..." -ForegroundColor Yellow
Write-Host ""

foreach ($model in $modelsToDownload) {
    $filePath = "$ipAdapterPath\$($model.Name)"
    
    if (Test-Path $filePath) {
        $fileSize = (Get-Item $filePath).Length / 1MB
        Write-Host "[SKIP] $($model.Name) - Already exists ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Cyan
        Write-Host ""
        continue
    }
    
    Write-Host "[DOWNLOAD] $($model.Name)..." -ForegroundColor Yellow
    
    # Create download script
    $downloadScript = @"
from huggingface_hub import hf_hub_download
import os

repo_id = "$($model.Repo)"
filename = "$($model.Name)"
local_dir = r"$ipAdapterPath"
subfolder = "$($model.Subfolder)"

try:
    print(f"Downloading {filename} from {repo_id}/{subfolder}...")
    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        subfolder=subfolder,
        local_dir=local_dir
    )
    print(f"SUCCESS: {downloaded_path}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
"@
    
    $scriptPath = "$env:TEMP\download_$($model.Name.Replace('.', '_')).py"
    $downloadScript | Out-File -FilePath $scriptPath -Encoding UTF8
    
    # Run download
    $output = & $pythonPath $scriptPath 2>&1
    
    if ($LASTEXITCODE -eq 0 -or (Test-Path $filePath)) {
        if (Test-Path $filePath) {
            $fileSize = (Get-Item $filePath).Length / 1MB
            Write-Host "  [OK] Downloaded ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
        } else {
            Write-Host "  [WARN] Check if download completed" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [ERROR] Failed - will try direct download" -ForegroundColor Red
        
        # Try direct download using wget/curl
        $url = "https://huggingface.co/$($model.Repo)/resolve/main/$($model.Subfolder)/$($model.Name)"
        Write-Host "  Attempting direct download from Hugging Face..." -ForegroundColor Yellow
        
        try {
            Invoke-WebRequest -Uri $url -OutFile $filePath -UseBasicParsing -ErrorAction Stop
            if (Test-Path $filePath) {
                $fileSize = (Get-Item $filePath).Length / 1MB
                Write-Host "  [OK] Direct download successful ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
            }
        } catch {
            Write-Host "  [ERROR] Direct download also failed" -ForegroundColor Red
            Write-Host "  Manual download required from:" -ForegroundColor Yellow
            Write-Host "  https://huggingface.co/$($model.Repo)/tree/main/$($model.Subfolder)" -ForegroundColor Cyan
        }
    }
    
    # Cleanup
    if (Test-Path $scriptPath) {
        Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$downloadedFiles = Get-ChildItem -Path $ipAdapterPath -Filter "*.safetensors" -ErrorAction SilentlyContinue

if ($downloadedFiles) {
    Write-Host "Downloaded models:" -ForegroundColor Green
    foreach ($file in $downloadedFiles) {
        $fileSize = $file.Length / 1MB
        Write-Host "  [OK] $($file.Name) ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Setup complete! Ready to use IP-Adapter." -ForegroundColor Green
} else {
    Write-Host "[X] No models found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually:" -ForegroundColor Yellow
    Write-Host "1. Visit: https://huggingface.co/h94/IP-Adapter" -ForegroundColor Cyan
    Write-Host "2. Go to 'Files and versions' tab" -ForegroundColor White
    Write-Host "3. Download from sdxl_models/ folder:" -ForegroundColor White
    Write-Host "   - ip-adapter_sdxl.safetensors" -ForegroundColor White
    Write-Host "4. Place in: $ipAdapterPath" -ForegroundColor White
}

Write-Host ""

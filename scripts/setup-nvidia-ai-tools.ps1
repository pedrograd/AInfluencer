# Complete NVIDIA AI Tools Setup Script
# Based on docs/18-AI-TOOLS-NVIDIA-SETUP.md
# This script automates the setup process described in the guide

param(
    [switch]$SkipDriverCheck,
    [switch]$SkipCudaCheck,
    [string]$ComfyUIPath = "C:\AI\ComfyUI"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NVIDIA AI Tools Setup Script" -ForegroundColor Cyan
Write-Host "Based on docs/18-AI-TOOLS-NVIDIA-SETUP.md" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Function to check NVIDIA driver
function Test-NVIDIADriver {
    Write-Host "Checking NVIDIA Driver..." -ForegroundColor Yellow
    if (Test-Command "nvidia-smi") {
        try {
            $output = nvidia-smi --query-gpu=driver_version,name --format=csv,noheader
            Write-Host "✓ NVIDIA Driver detected: $output" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "✗ Error checking NVIDIA driver" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "✗ nvidia-smi not found. Please install NVIDIA drivers from:" -ForegroundColor Red
        Write-Host "  https://www.nvidia.com/Download/index.aspx" -ForegroundColor Yellow
        return $false
    }
}

# Function to check CUDA
function Test-CUDA {
    Write-Host "Checking CUDA Toolkit..." -ForegroundColor Yellow
    if (Test-Command "nvcc") {
        try {
            $output = nvcc --version
            Write-Host "✓ CUDA Toolkit detected" -ForegroundColor Green
            Write-Host $output -ForegroundColor Gray
            return $true
        } catch {
            Write-Host "✗ Error checking CUDA" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "✗ CUDA Toolkit not found. Please install from:" -ForegroundColor Red
        Write-Host "  https://developer.nvidia.com/cuda-downloads" -ForegroundColor Yellow
        return $false
    }
}

# Function to check Python
function Test-PythonVersion {
    Write-Host "Checking Python version..." -ForegroundColor Yellow
    if (Test-Command "python") {
        try {
            $version = python --version
            $versionInfo = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            $major = [int]$versionInfo.Split('.')[0]
            $minor = [int]$versionInfo.Split('.')[1]
            
            if ($major -eq 3 -and ($minor -eq 10 -or $minor -eq 11)) {
                Write-Host "✓ Python $versionInfo (meets requirements)" -ForegroundColor Green
                return $true
            } else {
                Write-Host "✗ Python $versionInfo (requires 3.10 or 3.11)" -ForegroundColor Red
                return $false
            }
        } catch {
            Write-Host "✗ Error checking Python" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "✗ Python not found. Please install Python 3.10 or 3.11" -ForegroundColor Red
        return $false
    }
}

# Function to check ComfyUI
function Test-ComfyUI {
    param([string]$Path)
    Write-Host "Checking ComfyUI installation..." -ForegroundColor Yellow
    
    if (Test-Path $Path) {
        $mainPy = Join-Path $Path "main.py"
        if (Test-Path $mainPy) {
            Write-Host "✓ ComfyUI found at: $Path" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ ComfyUI directory exists but main.py not found" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "✗ ComfyUI not found at: $Path" -ForegroundColor Red
        Write-Host "  Would you like to install ComfyUI? (Y/N)" -ForegroundColor Yellow
        $response = Read-Host
        if ($response -eq "Y" -or $response -eq "y") {
            return Install-ComfyUI -Path $Path
        }
        return $false
    }
}

# Function to install ComfyUI
function Install-ComfyUI {
    param([string]$Path)
    Write-Host "Installing ComfyUI..." -ForegroundColor Yellow
    
    $parentDir = Split-Path -Parent $Path
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }
    
    if (Test-Command "git") {
        try {
            Set-Location $parentDir
            git clone https://github.com/comfyanonymous/ComfyUI.git
            Write-Host "✓ ComfyUI cloned successfully" -ForegroundColor Green
            
            # Create virtual environment
            Set-Location $Path
            python -m venv venv
            Write-Host "✓ Virtual environment created" -ForegroundColor Green
            
            # Activate and install requirements
            & "$Path\venv\Scripts\Activate.ps1"
            python -m pip install --upgrade pip
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
            pip install -r requirements.txt
            Write-Host "✓ ComfyUI dependencies installed" -ForegroundColor Green
            
            return $true
        } catch {
            Write-Host "✗ Error installing ComfyUI: $_" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "✗ Git not found. Please install Git first" -ForegroundColor Red
        return $false
    }
}

# Function to check models
function Test-Models {
    param([string]$ComfyUIPath)
    Write-Host "Checking installed models..." -ForegroundColor Yellow
    
    $modelsDir = Join-Path $ComfyUIPath "models\checkpoints"
    if (Test-Path $modelsDir) {
        $models = Get-ChildItem -Path $modelsDir -Filter "*.safetensors" -ErrorAction SilentlyContinue
        $models += Get-ChildItem -Path $modelsDir -Filter "*.ckpt" -ErrorAction SilentlyContinue
        
        if ($models.Count -gt 0) {
            Write-Host "✓ Found $($models.Count) model(s):" -ForegroundColor Green
            foreach ($model in $models) {
                $sizeGB = [math]::Round($model.Length / 1GB, 2)
                Write-Host "  - $($model.Name) ($sizeGB GB)" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host "⚠ No models found in $modelsDir" -ForegroundColor Yellow
            Write-Host "  Recommended models:" -ForegroundColor Yellow
            Write-Host "  1. Realistic Vision V6.0: https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE" -ForegroundColor Gray
            Write-Host "  2. Juggernaut XL V9: https://civitai.com/models/133005/juggernaut-xl" -ForegroundColor Gray
            return $false
        }
    } else {
        Write-Host "✗ Models directory not found" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "Starting setup verification..." -ForegroundColor Cyan
Write-Host ""

$allChecksPassed = $true

# Check NVIDIA driver
if (-not $SkipDriverCheck) {
    if (-not (Test-NVIDIADriver)) {
        $allChecksPassed = $false
    }
    Write-Host ""
}

# Check CUDA
if (-not $SkipCudaCheck) {
    if (-not (Test-CUDA)) {
        $allChecksPassed = $false
    }
    Write-Host ""
}

# Check Python
if (-not (Test-PythonVersion)) {
    $allChecksPassed = $false
}
Write-Host ""

# Check ComfyUI
if (-not (Test-ComfyUI -Path $ComfyUIPath)) {
    $allChecksPassed = $false
}
Write-Host ""

# Check models
Test-Models -ComfyUIPath $ComfyUIPath
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allChecksPassed) {
    Write-Host "✓ Setup verification completed!" -ForegroundColor Green
    Write-Host "Your system appears to be ready for AI generation." -ForegroundColor Green
} else {
    Write-Host "⚠ Setup verification completed with issues." -ForegroundColor Yellow
    Write-Host "Please address the issues above before proceeding." -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "For detailed setup instructions, see: docs/18-AI-TOOLS-NVIDIA-SETUP.md" -ForegroundColor Gray

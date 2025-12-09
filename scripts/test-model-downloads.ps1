# Test Model Downloads Script
# Validates that all required models are downloaded and accessible

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# Import common library
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
$commonPath = Join-Path $rootPath "scripts\lib\common.ps1"
if (Test-Path $commonPath) {
    . $commonPath
} else {
    function Write-Info { param([string]$Msg) Write-Host "[INFO] $Msg" -ForegroundColor White }
    function Write-Success { param([string]$Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
    function Write-Warning { param([string]$Msg) Write-Host "[WARN] $Msg" -ForegroundColor Yellow }
    function Write-Error { param([string]$Msg) Write-Host "[ERR] $Msg" -ForegroundColor Red }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MODEL DOWNLOAD TEST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get paths
$root = if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$comfyPath = Join-Path $root "ComfyUI"

if (-not (Test-Path $comfyPath)) {
    Write-Error "ComfyUI bulunamadi: $comfyPath"
    exit 1
}

# Define required models
$requiredModels = @(
    @{
        Name = "Checkpoint Model"
        Path = Join-Path $comfyPath "models\checkpoints"
        Pattern = "*.safetensors,*.ckpt"
        Required = $true
        MinSizeMB = 1000
        Description = "Stable Diffusion checkpoint (e.g., Realistic Vision V6.0)"
    },
    @{
        Name = "InstantID ip-adapter"
        Path = Join-Path $comfyPath "models\instantid\ip-adapter.bin"
        Pattern = ""
        Required = $true
        MinSizeMB = 100
        Description = "InstantID adapter model"
    },
    @{
        Name = "Real-ESRGAN"
        Path = Join-Path $comfyPath "models\upscale_models\RealESRGAN_x4plus.pth"
        Pattern = ""
        Required = $false
        MinSizeMB = 50
        Description = "Upscaling model"
    },
    @{
        Name = "GFPGAN"
        Path = Join-Path $comfyPath "models\face_restore\GFPGANv1.4.pth"
        Pattern = ""
        Required = $false
        MinSizeMB = 300
        Description = "Face restoration model"
    },
    @{
        Name = "InsightFace"
        Path = Join-Path $comfyPath "models\insightface"
        Pattern = "*.onnx,*.param,*.bin"
        Required = $true
        MinSizeMB = 1
        Description = "Face analysis models (antelopev2)"
    }
)

$allPassed = $true
$results = @()

foreach ($model in $requiredModels) {
    $found = $false
    $sizeMB = 0
    $status = "MISSING"
    
    if ($model.Pattern) {
        # Directory check with pattern
        $patterns = $model.Pattern.Split(',') | ForEach-Object { $_.Trim() }
        $files = @()
        foreach ($pattern in $patterns) {
            $foundFiles = Get-ChildItem -Path $model.Path -Recurse -Filter $pattern -ErrorAction SilentlyContinue
            if ($foundFiles) {
                if ($foundFiles -is [array]) {
                    $files += $foundFiles
                } else {
                    $files += $foundFiles
                }
            }
        }
        if ($files -and $files.Count -gt 0) {
            $found = $true
            $sizeMB = ($files | Measure-Object -Property Length -Sum).Sum / 1MB
            $status = "FOUND"
        }
    } else {
        # File check
        if (Test-Path $model.Path) {
            $found = $true
            $sizeMB = (Get-Item $model.Path).Length / 1MB
            $status = "FOUND"
        }
    }
    
    # Validate size
    if ($found -and $sizeMB -lt $model.MinSizeMB -and $model.MinSizeMB -gt 0) {
        $status = "TOO_SMALL"
        Write-Warning "$($model.Name): Dosya cok kucuk ($([math]::Round($sizeMB, 2)) MB, minimum: $($model.MinSizeMB) MB)"
    }
    
    # Check if required
    if (-not $found -and $model.Required) {
        $allPassed = $false
        Write-Error "$($model.Name): EKSIK (GEREKLI)"
    } elseif (-not $found) {
        Write-Warning "$($model.Name): Eksik (opsiyonel)"
    } elseif ($status -eq "TOO_SMALL") {
        $allPassed = $false
        Write-Error "$($model.Name): Dosya boyutu yetersiz"
    } else {
        $sizeGB = $sizeMB / 1024
        if ($sizeGB -ge 1) {
            Write-Success "$($model.Name): Mevcut ($([math]::Round($sizeGB, 2)) GB)"
        } else {
            Write-Success "$($model.Name): Mevcut ($([math]::Round($sizeMB, 2)) MB)"
        }
    }
    
    $results += @{
        Name = $model.Name
        Found = $found
        SizeMB = $sizeMB
        Status = $status
        Required = $model.Required
        Description = $model.Description
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TEST SONUCLARI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Fix: Wrap in @() to ensure array for Count property
$requiredMissing = @($results | Where-Object { $_.Required -and -not $_.Found }).Count
$optionalMissing = @($results | Where-Object { -not $_.Required -and -not $_.Found }).Count

if ($allPassed -and $requiredMissing -eq 0) {
    Write-Success "Tum gerekli modeller mevcut!"
    Write-Host ""
    if ($optionalMissing -gt 0) {
        Write-Info "Opsiyonel modeller eksik ($optionalMissing), ancak gerekli degil"
    }
    exit 0
} else {
    Write-Error "Eksik modeller var!"
    Write-Host ""
    Write-Host "Eksik gerekli modeller:" -ForegroundColor Yellow
    $results | Where-Object { $_.Required -and -not $_.Found } | ForEach-Object {
        Write-Host "  - $($_.Name): $($_.Description)" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Cozum: .\download-models-auto.ps1 scriptini calistirin" -ForegroundColor Cyan
    exit 1
}

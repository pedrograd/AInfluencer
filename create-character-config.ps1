# ============================================
# AInfluencer - Karakter Konfigurasyon Olusturucu
# ============================================
# Interaktif olarak karakter konfigurasyonu olusturur

# PHASE 5: Parameter definition must be at the top
param(
    [Parameter(Mandatory=$false)]
    [string]$CharacterName = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# PHASE 1: UTF-8 encoding enforcement
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try { 
    chcp 65001 | Out-Null 
} catch {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}

# Simple path resolution
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = $scriptRoot

# PHASE 2: Get-PythonCmd pattern (prefer .venv)
function Get-PythonCmd {
    $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        return $venvPy
    }
    # Fallback to system Python
    return Ensure-PythonInstalled
}

# Simple logging functions (ASCII only)
function Write-Info { param([string]$Msg) Write-Host "[AInfluencer] $Msg" -ForegroundColor White }
function Write-Success { param([string]$Msg) Write-Host "[AInfluencer] OK  $Msg" -ForegroundColor Green }
function Write-Warning { param([string]$Msg) Write-Host "[AInfluencer] !   $Msg" -ForegroundColor Yellow }
function Write-Error { param([string]$Msg) Write-Host "[AInfluencer] ERR $Msg" -ForegroundColor Red }
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

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Karakter Konfigurasyon Olusturucu" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$charactersPath = Get-CharactersPath

try {
    # PHASE 7: Character name consistency - use provided name, don't ask again
    if ($NonInteractive -and [string]::IsNullOrWhiteSpace($CharacterName)) {
        Write-Error "Non-interactive mode requires CharacterName parameter!"
        exit 1
    }
    
    $name = if ($CharacterName) { $CharacterName } else { Read-Host "Karakter adi" }
    if ([string]::IsNullOrWhiteSpace($name)) {
        Write-Error "Karakter adi bos olamaz!"
        exit 1
    }
    
    # PHASE 7: Ensure we use the provided name, not a different one
    if ($CharacterName -and $name -ne $CharacterName) {
        Write-Warning "CharacterName parameter ($CharacterName) differs from input ($name), using parameter value"
        $name = $CharacterName
    }
    
    if ($NonInteractive) {
        # Use defaults for smoke test
        $age = "25"
        $height = "5'7"
        $build = "athletic"
        $eyes = "large hazel eyes"
        $nose = "straight, well-defined"
        $lips = "full, naturally pink"
        $hair = "long wavy chestnut brown hair"
        $skin = "smooth olive-toned skin"
        $faceRef = Join-Path $charactersPath "$name\face_reference.jpg"
        Write-Info "Non-interactive mode: Using defaults for $name"
    } else {
        $age = Read-Host "Yas"
        $height = Read-Host "Boy (orn: 5'7`")"
        $build = Read-Host "Vucut tipi (orn: athletic)"
        
        Write-Host ""
        Write-Host "Yuz ozellikleri:" -ForegroundColor Yellow
        $eyes = Read-Host "Gozler (orn: large hazel eyes)"
        $nose = Read-Host "Burun (orn: straight, well-defined)"
        $lips = Read-Host "Dudaklar (orn: full, naturally pink)"
        $hair = Read-Host "Sac (orn: long wavy chestnut brown hair)"
        $skin = Read-Host "Ten (orn: smooth olive-toned skin)"
        
        Write-Host ""
        $faceRef = Read-Host "Referans fotograf yolu (orn: characters/Model1/face_reference.jpg)"
    }
    
    # Base prompt olustur
    $basePrompt = "A $age-year-old woman, $build, $height, mixed heritage. $eyes, $nose, $lips, defined jawline, high cheekbones. $hair, parted to the side, soft texture. $skin, clear complexion, natural glow. Slender athletic frame, toned arms and legs."
    
    # Negative prompt (standart)
    $negativePrompt = "low quality, worst quality, normal quality, lowres, low details, oversaturated, undersaturated, bad anatomy, bad proportions, blurry, disfigured, deformed, ugly, mutated, extra limbs, missing limbs, floating limbs, disconnected limbs, malformed hands, out of focus, long neck, long body, monochrome, grayscale, sepia, watermark, signature, text, logo, cartoon, anime, painting, drawing, 3d render, cgi, computer graphics, unrealistic, fake, artificial, ai generated, ai art, synthetic, extra fingers, missing fingers, too many fingers, wrong number of fingers, distorted face, asymmetrical face, blurry face, pixelated, artifacts, compression artifacts, jpeg artifacts, noise, grain, exaggerated proportions, fake appearance, plastic skin, unnatural lighting, oversharpened, overprocessed"
    
    # Quality modifiers
    $qualityMods = "8k uhd, highly detailed, sharp focus, professional quality, photorealistic, ultra-realistic, perfect anatomy, flawless skin, natural skin texture, realistic lighting, accurate proportions, masterful quality, indistinguishable from real photo, authentic appearance"
    
    # JSON olustur
    $config = @{
        name = $name
        description = "Ultra realistic OnlyFans model karakteri"
        appearance = @{
            age = [int]$age
            ethnicity = "mixed heritage"
            height = $height
            build = $build
            face = @{
                eyes = $eyes
                nose = $nose
                lips = $lips
                skin = @{
                    tone = "olive"
                    texture = "smooth, clear"
                }
            }
            hair = @{
                color = "chestnut brown"
                length = "shoulder-length"
                style = "wavy"
            }
        }
        base_prompt = $basePrompt
        prompt_variations = @{
            portrait = "standing pose, one hand on hip, natural confident smile, looking directly at camera, professional posture"
            sitting = "sitting on edge of elegant bed, natural relaxed pose, gentle smile, looking away from camera, artistic composition"
            lifestyle = "wearing stylish casual outfit, standing in modern coffee shop, natural smile, looking at camera, relaxed confident pose"
            boudoir = "in elegant bedroom setting with soft fabrics, natural relaxed pose, gentle smile, artistic composition, intimate but elegant"
        }
        negative_prompt = $negativePrompt
        quality_modifiers = $qualityMods
        face_consistency = @{
            method = "InstantID"
            strength = 0.8
            reference_image = $faceRef
        }
        generation_settings = @{
            model = "Realistic Vision V6.0"
            steps = 40
            cfg_scale = 8.0
            sampler = "DPM++ 2M Karras"
            resolution = "768x768"
            seed = -1
        }
    } | ConvertTo-Json -Depth 10
    
    # Dosyaya kaydet
    $characterDir = Join-Path $charactersPath $name
    $outputFile = Join-Path $characterDir "config.json"
    
    try {
        New-Item -ItemType Directory -Path $characterDir -Force | Out-Null
        # Write without BOM to avoid JSON parsing issues
        [System.IO.File]::WriteAllText($outputFile, $config, [System.Text.UTF8Encoding]::new($false))
        Write-Success "Karakter konfigurasyonu olusturuldu: $outputFile"
    } catch {
        Write-Error "Dosya kaydedilemedi: $_"
        exit 1
    }
    
    Write-Host ""
    Write-Host "Sonraki adimlar:" -ForegroundColor Yellow
    
    # Get Python command for next steps
    $pythonCmd = Get-PythonCmd
    
    Write-Host "1. Referans fotografini yukle: $faceRef" -ForegroundColor Cyan
    Write-Host "2. Prompt'lar olustur: $pythonCmd generate-prompt-auto.py `"$outputFile`"" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Error "Karakter olusturma sirasinda hata: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}

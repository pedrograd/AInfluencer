# ============================================
# AInfluencer - Quick Generate Wrapper
# ============================================
# Shortcut for full-auto-generate.ps1
# Usage: .\gen.ps1 TestModel
#        .\gen.ps1 TestModel -count 1
#        .\gen.ps1 TestModel -test

param(
    [Parameter(Position=0, HelpMessage="Character name to generate images for")]
    [string]$CharacterName = "",
    
    [Parameter(HelpMessage="Number of images to generate (default: 10)")]
    [Alias("c", "count")]
    [int]$ImageCount = 10,
    
    [Parameter(HelpMessage="Run smoke test (1 image, quick validation)")]
    [Alias("t", "test")]
    [switch]$SmokeTest,
    
    [Parameter(HelpMessage="Skip setup checks")]
    [switch]$SkipSetup,
    
    [Parameter(HelpMessage="Skip post-processing")]
    [switch]$SkipPostProcess,
    
    [Parameter()]
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "AInfluencer - Quick Generate" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\gen.ps1 [CharacterName] [Options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\gen.ps1 TestModel" -ForegroundColor White
    Write-Host "  .\gen.ps1 TestModel -count 1" -ForegroundColor White
    Write-Host "  .\gen.ps1 TestModel -test" -ForegroundColor White
    Write-Host "  .\gen.ps1 TestModel -c 5" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -CharacterName, [Position 0]  Character name (will prompt if not provided)" -ForegroundColor White
    Write-Host "  -count, -c                     Number of images (default: 10)" -ForegroundColor White
    Write-Host "  -test, -t                      Smoke test mode (1 image)" -ForegroundColor White
    Write-Host "  -SkipSetup                     Skip setup checks" -ForegroundColor White
    Write-Host "  -SkipPostProcess               Skip post-processing" -ForegroundColor White
    Write-Host "  -Help, -?                      Show this help message" -ForegroundColor White
    Write-Host ""
    exit 0
}

$scriptPath = Join-Path $PSScriptRoot "full-auto-generate.ps1"

# Build arguments
$args = @()
if ($CharacterName) {
    $args += "-CharacterName", "`"$CharacterName`""
}
if ($ImageCount -ne 10) {
    $args += "-ImageCount", $ImageCount
}
if ($SmokeTest) {
    $args += "-SmokeTest"
}
if ($SkipSetup) {
    $args += "-SkipSetup"
}
if ($SkipPostProcess) {
    $args += "-SkipPostProcess"
}

# Call the main script
& $scriptPath @args

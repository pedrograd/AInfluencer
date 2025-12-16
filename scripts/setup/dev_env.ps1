# Development environment bootstrap (Windows)
# Usage: .\scripts\setup\dev_env.ps1

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..\..

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Development Environment Setup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Cyan
$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
}

if ($pythonCmd) {
    $pythonVersion = & $pythonCmd --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python 3 not found. Install from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Cyan
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js not found. Install from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check npm
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmVersion = npm --version
    Write-Host "✓ npm: $npmVersion" -ForegroundColor Green
} else {
    Write-Host "✗ npm not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
if (Test-Path "backend\requirements.txt") {
    & $pythonCmd -m pip install --user -r backend\requirements.txt
    Write-Host "✓ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠ backend\requirements.txt not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Installing Node.js dependencies..." -ForegroundColor Cyan
if (Test-Path "frontend\package.json") {
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "✓ Node.js dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠ frontend\package.json not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Recommended VS Code / Cursor Extensions" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Install these extensions for best experience:" -ForegroundColor Cyan
Write-Host "  - dbaeumer.vscode-eslint (ESLint)" -ForegroundColor White
Write-Host "  - esbenp.prettier-vscode (Prettier)" -ForegroundColor White
Write-Host "  - ms-python.python (Python)" -ForegroundColor White
Write-Host "  - yzhang.markdown-all-in-one (Markdown)" -ForegroundColor White
Write-Host ""
Write-Host "Extensions are recommended in .vscode/extensions.json" -ForegroundColor Cyan
Write-Host "VS Code/Cursor should prompt you to install them." -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠ Note: App-level Cursor settings (keybindings, themes, etc.)" -ForegroundColor Yellow
Write-Host "  cannot be synced across different Cursor accounts via git." -ForegroundColor Yellow
Write-Host "  Use repo-level configs (.vscode/settings.json) as source of truth." -ForegroundColor Yellow
Write-Host ""
Write-Host "✓ Setup complete!" -ForegroundColor Green


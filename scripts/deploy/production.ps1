# Production Deployment Script for AInfluencer (PowerShell)
# This script automates the production deployment process on Windows

param(
    [string]$DeployDir = "C:\AInfluencer",
    [string]$Domain = "your-domain.com"
)

$ErrorActionPreference = "Stop"

Write-Host "=== AInfluencer Production Deployment ===" -ForegroundColor Green

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run as Administrator" -ForegroundColor Red
    exit 1
}

# Step 1: Create deployment directory
Write-Host "Step 1: Creating deployment directory..." -ForegroundColor Yellow
if (-not (Test-Path $DeployDir)) {
    New-Item -ItemType Directory -Path $DeployDir -Force | Out-Null
}
Set-Location $DeployDir

# Step 2: Clone or update repository
Write-Host "Step 2: Setting up repository..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "Repository exists, pulling latest changes..."
    git pull
} else {
    Write-Host "Please clone the repository to $DeployDir first" -ForegroundColor Red
    exit 1
}

# Step 3: Set up backend
Write-Host "Step 3: Setting up backend..." -ForegroundColor Yellow
Set-Location "$DeployDir\backend"

# Create virtual environment
if (-not (Test-Path "venv")) {
    python -m venv venv
}

& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
    } else {
        @"
# Database
AINFLUENCER_DATABASE_URL=postgresql+asyncpg://ainfluencer_user:CHANGE_ME@localhost:5432/ainfluencer

# Redis
AINFLUENCER_REDIS_URL=redis://localhost:6379/0

# API
AINFLUENCER_API_SECRET_KEY=CHANGE_ME_GENERATE_SECURE_KEY
AINFLUENCER_DEBUG=False

# JWT
AINFLUENCER_JWT_SECRET_KEY=CHANGE_ME_GENERATE_SECURE_KEY
AINFLUENCER_JWT_ALGORITHM=HS256
AINFLUENCER_JWT_EXPIRATION_HOURS=24

# ComfyUI
AINFLUENCER_COMFYUI_BASE_URL=http://localhost:8188

# Storage
AINFLUENCER_STORAGE_TYPE=local
AINFLUENCER_STORAGE_PATH=C:\AInfluencer\storage\content
"@ | Out-File -FilePath ".env" -Encoding UTF8
    }
    Write-Host "Please edit $DeployDir\backend\.env with your production configuration" -ForegroundColor Yellow
}

# Run database migrations
Write-Host "Running database migrations..."
alembic upgrade head

# Step 4: Set up frontend
Write-Host "Step 4: Setting up frontend..." -ForegroundColor Yellow
Set-Location "$DeployDir\frontend"

# Install dependencies
npm ci

# Build frontend
npm run build

# Set up environment variables
if (-not (Test-Path ".env.local")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env.local"
    } else {
        "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" | Out-File -FilePath ".env.local" -Encoding UTF8
    }
    Write-Host "Please edit $DeployDir\frontend\.env.local with your production configuration" -ForegroundColor Yellow
}

# Step 5: Create Windows Service scripts
Write-Host "Step 5: Creating Windows Service configuration..." -ForegroundColor Yellow

# Backend service script
$backendServiceScript = @"
@echo off
cd /d $DeployDir\backend
call venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 8000
"@
$backendServiceScript | Out-File -FilePath "$DeployDir\backend\start-backend.bat" -Encoding ASCII

# Frontend service script
$frontendServiceScript = @"
@echo off
cd /d $DeployDir\frontend
call npm start
"@
$frontendServiceScript | Out-File -FilePath "$DeployDir\frontend\start-frontend.bat" -Encoding ASCII

# NSSM (Non-Sucking Service Manager) installation instructions
Write-Host ""
Write-Host "To run as Windows Services, install NSSM:" -ForegroundColor Yellow
Write-Host "  1. Download NSSM from https://nssm.cc/download"
Write-Host "  2. Extract and add to PATH"
Write-Host "  3. Install backend service:"
Write-Host "     nssm install AInfluencerBackend `"$DeployDir\backend\start-backend.bat`""
Write-Host "  4. Install frontend service:"
Write-Host "     nssm install AInfluencerFrontend `"$DeployDir\frontend\start-frontend.bat`""
Write-Host "  5. Start services:"
Write-Host "     nssm start AInfluencerBackend"
Write-Host "     nssm start AInfluencerFrontend"

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit $DeployDir\backend\.env with your production configuration"
Write-Host "  2. Edit $DeployDir\frontend\.env.local with your production configuration"
Write-Host "  3. Set up Windows Services using NSSM (see instructions above)"
Write-Host "  4. Configure IIS or another reverse proxy for production"


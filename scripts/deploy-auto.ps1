[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\Users\vandan\AInfluencer",
    [int]$DockerWaitSeconds = 120
)

$ErrorActionPreference = "Stop"

function Ensure-Elevated {
    param(
        [string]$ProjectRoot,
        [int]$DockerWaitSeconds
    )
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "Re-launching as Administrator..."
        $argsList = "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -ProjectRoot `"$ProjectRoot`" -DockerWaitSeconds $DockerWaitSeconds"
        Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $argsList | Out-Null
        exit 0
    }
}

function Require-Admin {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Error "Run this script in an elevated PowerShell window (Administrator)."
        exit 1
    }
}

function Ensure-FeatureEnabled {
    param([string]$FeatureName)
    $feature = Get-WindowsOptionalFeature -Online -FeatureName $FeatureName
    if ($feature.State -ne "Enabled") {
        Write-Host "Enabling Windows feature: $FeatureName ..."
        dism.exe /online /enable-feature /featurename:$FeatureName /all /norestart | Out-Null
    }
}

function Ensure-WSL {
    Write-Host "Checking WSL installation..."
    Ensure-FeatureEnabled -FeatureName "Microsoft-Windows-Subsystem-Linux"
    Ensure-FeatureEnabled -FeatureName "VirtualMachinePlatform"
    try {
        $distros = wsl -l -q
        if (-not ($distros -match "^Ubuntu")) {
            Write-Host "Installing Ubuntu for WSL..."
            wsl --install -d Ubuntu
        }
    } catch {
        Write-Error "WSL not available. Reboot may be required after enabling features."
        exit 1
    }
    Write-Host "Setting WSL default version to 2..."
    wsl --set-default-version 2 | Out-Null
}

function Ensure-DockerDesktop {
    $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerExe)) {
        Write-Host "Installing Docker Desktop via winget..."
        winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
    }
    return $dockerExe
}

function Start-DockerDesktop {
    param([string]$DockerExe, [int]$TimeoutSeconds)
    if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) {
        Write-Host "Starting Docker Desktop..."
        Start-Process $DockerExe | Out-Null
    }
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            docker info | Out-Null
            Write-Host "Docker engine is ready."
            return
        } catch {
            Start-Sleep -Seconds 5
        }
    } while ((Get-Date) -lt $deadline)
    Write-Error "Docker engine did not start within $TimeoutSeconds seconds."
    exit 1
}

function Compose-Up {
    param([string]$RootPath)
    $envPath = Join-Path $RootPath ".env"
    if (-not (Test-Path $envPath)) {
        Write-Error "Missing .env at $envPath"
        exit 1
    }
    Write-Host "Bringing up production stack with docker-compose..."
    docker compose --env-file $envPath -f (Join-Path $RootPath "docker-compose.yml") -f (Join-Path $RootPath "docker-compose.prod.yml") up -d --build
    Write-Host "`nContainer status:"
    docker compose -f (Join-Path $RootPath "docker-compose.yml") ps
    Write-Host "`nRunning containers (docker ps):"
    docker ps
}

Ensure-Elevated -ProjectRoot $ProjectRoot -DockerWaitSeconds $DockerWaitSeconds
Require-Admin
Ensure-WSL
$dockerExe = Ensure-DockerDesktop
Start-DockerDesktop -DockerExe $dockerExe -TimeoutSeconds $DockerWaitSeconds
Compose-Up -RootPath $ProjectRoot

Write-Host "`nNext checks (run manually):"
Write-Host "  curl -f https://your-domain/health"
Write-Host "  curl -f https://your-domain/api/health"
Write-Host "Prometheus: https://your-domain:9090"
Write-Host "Grafana:    https://your-domain:3001"

# Stop All Services - AInfluencer Platform
# Gracefully stops all running services

$ErrorActionPreference = "Stop"

Write-Host "🛑 Stopping AInfluencer Platform..." -ForegroundColor Cyan
Write-Host ""

# Function to stop job by ID
function Stop-ServiceJob {
    param([int]$JobId, [string]$ServiceName)
    
    $job = Get-Job -Id $JobId -ErrorAction SilentlyContinue
    if ($job) {
        Write-Host "   Stopping $ServiceName (Job ID: $JobId)..." -ForegroundColor Yellow
        Stop-Job -Id $JobId -ErrorAction SilentlyContinue
        Remove-Job -Id $JobId -Force -ErrorAction SilentlyContinue
        Write-Host "   ✅ $ServiceName stopped" -ForegroundColor Green
    }
}

# Load job IDs from file
$jobsFile = ".service-jobs.json"
if (Test-Path $jobsFile) {
    $jobs = Get-Content $jobsFile | ConvertFrom-Json
    
    if ($jobs.ComfyUI) {
        Stop-ServiceJob -JobId $jobs.ComfyUI -ServiceName "ComfyUI"
    }
    if ($jobs.Backend) {
        Stop-ServiceJob -JobId $jobs.Backend -ServiceName "Backend API"
    }
    if ($jobs.Frontend) {
        Stop-ServiceJob -JobId $jobs.Frontend -ServiceName "Frontend"
    }
    
    Remove-Item $jobsFile -Force -ErrorAction SilentlyContinue
}

# Also check for any remaining jobs
$remainingJobs = Get-Job | Where-Object { 
    $_.Name -like "*ComfyUI*" -or 
    $_.Name -like "*Backend*" -or 
    $_.Name -like "*Frontend*" -or
    $_.Command -like "*uvicorn*" -or
    $_.Command -like "*npm*" -or
    $_.Command -like "*main.py*"
}

if ($remainingJobs) {
    Write-Host ""
    Write-Host "   Found additional service jobs, stopping..." -ForegroundColor Yellow
    $remainingJobs | ForEach-Object {
        Stop-Job -Id $_.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

# Stop Docker services if running
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host ""
    Write-Host "🐳 Stopping Docker services..." -ForegroundColor Cyan
    
    $dockerServices = @("redis", "postgres", "backend", "web", "nginx", "prometheus", "grafana")
    foreach ($service in $dockerServices) {
        $container = docker ps -a --filter "name=$service" --format "{{.Names}}" 2>$null
        if ($container) {
            Write-Host "   Stopping $service..." -ForegroundColor Yellow
            docker stop $container 2>$null | Out-Null
            Write-Host "   ✅ $service stopped" -ForegroundColor Green
        }
    }
}

# Kill processes on ports (fallback)
Write-Host ""
Write-Host "🔍 Checking for processes on service ports..." -ForegroundColor Cyan

$ports = @(
    @{Port = 8188; Service = "ComfyUI"},
    @{Port = 8000; Service = "Backend API"},
    @{Port = 3000; Service = "Frontend"}
)

foreach ($portInfo in $ports) {
    $port = $portInfo.Port
    $service = $portInfo.Service
    
    try {
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connection) {
            $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "   Found $service process (PID: $($process.Id)) on port $port" -ForegroundColor Yellow
                Write-Host "   ⚠️  Process may need manual termination: Stop-Process -Id $($process.Id) -Force" -ForegroundColor Yellow
            }
        }
    } catch {
        # Port not in use or access denied
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Shutdown Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "All services have been stopped." -ForegroundColor White
Write-Host ""
Write-Host "To start services again, run:" -ForegroundColor Yellow
Write-Host "  .\start-all.ps1" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

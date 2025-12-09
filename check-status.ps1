# Quick Status Checker for AInfluencer Services
Write-Host "`n=== AInfluencer Service Status ===" -ForegroundColor Cyan
Write-Host ""

# Check Backend
Write-Host "Checking Backend (port 8000)..." -ForegroundColor Yellow
try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "✅ Backend is RUNNING!" -ForegroundColor Green
    Write-Host "   URL: http://localhost:8000" -ForegroundColor Gray
    Write-Host "   Status: $($backendResponse.StatusCode)" -ForegroundColor Gray
    $backendRunning = $true
} catch {
    Write-Host "❌ Backend is NOT running" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    $backendRunning = $false
}

Write-Host ""

# Check Frontend
Write-Host "Checking Frontend (port 3000)..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "✅ Frontend is RUNNING!" -ForegroundColor Green
    Write-Host "   URL: http://localhost:3000" -ForegroundColor Gray
    Write-Host "   Status: $($frontendResponse.StatusCode)" -ForegroundColor Gray
    $frontendRunning = $true
} catch {
    Write-Host "❌ Frontend is NOT running" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    $frontendRunning = $false
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if ($backendRunning -and $frontendRunning) {
    Write-Host "🎉 All services are running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access your application at:" -ForegroundColor Cyan
    Write-Host "  • Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "  • Backend API: http://localhost:8000" -ForegroundColor White
    Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    $open = Read-Host "Open browser? (Y/N)"
    if ($open -eq "Y" -or $open -eq "y") {
        Start-Process "http://localhost:3000"
    }
} else {
    Write-Host "⚠️  Some services are not running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Cyan
    if (-not $backendRunning) {
        Write-Host "  • Check the 'Backend Server' command window for errors" -ForegroundColor Yellow
        Write-Host "  • Try: cd backend && pip install -r requirements.txt" -ForegroundColor Gray
    }
    if (-not $frontendRunning) {
        Write-Host "  • Check the 'Frontend Server' command window for errors" -ForegroundColor Yellow
        Write-Host "  • Try: cd web && npm install" -ForegroundColor Gray
    }
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# PowerShell script to run endpoint tests

Write-Host "🧪 Starting Endpoint Tests..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Server is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Server is not running. Please start the backend server first:" -ForegroundColor Red
    Write-Host "   cd backend && python -m uvicorn main:app --reload" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Run pytest
python -m pytest backend/tests/test_all_endpoints.py -v -s

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ Tests Complete" -ForegroundColor Green

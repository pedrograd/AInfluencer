@echo off
title AInfluencer Startup
color 0A

echo ========================================
echo   AInfluencer Application Startup
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Stopping existing services...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main.py*" 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *npm*" 2>nul
timeout /t 1 /nobreak >nul

echo [2/4] Starting Backend Server...
start "AInfluencer Backend - Port 8000" cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak >nul

echo [3/4] Starting Frontend Server...
start "AInfluencer Frontend - Port 3000" cmd /k "cd web && npm run dev"
timeout /t 8 /nobreak >nul

echo [4/4] Checking services...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Services Started!
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo   Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo   Check the command windows for any errors.
echo   Press any key to close this window...
pause >nul

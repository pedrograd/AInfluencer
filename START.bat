@echo off
echo ========================================
echo   AInfluencer - One-Click Start
echo ========================================
echo.
echo Running comprehensive fix and start...
echo.

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File ".\fix-all-automatic.ps1"

pause

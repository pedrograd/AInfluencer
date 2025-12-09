@echo off
REM AInfluencer - Master Setup (Batch Wrapper)
REM This runs the PowerShell master setup script

echo ========================================
echo   AInfluencer - Master Setup
echo ========================================
echo.

REM Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PowerShell is not available!
    echo Please install PowerShell and try again.
    pause
    exit /b 1
)

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0MASTER-SETUP.ps1"

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Setup completed with errors. Check the output above.
    pause
)

@echo off
REM Windows entry point - double-click friendly launcher
REM This file calls the PowerShell orchestrator

cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "%~dp0launch.ps1"
if errorlevel 1 (
    pause
)


@echo off
REM DEPRECATED: Use SYNC.bat instead
REM Entrypoint for follower sync (Windows)
REM Usage: SYNC-FOLLOWER.bat

echo WARNING: This script is DEPRECATED. Use SYNC.bat instead.
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "scripts\sync\follower-pull.ps1"


@echo off
REM Entrypoint for follower sync (Windows)
REM Usage: SYNC-FOLLOWER.bat

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "scripts\sync\follower-pull.ps1"


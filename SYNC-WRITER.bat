@echo off
REM DEPRECATED: Use SYNC.bat with SYNC_ROLE=WRITER instead
REM Entrypoint for writer sync (Windows)
REM Usage: SYNC-WRITER.bat

echo WARNING: This script is DEPRECATED. Use "set SYNC_ROLE=WRITER && SYNC.bat" instead.
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "scripts\sync\writer-sync.ps1"


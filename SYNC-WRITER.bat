@echo off
REM Entrypoint for writer sync (Windows)
REM Usage: SYNC-WRITER.bat

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "scripts\sync\writer-sync.ps1"


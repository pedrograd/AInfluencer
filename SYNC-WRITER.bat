@echo off
REM Entrypoint for writer push (Windows)
REM Usage: SYNC-WRITER.bat

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "scripts\sync\writer-push.ps1"


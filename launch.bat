@echo off
REM Windows entry point - double-click friendly launcher
REM This file calls the canonical Node.js orchestrator

cd /d "%~dp0"
node scripts/one.mjs
if errorlevel 1 (
    pause
)


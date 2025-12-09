@echo off
REM Quick shortcut for image generation
powershell -ExecutionPolicy Bypass -File "%~dp0gen.ps1" %*

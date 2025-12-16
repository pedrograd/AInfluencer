@echo off
REM Single-command sync entrypoint (Windows)
REM Usage: SYNC.bat
REM Or: set SYNC_ROLE=WRITER && SYNC.bat

cd /d "%~dp0"
python scripts\sync\sync_one.py %*


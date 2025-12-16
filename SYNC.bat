@echo off
REM Single-command sync entrypoint (Windows)
REM Usage: SYNC.bat
REM Or: set SYNC_ROLE=WRITER && SYNC.bat

cd /d "%~dp0"

REM Try python3 first, then python, then py -3
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python3 scripts\sync\sync_one.py %*
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        python scripts\sync\sync_one.py %*
    ) else (
        py -3 scripts\sync\sync_one.py %*
    )
)


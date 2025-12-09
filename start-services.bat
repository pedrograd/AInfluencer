@echo off
echo ========================================
echo   Starting AInfluencer Services
echo ========================================
echo.

cd /d "%~dp0"

REM Check for virtual environment
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
    set PIP_CMD=.venv\Scripts\pip.exe
    echo Using virtual environment
) else (
    set PYTHON_CMD=python
    set PIP_CMD=pip
    echo Using system Python
)
set VENV_PYTHON=%PYTHON_CMD%

REM Install backend dependencies if needed
echo Checking backend dependencies...
%PYTHON_CMD% -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Installing backend dependencies...
    cd backend
    %PIP_CMD% install -r requirements.txt
    cd ..
)

REM Install frontend dependencies if needed
if not exist "web\node_modules" (
    echo Installing frontend dependencies...
    cd web
    call npm install
    cd ..
)

echo.
echo [1/2] Starting Backend on port 8000...
echo    Window will stay open to show any errors
start "AInfluencer Backend - Port 8000" cmd /k "cd /d %~dp0backend && %VENV_PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul

echo [2/2] Starting Frontend on port 3000...
echo    Window will stay open to show any errors
start "AInfluencer Frontend - Port 3000" cmd /k "cd /d %~dp0web && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   Services Starting...
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo   Check the command windows for any errors.
echo   If you see errors, the services may need:
echo   - Backend: pip install -r backend/requirements.txt
echo   - Frontend: cd web && npm install
echo.
echo   Waiting 15 seconds, then opening browser...
timeout /t 15 /nobreak >nul
start http://localhost:3000

echo.
echo   Done! Services should be running.
echo   Press any key to close this window...
pause >nul

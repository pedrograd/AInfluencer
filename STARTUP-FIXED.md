# AInfluencer Startup - Fixed

## ✅ What Was Fixed

1. **Backend startup** - Now uses `uvicorn` directly instead of `python main.py` (more reliable)
2. **Virtual environment detection** - Automatically detects and uses `.venv` if it exists
3. **Dependency installation** - Automatically installs missing dependencies
4. **Port management** - Kills processes on ports 8000 and 3000 before starting
5. **Error visibility** - Services run in separate windows so you can see errors

## 🚀 How to Start

### Option 1: Auto-Start Script (Recommended)
```powershell
.\start-app-auto.ps1
```

This script will:
- ✅ Check Python and Node.js
- ✅ Install backend dependencies if needed
- ✅ Install frontend dependencies if needed
- ✅ Kill any processes on ports 8000/3000
- ✅ Start backend in a separate window
- ✅ Start frontend in a separate window
- ✅ Wait for services to be ready
- ✅ Open browser automatically

### Option 2: Batch File
```cmd
START-SERVICES.bat
```

### Option 3: PowerShell Script
```powershell
.\start-all.ps1
```

## 📋 Manual Start (If Scripts Don't Work)

### Backend
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or with virtual environment:
```powershell
cd backend
..\..venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```powershell
cd web
npm run dev
```

## 🔍 Check Status

Run the status checker:
```powershell
.\check-status.ps1
```

Or manually check:
- Backend: http://localhost:8000/api/health
- Frontend: http://localhost:3000

## 🐛 Troubleshooting

### Backend won't start
1. Check the "Backend Server" window for errors
2. Install dependencies: `cd backend && pip install -r requirements.txt`
3. Check if port 8000 is in use: `netstat -ano | findstr :8000`

### Frontend won't start
1. Check the "Frontend Server" window for errors
2. Install dependencies: `cd web && npm install`
3. Check if port 3000 is in use: `netstat -ano | findstr :3000`

### Port already in use
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
# Kill it (replace PID)
Stop-Process -Id <PID> -Force

# Or use the auto-start script which handles this automatically
```

## 📝 Notes

- Services run in **separate command windows** so you can see logs and errors
- The windows will stay open even if there are errors
- Use `Ctrl+C` in the windows to stop the services
- The auto-start script handles virtual environments automatically

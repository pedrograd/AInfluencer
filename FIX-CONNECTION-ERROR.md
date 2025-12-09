# Fix Connection Error - ERR_CONNECTION_REFUSED

## Problem
You're getting `ERR_CONNECTION_REFUSED` when trying to access `http://localhost:3001/`

## Root Cause
The frontend runs on **port 3000** by default, not 3001. The error occurs because:
1. No service is running on port 3001
2. The frontend is configured to run on port 3000

## Solution

### ✅ Quick Fix (Recommended)
Run this single command:
```powershell
.\QUICK-START.ps1
```

This will:
- Stop any conflicting processes
- Install missing dependencies
- Start backend on port 8000
- Start frontend on port 3000
- Open your browser automatically

### ✅ Manual Fix

**Step 1: Stop existing processes**
```powershell
# Stop processes on ports 3000, 3001, 8000
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

**Step 2: Start Backend**
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Step 3: Start Frontend (in a new terminal)**
```powershell
cd web
npm run dev
```

**Step 4: Access the application**
Open your browser and go to:
```
http://localhost:3000
```

## If You Need Port 3001

If you specifically need to run on port 3001:

```powershell
cd web
npm run dev:3001
```

Then access:
```
http://localhost:3001
```

## Verify Services Are Running

Check if services are accessible:
```powershell
# Check Backend
Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing

# Check Frontend
Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
```

## Common Issues

### Issue 1: Port Already in Use
**Solution**: Stop the process using the port:
```powershell
# Find process on port 3000
Get-NetTCPConnection -LocalPort 3000 | Select-Object OwningProcess

# Stop it (replace PID with actual process ID)
Stop-Process -Id <PID> -Force
```

### Issue 2: Dependencies Missing
**Solution**: Install dependencies:
```powershell
# Frontend
cd web
npm install

# Backend
cd backend
pip install -r requirements.txt
```

### Issue 3: Environment Variables Missing
**Solution**: Create `web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Issue 4: Backend Not Starting
**Solution**: Check Python and dependencies:
```powershell
# Check Python
python --version

# Check if FastAPI is installed
python -c "import fastapi; print('OK')"

# Install if missing
pip install fastapi uvicorn
```

## Summary

| Service | Default Port | URL |
|---------|-------------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 8000 | http://localhost:8000 |
| ComfyUI | 8188 | http://127.0.0.1:8188 |

**Remember**: Use port **3000** for the frontend, not 3001!

## Still Having Issues?

1. Run `.\fix-connection-issues.ps1` to diagnose problems
2. Check the terminal windows for error messages
3. Verify all dependencies are installed
4. Check firewall settings
5. Make sure no antivirus is blocking the ports

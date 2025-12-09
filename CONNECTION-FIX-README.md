# Connection Issues Fix Guide

## Problem
You're trying to access `http://localhost:3001/` but getting `ERR_CONNECTION_REFUSED`.

## Solution

### Option 1: Use Port 3000 (Recommended)
The frontend runs on **port 3000** by default. Simply access:
```
http://localhost:3000
```

### Option 2: Run on Port 3001
If you specifically need port 3001, run:
```powershell
.\start-frontend-3001.ps1
```
Or manually:
```powershell
cd web
npm run dev:3001
```

## Quick Fix Script

Run this to automatically fix all connection issues:
```powershell
.\fix-connection-issues.ps1
```

This script will:
- ✅ Stop processes blocking ports 3000, 3001, 8000, 8188
- ✅ Check Node.js and Python installations
- ✅ Install missing dependencies
- ✅ Create environment configuration files
- ✅ Verify everything is ready

## Start All Services

After running the fix script, start all services:
```powershell
.\start-all.ps1
```

This will start:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **ComfyUI**: http://127.0.0.1:8188

## Manual Start (If Scripts Don't Work)

### 1. Start Backend
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start Frontend (Port 3000)
```powershell
cd web
npm run dev
```

### 3. Start Frontend (Port 3001)
```powershell
cd web
npm run dev:3001
```

## Troubleshooting

### Port Already in Use
If you get "port already in use" errors:
```powershell
# Stop processes on specific ports
Get-NetTCPConnection -LocalPort 3000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
Get-NetTCPConnection -LocalPort 3001 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

### Missing Dependencies
```powershell
# Frontend
cd web
npm install

# Backend
cd backend
pip install -r requirements.txt
```

### Check Service Status
```powershell
# Check if services are running
Test-NetConnection -ComputerName localhost -Port 3000
Test-NetConnection -ComputerName localhost -Port 8000
Test-NetConnection -ComputerName localhost -Port 8188
```

## Environment Configuration

Make sure `web/.env.local` exists with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The fix script will create this automatically.

## Common Issues

1. **ERR_CONNECTION_REFUSED**: Service isn't running. Start it first.
2. **Port 3001 not working**: Use port 3000 instead, or run `npm run dev:3001`
3. **Backend not responding**: Check if backend is running on port 8000
4. **CORS errors**: Make sure backend is running and `NEXT_PUBLIC_API_URL` is correct

## Need Help?

1. Run `.\fix-connection-issues.ps1` first
2. Check service logs in the terminal windows
3. Verify all ports are accessible
4. Check firewall settings if accessing from another device

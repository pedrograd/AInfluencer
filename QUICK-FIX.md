# Quick Fix Guide

## Issues Fixed

1. **Pillow version conflict** - Changed from `Pillow==10.1.0` to `Pillow==10.0.1` (compatible with imageio)
2. **Missing uvicorn** - Added installation of uvicorn before other dependencies

## Quick Start (After Fix)

Run this command to fix dependencies and start services:

```powershell
.\fix-and-start.ps1
```

Or manually:

### 1. Install Critical Packages First
```powershell
.venv\Scripts\pip.exe install uvicorn[standard]==0.24.0 fastapi==0.104.1
.venv\Scripts\pip.exe install Pillow==10.0.1
```

### 2. Install All Dependencies
```powershell
.venv\Scripts\pip.exe install -r backend\requirements.txt
```

### 3. Start Backend
```powershell
cd backend
..\..venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start Frontend (in another terminal)
```powershell
cd web
npm run dev
```

## What Was Wrong

1. **Pillow 10.1.0** conflicts with **imageio 2.31.6** which requires `pillow<10.1.0`
2. **uvicorn** wasn't installed, causing "No module named uvicorn" error

## Fixed Files

- `backend/requirements.txt` - Pillow version changed to 10.0.1
- `fix-and-start.ps1` - New script that fixes and starts everything

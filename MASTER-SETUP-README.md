# 🚀 MASTER SETUP SCRIPT - Complete Guide

## Overview

The `MASTER-SETUP.ps1` script is a **one-command solution** that automates the entire AInfluencer setup process. It combines all setup, installation, testing, and startup steps into a single, easy-to-use script.

## What It Does

The master setup script performs these steps automatically:

1. ✅ **System Prerequisites Check**
   - Python 3.10+ (with virtual environment support)
   - Node.js (for frontend)
   - Git (for ComfyUI)
   - GPU detection (NVIDIA)

2. ✅ **Environment Setup**
   - Creates Python virtual environment (`.venv`)
   - Upgrades pip to latest version

3. ✅ **ComfyUI Setup**
   - Clones ComfyUI from GitHub (if not present)
   - Installs ComfyUI Python dependencies

4. ✅ **Backend Setup**
   - Installs all backend Python packages from `backend/requirements.txt`
   - Installs base requirements

5. ✅ **Frontend Setup**
   - Installs Node.js dependencies (`npm install`)

6. ✅ **Directory Structure**
   - Creates all required directories (characters, output folders, etc.)

7. ✅ **Model Downloads**
   - Downloads all required AI models (checkpoints, IP-Adapter, InstantID, etc.)
   - This step can take 10-30 minutes depending on internet speed

8. ✅ **Testing**
   - Runs all tests (backend, frontend, integration)

9. ✅ **Service Startup**
   - Starts ComfyUI (port 8188)
   - Starts Backend API (port 8000)
   - Starts Frontend (port 3000)

10. ✅ **Browser Launch**
    - Automatically opens the web interface in your default browser

## Usage

### Basic Usage (Recommended)

```powershell
.\MASTER-SETUP.ps1
```

Or simply **double-click** `MASTER-SETUP.bat`

### Advanced Usage with Flags

```powershell
# Skip tests (faster setup)
.\MASTER-SETUP.ps1 -SkipTests

# Skip model downloads (if you already have models)
.\MASTER-SETUP.ps1 -SkipModels

# Skip service startup (setup only)
.\MASTER-SETUP.ps1 -SkipServices

# Skip browser launch
.\MASTER-SETUP.ps1 -SkipBrowser

# Force reinstall (removes existing virtual environment)
.\MASTER-SETUP.ps1 -ForceReinstall

# Combine multiple flags
.\MASTER-SETUP.ps1 -SkipTests -SkipBrowser
```

## Prerequisites

Before running the master setup, ensure you have:

- **Python 3.10+** - Download from https://www.python.org/downloads/
  - ⚠️ Important: Check "Add Python to PATH" during installation
- **Node.js 18+** - Download from https://nodejs.org/
- **Git** - Download from https://git-scm.com/ (required for ComfyUI)
- **NVIDIA GPU** (optional but recommended) - For faster image generation

## What to Expect

### First Run (Full Setup)

- **Duration**: 15-45 minutes (depending on internet speed and system performance)
- **Steps**: All 10 steps will run
- **Downloads**: ~5-10 GB of AI models will be downloaded
- **Services**: All services will start automatically
- **Browser**: Web interface will open automatically

### Subsequent Runs

- **Duration**: 2-5 minutes (only checks and updates)
- **Steps**: Only missing components are installed/updated
- **Downloads**: Only missing models are downloaded
- **Services**: Only stopped services are started

## Troubleshooting

### Python Not Found

If you see "Python not found":
1. Install Python from https://www.python.org/downloads/
2. Make sure to check "Add Python to PATH" during installation
3. Restart PowerShell/terminal after installation
4. Run the script again

### Node.js Not Found

If you see "Node.js not found":
1. Install Node.js from https://nodejs.org/
2. Restart PowerShell/terminal after installation
3. Run the script again

### Port Already in Use

If you see "Port already in use":
- The script will detect running services and skip starting them
- To stop all services: `.\stop-all.ps1`
- Then run the master setup again

### Model Download Fails

If model downloads fail:
1. Check your internet connection
2. Run manually: `.\download-models-auto.ps1`
3. Some models may require manual download (script will provide links)

### Services Don't Start

If services don't start:
1. Check the error messages in the service windows
2. Verify ports 8188, 8000, and 3000 are not in use
3. Check `.\health-check.ps1` for detailed status
4. Try starting manually: `.\start-all.ps1`

## Manual Steps (If Needed)

If the automated setup fails, you can run steps manually:

1. **Setup**: `.\auto-complete-setup.ps1`
2. **Models**: `.\download-models-auto.ps1`
3. **Start**: `.\start-all.ps1`
4. **Test**: `.\test-all.ps1`
5. **Health**: `.\health-check.ps1`

## Service URLs

After successful setup, access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ComfyUI**: http://127.0.0.1:8188

## Next Steps

After setup completes:

1. **Create a Character**: `.\create-character-config.ps1`
2. **Generate Images**: `.\gen.ps1 CharacterName -count 10`
3. **Read Documentation**: See `SETUP.md` and `docs/` folder

## Command Reference

```powershell
# Full setup (everything)
.\MASTER-SETUP.ps1

# Setup only (no services)
.\MASTER-SETUP.ps1 -SkipServices -SkipBrowser

# Quick setup (skip tests and models)
.\MASTER-SETUP.ps1 -SkipTests -SkipModels

# Reinstall everything
.\MASTER-SETUP.ps1 -ForceReinstall

# Stop all services
.\stop-all.ps1

# Check system health
.\health-check.ps1

# Run tests
.\test-all.ps1
```

## Support

If you encounter issues:

1. Check `docs/30-TROUBLESHOOTING-COMPLETE.md` for detailed troubleshooting
2. Review the error messages in the script output
3. Check service logs in the opened windows
4. Run `.\health-check.ps1` to diagnose issues

---

**Happy generating! 🎨**

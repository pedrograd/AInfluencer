# 🚀 AInfluencer Setup Guide

Complete setup instructions for the AInfluencer platform.

## 📋 Prerequisites

- **Python 3.10+** installed
- **NVIDIA GPU** (RTX 3060+ recommended, 8GB+ VRAM)
- **Git** installed
- **NVIDIA Drivers** installed
- **CUDA Toolkit** (optional but recommended)

### Quick Prerequisites Check

```powershell
python --version
git --version
nvidia-smi
```

---

## ⚡ Quick Start (3 Steps)

### Step 1: Complete Setup (First Time Only)

```powershell
.\setup.ps1
```

This automated script will:
- ✅ Check and install Python if needed
- ✅ Clone/verify ComfyUI
- ✅ Install all required extensions (IP-Adapter, InstantID, AnimateDiff)
- ✅ Install Python dependencies
- ✅ Set up directory structure
- ✅ Verify installation

### Step 2: Download Models

```powershell
.\download-models.ps1
```

This will download:
- ✅ Stable Diffusion checkpoint models
- ✅ IP-Adapter models (for face consistency)
- ✅ Video generation models (if requested)
- ✅ Upscaling models

### Step 3: Create Character & Generate

```powershell
# Create a character (first time)
.\create-character-config.ps1

# Generate images
.\gen.ps1 CharacterName -count 10
```

---

## 🔧 Manual Setup (If Needed)

### Install ComfyUI

If ComfyUI is not automatically set up:

```powershell
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
python -m pip install -r requirements.txt
```

### Install Extensions

ComfyUI custom nodes:

1. **IP-Adapter Plus** (Face Consistency)
   ```powershell
   cd ComfyUI\custom_nodes
   git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git
   cd ComfyUI_IPAdapter_plus
   pip install -r requirements.txt
   ```

2. **InstantID** (Better Face Control)
   ```powershell
   cd ComfyUI\custom_nodes
   git clone https://github.com/cubiq/ComfyUI_InstantID.git
   cd ComfyUI_InstantID
   pip install -r requirements.txt
   ```

3. **AnimateDiff** (Video Generation)
   ```powershell
   cd ComfyUI\custom_nodes
   git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git
   cd ComfyUI-AnimateDiff-Evolved
   pip install -r requirements.txt
   ```

---

## 📦 Required Models

### Checkpoint Models (Required)

Place in `ComfyUI/models/checkpoints/`:
- **Realistic Vision V6.0** (Recommended) - `realisticVisionV60B1_v51HyperInpaintVAE.safetensors`
- Alternative: Juggernaut XL, DreamShaper XL

### IP-Adapter Models (For Face Consistency)

Place in `ComfyUI/models/ip-adapter/`:
- `ip-adapter_sdxl.safetensors` (SDXL)
- `ip-adapter_sd15.safetensors` (SD 1.5)

Download from: https://huggingface.co/h94/IP-Adapter

### Video Models (Optional)

Place in `ComfyUI/models/animatediff/`:
- AnimateDiff motion models

---

## 🚀 Starting Services

### Start All Services

```powershell
.\start-all.ps1
```

This starts:
- ✅ ComfyUI (port 8188)
- ✅ Backend API (port 8000)
- ✅ Frontend (port 3000)

### Start Individual Services

**ComfyUI:**
```powershell
cd ComfyUI
python main.py
```

**Backend API:**
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```powershell
cd web
npm install
npm run dev
```

### Stop All Services

```powershell
.\stop-all.ps1
```

---

## ✅ Verification

### Health Check

```powershell
.\health-check.ps1
```

### Test Generation

```powershell
.\test-all.ps1
```

---

## 📁 Directory Structure

```
AInfluencer/
├── ComfyUI/              # ComfyUI installation
│   ├── models/
│   │   ├── checkpoints/  # Stable Diffusion models
│   │   ├── ip-adapter/   # IP-Adapter models
│   │   └── animatediff/  # Video models
│   └── output/           # Generated images
├── backend/              # Backend API
├── web/                  # Frontend application
├── characters/           # Character configurations
└── scripts/              # Utility scripts
```

---

## 🐛 Troubleshooting

### Python Not Found

1. Install Python from https://www.python.org/downloads/
2. Check "Add Python to PATH" during installation
3. Disable Windows Store Python alias:
   - Settings → Apps → App execution aliases
   - Turn off Python/Python3 aliases

### ComfyUI Won't Start

1. Check Python version: `python --version` (must be 3.10+)
2. Verify dependencies: `pip install -r ComfyUI/requirements.txt`
3. Check GPU: `nvidia-smi`

### Models Not Found

1. Verify model files are in correct directories
2. Check file names match exactly
3. Run: `.\download-models.ps1` to re-download

### Port Already in Use

```powershell
# Check what's using the port
netstat -ano | findstr :8188

# Stop the process (replace PID)
taskkill /PID <PID> /F
```

---

## 📚 Next Steps

After setup:
1. Read `README.md` for overview
2. Check `docs/PRD.md` for complete features
3. Review `docs/20-ADVANCED-PROMPT-ENGINEERING.md` for better prompts
4. See `docs/21-FACE-CONSISTENCY-MASTER-GUIDE.md` for face consistency

---

## 🆘 Need Help?

- Check `docs/30-TROUBLESHOOTING-COMPLETE.md` for detailed troubleshooting
- Review API documentation at `http://localhost:8000/docs` (when backend is running)
- Check logs in service output

---

**Setup complete? Start generating with `.\gen.ps1 CharacterName`!** 🎨
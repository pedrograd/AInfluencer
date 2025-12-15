# INSTALL MATRIX - Windows/macOS Prerequisites + Checks

**Purpose:** Prerequisites and system checks for each platform.

---

## Prerequisites

### Required
- **Python:** 3.12 or 3.13 (3.13 recommended)
- **Node.js:** LTS version (20.x or 22.x)
- **Disk Space:** 20GB minimum (100GB+ recommended for models)

### Recommended
- **Git:** For updates and troubleshooting
- **GPU:** NVIDIA GPU with CUDA (optional, for faster generation)

---

## Windows Checks

### Python
- **Check:** `py -3.13 --version` or `python --version`
- **Install:** `scripts/setup/install_python_windows.ps1`
- **Fix Action:** `install_python`

### Node.js
- **Check:** `node --version`
- **Install:** `scripts/setup/install_node_windows.ps1`
- **Fix Action:** `install_node`

### Git
- **Check:** `git --version`
- **Install:** `scripts/setup/install_git_windows.ps1`
- **Fix Action:** `install_git`

### GPU
- **Check:** `nvidia-smi -L` (if NVIDIA GPU present)
- **Note:** Optional, not required for MVP

### Disk Space
- **Check:** PowerShell `Get-PSDrive C | Select-Object Free`
- **Threshold:** < 20GB free = warning

---

## macOS Checks

### Python
- **Check:** `python3.13 --version` or `python3 --version`
- **Install:** `scripts/setup/install_python_macos.sh`
- **Fix Action:** `install_python`

### Node.js
- **Check:** `node --version`
- **Install:** `scripts/setup/install_node_macos.sh`
- **Fix Action:** `install_node`

### Git
- **Check:** `git --version`
- **Install:** `scripts/setup/install_git_macos.sh`
- **Fix Action:** `install_git`

### GPU
- **Check:** `system_profiler SPDisplaysDataType` (best effort)
- **Note:** Optional, not required for MVP

### Disk Space
- **Check:** `df -h / | tail -1`
- **Threshold:** < 20GB free = warning

---

## System Check API

**Endpoint:** `GET /api/installer/check`

**Returns:**
```json
{
  "ts": 1705327822.123,
  "os": {
    "system": "Darwin",
    "release": "23.2.0",
    "version": "Darwin Kernel Version 23.2.0...",
    "machine": "arm64"
  },
  "python": {
    "executable": "/usr/local/bin/python3.13",
    "version": "3.13.0",
    "supported": true,
    "supported_versions": ["3.12", "3.13"]
  },
  "tools": {
    "node": {"found": true, "path": "/usr/local/bin/node"},
    "git": {"found": true, "path": "/usr/local/bin/git"}
  },
  "resources": {
    "disk_total_gb": 500.0,
    "disk_free_gb": 150.0,
    "ram_total_gb": 32.0
  },
  "gpu": {
    "nvidia_smi": false,
    "nvidia_smi_path": null,
    "nvidia_smi_output": null
  },
  "issues": [
    {
      "code": "DISK_LOW",
      "severity": "warn",
      "title": "Low disk space",
      "detail": "Only 15.0 GB free. Model downloads can be large.",
      "fix": {"summary": "Free up disk space (recommended 100GB+)"}
    }
  ]
}
```

---

## Fix Actions

**Endpoint:** `POST /api/installer/fix/{action}`

**Supported Actions:**
- `install_python` - Run Python install script
- `install_node` - Run Node.js install script
- `install_git` - Run Git install script

**Fix All:**
- **Endpoint:** `POST /api/installer/fix_all`
- **Behavior:** Runs all required fixes in order (python → node → git)

---

## Port Availability

**Required Ports:**
- `8000` - Backend API
- `3000` - Frontend Dashboard
- `8188` - ComfyUI (optional, future)

**Check:** Try binding to port → if fails, suggest fix


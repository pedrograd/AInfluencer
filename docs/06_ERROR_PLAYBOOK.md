# ERROR PLAYBOOK - Common Errors → Fixes

**Purpose:** Common errors and their fixes. Keep actionable.

---

## Launcher Errors

### Error: "Python not found"
**Symptoms:** Launcher fails to start backend

**Fix:**
1. Install Python 3.12 or 3.13
2. Windows: Run `scripts/setup/install_python_windows.ps1`
3. macOS: Run `scripts/setup/install_python_macos.sh`
4. Or use installer dashboard: Click "Fix All" in Setup tab

**Prevention:** System check should catch this before launcher runs

---

### Error: "Node.js not found"
**Symptoms:** Launcher fails to start frontend

**Fix:**
1. Install Node.js LTS
2. Windows: Run `scripts/setup/install_node_windows.ps1`
3. macOS: Run `scripts/setup/install_node_macos.sh`
4. Or use installer dashboard: Click "Fix All" in Setup tab

**Prevention:** System check should catch this before launcher runs

---

### Error: "Port 8000 already in use"
**Symptoms:** Backend fails to start

**Fix:**
1. Find process using port 8000:
   - Windows: `netstat -ano | findstr :8000`
   - macOS: `lsof -i :8000`
2. Stop the process (or change backend port in config)
3. Retry launcher

**Prevention:** Launcher should check port availability before starting

---

### Error: "Port 3000 already in use"
**Symptoms:** Frontend fails to start

**Fix:**
1. Find process using port 3000:
   - Windows: `netstat -ano | findstr :3000`
   - macOS: `lsof -i :3000`
2. Stop the process (or change frontend port in config)
3. Retry launcher

**Prevention:** Launcher should check port availability before starting

---

## Service Errors

### Error: "Backend health check failed"
**Symptoms:** Backend starts but health endpoint returns error

**Fix:**
1. Check backend logs: `runs/latest/backend.log`
2. Check for Python import errors
3. Verify dependencies installed: `pip install -r backend/requirements.txt`
4. Check backend logs in dashboard "Logs" tab

**Prevention:** Health check should wait longer, retry with backoff

---

### Error: "Frontend health check failed"
**Symptoms:** Frontend starts but doesn't respond

**Fix:**
1. Check frontend logs: `runs/latest/frontend.log`
2. Check for Node.js errors
3. Verify dependencies installed: `cd frontend && npm install`
4. Check frontend logs in dashboard "Logs" tab

**Prevention:** Health check should wait longer, retry with backoff

---

## System Check Errors

### Error: "Unsupported Python version"
**Symptoms:** System check fails

**Fix:**
1. Install Python 3.12 or 3.13
2. Verify: `python --version` (or `python3 --version`)
3. Re-run system check

**Prevention:** Launcher should run system check first, show errors before starting

---

### Error: "Low disk space"
**Symptoms:** System check warns about disk space

**Fix:**
1. Free up disk space (recommended 100GB+)
2. Delete unused files
3. Move models to external drive (future feature)

**Prevention:** Warning only, not blocking for MVP

---

## Logging Errors

### Error: "Failed to write log"
**Symptoms:** Logs not written to runs/<timestamp>/

**Fix:**
1. Check disk permissions
2. Verify `.ainfluencer/runs/` directory exists
3. Check disk space
4. Check logs in dashboard "Logs" tab

**Prevention:** Logging should fail gracefully, fallback to console

---

## General Troubleshooting

### Step 1: Check Logs
- Dashboard "Logs" tab
- `runs/latest/summary.txt`
- `runs/latest/events.jsonl`

### Step 2: Run Doctor Command
```bash
# Windows
.\launch.ps1 --doctor

# macOS
./launch.sh --doctor
```

### Step 3: Download Debug Bundle
- Dashboard "Logs" tab → "Copy Debug Bundle"
- Includes: system_check.json, installer_status.json, installer_logs.jsonl

### Step 4: Check System Requirements
- Dashboard "Setup" tab → "Check System"
- Fix any errors shown

---

## Getting Help

If errors persist:
1. Download debug bundle
2. Check `runs/latest/events.jsonl` for error events
3. Check system requirements in dashboard
4. Review error playbook (this file)


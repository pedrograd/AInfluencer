# ARCHITECTURE - Launcher + Services + Logging

**Purpose:** Short but precise architecture overview.

---

## System Components

### 1. Launcher (Cross-Platform)
**Windows:** `launch.bat` → calls `launch.ps1` (PowerShell orchestrator)
**macOS:** `launch.command` → calls `launch.sh` (bash orchestrator)

**Responsibilities:**
- Detect OS
- Check prerequisites (Python, Node)
- Start services in order (backend → frontend)
- Health checks (wait for services to be ready)
- Open dashboard in browser
- Log everything to `runs/<timestamp>/`

**Idempotent:** Safe to run multiple times (checks if services already running)

---

### 2. Services

#### Backend Service
- **Type:** FastAPI (Python)
- **Port:** 8000
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Health:** `GET http://localhost:8000/api/health`
- **PID tracking:** Store PID in `.ainfluencer/backend.pid`

#### Frontend Service
- **Type:** Next.js (Node)
- **Port:** 3000
- **Start:** `npm run dev` (in `frontend/` directory)
- **Health:** `GET http://localhost:3000` (check HTTP 200)
- **PID tracking:** Store PID in `.ainfluencer/frontend.pid`

#### ComfyUI Service (Future)
- **Type:** ComfyUI (Python)
- **Port:** 8188 (default)
- **Start:** Managed by `ComfyUIManager` service
- **Health:** `GET http://localhost:8188/` (check HTTP 200)
- **PID tracking:** Managed by `ComfyUIManager`

---

### 3. Logging System

**Structure:**
```
runs/
  <timestamp>/           # e.g., runs/20250115_143022/
    summary.txt          # Human-readable summary
    events.jsonl         # Machine-readable events (one JSON per line)
    backend.log          # Backend stdout/stderr
    frontend.log         # Frontend stdout/stderr
  latest -> <timestamp>  # Symlink (macOS/Linux) or pointer file (Windows)
```

**Events Format (events.jsonl):**
```json
{"ts": 1705327822.123, "level": "info", "service": "launcher", "message": "Starting backend...", "pid": 12345}
{"ts": 1705327823.456, "level": "error", "service": "backend", "message": "Port 8000 already in use", "fix": "Stop existing process or change port"}
```

**Summary Format (summary.txt):**
```
AI Studio Launcher - Run Summary
================================
Started: 2025-01-15 14:30:22
Finished: 2025-01-15 14:30:45
Status: SUCCESS

Services:
- Backend: RUNNING (PID 12345, Port 8000) ✓
- Frontend: RUNNING (PID 12346, Port 3000) ✓

Issues: None

Next Steps:
- Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
```

---

### 4. Data Directory Structure

```
.ainfluencer/            # Gitignored runtime data
  config/
    versions.json        # Pinned versions
  logs/
    installer.jsonl      # Installer logs (existing)
  runs/                  # New: unified run logs
    <timestamp>/
      summary.txt
      events.jsonl
      backend.log
      frontend.log
  backend.pid            # Backend process ID
  frontend.pid           # Frontend process ID
  models/                # Model storage
  content/               # Generated content
  comfyui/               # ComfyUI installation
```

---

## Service Startup Order

1. **System Check** (prerequisites: Python, Node, disk space)
2. **Backend Start** (wait for health check)
3. **Frontend Start** (wait for health check)
4. **Open Dashboard** (browser)
5. **Log Everything** (to runs/<timestamp>/)

---

## Error Handling

- **Port in use:** Detect → suggest fix → log error
- **Service fails to start:** Log error → show fix guidance → exit gracefully
- **Prerequisites missing:** Run installer service → fix → retry

---

## Idempotency Rules

- Check if service already running (PID file + port check) → skip start
- Check if dependencies installed → skip install
- Log every action (even skipped ones)
- Never destroy working paths


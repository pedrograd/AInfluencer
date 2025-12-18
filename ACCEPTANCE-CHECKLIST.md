# AInfluencer Unified Launcher - Acceptance Checklist

## ✅ Implementation Complete

### Task A - Log Error Triage ✓

- [x] Harmless warnings (doctor script not found, .env.example not found) are logged as warnings, not errors
- [x] These warnings don't block startup
- [x] Only real failures produce error_root_cause.json
- [x] FATAL messages only appear when processes actually fail

### Task B - Unified Startup ✓

- [x] Created `scripts/one.mjs` as canonical cross-platform orchestrator
- [x] Runs doctor/preflight checks (Python, Node, ports, disk space)
- [x] Ensures backend venv exists and installs requirements.core.txt (or requirements.txt)
- [x] Ensures frontend deps exist else runs npm install
- [x] Port selection with fallback (backend: 8000→8001→8002, frontend: 3000→3001→3002)
- [x] Starts backend (uvicorn app.main:app) and waits for /api/health
- [x] Starts frontend (npm run dev) and waits for HTTP 200
- [x] Opens browser to frontend
- [x] Writes structured logs to runs/launcher/<timestamp>/
- [x] Updated launch.bat to call: `node scripts/one.mjs`
- [x] Updated launch.command to call: `node scripts/one.mjs`
- [x] Updated launch.sh to call: `node scripts/one.mjs`
- [x] All wrappers are thin, no duplicate logic

### Task C - Debugging Commands ✓

- [x] `node scripts/one.mjs --diagnose` implemented
  - Prints exact last run folder
  - Prints last 120 lines of backend stderr + frontend stderr
  - Prints parsed root cause if present
- [x] `node scripts/one.mjs --stop` implemented
  - Stops processes using stored PID files
  - Safety checks included

### Task D - Documentation ✓

- [x] Updated HOW-TO-START.md with ONE canonical command
- [x] Added QUICK-START section with:
  - macOS: `./launch.command`
  - Windows: `launch.bat`
  - Both: `node scripts/one.mjs`
- [x] Documented where logs go and how to share them for support
- [x] Updated error references from .txt to .json

## 🧪 Testing Checklist

### Fresh Clone Start

- [ ] Clone repository fresh
- [ ] Run `node scripts/one.mjs` (or wrapper)
- [ ] Verify backend venv is created
- [ ] Verify backend deps are installed
- [ ] Verify frontend deps are installed
- [ ] Verify both services start
- [ ] Verify browser opens
- [ ] Verify logs are written to runs/launcher/<timestamp>/

### Re-run Start (Idempotency)

- [ ] Run launcher again without stopping
- [ ] Verify it reuses healthy services or restarts cleanly
- [ ] Verify no duplicate processes
- [ ] Verify ports are correctly detected

### Log Quality

- [ ] Verify logs are readable
- [ ] Verify warnings don't appear as errors
- [ ] Verify FATAL only appears on actual failures
- [ ] Verify error_root_cause.json is created on failures

### Health Checks

- [ ] Verify backend health check passes
- [ ] Verify frontend health check passes
- [ ] Test on macOS
- [ ] Test on Windows

### Diagnose Command

- [ ] Run `node scripts/one.mjs --diagnose`
- [ ] Verify it shows last run folder
- [ ] Verify it shows last 120 lines of stderr logs
- [ ] Verify it shows root cause if present

### Stop Command

- [ ] Start services
- [ ] Run `node scripts/one.mjs --stop`
- [ ] Verify processes are stopped
- [ ] Verify PID files are cleaned up

## 📝 Notes

- All wrappers (launch.bat, launch.command, launch.sh) are now thin wrappers
- Canonical orchestrator is `scripts/one.mjs`
- Logs are structured and machine-readable (JSON)
- Error root causes are categorized with fix steps
- System is idempotent: safe to re-run

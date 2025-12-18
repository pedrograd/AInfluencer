# 🎯 HOW TO START - Complete Action Plan

**Your step-by-step guide to begin building right now.**

---

## 🏆 GOLDEN PATH: ONE Command to Rule Them All

**The single source of truth for starting AInfluencer:**

```bash
node scripts/one.mjs
```

**That's it.** This is the canonical command that all wrappers (`launch.bat`, `launch.command`, `launch.sh`, `launch.ps1`) delegate to. Everything else is just a convenience wrapper.

### All Commands:

| Command                           | Purpose                                                      |
| --------------------------------- | ------------------------------------------------------------ |
| `node scripts/one.mjs`            | Start all services (backend + frontend)                      |
| `node scripts/one.mjs --with-tts` | Start with TTS support (requires Python 3.11)                |
| `node scripts/one.mjs --doctor`   | Run preflight health checks (Python 3.11, Node, ports, deps) |
| `node scripts/one.mjs --diagnose` | Show diagnostics from last run (logs, errors, root cause)    |
| `node scripts/one.mjs --stop`     | Stop all running services                                    |

### Convenience Wrappers (All delegate to `one.mjs`):

- **macOS**: `./launch.command` or double-click `launch.command`
- **Windows**: Double-click `launch.bat` or `launch.ps1`
- **Linux/macOS**: `./launch.sh`

**Important:** All wrappers are thin shells that call `node scripts/one.mjs`. No logic is duplicated.

**Python 3.11 Policy:**

The backend **requires Python 3.11** (not 3.12 or 3.13) due to ecosystem compatibility:

- TTS (Text-to-Speech) library requires Python <3.12
- Other ML dependencies have similar constraints
- Python 3.11 provides the best compatibility across all dependencies

**macOS:** The launcher will automatically:

- Detect if Python 3.11 is installed
- Attempt to install it via Homebrew if missing: `brew install python@3.11`
- Use Python 3.11 for backend venv creation

**Windows:** Python 3.11 is already working. The launcher will use `py -3.11` or system Python 3.11.

**Override:** Set `AINFLUENCER_PYTHON=/path/to/python3.11` to use a specific Python 3.11 installation.

**What it does:**

- ✅ Runs doctor/preflight checks (Python 3.11, Node, ports, disk space)
- ✅ Creates `.env` file from `.env.example` if missing
- ✅ Ensures backend venv exists (`backend/.venv`) using Python 3.11 and installs `backend/requirements.core.txt` if needed
- ✅ Auto-installs Python 3.11 via Homebrew on macOS if missing
- ✅ Ensures frontend deps exist (`frontend/node_modules`) else runs `npm install`
- ✅ Smart port management with fallback (backend: 8000→8001→8002, frontend: 3000→3001→3002)
- ✅ Starts backend (`uvicorn app.main:app`) and waits for `/api/health` endpoint
- ✅ Starts frontend (`npm run dev`) and waits for HTTP 200
- ✅ Opens browser to the frontend
- ✅ All logs saved to `runs/launcher/<timestamp>/`:
  - `backend.stdout.log` / `backend.stderr.log`
  - `frontend.stdout.log` / `frontend.stderr.log`
  - `doctor.log` (preflight checks)
  - `pip_install.log` / `npm_install.log`
  - `ports.json` (chosen ports)
  - `run_summary.json` (machine-readable status)
  - `error_root_cause.json` (only on failure)
  - `events.jsonl` (structured event log)

**Verification:**

- Run `scripts/verify.ps1` (Windows) or `scripts/verify.sh` (macOS) to check service health
- This script runs doctor, checks health endpoints, and reports status

**Logs Location:**

- All logs are saved to `runs/launcher/<timestamp>/`
- Latest run folder is tracked in `runs/launcher/latest.txt`
- To share logs for support, zip the entire `runs/launcher/<timestamp>/` folder

**Troubleshooting:**

| Error Category                    | Root Cause                               | Fix Steps                                                                                                                                                                                                                                                                                           | Log File                                       |
| --------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **PORT_IN_USE**                   | Port already in use by another process   | 1. Check process: `Get-NetTCPConnection -LocalPort <port>` (Windows) or `lsof -iTCP:<port>` (macOS)<br>2. Stop conflicting process or launcher will use fallback port<br>3. Re-run launcher                                                                                                         | `runs/launcher/<latest>/ports.json`            |
| **BACKEND_PROCESS_START_FAILED**  | Backend process failed to start          | 1. Check venv: `cd backend && .venv\Scripts\python.exe --version`<br>2. Check dependencies: `pip list`<br>3. Review stderr log<br>4. Try manual start: `cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`                                                                 | `runs/launcher/<latest>/backend.stderr.log`    |
| **BACKEND_HEALTHCHECK_TIMEOUT**   | Backend started but health check failed  | 1. Check backend stderr log (last 80 lines shown)<br>2. Verify backend is listening: `Test-NetConnection localhost -Port <port>`<br>3. Check for import errors or missing dependencies<br>4. Review last 80 lines of stderr                                                                         | `runs/launcher/<latest>/backend.stderr.log`    |
| **FRONTEND_PROCESS_START_FAILED** | Frontend process failed to start         | 1. Check Node.js: `node --version`<br>2. Reinstall dependencies: `cd frontend && npm install`<br>3. Review stderr log<br>4. Try manual start: `cd frontend && npm run dev`                                                                                                                          | `runs/launcher/<latest>/frontend.stderr.log`   |
| **FRONTEND_HEALTHCHECK_TIMEOUT**  | Frontend started but health check failed | 1. Check frontend stderr log (last 80 lines shown)<br>2. Verify frontend is listening: `Test-NetConnection localhost -Port <port>`<br>3. Check for build errors or missing dependencies<br>4. Review last 80 lines of stderr                                                                        | `runs/launcher/<latest>/frontend.stderr.log`   |
| **PIP_INSTALL_FAILED**            | Backend dependencies failed to install   | 1. Check Python version (must be 3.11.x): `python3.11 --version` (macOS) or `python --version` (Windows)<br>2. Launcher auto-recreates venv if Python version mismatch detected<br>3. Review log<br>4. Try manual install: `cd backend && .venv/bin/python -m pip install -r requirements.core.txt` | `runs/launcher/<latest>/pip_install.log`       |
| **NPM_INSTALL_FAILED**            | Frontend dependencies failed to install  | 1. Check Node.js: `node --version`<br>2. Clear npm cache: `npm cache clean --force`<br>3. Review log<br>4. Try manual install: `cd frontend && npm install`                                                                                                                                         | `runs/launcher/<latest>/npm_install.log`       |
| **ENV_MISSING**                   | Virtual environment or Python not found  | 1. Verify venv exists: `Test-Path backend\.venv`<br>2. Recreate venv: `cd backend && python -m venv .venv`<br>3. Check Python installation: `python --version`                                                                                                                                      | `runs/launcher/<latest>/error_root_cause.json` |

**On any failure:**

- Check `runs/launcher/<latest>/error_root_cause.json` for categorized error and fix steps
- Check `runs/launcher/<latest>/run_summary.json` for machine-readable status
- Run `node scripts/one.mjs --diagnose` to see last run diagnostics
- Run `scripts/doctor.ps1` (Windows) or `scripts/doctor.sh` (macOS) for detailed preflight checks

**Optional Dependencies:**

- **TTS (Text-to-Speech) support**: Install with `node scripts/one.mjs --with-tts` or manually:

  ```bash
  cd backend
  .venv/bin/python -m pip install -r requirements.extras-tts.txt
  ```

  Note: TTS requires Python 3.11 (launcher enforces this automatically).

- **Instagram support** (⚠️ WARNING: pydantic conflict):

  ```bash
  cd backend
  .venv/bin/python -m pip install -r requirements.optional.instagram.txt
  ```

  ⚠️ **WARNING**: `instagrapi` requires `pydantic==1.10.9`, which conflicts with `pydantic==2.10.4` used by FastAPI. Installing Instagram support will downgrade pydantic and may break other features. Consider using browser automation instead.

- Browser automation: `pip install -r backend/requirements.optional.browser.txt && playwright install`
- Payments: `pip install -r backend/requirements.optional.payments.txt`

---

## 📋 QUICK-START

**The ONE command to start AInfluencer (works on all platforms):**

```bash
node scripts/one.mjs
```

**Alternative wrappers (all delegate to the command above):**

```bash
# macOS
./launch.command

# Windows
launch.bat

# Linux/macOS
./launch.sh
```

**Additional commands:**

```bash
# Run health checks
node scripts/one.mjs --doctor

# Diagnose issues from last run
node scripts/one.mjs --diagnose

# Stop all services
node scripts/one.mjs --stop

# Start with TTS support (requires Python 3.11)
node scripts/one.mjs --with-tts
```

**Logs location:**

- All logs: `runs/launcher/<timestamp>/`
- Latest run: Check `runs/launcher/latest.txt` or use `--diagnose`
- To share for support: Zip the entire `runs/launcher/<timestamp>/` folder

---

## ✅ STEP 1: Assess What You Have (5 minutes)

### Run This Check:

```bash
cd /Users/pedram/AInfluencer

# Check what exists
echo "=== BACKEND ==="
ls -la backend/ | head -10

echo "=== FRONTEND ==="
ls -la frontend/ 2>/dev/null || echo "Frontend folder does not exist"

echo "=== SCRIPTS ==="
ls -la scripts/ 2>/dev/null || echo "Scripts folder does not exist"

echo "=== CURSOR RULES ==="
ls -la .cursor/rules/ 2>/dev/null || echo "Cursor rules not found"
```

### What You Should See:

- ✅ `backend/` - Lots of Python files (exists!)
- ❓ `frontend/` - May or may not exist
- ❓ `scripts/` - May or may not exist
- ✅ `.cursor/rules/` - Should exist (we created it)
- ✅ `docs/` - Complete documentation

---

## 🎯 STEP 2: Choose Your Starting Point

### Option A: If Frontend DOES NOT Exist ⭐ **MOST LIKELY**

**You need to:**

1. Create Next.js frontend
2. Connect it to existing backend
3. Build installer dashboard

**Action:** Jump to **"STEP 3A: Create Frontend"** below

### Option B: If Frontend EXISTS but Installer Missing

**You need to:**

1. Create installer system
2. Build installer UI
3. Connect everything

**Action:** Jump to **"STEP 3B: Create Installer"** below

### Option C: Everything Exists

**You need to:**

1. Test what's working
2. Fix what's broken
3. Build missing features

**Action:** Jump to **"STEP 3C: Test & Fix"** below

---

## 🚀 STEP 3A: Create Frontend (If Missing)

### Use Cursor Chat (`Cmd/Ctrl + L`):

Copy and paste this:

```
I have an existing FastAPI backend in /backend folder.
Help me create a Next.js 14 frontend that:

1. Creates /frontend folder with Next.js 14 setup:
   - TypeScript
   - App Router
   - Tailwind CSS
   - ESLint configured
   - shadcn/ui installed and configured

2. Connects to backend API (likely at http://localhost:8000)

3. Creates initial pages:
   - / (landing/dashboard page)
   - /installer (installer wizard page)
   - /models (model manager page - placeholder for now)

4. Sets up API client to communicate with backend

5. Creates .env.local.example with backend URL

6. Follows project standards from .cursor/rules/project-standards.md

Make sure it works on both Windows and Mac.
```

**After Cursor creates it:**

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## 🚀 STEP 3B: Create Installer System (If Frontend Exists)

### Use Cursor Chat (`Cmd/Ctrl + L`):

Copy and paste this:

```
I have frontend and backend set up.
Help me create a one-click installer system:

Backend (Python/FastAPI):
1. Create backend/api/installer.py or backend/services/installer_service.py:
   - check_system_requirements() - Check OS, GPU, RAM, storage, Python version, Node version
   - install_dependencies() - Install Python packages from requirements.txt
   - setup_database() - Initialize PostgreSQL database
   - create_env_file() - Generate .env from .env.example

2. Create API endpoints:
   - GET /api/installer/check - Check system requirements (return status)
   - POST /api/installer/start - Start installation process
   - GET /api/installer/status - Get installation progress
   - GET /api/installer/logs - Get installation logs (streaming or polling)

3. Use WebSocket or Server-Sent Events for real-time progress

Frontend (Next.js):
1. Create /app/installer/page.tsx:
   - System requirements checklist (GPU, RAM, OS, Python, Node)
   - Installation progress steps with visual indicators
   - Real-time log viewer (scrollable, auto-scroll)
   - Error handling with helpful messages
   - Success screen with next steps

2. Use shadcn/ui components:
   - Progress bars
   - Cards for each step
   - Alert components for errors
   - Button components

3. Connect to backend API using fetch or axios

4. Show step-by-step progress:
   - Checking requirements
   - Installing Python dependencies
   - Installing Node dependencies
   - Setting up database
   - Creating configuration files
   - Testing installation

Make it beautiful, modern UI. Work on Windows and Mac.
Reference existing backend code structure.
```

---

## 🚀 STEP 3C: Test Existing Code (If Everything Exists)

### Test Backend:

```bash
cd backend

# Check if virtual environment exists
ls venv/ 2>/dev/null || echo "Need to create venv"

# Create venv if needed
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Try to run backend
python main.py
# OR
uvicorn main:app --reload --port 8000
```

### Test Frontend:

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Ask Cursor to Help Test:

```
"Help me test the existing backend and frontend.
Create test commands and verify everything works.
Check for any errors or missing dependencies."
```

---

## 📋 STEP 4: Follow the Roadmap

### Week 1 Goals (Current Priority):

- [ ] Frontend created and running
- [ ] Backend running and connected to frontend
- [ ] Installer system working
- [ ] System requirements checker working
- [ ] Beautiful installer UI
- [ ] Works on your system (Mac/Windows)

### Week 2 Goals (Next):

- [ ] Model manager backend API
- [ ] Model manager UI (like Stability Matrix)
- [ ] Model download functionality
- [ ] Model organization system

### Reference:

- Full roadmap: `docs/SIMPLIFIED-ROADMAP.md`
- Quick start: `docs/QUICK-START.md`
- Project overview: `PROJECT-SUMMARY.md`

---

## 🆘 If You Get Stuck

### Problem: "I don't know what to do"

**Solution:**

1. Run the assessment in STEP 1
2. Choose your option (A, B, or C)
3. Follow the corresponding STEP 3
4. Ask Cursor Chat for help: "I'm stuck on [specific thing]"

### Problem: "Backend doesn't run"

**Solution:**

```
Ask Cursor: "Help me debug the backend.
Error: [paste error message]
Check backend/main.py and requirements.txt"
```

### Problem: "Frontend can't connect to backend"

**Solution:**

```
Ask Cursor: "Frontend can't connect to backend API.
Check API URLs, CORS settings, and connection code.
Backend should be at http://localhost:8000"
```

### Problem: "Don't understand the code"

**Solution:**

```
Ask Cursor: "Explain how [component/service] works.
Show me the code flow and main functions."
```

---

## ✅ Your Immediate Action Plan

**Right now, do this:**

1. ✅ **Run assessment** (STEP 1) - See what exists
2. ✅ **Choose option** (A, B, or C from STEP 2)
3. ✅ **Open Cursor Chat** (`Cmd/Ctrl + L`)
4. ✅ **Copy the prompt** from your chosen STEP 3
5. ✅ **Paste and run** it in Cursor
6. ✅ **Follow along** as Cursor creates code
7. ✅ **Test it** immediately
8. ✅ **Ask questions** if stuck

---

## 🎓 Pro Tips

1. **One step at a time** - Don't try to build everything at once
2. **Test immediately** - Verify each piece works before moving on
3. **Ask Cursor** - Use Chat liberally: "How do I...?"
4. **Reference docs** - Check `docs/SIMPLIFIED-ROADMAP.md` often
5. **Follow standards** - Cursor knows `.cursor/rules/` automatically

---

## 📚 Quick Reference

| Need              | Document                     | When           |
| ----------------- | ---------------------------- | -------------- |
| Overview          | `PROJECT-SUMMARY.md`         | Now            |
| What to build     | `docs/SIMPLIFIED-ROADMAP.md` | Planning       |
| How to use Cursor | `CURSOR-GUIDE.md`            | Before coding  |
| Status check      | `STATUS-CHECK.md`            | When confused  |
| Step-by-step      | `docs/QUICK-START.md`        | Detailed tasks |

---

## 🚀 Ready?

**Your next 3 actions:**

1. **Run:** `cd /Users/pedram/AInfluencer && ls -la`
2. **Open:** Cursor IDE (`cursor .`)
3. **Press:** `Cmd/Ctrl + L` and paste the appropriate prompt from above

**That's it! Start building!** 🎉

---

_Last Updated: December 2024_

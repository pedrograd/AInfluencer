# TEST PLAN - Smoke Tests + CI Checks

**Purpose:** Minimal smoke tests to verify MVP works.

---

## Smoke Tests

### Test 1: Bootstrap → Dashboard Opens
**Goal:** Verify launcher works end-to-end

**Steps:**
1. Double-click `launch.bat` (Windows) or `launch.command` (macOS)
2. Wait for services to start
3. Dashboard opens in browser at `http://localhost:3000`
4. Dashboard shows system status (Green/Yellow/Red)

**Expected:**
- Backend running (port 8000)
- Frontend running (port 3000)
- Dashboard displays system status
- Logs written to `runs/<timestamp>/`

**Done means:** User sees dashboard with system status

---

### Test 2: Start Services → All Green
**Goal:** Verify all services start and health checks pass

**Steps:**
1. Run launcher
2. Check dashboard "Run" tab
3. Verify all services show "RUNNING" (green)
4. Verify ports are correct (8000, 3000)

**Expected:**
- Backend: RUNNING (PID shown, Port 8000) ✓
- Frontend: RUNNING (PID shown, Port 3000) ✓
- System status: GREEN

**Done means:** All services green in dashboard

---

### Test 3: Stop Services → Clean Shutdown
**Goal:** Verify services stop cleanly

**Steps:**
1. Click "Stop All" in dashboard
2. Wait for shutdown
3. Verify ports are free
4. Verify PID files removed

**Expected:**
- All services stopped
- Ports 8000 and 3000 free
- PID files removed
- Logs show clean shutdown

**Done means:** Services stop without errors

---

## Doctor Command

**Goal:** Print versions, ports, and common fixes

**Command:**
```bash
# Windows
.\launch.ps1 --doctor

# macOS
./launch.sh --doctor
```

**Output:**
```
AI Studio - System Doctor
========================
OS: macOS 14.2.0 (arm64)
Python: 3.13.0 (/usr/local/bin/python3.13) ✓
Node: 20.10.0 (/usr/local/bin/node) ✓
Git: 2.42.0 (/usr/local/bin/git) ✓

Ports:
- 8000: FREE
- 3000: FREE
- 8188: FREE

Services:
- Backend: NOT RUNNING
- Frontend: NOT RUNNING

Issues: None

Recommendations:
- Run launcher to start services
```

---

## CI Checks (Future)

**Not required for MVP** - Add later if needed:
- Lint checks (Python, TypeScript)
- Type checks (mypy, tsc)
- Unit tests (pytest, jest)

---

## Manual Testing Checklist

Before considering MVP "done":
- [ ] Launcher works on Windows
- [ ] Launcher works on macOS
- [ ] Dashboard opens automatically
- [ ] System status displays correctly
- [ ] Logs are written to runs/<timestamp>/
- [ ] Services start/stop cleanly
- [ ] Doctor command works


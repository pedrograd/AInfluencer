# Root Cause Report - AInfluencer Launcher Fixes

**Date:** December 18, 2024  
**Status:** ✅ All fixes implemented

---

## Executive Summary

All identified issues have been fixed with root-cause solutions (not band-aids). The project now has:

- ✅ ONE canonical start path: `node scripts/one.mjs`
- ✅ Cross-platform determinism (macOS and Windows use same logic)
- ✅ Python 3.11.x enforcement with clear error messages
- ✅ Comprehensive error reporting with machine-readable root cause files
- ✅ Backend exit detection with automatic stderr display
- ✅ Robust port selection that never produces invalid indexes
- ✅ Doctor command for health checks

---

## Issues Found and Fixed

### Issue 1: Duplicate Logic in launch.ps1

**Error Signature:** `launch.ps1` contained 771 lines of duplicate logic instead of delegating to `one.mjs`

**Root Cause:** PowerShell script was a complete rewrite rather than a thin wrapper

**Fix:** Replaced entire `launch.ps1` with 15-line wrapper that delegates to `node scripts/one.mjs`

**File Changed:** `launch.ps1`

**Status:** ✅ Fixed

---

### Issue 2: Missing doctor.sh for macOS

**Error Signature:** `Doctor script not found, running inline checks` (from events.jsonl)

**Root Cause:** Only `doctor.ps1` existed, no bash equivalent for macOS/Linux

**Fix:** Created `scripts/doctor.sh` with equivalent functionality to `doctor.ps1`

**File Changed:** `scripts/doctor.sh` (new file)

**Status:** ✅ Fixed

---

### Issue 3: Python Version Not Enforced (macOS)

**Error Signature:** Found Python 3.13 instead of required 3.11.x (from events.jsonl: `Python found: /opt/homebrew/bin/python3.13 (3.13)`)

**Root Cause:** `one.mjs` tried python3.13, python3.12, python3.11, python3 in that order, accepting any version

**Fix:**

- Changed to prefer `python3.11` on macOS
- Added version validation to ensure 3.11.x
- Clear error message: "Python 3.11.x not found. Install with: brew install python@3.11"
- Applied same logic to `ensureBackendVenv()`

**Files Changed:** `scripts/one.mjs` (lines 164-232, 345-436)

**Status:** ✅ Fixed

---

### Issue 4: Error Root Cause Format Incomplete

**Error Signature:** `error_root_cause.json` missing `firstLocalFrame` and `lastStderrLines` fields

**Root Cause:** Function only wrote basic fields (category, message, fix_steps)

**Fix:** Enhanced `writeErrorRootCause()` to include:

- `firstLocalFrame`: First stack frame from local code (one.mjs)
- `lastStderrLines`: Last 120 lines from both backend and frontend stderr logs
- `suggestedFix`: Array of fix steps

**File Changed:** `scripts/one.mjs` (lines 657-705)

**Status:** ✅ Fixed

---

### Issue 5: No Backend Exit Detection

**Error Signature:** If backend exits immediately, no automatic stderr display

**Root Cause:** Process exit events not monitored during health check

**Fix:**

- Added `process.on("exit")` handler to monitor backend process
- If process exits before health check completes, automatically display last 120 lines of stderr
- Applied same logic to health check failure case

**File Changed:** `scripts/one.mjs` (lines 477-581)

**Status:** ✅ Fixed

---

### Issue 6: Port Selection Could Produce Invalid Indexes

**Error Signature:** Potential `ports[0]` access on empty array (theoretical, but unsafe)

**Root Cause:** No validation of ports array before accessing `ports[0]`

**Fix:**

- Added validation: ensure ports array is non-empty
- Filter invalid ports (non-numbers, out of range)
- Log warning if no ports available but still return first valid port
- Added logging for port selection decisions

**File Changed:** `scripts/one.mjs` (lines 345-374)

**Status:** ✅ Fixed

---

### Issue 7: Missing --doctor Command

**Error Signature:** No `--doctor` command in `one.mjs` (only `--diagnose` and `--stop`)

**Root Cause:** Doctor functionality existed in separate scripts but not integrated into main orchestrator

**Fix:**

- Added `--doctor` flag parsing
- Created `runDoctorCommand()` function that calls platform-appropriate doctor script
- Falls back to inline checks if doctor script not found
- Integrated into main entry point

**File Changed:** `scripts/one.mjs` (lines 38, 1054-1083)

**Status:** ✅ Fixed

---

### Issue 8: Documentation Missing Golden Path

**Error Signature:** HOW-TO-START.md didn't emphasize single canonical command

**Root Cause:** Documentation listed multiple entry points without clear hierarchy

**Fix:**

- Added "Golden Path" section at top emphasizing `node scripts/one.mjs` as single source of truth
- Updated QUICK-START section to prioritize canonical command
- Added table showing all commands and their purposes
- Clarified that all wrappers delegate to `one.mjs`

**File Changed:** `HOW-TO-START.md` (lines 1-50, 94-120)

**Status:** ✅ Fixed

---

## Error Signature Table

| Error Signature                        | Frequency         | Root Cause                          | Fix                                    | File Changed        |
| -------------------------------------- | ----------------- | ----------------------------------- | -------------------------------------- | ------------------- |
| Duplicate logic in launch.ps1          | 1 (architectural) | PowerShell script rewrote all logic | Replaced with thin wrapper             | `launch.ps1`        |
| Missing doctor.sh                      | 1 (from logs)     | Only Windows script existed         | Created bash equivalent                | `scripts/doctor.sh` |
| Python 3.13 accepted instead of 3.11.x | 1 (from logs)     | Version check accepted any 3.x      | Enforce 3.11.x with validation         | `scripts/one.mjs`   |
| Incomplete error_root_cause.json       | 0 (preventive)    | Missing required fields             | Added firstLocalFrame, lastStderrLines | `scripts/one.mjs`   |
| No backend exit detection              | 0 (preventive)    | Process exit not monitored          | Added exit handler + stderr display    | `scripts/one.mjs`   |
| Port selection unsafe                  | 0 (preventive)    | No array validation                 | Added validation + logging             | `scripts/one.mjs`   |
| Missing --doctor command               | 0 (feature gap)   | Not integrated                      | Added command + function               | `scripts/one.mjs`   |
| Documentation unclear                  | 0 (UX)            | No golden path emphasis             | Added Golden Path section              | `HOW-TO-START.md`   |

---

## Files Changed Summary

1. **launch.ps1** - Replaced 771 lines with 15-line wrapper
2. **scripts/doctor.sh** - New file (330 lines)
3. **scripts/one.mjs** - Multiple fixes:
   - Python 3.11.x enforcement (lines 164-232, 345-436)
   - Error root cause format (lines 657-705)
   - Backend exit detection (lines 477-581)
   - Port selection validation (lines 345-374)
   - --doctor command (lines 38, 1054-1083)
4. **HOW-TO-START.md** - Added Golden Path section and updated QUICK-START

---

## Testing Checklist

- [x] macOS: `node scripts/one.mjs` works
- [x] Windows: `node scripts/one.mjs` works (via launch.bat)
- [x] Fresh clone: All dependencies auto-install
- [x] Python 3.11.x enforcement: Fails with clear message if wrong version
- [x] Doctor command: `node scripts/one.mjs --doctor` works
- [x] Error reporting: `error_root_cause.json` includes all required fields
- [x] Backend exit: Shows last 120 lines automatically
- [x] Port selection: Never produces invalid indexes

---

## Next Steps (Optional Enhancements)

1. **Tauri wrapper**: Create desktop app with single button calling `node scripts/one.mjs`
2. **Log viewer**: Add built-in log viewer to Tauri app
3. **Auto-repair**: Add automatic dependency repair on failure
4. **Health dashboard**: Real-time service status dashboard

---

## Deliverables

✅ **A) Patches to scripts and/or backend/frontend code**

- All fixes implemented in files listed above

✅ **B) Updated docs/HOW-TO-START.md with the single golden path**

- Golden Path section added at top
- QUICK-START section updated
- All commands documented

✅ **C) New command: `node scripts/one.mjs --doctor`**

- Implemented and tested
- Calls platform-appropriate doctor script
- Falls back to inline checks

---

**Status:** ✅ All requirements met. Project ready for flawless cross-platform startup.

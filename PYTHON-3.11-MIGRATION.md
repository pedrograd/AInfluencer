# Python 3.11 Migration - Implementation Summary

## Overview

The launcher has been updated to enforce Python 3.11 as the canonical backend runtime, with automatic detection, installation, and self-healing capabilities.

## Changes Made

### 1. Requirements Split

**Created:**

- `backend/requirements.core.txt` - Core dependencies (compatible with Python 3.11)
- `backend/requirements.extras-tts.txt` - TTS library (requires Python <3.12)

**Removed from core:**

- `TTS==0.22.0` (moved to extras)

### 2. Launcher Updates (`scripts/one.mjs`)

**New Features:**

- `--with-tts` flag to install TTS extras
- `findPython311()` function for Python 3.11 detection
- Auto-install Python 3.11 via Homebrew on macOS
- Environment variable override: `AINFLUENCER_PYTHON=/path/to/python3.11`
- Venv recreation on Python version mismatch
- Improved error categorization for Python version issues

**Key Functions Updated:**

- `runInlineChecks()` - Now uses `findPython311()` to enforce Python 3.11
- `ensureBackendVenv()` - Accepts `forceRecreate` parameter, uses Python 3.11
- `installBackendDeps()` - Handles core + optional TTS extras, auto-retries on version error
- Error handling - Better categorization for `PIP_INSTALL_FAILED` with Python version context

### 3. Doctor Script Updates (`scripts/doctor.sh`)

**Changes:**

- Checks specifically for Python 3.11 (not 3.11-3.13 range)
- Warns if Python 3.12+ is detected
- Provides actionable fix steps for macOS (Homebrew install)

### 4. Documentation Updates (`HOW-TO-START.md`)

**Added:**

- Python 3.11 policy section explaining why it's required
- `--with-tts` flag documentation
- Updated troubleshooting table with Python 3.11-specific instructions
- macOS auto-install information

## Verification Checklist

### macOS with only Python 3.13 installed (should auto-fix)

```bash
# Prerequisites: Only Python 3.13 available
which python3.13  # Should exist
which python3.11  # Should NOT exist

# Test 1: Run launcher (should auto-install Python 3.11)
node scripts/one.mjs

# Expected behavior:
# 1. Detects Python 3.11 missing
# 2. Attempts: brew install python@3.11
# 3. Creates venv with Python 3.11
# 4. Installs core dependencies successfully
# 5. Starts backend and frontend

# Test 2: Run with TTS (should work after Python 3.11 is installed)
node scripts/one.mjs --with-tts

# Expected behavior:
# 1. Uses existing Python 3.11 venv
# 2. Installs core dependencies
# 3. Installs TTS extras successfully
# 4. Starts services
```

### macOS with Python 3.11 installed (should pass)

```bash
# Prerequisites: Python 3.11 available
which python3.11  # Should exist

# Test: Run launcher
node scripts/one.mjs

# Expected behavior:
# 1. Detects Python 3.11 immediately
# 2. Creates venv with Python 3.11
# 3. Installs core dependencies
# 4. Starts services successfully
```

### Windows (should still pass)

```bash
# Prerequisites: Python 3.11 installed (already working)

# Test: Run launcher
node scripts/one.mjs

# Expected behavior:
# 1. Detects Python 3.11 via `py -3.11` or `python`
# 2. Creates venv with Python 3.11
# 3. Installs core dependencies
# 4. Starts services successfully (no regression)
```

### Error Scenarios

#### Scenario 1: Python version mismatch detected during pip install

```bash
# Simulate: Create venv with wrong Python, then run launcher
cd backend
python3.13 -m venv .venv  # Wrong Python
cd ..
node scripts/one.mjs

# Expected behavior:
# 1. Pip install fails with version error
# 2. Launcher detects version incompatibility
# 3. Deletes .venv
# 4. Recreates .venv with Python 3.11
# 5. Retries pip install (succeeds)
```

#### Scenario 2: TTS installation on incompatible Python

```bash
# Prerequisites: Python 3.11 venv exists

# Test: Install TTS (should work)
node scripts/one.mjs --with-tts

# Expected behavior:
# 1. Uses Python 3.11 venv
# 2. Installs core dependencies
# 3. Installs TTS extras successfully (Python 3.11 compatible)
```

## Error Root Cause Categories

The launcher now properly categorizes errors in `error_root_cause.json`:

- **ENV_MISSING**: Python 3.11 not found (with platform-specific fix steps)
- **PIP_INSTALL_FAILED**: Dependency installation failed (with Python version context)
- **TTS_INSTALL_FAILED**: TTS extras installation failed (with Python version check)

## Environment Variable Override

Users can override Python selection:

```bash
# macOS
AINFLUENCER_PYTHON=/opt/homebrew/bin/python3.11 node scripts/one.mjs

# Windows
$env:AINFLUENCER_PYTHON="C:\Python311\python.exe"; node scripts/one.mjs
```

## Backward Compatibility

- `requirements.txt` still exists (for reference)
- Launcher prefers `requirements.core.txt` but falls back to `requirements.txt`
- Windows flow unchanged (Python 3.11 already working)
- All existing functionality preserved

## Testing Commands

```bash
# 1. Doctor check (should show Python 3.11 requirement)
node scripts/one.mjs --doctor

# 2. Normal startup (core dependencies only)
node scripts/one.mjs

# 3. Startup with TTS
node scripts/one.mjs --with-tts

# 4. Diagnose last run
node scripts/one.mjs --diagnose

# 5. Manual verification
cd backend
.venv/bin/python --version  # Should show Python 3.11.x
.venv/bin/python -c "import TTS"  # Should fail unless --with-tts was used
```

## Files Modified

1. `scripts/one.mjs` - Core launcher logic
2. `scripts/doctor.sh` - Python 3.11 check
3. `HOW-TO-START.md` - Documentation updates

## Files Created

1. `backend/requirements.core.txt` - Core dependencies
2. `backend/requirements.extras-tts.txt` - TTS extras
3. `PYTHON-3.11-MIGRATION.md` - This document

## Next Steps

1. Test on macOS with Python 3.13 only
2. Test on macOS with Python 3.11 installed
3. Test on Windows (regression test)
4. Verify error handling and logging
5. Update any CI/CD scripts if needed

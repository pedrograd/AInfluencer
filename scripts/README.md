# Deployment & Testing Scripts

## Deployment / Preflight

- `deploy-preflight.ps1` (Windows) / `deploy-preflight.sh` (Linux/Mac)
- Loads `.env`, `backend/.env`, and `web/.env.local` automatically (falls back to localhost/demo-safe defaults).
- Recommended flow: start the backend (`uvicorn main:app --host 0.0.0.0 --port 8000`) if you want `/api/health` to pass, then run the preflight. If the backend is stopped, the health probe will warn and continue.
- Runs: env guard, frontend build, backend import check, optional health ping.

## Anti-Detection Testing Scripts

Automated scripts for testing and monitoring anti-detection features.

## Available Scripts

### 1. `run-all-tests.ps1` / `test-anti-detection.sh`
Complete test suite runner. Runs all tests automatically.

**Windows:**
```powershell
.\scripts\run-all-tests.ps1
```

**Linux/Mac:**
```bash
./scripts/test-anti-detection.sh
```

### 2. `test_anti_detection.py`
Python test suite with detailed reporting.

```bash
cd backend
python test_anti_detection.py
```

### 3. `generate-test-image.py`
Generate test images for detection testing.

```bash
python scripts/generate-test-image.py --output test.png --width 1024 --height 1024
```

### 4. `monitor-detection-stats.py`
Monitor detection statistics continuously.

```bash
python scripts/monitor-detection-stats.py
```

## Quick Start

1. **Configure API keys** in `backend/.env`
2. **Run tests:**
   ```bash
   # Windows
   .\scripts\run-all-tests.ps1
   
   # Linux/Mac
   ./scripts/test-anti-detection.sh
   ```
3. **Review results** in `backend/test_output/`

## Documentation

See `docs/ANTI-DETECTION-TESTING-GUIDE.md` for complete documentation.

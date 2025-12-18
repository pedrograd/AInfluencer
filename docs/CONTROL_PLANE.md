# 🎯 CONTROL_PLANE — Single Source of Truth for AInfluencer

> **Last Updated:** 2025-01-16  
> **Version:** 1.0 (Master Plan)  
> **Status:** Active Planning & Implementation Document

---

## 1. Product North Star (1 page)

### Who It's For

**Non-technical creators** who want to:

- Create AI influencer characters
- Generate images and videos
- Manage content across platforms
- Analyze performance

**No coding required.** One-button promise: Install → Launch → Create character → Generate image/video.

### One-Button Promise

1. **Install**: Single command (`node scripts/one.mjs`) sets up everything
2. **Launch**: Automatically starts backend + frontend, opens dashboard
3. **Create Character**: Visual form to define appearance, personality, style
4. **Generate**: Click "Generate Image" → get results (if ComfyUI installed)

### Offline-First / Local-First Posture

- **Default**: Everything runs locally (backend, frontend, ComfyUI, models)
- **Optional**: Cloud connectors for platform APIs (Instagram, TikTok, etc.)
- **Data**: SQLite by default (MVP), optional Postgres for production
- **Models**: Downloaded and stored locally
- **No external dependencies required** for core functionality

---

## 2. Golden Path (Run)

### macOS

```bash
node scripts/one.mjs
```

### Windows

```bash
launch.bat
# OR
node scripts/one.mjs
```

**Note:** All wrappers (`launch.bat`, `launch.command`, `launch.sh`, `launch.ps1`) delegate to `node scripts/one.mjs`. No logic duplication.

### Ports & Health Endpoints

| Service  | Default Port | Health Endpoint                    | Fallback Ports          |
| -------- | ------------ | ---------------------------------- | ----------------------- |
| Backend  | 8000         | `http://localhost:8000/api/health` | 8001, 8002              |
| Frontend | 3000         | `http://localhost:3000`            | 3001, 3002              |
| ComfyUI  | 8188         | `http://localhost:8188`            | N/A (user configurable) |

### Logs Location

- **All logs**: `runs/launcher/<timestamp>/`
- **Latest run**: `runs/launcher/latest.txt` or `node scripts/one.mjs --diagnose`
- **Backend logs**: `runs/launcher/<timestamp>/backend.stdout.log`, `backend.stderr.log`
- **Frontend logs**: `runs/launcher/<timestamp>/frontend.stdout.log`, `frontend.stderr.log`
- **Doctor checks**: `runs/launcher/<timestamp>/doctor.log`
- **Error root cause**: `runs/launcher/<timestamp>/error_root_cause.json`

---

## 3. Current Known Issues — Root Cause Table

| Issue                                              | Symptoms                                                                  | Likely Root Cause                                                                                                | Fix Plan                                                                                           | Owner              | Acceptance Test                                                                                                             |
| -------------------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| **401 Authorization header missing**               | `POST /api/characters` fails with 401                                     | Auth dependency requires `Authorization: Bearer <token>` header, but frontend doesn't send it on localhost       | **B1**: Implement localhost dev mode that bypasses auth when request comes from localhost          | Backend            | `POST /api/characters` works from UI without manual headers on localhost                                                    |
| **422 missing `req`**                              | `POST /api/generate/image` fails 422                                      | API contract mismatch: backend expects `req` in JSON body, but frontend may send query params or wrong structure | **B2**: Ensure consistent JSON body schema (Pydantic model), improve error messages                | Backend + Frontend | Generate page can submit without 422; if ComfyUI not reachable, error is specifically "ComfyUI offline" with install CTA    |
| **500 analytics connection refused**               | `GET /api/analytics/overview` fails 500                                   | Database connection fails (Postgres not running or SQLite not initialized)                                       | **B3**: Implement SQLite default, graceful degradation when DB unavailable                         | Backend            | Analytics page does not show 500 on fresh setup; shows "not configured" state                                               |
| **ComfyUI unreachable + not installed**            | ComfyUI health check fails, default `http://localhost:8188` not reachable | ComfyUI not installed or not running                                                                             | **B4**: Add connector layer with health checks, setup flow with install button                     | Backend + Frontend | If ComfyUI missing: Setup page offers install; Generate page blocks with clear CTA. If installed: Generate works end-to-end |
| **No checkpoints/models; placeholder model links** | "No checkpoints found", Model Manager has placeholder links               | Model catalog is placeholder, no real download/install system                                                    | **B5**: Replace placeholders with minimal curated catalog, implement download queue with checksums | Backend + Frontend | "No checkpoints found" disappears after installing one model; Generate dropdown shows installed checkpoints                 |

---

## 4. Architecture (MVP)

### Frontend (UI)

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **API Client**: Fetch API with `apiGet`, `apiPost`, etc. (see `frontend/src/lib/api.ts`)

### Backend (FastAPI)

- **Framework**: FastAPI
- **Language**: Python 3.11 (required)
- **Database**: SQLite (default MVP) → Postgres (optional production)
- **Auth**: JWT tokens (optional on localhost for dev mode)
- **API**: RESTful endpoints under `/api/*`

### Engine Connectors

#### ComfyUI (Local) — Primary Engine

- **Status**: First-class engine (MVP)
- **Base URL**: `http://localhost:8188` (configurable via `AINFLUENCER_COMFYUI_BASE_URL`)
- **Health Check**: `GET http://localhost:8188/` or `/api/health` if available
- **Installation**: Manual or via setup flow (future)
- **Workflows**: Custom ComfyUI workflows for image generation

#### Optional Future Engines (Do NOT Implement Now)

- SD WebUI (Automatic1111)
- Fooocus
- InvokeAI

**Interface Definition** (for future):

```python
class EngineConnector:
    async def health_check() -> bool
    async def generate_image(prompt: str, params: dict) -> dict
    async def list_models() -> list[str]
```

### Data Store

- **MVP Default**: SQLite (`sqlite:///./ainfluencer.db`)
- **Production Optional**: PostgreSQL (`postgresql+asyncpg://...`)
- **Migration Path**: SQLite → Postgres (same schema, different connection string)

### Auth

- **MVP (Localhost)**:
  - Option 1 (fastest): If request comes from localhost, allow default dev auth mode (no header required)
  - Option 2: Frontend automatically attaches stored token (generated on first run) to every API call
- **Production**: JWT tokens with `Authorization: Bearer <token>` header
- **Settings**: "Settings → Security" can enable real auth. Default is "local dev mode" on localhost.

---

## 5. Installer & "Non-Technical Mode"

### Setup Page (Single Button)

The existing Setup page (`/installer`) becomes the single entry point:

**"Download & Install All" Button:**

1. Runs system checks (Python 3.11, Node.js, disk space, ports)
2. Installs backend dependencies (`requirements.core.txt`)
3. Installs frontend dependencies (`npm install`)
4. Downloads/installs ComfyUI (if user chooses)
5. Downloads model packs (if user chooses)
6. Verifies health (backend, frontend, ComfyUI)
7. Opens dashboard automatically

**Requirements:**

- **Idempotent**: Can run multiple times safely
- **Resumable**: If interrupted, can resume from last step
- **Progress**: Shows real-time progress with logs
- **Error Handling**: Clear error messages with fix steps

---

## 6. Roadmap (Phased)

### Phase 0: Stabilize API Contracts + Remove Auth Friction on Localhost

**Status**: In Progress  
**Tasks**:

- [x] B1: Localhost auth bypass (dev mode)
- [x] B2: Fix 422 missing `req` (API contract consistency)
- [x] B3: Analytics 500 → graceful degradation

**Acceptance**: All API endpoints work from UI on localhost without manual auth headers.

### Phase 1: ComfyUI Integration (Auto-Install + Health + Workflows)

**Status**: Planned  
**Tasks**:

- [ ] B4: ComfyUI connector with health checks
- [ ] Setup flow: Detect/Install/Start ComfyUI
- [ ] Environment override: `AINFLUENCER_COMFYUI_BASE_URL`
- [ ] UI: ComfyUI status box (accurate and actionable)

**Acceptance**: If ComfyUI missing, Setup offers install. If installed, Generate works end-to-end.

### Phase 2: Model Manager Real Catalog (No Placeholders) + Downloader + Checksums

**Status**: Planned  
**Tasks**:

- [ ] B5: Replace placeholder links with minimal curated catalog:
  - SDXL base, SDXL refiner
  - 1-2 popular photoreal checkpoints (legally redistributable)
  - 3-5 essential ControlNet models
  - Minimal LoRA starter pack (optional)
- [ ] Download queue with progress
- [ ] SHA256 checksum verification
- [ ] Resume support
- [ ] Install location mapping (ComfyUI folders or shared models dir + symlinks)
- [ ] UI: Installed vs available, disk impact, "Sync to ComfyUI" action

**Acceptance**: "No checkpoints found" disappears after installing one model. Generate dropdown shows installed checkpoints.

### Phase 3: Image Quality Pipeline (Skin Texture Fix, Anti-Wax, Identity Consistency) via Workflows

**Status**: Planned  
**Tasks**:

- [ ] D: Create 3 workflow presets:
  - Photoreal Portrait (anti-wax)
  - Full-body Photoreal (anti-plastic)
  - Cinematic (film grain, tone mapping)
- [ ] Optional post-processing toggles:
  - Face restoration (GFPGAN/CodeFormer)
  - Upscale (Real-ESRGAN)
- [ ] UI: Presets explainable with tooltips

**Acceptance**: Presets selectable; each preset has short tooltip describing what it optimizes.

### Phase 4: Video Pipeline (AnimateDiff/SVD/RIFE Optional) — Later

**Status**: Future  
**Scope**: Video generation workflows (not in MVP)

### Phase 5: Packaging (Tauri Recommended) — Last

**Status**: Future  
**Scope**: Desktop app packaging for distribution

---

## 7. Acceptance Criteria & Test Matrix

### Fresh Clone Test Steps

#### macOS

```bash
git clone <repo>
cd AInfluencer
node scripts/one.mjs
# Wait for services to start
# Open http://localhost:3000 (or port shown)
```

**Expected**:

- ✅ Dashboard loads
- ✅ Create Character page works (no 401)
- ✅ Generate page works (no 422, shows ComfyUI status)
- ✅ Analytics page works (no 500, shows "not configured" if DB missing)

#### Windows

```bash
git clone <repo>
cd AInfluencer
launch.bat
# OR
node scripts/one.mjs
# Wait for services to start
# Open http://localhost:3000 (or port shown)
```

**Expected**: Same as macOS

### Smoke Tests

| Test                                               | Steps                                           | Expected Result                                                            | Pass/Fail |
| -------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------- | --------- |
| **Dashboard loads**                                | Open `http://localhost:3000`                    | Dashboard renders without errors                                           | ✅/❌     |
| **Create Character succeeds**                      | Navigate to Create Character, fill form, submit | Character created, no 401 error                                            | ✅/❌     |
| **Generate image succeeds (if ComfyUI installed)** | Navigate to Generate, fill prompt, submit       | Job created, no 422 error                                                  | ✅/❌     |
| **Generate image (ComfyUI NOT installed)**         | Navigate to Generate                            | UI shows "ComfyUI not installed" with install CTA, no cryptic stack traces | ✅/❌     |
| **Analytics page does not 500**                    | Navigate to Analytics                           | Page loads, shows "not configured" if DB missing, shows data if configured | ✅/❌     |

---

## 8. Operational Discipline

### Error Taxonomy (Stable Enums)

```python
class ErrorCode(str, Enum):
    # Auth
    AUTH_MISSING = "AUTH_MISSING"
    AUTH_INVALID = "AUTH_INVALID"
    AUTH_EXPIRED = "AUTH_EXPIRED"

    # API Contract
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"

    # Dependencies
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    ENGINE_OFFLINE = "ENGINE_OFFLINE"
    DB_UNAVAILABLE = "DB_UNAVAILABLE"

    # Downloads
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    CHECKSUM_MISMATCH = "CHECKSUM_MISMATCH"
    DISK_FULL = "DISK_FULL"

    # Unknown
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
```

**Every thrown error must map to a taxonomy code + user-facing remediation steps.**

### Logs: What Goes Where

| Log Type             | Location                                          | Purpose                                    |
| -------------------- | ------------------------------------------------- | ------------------------------------------ |
| **Launcher logs**    | `runs/launcher/<timestamp>/`                      | Startup, health checks, service management |
| **Backend stdout**   | `runs/launcher/<timestamp>/backend.stdout.log`    | Backend application logs                   |
| **Backend stderr**   | `runs/launcher/<timestamp>/backend.stderr.log`    | Backend errors                             |
| **Frontend stdout**  | `runs/launcher/<timestamp>/frontend.stdout.log`   | Frontend build/dev server logs             |
| **Frontend stderr**  | `runs/launcher/<timestamp>/frontend.stderr.log`   | Frontend errors                            |
| **Doctor checks**    | `runs/launcher/<timestamp>/doctor.log`            | Preflight health checks                    |
| **Error root cause** | `runs/launcher/<timestamp>/error_root_cause.json` | Categorized errors with fix steps          |
| **Events**           | `runs/launcher/<timestamp>/events.jsonl`          | Structured event log                       |

### "How to File a Bug" Template

```markdown
## Bug Report

**Error Code**: [e.g., AUTH_MISSING, ENGINE_OFFLINE]
**Symptoms**: [What happened?]
**Steps to Reproduce**:

1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior**: [What should happen?]
**Actual Behavior**: [What actually happened?]

**Environment**:

- OS: [macOS/Windows/Linux]
- Python: [version]
- Node: [version]
- Backend Port: [8000/8001/8002]
- Frontend Port: [3000/3001/3002]

**Logs**:

- Latest run: `runs/launcher/<timestamp>/`
- Error root cause: `runs/launcher/<timestamp>/error_root_cause.json`

**Screenshots**: [If applicable]
```

---

## 9. Implementation Status

### Completed

- ✅ Golden path launcher (`node scripts/one.mjs`)
- ✅ Cross-platform wrappers (delegate to `one.mjs`)
- ✅ Structured logging (`runs/launcher/<timestamp>/`)
- ✅ Error root cause classification
- ✅ **B1: Localhost auth bypass** (2025-01-16) - Implemented dev mode that allows localhost requests without auth header
- ✅ **B2: Fix 422 missing `req`** (2025-01-16) - Added custom validation error handler with user-friendly messages
- ✅ **B3: Analytics graceful degradation** (2025-01-16) - Changed default DB to SQLite, added graceful degradation when DB unavailable
- ✅ **B4: ComfyUI integration** (2025-01-16) - Enhanced status endpoint with install/running/reachable detection, actionable CTAs in UI, environment variable override support
- ✅ **B5: Model Manager real catalog** (2025-01-16) - Replaced placeholder with minimal curated catalog (SDXL base/refiner, 5 ControlNet models), added resume support for downloads
- ✅ **Error Taxonomy System** (2025-01-16) - Implemented stable error codes enum, automatic error classification, user-facing remediation steps, integrated into middleware and validation handlers
- ✅ **Auto-Fix Mechanism** (2025-01-16) - Added comprehensive repair endpoint that re-runs doctor checks, repairs venv, reinstalls deps, checks ports, and checks ComfyUI health
- ✅ **UX Simplification** (2025-01-16) - Redesigned navigation into Setup/Create/Generate/Library modes with Advanced toggle, Setup is homepage on first run until system is configured
- ✅ **Quality Pipelines** (2025-01-16) - Created 3 workflow presets (Photoreal Portrait, Full-body Photoreal, Cinematic) with optional post-processing toggles (face restoration, upscale, film grain, tone mapping)

### In Progress

- (None currently)

### Planned

- ⏳ B4: ComfyUI integration
- ⏳ B5: Model Manager real catalog
- ⏳ C: UX simplification
- ⏳ D: Quality pipelines
- ⏳ E: Auto-fix mechanism

---

## 10. Change Log

### 2025-01-16

- Created CONTROL_PLANE.md with master plan structure
- Documented current known issues and root causes
- Defined roadmap phases
- Established error taxonomy and operational discipline
- **Implemented B1**: Localhost auth bypass - Modified `get_current_user_from_token` to detect localhost requests and create/return default dev user in dev mode
- **Implemented B2**: Fixed 422 validation errors - Added custom `RequestValidationError` handler in `main.py` with user-friendly error messages
- **Implemented B3**: Analytics graceful degradation - Changed default database to SQLite, updated database.py to handle SQLite properly, added graceful degradation in analytics endpoint when DB unavailable
- **Implemented B4**: ComfyUI integration - Enhanced `/api/comfyui/status` endpoint with comprehensive status (installed/running/reachable), added `action_required` field for UI CTAs, fixed environment variable override bug, updated frontend Generate page with Install/Start buttons
- **Implemented B5**: Model Manager real catalog - Replaced single placeholder model with minimal curated catalog (SDXL base 1.0, SDXL refiner 1.0, 5 essential ControlNet models), added resume support for interrupted downloads using HTTP Range headers, maintained SHA256 checksum verification
- **Implemented Error Taxonomy System**: Created `backend/app/core/error_taxonomy.py` with stable ErrorCode enum (AUTH_MISSING, CONTRACT_MISMATCH, DEPENDENCY_MISSING, ENGINE_OFFLINE, etc.), automatic error classification function, user-facing remediation steps for each error type, integrated into middleware and validation handlers
- **Implemented Auto-Fix Mechanism**: Added `/api/installer/repair` endpoint that performs comprehensive system repair (re-runs doctor checks, repairs venv if Python version mismatch, reinstalls deps if corrupted, checks port availability, checks ComfyUI health), added "Repair System" button to Setup page with results display
- **Implemented UX Simplification**: Created `MainNavigation` component with 4 main modes (Setup, Create, Generate, Library) and Advanced toggle for advanced features (Models, Analytics, Workflows, ComfyUI, Settings), updated layout to include navigation on all pages, added first-run detection that redirects to Setup if installer hasn't succeeded
- **Implemented Quality Pipelines**: Added 3 quality workflow presets to `backend/app/api/presets.py`:
  - **Photoreal Portrait**: Anti-wax skin texture, optimized for natural skin detail (40 steps, dpmpp_2m, karras scheduler)
  - **Full-body Photoreal**: Anti-plastic appearance, natural body proportions (45 steps, 1024x1536)
  - **Cinematic**: Film grain and tone mapping, dramatic lighting (35 steps, 1536x1024, Reinhard tone mapping)
  - Each preset includes post-processing options (face restoration, upscale, film grain, tone mapping) with UI toggles
  - Updated frontend Generate page to show quality presets first (⭐ indicator) and display post-processing toggles when quality preset is selected
- **Updated requirements**: Added `aiosqlite==0.20.0` to `requirements.core.txt` for SQLite async support

---

_This document is the single source of truth for AInfluencer planning and implementation. All changes must be logged here._

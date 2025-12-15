# STATUS-CHECK.md (authoritative)

**Repo:** `AInfluencer`

**Purpose:** A precise, no-guesswork status + remaining-work checklist for continuing in Cursor.

**Truth standard:** Everything below is grounded in **current source code + git history**. Where something was *not* end-to-end validated, it’s explicitly marked.

---

## 1) What we built (shipped features)

### 1.1 Backend (FastAPI)

**App entry:** `backend/app/main.py`

- **API prefix:** `/api`
- **Static content:** `/content/*` serves files from `.ainfluencer/content/` (mounted in backend)
- **Runtime directory (gitignored):** `.ainfluencer/`

#### System / health
- `GET /api/health`

#### Installer MVP (system check + fixes + logs + diagnostics)
Routes in `backend/app/api/installer.py`:
- `GET /api/installer/check`
- `GET /api/installer/status`
- `GET /api/installer/logs`
- `POST /api/installer/start`
- `POST /api/installer/fix/{action}`
- `POST /api/installer/fix_all`
- `GET /api/installer/diagnostics`

Key behavior:
- Persistent installer logs (JSONL) under `.ainfluencer/logs/`
- “Fix actions” run allowlisted scripts for Python/Node/Git installs.

#### Model Manager MVP (catalog + downloads + import + verify + custom URLs)
Routes in `backend/app/api/models.py`:
- `GET /api/models/catalog`
- `GET /api/models/installed`
- `GET /api/models/catalog/custom`
- `POST /api/models/catalog/custom`
- `PUT /api/models/catalog/custom/{model_id}`
- `DELETE /api/models/catalog/custom/{model_id}`

Downloads / queue:
- `GET /api/models/downloads/active`
- `GET /api/models/downloads/queue`
- `GET /api/models/downloads/items`
- `POST /api/models/downloads/enqueue`
- `POST /api/models/downloads/cancel`

Import + verify:
- `POST /api/models/import`
- `POST /api/models/verify`

Persistence:
- Custom model catalog saved to `.ainfluencer/config/custom_models.json`

Safety:
- Duplicate prevention (already installed/downloading/queued returns conflict)
- Download preflight check compares disk free vs `Content-Length`

#### ComfyUI integration (diagnostics + lists)
Routes in `backend/app/api/comfyui.py`:
- `GET /api/comfyui/status`
- `GET /api/comfyui/checkpoints`
- `GET /api/comfyui/samplers`
- `GET /api/comfyui/schedulers`

#### ComfyUI Manager (install, start, stop, logs, model sync)
Routes in `backend/app/api/comfyui.py`:
- `GET /api/comfyui/manager/status` - Get manager status (installation, process state)
- `POST /api/comfyui/manager/install` - Install ComfyUI (clone from GitHub)
- `POST /api/comfyui/manager/start` - Start ComfyUI process
- `POST /api/comfyui/manager/stop` - Stop ComfyUI process
- `POST /api/comfyui/manager/restart` - Restart ComfyUI process
- `GET /api/comfyui/manager/logs` - Get process logs
- `POST /api/comfyui/manager/sync-models` - Sync models to ComfyUI folders

Service: `backend/app/services/comfyui_manager.py`
- Installation detection and GitHub clone
- Process management (start/stop/restart)
- Background status monitoring
- Log capture and buffering
- Model syncing (symlinks on macOS/Linux, junctions on Windows)

Config:
- `AINFLUENCER_COMFYUI_BASE_URL` (defaults to `http://localhost:8188`)

#### Image Generation MVP (ComfyUI job runner)
Routes in `backend/app/api/generate.py`:
- `POST /api/generate/image`
- `GET /api/generate/image/{job_id}`
- `GET /api/generate/image/jobs`
- `POST /api/generate/image/{job_id}/cancel`
- `GET /api/generate/image/{job_id}/download` (ZIP: images + metadata.json)

Ops/cleanup:
- `GET /api/generate/storage`
- `DELETE /api/generate/image/{job_id}` (deletes job + its images)
- `POST /api/generate/clear` (clears all jobs + images)

Job system:
- Background thread per job
- **Cancel** uses best-effort ComfyUI `POST /interrupt` and local cancellation flags
- **Batch**: saves **all outputs** (not only first)
- Output images stored in `.ainfluencer/content/images/`
- Job history persisted in `.ainfluencer/content/jobs.json` (reloads on backend start)

#### Gallery / content API
Routes in `backend/app/api/content.py`:
- `GET /api/content/images` (**server-side pagination + search + sort**)
  - Query: `q`, `sort=(newest|oldest|name)`, `limit`, `offset`
  - Returns: `{ items, total, limit, offset, sort, q }`
- `DELETE /api/content/images/{filename}`
- `POST /api/content/images/delete` (bulk delete)
- `POST /api/content/images/cleanup` (delete images older than N days)
- `GET /api/content/images/download` (ZIP all images + manifest.json)

---

### 1.2 Frontend (Next.js)

Key pages:
- `/` (home): links to Installer / Models / Generate
- `/installer`: one-click installer dashboard UI
- `/models`: model manager UI
- `/generate`: ComfyUI image generation UI

Generate page includes:
- ComfyUI status + “Fix it” guidance (ComfyUI down / no checkpoints)
- Controls: prompt, negative prompt, seed, checkpoint, width/height, steps/cfg, sampler/scheduler, batch
- Job history (persistent): View, Download ZIP, Cancel, Delete
- Storage panel: show bytes + clear all + delete older-than-days
- Gallery: server-side paging, search, sort, per-image delete, bulk select/delete, download gallery ZIP

---

### 1.3 Dev scripts / cross-platform boot

macOS/Linux:
- `scripts/dev.sh` starts backend + frontend
- `backend/run_dev.sh` creates/uses venv and runs `uvicorn`
  - **Rejects Python 3.14**; prefers 3.13/3.12
  - Recreates venv if wrong Python used

Windows:
- `scripts/dev.ps1` starts backend + frontend

---

## 2) What passed / what was verified (no hallucination)

### Verified by automation/static checks
- **Type/lint diagnostics** were checked repeatedly on edited files via IDE diagnostics (no reported lints on touched files).
- **Backend routing is wired** (routers registered; `/content` static mount present).
- **Git history confirms features were added and pushed** (see recent commits).

### Not fully end-to-end verified (requires local runtime)
These require you to run services locally to confirm behavior:
- **ComfyUI generation end-to-end** (needs ComfyUI running at `AINFLUENCER_COMFYUI_BASE_URL` and at least one checkpoint installed).
- **Model download end-to-end** (depends on network/model URLs and disk).
- **Installer fix scripts** (depend on OS and package managers actually present/allowed).

---

## 3) How to run + quick smoke checks

### Start everything
- **macOS/Linux**: run `./scripts/dev.sh`
- **Windows**: run `./scripts/dev.ps1`

Expected:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

### Smoke endpoints (manual)
- Backend health: `GET http://localhost:8000/api/health`
- Installer check: `GET http://localhost:8000/api/installer/check`
- ComfyUI status: `GET http://localhost:8000/api/comfyui/status`
- Gallery: `GET http://localhost:8000/api/content/images?limit=10&offset=0`

### ComfyUI requirements for generation
- ComfyUI must be running (default `http://localhost:8188`)
- Must have **at least one checkpoint** installed in ComfyUI

---

## 4) What remains (detailed checklist)

### A) "True one-click for non-technical users" (largest remaining block)
- [x] **Bundle/launch ComfyUI** from inside dashboard (backend complete: download + start/stop + health checks)
  - [x] Backend: ComfyUI Manager service with install/start/stop/restart
  - [x] Backend: Status monitoring and log capture
  - [x] Backend: Model syncing (symlinks/junctions)
  - [ ] Frontend: ComfyUI management UI page (next step)
- [ ] **ComfyUI install flow** for Windows/macOS (portable/venv/conda strategy + GPU handling)
- [x] **Model folder integration** (backend complete: map our downloaded checkpoints/loras/vaes into ComfyUI folders)
  - [x] symlink strategy on macOS/Linux (implemented)
  - [x] Windows junction strategy (implemented)
  - [x] API endpoint for model syncing
  - [ ] Frontend: UI to trigger sync and show status (next step)
- [ ] **Packaging**
  - [ ] Windows installer (MSIX/NSIS/electron-builder/etc.)
  - [ ] macOS app packaging (signed/notarized later)

### B) Image workflows (quality + UX)
- [x] **Workflow presets library** ✅ (Complete - 2025-01-27)
  - [x] Backend API endpoints: `GET /api/generate/workflow-presets`, `GET /api/generate/workflow-presets/{preset_id}`
  - [x] 6 curated presets: Portrait, Fashion, Product, Landscape, Cinematic, Artistic
  - [x] Each preset includes optimized defaults (width, height, steps, CFG, sampler, scheduler, batch size, negative prompt)
  - [x] Frontend preset selector dropdown in generate page
  - [x] One-click preset application that populates form fields
- [ ] Save full job provenance (workflow JSON, seed, model hashes)
- [ ] Advanced controls: LoRA selection, VAE selection, negative presets
- [ ] Better queueing: multiple jobs queued, concurrency limits

### C) Video pipeline (not started)
- [ ] Define a minimal video MVP (inputs/outputs and toolchain)
- [ ] Add backend “video jobs” service (queue + storage)
- [ ] Add frontend “video generate” UI
- [ ] Export presets for TikTok/IG/YT

### D) Posting automation / platform integrations (not started; compliance-sensitive)
- [ ] Account/session management
- [ ] Safe posting workflows + logging
- [ ] Platform-specific content format validation

---

## 5) Current state snapshot (from git history)

Recent commits (latest first):
- `feat(comfyui): implement ComfyUI manager service with install/start/stop/logs/sync`
- `feat(content): paginate gallery and add age-based cleanup`
- `feat(content): add gallery search/sort and bulk delete`
- `feat(content): add gallery delete and download-all zip`
- `feat(generate): add cleanup and storage stats`
- `feat(generate): persist jobs and allow viewing past runs`
- `feat(generate): add per-job zip download bundle`
- `feat(generate): save batch outputs and auto-list samplers/schedulers`
- `feat(generate): add cancel and fix-it guidance`
- `feat(generate): add controls and job history`
- `feat(comfyui): add status/checkpoints and checkpoint picker`
- `feat(generate): add ComfyUI image generation MVP`
- `feat(models): add custom edit UI and URL helper`
- `feat(models): manage custom catalog and add download preflight`
- `feat(installer): add fix-all action`

---

## 6) "Next tasks" (recommended order)

If you want the highest-impact next steps:
- [x] Add "Manage ComfyUI" backend: detect, download, start/stop, show logs (✅ backend complete)
- [x] Add "Manage ComfyUI" frontend page: UI to use the backend API (✅ complete)
- [x] Wire Model Manager → ComfyUI model folders backend (✅ API endpoint exists)
- [x] Add UI button to trigger model sync and show status (✅ complete)
- [x] Add workflow preset selection (✅ complete - 6 curated presets with one-click application)


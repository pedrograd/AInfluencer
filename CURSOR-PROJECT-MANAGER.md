# Cursor Project Manager - Executive Context Prompt

> **⚠️ DEPRECATED:** This file is being consolidated into `docs/CONTROL_PLANE.md`.  
> **Please use:** `docs/CONTROL_PLANE.md` as the single source of truth for project governance and state.  
> This file is kept for reference only and will be moved to `/deprecated/` after all references are updated.

**Purpose:** This document serves as the authoritative context for every new Cursor chat session. When you start a new chat, you are acting as the **CEO/CTO/CPO** of the AInfluencer project. Your role is to understand the complete project state, prioritize remaining work, and execute tasks efficiently.

**How to Use:** Copy the relevant sections below into your Cursor chat when starting a new session, or simply reference this file. The AI will automatically understand the project state and can execute tasks with minimal context.

---

## 🚀 Autopilot System (Primary Workflow)

**IMPORTANT:** This repository uses a one-word command Autopilot system. See `.cursor/rules/autopilot-protocol.md` for complete details.

**Quick Start:**
- **Fastest path:** Use a single chat and type `AUTO` repeatedly.
- **One-word commands:** `STATUS`, `SCAN`, `PLAN`, `DO`, `SAVE`, `AUTO`, `NEXT`, `UNLOCK`
- **Multi-chat safety:** Only ONE chat may write changes (AUTO/DO/SAVE). All other chats must be read-only (STATUS only).

**Source of Truth (SINGLE-FILE GOVERNANCE v4):**
- `docs/CONTROL_PLANE.md` - **ONLY** governance/state/tasks/logs source (MUST READ on every chat)
- Deprecated files in `docs/deprecated/202512/` are read-only historical reference
- All tasks are in CONTROL_PLANE.md TASK_LEDGER section
- All state is in CONTROL_PLANE.md DASHBOARD section
- All logs are in CONTROL_PLANE.md RUN LOG section

**Core Principles:**
1. No hallucinations - Never invent tasks. Only extract from docs.
2. No task loss - Never delete tasks. Only change status: TODO → DOING → DONE.
3. Evidence & Tests required - DONE tasks must include evidence (files) + tests (commands + results).
4. Single Writer Lock - Only one chat session may modify files at a time.
5. Cost discipline - Always read `docs/00_STATE.md` first. Read additional docs only when needed.

For complete protocol details, see: `.cursor/rules/autopilot-protocol.md` or `.cursor/rules/main.md`

---

## 🎯 Your Role & Responsibilities

You are the **executive leadership** (CEO/CTO/CPO) of the AInfluencer project. Your responsibilities include:

1. **Project State Awareness**: Always know what's built, what's tested, what's pending, and what needs implementation
2. **Task Prioritization**: Understand which tasks are highest priority and why
3. **Quick Execution**: Execute tasks with minimal back-and-forth using the quick action commands
4. **Quality Assurance**: Ensure code quality, testing, and documentation standards
5. **Strategic Planning**: Make architectural decisions and guide development direction

---

## 📊 Project Overview

**Project Name:** AInfluencer  
**Type:** Fully automated, self-hosted AI influencer platform  
**Stack:** Next.js 14 (Frontend) + FastAPI (Backend) + Python 3.11+  
**Status:** Active Development - Phase 1 (Foundation)  
**Repository:** `/Users/pedram/AInfluencer`

### Core Value Propositions
- ✅ Fully Automated: Zero manual intervention required
- ✅ Free & Open-Source: No costs, full source code access
- ✅ Ultra-Realistic: Indistinguishable from real content
- ✅ Multi-Platform: Instagram, Twitter, Facebook, Telegram, OnlyFans, YouTube
- ✅ Character Consistency: Advanced face/style consistency
- ✅ Self-Hosted: Privacy and data control
- ✅ +18 Support: Built-in adult content generation

---

## 📁 Critical Files to Always Reference

Before starting any task, read these files to understand current state:

1. **`STATUS-CHECK.md`** - Authoritative status of what's built and verified
2. **`PROJECT-STATUS.md`** - Real-time project status (updated after each session)
3. **`QUICK-ACTIONS.md`** - Quick command reference for common tasks
4. **`docs/PRD.md`** - Complete product requirements
5. **`docs/03-FEATURE-ROADMAP.md`** - Development phases and roadmap
6. **`docs/01-PROJECT-OVERVIEW.md`** - Extended vision and goals

---

## ✅ What's Built & Shipped (Verified)

### Backend (FastAPI) - `/backend/app/`

#### System & Health
- ✅ `GET /api/health` - Health check endpoint
- ✅ Static content serving from `.ainfluencer/content/`
- ✅ Runtime directory management (`.ainfluencer/`)

#### Installer MVP (`backend/app/api/installer.py`)
- ✅ `GET /api/installer/check` - System requirements check
- ✅ `GET /api/installer/status` - Installation status
- ✅ `GET /api/installer/logs` - Installation logs
- ✅ `POST /api/installer/start` - Start installation
- ✅ `POST /api/installer/fix/{action}` - Fix specific issues
- ✅ `POST /api/installer/fix_all` - Fix all issues
- ✅ `GET /api/installer/diagnostics` - System diagnostics
- ✅ Persistent installer logs (JSONL) under `.ainfluencer/logs/`
- ✅ Allowlisted fix scripts for Python/Node/Git installs

#### Model Manager MVP (`backend/app/api/models.py`)
- ✅ `GET /api/models/catalog` - Browse model catalog
- ✅ `GET /api/models/installed` - List installed models
- ✅ `GET /api/models/catalog/custom` - Custom model catalog
- ✅ `POST /api/models/catalog/custom` - Add custom model
- ✅ `PUT /api/models/catalog/custom/{model_id}` - Update custom model
- ✅ `DELETE /api/models/catalog/custom/{model_id}` - Delete custom model
- ✅ `GET /api/models/downloads/active` - Active downloads
- ✅ `GET /api/models/downloads/queue` - Download queue
- ✅ `GET /api/models/downloads/items` - Download items
- ✅ `POST /api/models/downloads/enqueue` - Queue download
- ✅ `POST /api/models/downloads/cancel` - Cancel download
- ✅ `POST /api/models/import` - Import model
- ✅ `POST /api/models/verify` - Verify model
- ✅ Custom model catalog persistence (`.ainfluencer/config/custom_models.json`)
- ✅ Duplicate prevention (installed/downloading/queued)
- ✅ Download preflight check (disk space validation)

#### ComfyUI Integration (`backend/app/api/comfyui.py`)
- ✅ `GET /api/comfyui/status` - ComfyUI connection status
- ✅ `GET /api/comfyui/checkpoints` - List available checkpoints
- ✅ `GET /api/comfyui/samplers` - List samplers
- ✅ `GET /api/comfyui/schedulers` - List schedulers
- ✅ Configurable ComfyUI base URL (`AINFLUENCER_COMFYUI_BASE_URL`)

#### ComfyUI Manager MVP (`backend/app/services/comfyui_manager.py` + `backend/app/api/comfyui.py` + `frontend/src/app/comfyui/page.tsx`)
- ✅ **ComfyUI Manager Service** - Complete backend implementation
  - ✅ Installation detection and GitHub clone support
  - ✅ Process management (start, stop, restart)
  - ✅ Background status monitoring (process state + HTTP availability)
  - ✅ Log management (stdout/stderr capture and buffering)
  - ✅ Model syncing (symlinks on macOS/Linux, junctions on Windows)
- ✅ **Manager API Endpoints** (`/api/comfyui/manager/*`)
  - ✅ `GET /api/comfyui/manager/status` - Get manager status
  - ✅ `POST /api/comfyui/manager/install` - Install ComfyUI
  - ✅ `POST /api/comfyui/manager/start` - Start ComfyUI
  - ✅ `POST /api/comfyui/manager/stop` - Stop ComfyUI
  - ✅ `POST /api/comfyui/manager/restart` - Restart ComfyUI
  - ✅ `GET /api/comfyui/manager/logs` - Get process logs
  - ✅ `POST /api/comfyui/manager/sync-models` - Sync models to ComfyUI folders
- ✅ **Frontend UI** - Complete (`frontend/src/app/comfyui/page.tsx`)
  - ✅ Real-time status display with auto-refresh
  - ✅ Action buttons: Install, Start, Stop, Restart, Sync Models
  - ✅ Log viewer with color-coded levels
  - ✅ Error handling and loading states
  - ✅ Added link to home page

#### Image Generation MVP (`backend/app/api/generate.py`)
- ✅ `POST /api/generate/image` - Generate image
- ✅ `GET /api/generate/image/{job_id}` - Get job status
- ✅ `GET /api/generate/image/jobs` - List all jobs
- ✅ `POST /api/generate/image/{job_id}/cancel` - Cancel job
- ✅ `GET /api/generate/image/{job_id}/download` - Download ZIP (images + metadata)
- ✅ `GET /api/generate/storage` - Storage statistics
- ✅ `DELETE /api/generate/image/{job_id}` - Delete job + images
- ✅ `POST /api/generate/clear` - Clear all jobs + images
- ✅ Background thread per job
- ✅ Cancel support (ComfyUI interrupt + local flags)
- ✅ Batch output saving (all outputs, not just first)
- ✅ Output images stored in `.ainfluencer/content/images/`
- ✅ Job history persisted (`.ainfluencer/content/jobs.json`)

#### Gallery / Content API (`backend/app/api/content.py`)
- ✅ `GET /api/content/images` - Server-side pagination + search + sort
  - Query params: `q`, `sort=(newest|oldest|name)`, `limit`, `offset`
  - Returns: `{ items, total, limit, offset, sort, q }`
- ✅ `DELETE /api/content/images/{filename}` - Delete single image
- ✅ `POST /api/content/images/delete` - Bulk delete
- ✅ `POST /api/content/images/cleanup` - Delete images older than N days
- ✅ `GET /api/content/images/download` - Download ZIP (all images + manifest)

### Frontend (Next.js) - `/frontend/src/app/`

#### Pages
- ✅ `/` - Home page (links to Installer / Models / Generate / ComfyUI Manager)
- ✅ `/installer` - One-click installer dashboard UI
- ✅ `/models` - Model manager UI
- ✅ `/generate` - ComfyUI image generation UI
- ✅ `/comfyui` - ComfyUI Manager UI (install, start, stop, restart, logs, sync models)

#### Generate Page Features
- ✅ ComfyUI status + "Fix it" guidance
- ✅ Controls: prompt, negative prompt, seed, checkpoint, width/height, steps/cfg, sampler/scheduler, batch
- ✅ Job history (persistent): View, Download ZIP, Cancel, Delete
- ✅ Storage panel: show bytes + clear all + delete older-than-days
- ✅ Gallery: server-side paging, search, sort, per-image delete, bulk select/delete, download gallery ZIP

### Dev Scripts
- ✅ `scripts/dev.sh` - macOS/Linux dev startup
- ✅ `scripts/dev.ps1` - Windows dev startup
- ✅ `backend/run_dev.sh` - Backend dev script (creates/uses venv, rejects Python 3.14)

---

## 🧪 What's Tested & Verified

### Verified by Automation/Static Checks
- ✅ Type/lint diagnostics checked on edited files
- ✅ Backend routing wired (routers registered, `/content` static mount present)
- ✅ Git history confirms features added and pushed

### Not Fully End-to-End Verified (Requires Local Runtime)
These require local runtime to confirm:
- ⚠️ ComfyUI generation end-to-end (needs ComfyUI running + checkpoint installed)
- ⚠️ Model download end-to-end (depends on network/model URLs and disk)
- ⚠️ Installer fix scripts (depends on OS and package managers)

---

## 🚧 What Remains (Priority Order)

### A) "True One-Click for Non-Technical Users" (Highest Priority)

#### ComfyUI Bundle & Launch
- [x] **Backend: Bundle/launch ComfyUI** ✅ (Complete)
  - [x] Download ComfyUI automatically (API endpoint exists)
  - [x] Start/stop ComfyUI from dashboard (API endpoints exist)
  - [x] Health checks and status monitoring (background thread)
  - [x] Log viewing in dashboard (API endpoint exists)
- [x] **Frontend: ComfyUI Management UI** ✅ (Complete)
  - [x] Create `/comfyui` page in frontend
  - [x] Connect to backend API endpoints
  - [x] Real-time status updates
  - [x] Log viewer component

#### ComfyUI Install Flow
- [ ] **ComfyUI install flow** for Windows/macOS
  - [ ] Portable/venv/conda strategy
  - [ ] GPU handling (CUDA/cuDNN detection)
  - [ ] Automatic dependency installation
  - [ ] Cross-platform compatibility

#### Model Folder Integration
- [x] **Backend: Model folder integration** ✅ (Complete)
  - [x] Symlink strategy on macOS/Linux (implemented)
  - [x] Windows junction strategy (implemented)
  - [x] Auto-sync downloaded models to ComfyUI folders (API endpoint exists)
- [x] **Frontend: Model sync UI** ✅ (Complete - 2025-01-27)
  - [x] Added "Sync to ComfyUI" button in Model Manager header
  - [x] Show sync status (success/error messages)
  - [ ] Verify ComfyUI sees installed models (UI feedback) - Optional enhancement

#### Packaging
- [ ] **Windows installer** (MSIX/NSIS/electron-builder/etc.)
- [ ] **macOS app packaging** (signed/notarized later)

### B) Image Workflows (Quality + UX)

- [ ] **Workflow presets library** (portrait, fashion, product, etc.)
- [ ] **Save full job provenance** (workflow JSON, seed, model hashes)
- [ ] **Advanced controls**: LoRA selection, VAE selection, negative presets
- [ ] **Better queueing**: Multiple jobs queued, concurrency limits

### C) Video Pipeline (Not Started)

- [ ] **Define minimal video MVP** (inputs/outputs and toolchain)
- [ ] **Add backend "video jobs" service** (queue + storage)
- [ ] **Add frontend "video generate" UI**
- [ ] **Export presets** for TikTok/IG/YT

### D) Posting Automation / Platform Integrations (Not Started; Compliance-Sensitive)

- [ ] **Account/session management**
- [ ] **Safe posting workflows + logging**
- [ ] **Platform-specific content format validation**

---

## 🎯 Recommended Next Tasks (Highest Impact)

If you want the highest-impact next steps, prioritize these:

1. **Add "Manage ComfyUI" Frontend Page** ✅ (Complete!)
   - ✅ Backend API complete (all endpoints implemented)
   - ✅ Create `/comfyui` page in frontend
   - ✅ Show installation status
   - ✅ Install/start/stop/restart buttons
   - ✅ Real-time status display
   - ✅ Log viewer component
   - ✅ Model sync button

2. **Wire Model Manager → ComfyUI model folders** ✅ (Complete - 2025-01-27)
   - ✅ Model sync API endpoint exists (`/api/comfyui/manager/sync-models`)
   - ✅ Symlinks/junctions implemented cross-platform
   - ✅ Added "Sync to ComfyUI" button in Model Manager page header
   - ✅ Show sync status in UI (success/error messages)
   - [ ] Verify ComfyUI sees installed models (UI feedback) - Optional enhancement

3. **Add workflow preset selection**
   - Simple curated list of workflows
   - Portrait, fashion, product, etc.
   - One-click workflow application

---

## 🚀 Quick Start Commands

### Start Development
```bash
# macOS/Linux
./scripts/dev.sh

# Windows
./scripts/dev.ps1
```

### Expected Endpoints
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

### Smoke Tests
- Backend health: `GET http://localhost:8000/api/health`
- Installer check: `GET http://localhost:8000/api/installer/check`
- ComfyUI status: `GET http://localhost:8000/api/comfyui/status`
- Gallery: `GET http://localhost:8000/api/content/images?limit=10&offset=0`

### ComfyUI Requirements for Generation
- ComfyUI must be running (default `http://localhost:8188`)
- Must have at least one checkpoint installed in ComfyUI

---

## 📋 Project Standards & Rules

### Code Quality
- Follow `.cursor/rules/project-standards.md`
- TypeScript strict mode enabled
- Python type hints required
- Comprehensive error handling
- Logging for all operations

### File Structure
- Backend: `/backend/app/`
- Frontend: `/frontend/src/app/`
- Documentation: `/docs/`
- Scripts: `/scripts/`

### Git Workflow
- Commit messages: `feat(scope): description`
- Examples: `feat(generate): add cancel and fix-it guidance`
- Keep commits atomic and meaningful

---

## 💡 How to Use This Document in Cursor

### Starting a New Chat Session

1. **Read Current State**: Always start by reading `PROJECT-STATUS.md` to see what changed since last session

2. **Quick Actions**: Use commands from `QUICK-ACTIONS.md` for common tasks:
   - "implement comfyui manager" → Creates ComfyUI management page
   - "add workflow presets" → Adds workflow preset system
   - "wire model sync" → Connects Model Manager to ComfyUI folders

3. **Context Awareness**: Reference this document when:
   - User asks "what's left?" → Check "What Remains" section
   - User asks "what's done?" → Check "What's Built & Shipped" section
   - User asks "what's next?" → Check "Recommended Next Tasks" section

4. **Task Execution**: When user gives a task:
   - Check if it's already built (search "What's Built")
   - Check if it's in "What Remains"
   - If new, add to appropriate section
   - Execute with full context from this document

### Example Interactions

**User:** "implement comfyui manager"  
**You:** Understand this means creating the "Manage ComfyUI" page from recommended tasks. Check what's already built (ComfyUI status endpoints exist), then implement the full UI with download/start/stop/logs.

**User:** "what's left?"  
**You:** Reference "What Remains" section, prioritize by "Recommended Next Tasks", and provide a clear summary.

**User:** "add workflow presets"  
**You:** Understand this is from "Image Workflows" section. Check existing generation API, then add preset system with UI.

---

## 🔄 Updating This Document

After completing any task:

1. **Update `PROJECT-STATUS.md`** with:
   - What was completed
   - What was tested
   - What's next

2. **Update this document** if:
   - New features are shipped (add to "What's Built")
   - Features are verified (move from "Not Verified" to "Verified")
   - Priorities change (update "Recommended Next Tasks")

3. **Update `STATUS-CHECK.md`** if:
   - Major features are completed
   - Verification status changes

---

## 📚 Additional Resources

- **Full PRD**: `docs/PRD.md` - Complete product requirements
- **Technical Architecture**: `docs/02-TECHNICAL-ARCHITECTURE.md`
- **Feature Roadmap**: `docs/03-FEATURE-ROADMAP.md`
- **AI Models Guide**: `docs/04-AI-MODELS-REALISM.md`
- **Content Strategy**: `docs/13-CONTENT-STRATEGY.md`

---

## 🎓 Your Executive Decision Framework

When making decisions, consider:

1. **User Impact**: Does this help non-technical users?
2. **Automation**: Does this reduce manual work?
3. **Quality**: Does this improve content quality?
4. **Scalability**: Can this handle 10+ characters?
5. **Maintainability**: Is this easy to maintain and extend?

---

**Last Updated:** Based on `STATUS-CHECK.md` and `PROJECT-STATUS.md`  
**Next Review:** After each major feature completion

---

*This document is your single source of truth for project state. Always reference it when starting a new chat session.*

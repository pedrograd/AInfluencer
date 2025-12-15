# 🧠 CONTROL_PLANE — Single Source of Truth (Autopilot)

> **Rule:** Only governance/docs come from this file; code files are allowed for implementation.
> **Last Updated:** 2025-12-15 17:38:29
> **Project:** AInfluencer

---

## 0) 🧭 DASHBOARD (Read First)

| Field | Value |
|---|---|
| **STATE_ID** | `STATE_001` |
| **STATUS** | 🟢 GREEN |
| **REPO_CLEAN** | `false` (3 modified) |
| **NEEDS_SAVE** | `true` |
| **LOCK** | `none` |
| **ACTIVE_EPIC** | `none` |
| **ACTIVE_TASK** | `none` |
| **LAST_CHECKPOINT** | `07b27b2` — `chore(autopilot): update checkpoint STATE_001 with commit hash` |
| **NEXT_MODE** | `SAVE` |

### 📊 Progress
- **DONE:** `40`
- **TODO:** `536`
- **Progress %:** `7%`  <!-- AUTO: compute = DONE/(DONE+TODO) -->

---

## 1) 🧩 OPERATING MODES (Commands)

Use one of these keywords as the user's message:

- `STATUS` → read this file, run quick repo sanity check, update Dashboard only.
- `PLAN` → select next EPIC/TASK from Backlog, write a plan + acceptance checklist.
- `DO` → implement the selected task(s) only (no planning rewrite).
- `SAVE` → run minimal tests + commit + write checkpoint entry.
- `AUTO` → PLAN → DO → SAVE in one pass.
- `BURST` → complete 3–7 **subtasks** inside one EPIC before SAVE (fast lane).
- `BLITZ` → complete **up to 50 micro-tasks** as one **WORK_PACKET** (batched, same-area changes), with **mini-checks every 10 items**, then one SAVE.

### ⚡ FAST PATH (Default behavior)
**Default:** Read CONTROL_PLANE.md + run `git status --porcelain` + `git log -1 --oneline` only.

**Deep Dive triggers (set Deep Dive Needed: true):**
- Schema/database changes detected
- Tests failing unexpectedly
- Unknown API endpoints referenced
- Missing implementation details in codebase
- Backlog item requires context from TASKS.md/PRD/ROADMAP

**When Deep Dive Needed = true:**
- Record in RUN LOG: why + which doc(s) read
- Set flag back to false after reading

### 📊 INVENTORY MODE (Rare, explicit)
**When to use:** Only when explicitly refreshing backlog counts or scanning full task inventory.

**Process:**
1. Set Deep Dive Needed: true
2. Scan TASKS.md or other long docs ONLY if needed
3. Update DONE/TODO counts in Dashboard
4. Refresh Backlog "Next 10" if stale
5. Record in RUN LOG: "INVENTORY MODE: scanned <files>, updated counts"

**Frequency:** Max once per 10+ runs, or when explicitly requested.

### 🚀 BURST POLICY
**When BURST is allowed:**
- ACTIVE_EPIC exists with clear subtasks (3–7 items)
- All subtasks have clear code targets (file paths)
- No blockers present
- Deep Dive Needed = false

**What stops BURST:**
- Missing requirements (create BLOCKER, set STATUS=YELLOW)
- Test failures (fix first, then continue)
- Ambiguous code targets (clarify in ACTIVE_TASK first)
- External dependency not available (create BLOCKER)

**BURST commit rule:** Only commit once at SAVE after completing all subtasks.

---

## 1B) 🧰 WORK PACKETS (Batching for speed)

**Goal:** Go faster **without** turning the repo into a mystery novel.

**WORK_PACKET definition:** a numbered list of micro-tasks that:
- touch the **same surface area** (same folder / same service)
- share the **same dependency context**
- can be verified with a **small test set**

**BLITZ rules (50 micro-tasks):**
- Only allowed when tasks are **micro** (tiny, localized, low-risk).
- Must be **same-area**: max 2 adjacent folders (e.g., `backend/app/api/*` + `backend/app/services/*`).
- No sweeping renames, no mass refactors, no large dependency upgrades.
- Never mark items DONE unless there is **evidence** (files changed + commands run).
- Run **mini-checks** every 10 items:
  - record `git diff --name-only`
  - run the cheapest relevant check (e.g., `python -m py_compile <changed_py_files>`)
- If any mini-check fails: stop, create a BLOCKER, set `STATUS=YELLOW`.

**WORK_PACKET format (must be used in PLAN):**
- **PACKET_ID:** `P-YYYYMMDD-HHMM`
- **SCOPE:** `backend|frontend|ai|docs|mixed`
- **AREA:** exact folders/files this packet may touch
- **ITEMS (max 50):**
  - [ ] PK-01 — ... (file target)
  - [ ] PK-02 — ... (file target)
  - ...
- **Mini-check cadence:** every 10 items (10/20/30/40/50)
- **Final checks:** the normal SAVE checks

**BLITZ acceptance:** After SAVE, the packet must be either:
- ✅ 100% completed, or
- 🟡 stopped with a BLOCKER + smallest next fix clearly written.

---

## 2) 🧱 GOVERNANCE (Fast but real)

### ✅ Minimum checks per SAVE
- [ ] `git status --porcelain` recorded
- [ ] relevant tests executed (pick smallest set)
- [ ] evidence recorded (changed files + commands + results)
- [ ] checkpoint appended (with commit hash)

### 🧪 Test selection policy (minimal)
- If **Python backend** changed → `python -m py_compile <changed_py_files>`
- If **Frontend** changed → run the smallest lint/build already used in repo
- If **DB/schema** changed → include migration note or blocker
- If unsure → do the cheapest sanity check first, escalate only if needed

---

## 3) 🗺️ WORK MAP (What exists + where)

### Services
- Backend: `backend/` (FastAPI)
- Frontend: `frontend/` (Next.js 16.0.10, TypeScript)
- AI/ComfyUI: `backend/app/services/comfyui_service.py`, `backend/app/services/comfyui_manager.py`

### Key entry points
- Backend main: `backend/app/main.py` (FastAPI app creation)
- API router: `backend/app/api/router.py` (aggregates all API routers)
- Service patterns: `backend/app/services/` (service managers, generation, content, etc.)
- Frontend entry: `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`

### Key API endpoints
- `/api/health` — Health check
- `/api/status` — Unified system status
- `/api/services/*` — Service orchestration (backend, frontend, comfyui)
- `/api/characters/*` — Character CRUD
- `/api/generate/*` — Image/text generation
- `/api/content/*` — Content library
- `/api/workflows/*` — Workflow catalog and execution
- `/api/models/*` — Model management

---

## 4) 🧾 ACTIVE WORK (Single writer)

### EPIC: <!-- ACTIVE_EPIC -->
**Goal:**  
**Why now:**  
**Definition of Done (DoD):**
- [ ] ...
- [ ] ...
**Risks:**
- ...
**Deep Dive Needed:** `false`  <!-- set true if must read other docs -->

### TASKS (within EPIC)
> Rule: At most **1 ACTIVE_TASK**. BURST may finish 3–7 subtasks; BLITZ uses a WORK_PACKET of up to 50 micro-tasks before SAVE.

### WORK_PACKET (BLITZ only)
**PACKET_ID:** `none`
**SCOPE:** `none`
**AREA:** `none`
**ITEMS:**
- (empty)

- [ ] **T-001** (tag: #backend #api) — ...
  - Subtasks:
    - [ ] ST-001.1 ...
    - [ ] ST-001.2 ...
  - Evidence targets (expected changed files):
    - `...`
  - Tests to run:
    - `...`

### 🚫 BLOCKERS (Prevent silent stalling)
> If work cannot proceed, create entry here. Set STATUS=YELLOW.

**Current blockers:**
- None

**Blocker format:**
- **B-YYYYMMDD-XXX** — Short description
  - **Why blocked:** ...
  - **What's needed:** ...
  - **Created:** YYYY-MM-DD HH:MM:SS

---

## 5) 🧠 DECISIONS (Short, useful)

- **D-0001:** Single-file control plane → reduces file reads per run → faster iterations → better autonomy

---

## 6) 🧷 RUN LOG (Append-only)

> Format: newest at top. Keep each run tight. Max 15 lines per entry (BLITZ runs may use up to 25 lines, but must stay structured).

### RUN 2025-12-15 18:00:00
**MODE:** `DO`  
**STATE_BEFORE:** `STATE_000`  
**SELECTED:** `OPTIMIZATION_TASK`  
**PLAN (if any):**
- Add FAST PATH, INVENTORY MODE, BURST POLICY, BLOCKERS sections to CONTROL_PLANE
- Create .cursor/rules/autopilot.md
**WORK DONE:**
- Added FAST PATH section with Deep Dive triggers
- Added INVENTORY MODE section (rare, explicit)
- Added BURST POLICY with start/stop conditions
- Added BLOCKERS subsection under ACTIVE WORK
- Created .cursor/rules/autopilot.md with CONTROL_PLANE-first rules
**COMMANDS RUN:**
- `git status --porcelain` → 2 modified, 2 untracked
- `git log -1 --oneline` → e99047c
**FILES CHANGED:**
- `docs/CONTROL_PLANE.md` (optimization sections added)
- `.cursor/rules/autopilot.md` (new)
**GOVERNANCE CHECKS:**
- Git cleanliness: PASS (recorded)
- Tests: N/A (docs only)
- Evidence: PASS
**STATE_AFTER:** `STATE_000`  
**NOTES / BLOCKERS:**
- Control plane optimization complete. Ready for BURST on next code task.

### RUN 2025-12-15 17:27:26
**MODE:** `STATUS`  
**STATE_BEFORE:** `STATE_000`  
**SELECTED:** `none`  
**PLAN (if any):**
- Initial setup of CONTROL_PLANE.md
**WORK DONE:**
- Created CONTROL_PLANE.md structure
- Populated WORK MAP with real paths
- Initialized Dashboard with current repo state
**COMMANDS RUN:**
- `git status --porcelain` → 2 modified files: docs/00_STATE.md, docs/_generated/EXEC_REPORT.md
- `git log -1 --oneline` → e99047c (HEAD -> main) chore(autopilot): checkpoint BOOTSTRAP_038 T-20251215-040 - content library management
**FILES CHANGED:**
- `docs/CONTROL_PLANE.md` (new)
**GOVERNANCE CHECKS:**
- Git cleanliness: PASS (2 modified files recorded)
- Tests: N/A (initialization only)
- Evidence: PASS
**STATE_AFTER:** `STATE_000`  
**NOTES / BLOCKERS:**
- Initial setup complete. Ready for first AUTO/PLAN/DO command.

---

## 7) 🧾 CHECKPOINT HISTORY (Append-only)

### CHECKPOINT STATE_001 — 2025-12-15 17:38:29
- **Commit:** `09f24ce` — `chore(autopilot): checkpoint STATE_001 OPTIMIZATION_TASK - control plane optimization`
- **What changed:** Added FAST PATH, INVENTORY MODE, BURST POLICY, BLOCKERS sections. Created .cursor/rules/autopilot.md
- **Evidence:** docs/CONTROL_PLANE.md (optimized), .cursor/rules/autopilot.md (new)
- **Tests:** N/A (docs only)
- **Status:** GREEN

### CHECKPOINT STATE_000 — 2025-12-15 17:27:26
- **Commit:** `e99047c` — `chore(autopilot): checkpoint BOOTSTRAP_038 T-20251215-040 - content library management`
- **What changed:** Initial CONTROL_PLANE.md setup
- **Evidence:** docs/CONTROL_PLANE.md (new)
- **Tests:** N/A (initialization)
- **Status:** GREEN

---

## 8) 📦 BACKLOG (Curated, not infinite)

> Keep only the next 10–30 items here. Archive older backlog below.

### Next 10 (priority order)
1. **T-20251215-007** — Canonical docs structure created (#docs #foundation)
   - Source: `docs/01_ROADMAP.md:24`
2. **T-20251215-008** — Unified logging system created (#backend #logging #foundation)
   - Source: `docs/01_ROADMAP.md:26`
3. **T-20251215-009** — Dashboard shows system status + logs (#frontend #dashboard #foundation)
   - Source: `docs/01_ROADMAP.md:27`
4. **T-20251215-034** — Install and configure Stable Diffusion (#ai #models #setup)
   - Source: `docs/TASKS.md:130`
5. **T-20251215-035** — Test image generation pipeline (#ai #testing)
   - Source: `docs/TASKS.md:132`
6. **T-20251215-036** — Character face consistency setup (IP-Adapter/InstantID) (#ai #characters)
   - Source: `docs/TASKS.md:134`
7. **T-20251215-041** — Multiple image styles per character (#ai #characters)
   - Source: `docs/TASKS.md:163`
8. **T-20251215-042** — Batch image generation (#ai #performance)
   - Source: `docs/TASKS.md:165`
9. **T-20251215-043** — Image quality optimization (#ai #quality)
   - Source: `docs/TASKS.md:167`
10. **T-20251215-044** — +18 content generation system (#ai #content #features)
    - Source: `docs/TASKS.md:169`

### Archive
<details>
<summary>Older backlog (500+ items)</summary>

See `docs/TASKS.md` for full backlog with all 536 TODO items.

</details>

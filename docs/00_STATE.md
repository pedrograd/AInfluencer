# STATE - Single Source of Truth

**Purpose:** This file is the canonical state machine. Every new chat session should read this first to understand where we are.

---

## READ_POLICY (LOW-COST DEFAULT)

**MUST_READ (Always):**
- `docs/00_STATE.md` - This file (single source of truth)

**OPTIONAL_READ (Only if task needs them):**
- `PROJECT-STATUS.md` - Recent status summary
- `CURSOR-PROJECT-MANAGER.md` - Project context
- `docs/07_WORKLOG.md` - Recent work history

**NEVER_BY_DEFAULT (Only on INVENTORY command or BOOTSTRAP state):**
- `docs/CONTROL_PLANE.md` - Contains consolidated governance and session history (see CONSOLIDATION_AUDIT section)
- All other docs in `docs/` unless explicitly needed for the task

**Rule:** In any new chat, read ONLY `docs/00_STATE.md` first. Read additional files ONLY if the task requires them.

---

## AUTO_MODE (FULL AUTONOMY, SAFE)

**Goal:** Allow one-word operation where the AI plans, executes, tests, logs, and updates state *without requiring human task selection*.

**AUTO_MODE:** ENABLED

**AUTO_POLICY (How tasks are chosen automatically):**
1) **Golden Path First (Foundation before features):**
   - Cross-platform launcher (double-click) + health checks
   - Unified run logging (runs/<timestamp>/summary.txt + events.jsonl + latest)
   - Dashboard system status + error visibility
2) **Then UX accelerators:** presets, model sync buttons, workflow catalog UI
3) **Then expansions:** new workflows, advanced presets, extra pages

**DEPENDENCY RULE:** A task cannot be executed if it depends on a missing foundation. If dependencies are missing, AUTO must select the prerequisite task.

**STOP CONDITIONS (Safety brakes):**
- Tests fail or a command errors → stop, set `STATUS: RED`, write the error + next fix into `CURRENT_BLOCKER`, and set `NEXT_ACTION` to the smallest fix.
- Missing critical information (ports, endpoints, script names) that cannot be discovered by quick grep → stop and ask *one* question.
- Risky change (mass refactor, deletes, sweeping renames) → stop and propose a smaller change.

**RECONCILIATION (Never lose work):**
On every new chat, the AI must:
- Read `docs/00_STATE.md`
- Run cheap checks (`git status --porcelain`, `git diff --name-only`)
- If code changed but docs not updated → set `NEEDS_SAVE: false` and run SAVE automatically.

**PROMISE:** In AUTO_MODE, you (the user) do not need to decide what’s next. The AI chooses the correct next step.

---

## COMMAND_PROTOCOL (One-Word Protocol)

**STATUS** → Read-only status check:
- Output short status summary
- Verify: `git status --porcelain`
- Check `docs/00_STATE.md` exists and parse key fields
- Check `docs/TASKS.md` exists and show counts (TODO/DOING/DONE)
- Do NOT modify files
- If the repo is locked by another session, still OK (read-only).

**SCAN** → Extract tasks from docs incrementally:
- Read `SCAN_CURSOR` and `SCAN_LIST` from this file
- Read next 2-4 docs files from SCAN_LIST starting at SCAN_CURSOR
- Extract actionable tasks, create Task IDs in `docs/TASKS.md`
- Advance SCAN_CURSOR and write back
- Append to `docs/CONTROL_PLANE.md` RUN LOG section
- Every extracted task MUST include Source: <file>:<line-range or section> so humans can verify it.
- Never invent tasks; only extract what is explicitly written (checkboxes, TODO keywords, requirements, missing features).

**PLAN** → Auto-select next task:
- Acquire lock (Single Writer rule)
- Read: `docs/00_STATE.md`, `docs/TASKS.md`, optional `docs/07_WORKLOG.md`
- If there is a DOING task already: keep it selected (do NOT switch tasks)
- Else: auto-prioritize using AUTO_POLICY and move the best TODO task to DOING
- Persist selection in `docs/00_STATE.md` (SELECTED_TASK_*) and `docs/TASKS.md`
- Output: selected task + next atomic step

**DO** (alias: **CONTINUE**) → Execute selected task safely in ONE atomic step:
- Acquire lock
- Read: `docs/00_STATE.md`, `docs/TASKS.md`, plus only the files needed for this atomic step
- Implement EXACTLY ONE atomic sub-step (keep it small and reversible)
- Run minimal tests (typecheck/lint + smallest smoke check)
- Write evidence: update task status/notes in `docs/TASKS.md`, append to `docs/07_WORKLOG.md`, append to `docs/CONTROL_PLANE.md` RUN LOG section
- If the whole task is done, move it to DONE (DONE requires Evidence + Tests recorded)
- If anything fails: stop immediately, set `STATUS: RED`, write the error into `CURRENT_BLOCKER`, set `NEXT_ACTION` to the smallest fix
- If code changed, set `NEEDS_SAVE: false`

**SAVE** → Checkpoint state (never lose work):
- Acquire lock
- Refresh EXECUTIVE_CAPSULE block in `docs/00_STATE.md` (update RUN_TS, STATE_ID, STATUS, NEEDS_SAVE, SELECTED_TASK_*, LAST_CHECKPOINT, REPO_CLEAN, CHANGED_FILES_THIS_RUN, TESTS_RUN_THIS_RUN, DOC_SOURCES_USED_THIS_RUN, EVIDENCE_SUMMARY, ADHERENCE_CHECK, RISKS/BLOCKERS, NEXT_3_TASKS)
- Append new checkpoint entry to `docs/CONTROL_PLANE.md` CHECKPOINT HISTORY section (duplicate capsule + deltas + doc adherence audit + risks/next steps)
- **Governance Checks (MANDATORY):** Run all checks and report PASS/FAIL in EXEC_REPORT:
  1. **Git Cleanliness Truth:** REPO_CLEAN equals actual `git status --porcelain` (empty = clean, non-empty = dirty)
  2. **NEEDS_SAVE Truth:** NEEDS_SAVE equals (repo dirty ? true : false)
  3. **Single-writer Lock:** One writer; lock cleared after SAVE completes
  4. **Task Ledger Integrity:** ≤ 1 DOING task; selected task exists in TASKS.md
  5. **Traceability:** Every new/updated task has Source: file:line-range
  6. **DONE Requirements:** DONE tasks include Evidence (changed files) + Tests (commands + results)
  7. **EXEC_REPORT Currency:** Latest Snapshot matches current STATE_ID + LAST_CHECKPOINT
  8. **State Progression:** STATE_ID increments only on successful checkpoint
  9. **No Silent Skips:** If something can't be executed, it must remain TODO with Source and a blocker note
- If any governance check FAILS:
  - Set `STATUS: YELLOW` in `docs/00_STATE.md`
  - Report failure in EXEC_REPORT governance block
  - Propose the smallest fix
  - Do NOT proceed to DO until fixed
- Ensure state files consistent: `docs/00_STATE.md`, `docs/TASKS.md`, `docs/07_WORKLOG.md`, `docs/CONTROL_PLANE.md`
- Run `git status --porcelain`
- Stage + commit with message: `chore(autopilot): checkpoint <STATE_ID> <SELECTED_TASK_ID>`
- Set `NEEDS_SAVE: false` after a successful commit
- Clear lock after successful commit

**AUTO** → Fully autonomous cycle (lowest-effort, safest default):
- Acquire lock
- **Definition:** STATUS → (SAVE if repo dirty or NEEDS_SAVE true) → PLAN → DO → SAVE
- **AUTO must ALWAYS end with SAVE** so governance files stay synced.
- Run STATUS first (read-only check)
- If repo is dirty (`git status --porcelain` returns non-empty) OR `NEEDS_SAVE: false`: run SAVE first (pre-save checkpoint)
- Then run: PLAN → DO → SAVE (post-save checkpoint)
- If blocked, stop and write blocker + smallest fix into `docs/00_STATE.md`
- The assistant must NOT tell the user to type SAVE unless:
  1. User made manual edits outside autopilot and wants a checkpoint without running a task
  2. A run aborted mid-cycle leaving repo dirty
  3. User explicitly requests "checkpoint now"

**NEXT** → Force-select next task (rare):
- Only when no DOING tasks OR current task blocked
- Persist new selection in 00_STATE and TASKS

**UNLOCK** → Clear stale lock (rare):
- Only if the lock is stale (>2 hours) OR you are certain no other session is writing
- Clears `LOCKED_BY`, `LOCK_REASON`, `LOCK_TIMESTAMP`
- Output: "UNLOCKED" and recommended next command (usually STATUS)

---

## SINGLE WRITER LOCK (Anti-Conflict)

**LOCKED_BY:** (empty - no active lock)
**LOCK_REASON:** 
**LOCK_TIMESTAMP:** 

**Lock Rules:**
**Multi-chat rule:** You may open multiple chats, but only ONE chat is allowed to acquire the lock and write changes. All other chats must stay in READ-ONLY MODE and may only run STATUS (or explain what they see). Do not run AUTO/DO/SAVE in multiple chats at once.
- Before editing any file, acquire the lock
- If LOCKED_BY is empty OR lock is stale (>2 hours), set LOCKED_BY to unique session id (timestamp) and proceed
- If LOCKED_BY is set and not yours, DO NOT EDIT files. Output: "READ-ONLY MODE: locked by <id>"

---

## SCAN STATE (Incremental Task Extraction)

**SCAN_LAST_RUN:** 2025-12-15T12:56:50
**SCAN_FILES_TOTAL:** 35
**SCAN_FILES_DONE:** 35
**SCAN_EXTRACTIONS:** 585
**SCAN_NEW_TASKS:** 564
**SCAN_SUMMARY:** If SCAN_FILES_DONE == SCAN_FILES_TOTAL, SCAN is complete. New SCAN runs continue incrementally (2–4 files per run) and only add truly new tasks (with sources).

**SCAN_CURSOR:** 35
**SCAN_LIST:** Stored explicitly here once created. If empty, SCAN must build it via `git ls-files docs/*.md | sort`, write it here, and then continue from SCAN_CURSOR.

**SCAN** → Extract tasks from docs incrementally:
- Read next 2-4 docs from SCAN_LIST starting at SCAN_CURSOR
- Extract actionable tasks, create Task IDs in TASKS.md
- Advance SCAN_CURSOR and write back
- De-duplicate: if similar task exists, append "Related sources" instead of creating new
- Every extracted task MUST include Source: <file>:<line-range or section> so humans can verify it.
- Never invent tasks; only extract what is explicitly written (checkboxes, TODO keywords, requirements, missing features).

---

## STATE_ID: BOOTSTRAP_041
**STATUS:** GREEN
**NEEDS_SAVE:** false
**LAST_COMMAND:** AUTO
**LAST_PASS:** Added artifact detection to image quality validator
**CURRENT_BLOCKER:** None
**NEXT_ACTION:** Continue implementing T-20251215-043 - add color/contrast checks or integrate into generation pipeline
**SELECTED_TASK_ID:** T-20251215-043
**SELECTED_TASK_TITLE:** Image quality optimization
**NEXT_ATOMIC_STEP:** Add color/contrast quality checks or integrate quality optimization into generation pipeline

**NEXT_3_TASKS:**
- [x] Backend service orchestration (start/stop/health) - COMPLETE
- [x] Frontend service orchestration (start/stop/health) - COMPLETE
- [x] ComfyUI service orchestration (start/stop/health) - COMPLETE
- [x] Service status dashboard (all services + ports + health) - COMPLETE
- [x] Workflow catalog (curated workflow packs) - COMPLETE
- [x] Workflow validation (required nodes/models/extensions) - COMPLETE
- [x] One-click workflow run - COMPLETE
- [x] T-20251215-017 Initialize project structure - COMPLETE
- [x] T-20251215-018 Set up Python backend (FastAPI) - COMPLETE
- [x] T-20251215-019 Set up Next.js frontend - COMPLETE
- [x] T-20251215-020 Configure database (PostgreSQL) - COMPLETE
- [x] T-20251215-021 Set up Redis - COMPLETE
- [x] T-20251215-022 Docker configuration (optional) - COMPLETE
- [x] T-20251215-023 Development environment documentation - COMPLETE
- [x] T-20251215-024 Character data model (database schema) - COMPLETE
- [x] T-20251215-025 Character creation API - COMPLETE
- [x] T-20251215-026 Character profile management - COMPLETE
- [x] T-20251215-027 Personality system design - COMPLETE
- [x] T-20251215-028 Character storage and retrieval - COMPLETE
- [x] T-20251215-029 Basic UI for character creation - COMPLETE
- [x] T-20251215-030 Character list view - COMPLETE
- [x] T-20251215-031 Character detail view - COMPLETE
- [x] T-20251215-032 Character edit functionality - COMPLETE
- [x] T-20251215-033 Image generation API endpoint - COMPLETE
- [x] T-20251215-034 Image storage system - COMPLETE
- [x] T-20251215-035 Quality validation system - COMPLETE
- [x] T-20251215-036 Text generation setup (Ollama + Llama) - COMPLETE
- [x] T-20251215-037 Caption generation for images - COMPLETE
- [x] T-20251215-038 Character-specific content generation - COMPLETE
- [x] T-20251215-039 Content scheduling system (basic) - COMPLETE
- [x] T-20251215-040 Content library management - COMPLETE

---

## EXECUTIVE_CAPSULE (copy/paste)
RUN_TS: 2025-12-15T21:00:00Z
STATE_ID: BOOTSTRAP_041
STATUS: GREEN
NEEDS_SAVE: false
SELECTED_TASK_ID: T-20251215-043
SELECTED_TASK_TITLE: Image quality optimization
LAST_CHECKPOINT: b501674 chore(autopilot): checkpoint BOOTSTRAP_040 - blur detection complete
REPO_CLEAN: clean
CHANGED_FILES_THIS_RUN:
- backend/app/services/quality_validator.py (added artifact detection using edge/texture analysis and color banding detection)
- docs/00_STATE.md (updated state, selected task)
- docs/TASKS.md (updated task status and progress)
TESTS_RUN_THIS_RUN:
- Syntax check passed (python3 -m py_compile backend/app/services/quality_validator.py)
- Lint verified (no errors)
DOC_SOURCES_USED_THIS_RUN:
- docs/00_STATE.md:178-187 (STATE_ID section, NEXT_3_TASKS)
- docs/TASKS.md:170-177 (task T-20251215-043)
- backend/app/services/quality_validator.py (existing quality validation service)
- docs/03-FEATURE-ROADMAP.md:65 (task source)
- docs/04-AI-MODELS-REALISM.md:257 (artifact detection reference)
EVIDENCE_SUMMARY:
- Added artifact detection method `_detect_artifacts` using edge and texture analysis (Sobel-like filters)
- Added helper methods: `_apply_kernel` (convolution), `_detect_color_banding` (gradient analysis)
- Integrated artifact check into `_validate_image` method with thresholds: < 0.3 = likely artifacts, 0.3-0.5 = possible, > 0.5 = clean
- Added artifact_score to metadata in QualityResult
- Updated quality score calculation to give +0.1 bonus for artifact-free images (artifact_check_clean)
- Detects unnatural patterns, color banding, and texture inconsistencies
- All syntax and lint checks passed
ADHERENCE_CHECK:
- PASS: Artifact detection follows existing quality check patterns
- PASS: Uses PIL and numpy (lightweight, no OpenCV dependency)
- PASS: Proper error handling (returns None if numpy unavailable)
- PASS: Quality score calculation updated correctly
- PASS: Syntax and lint checks passed
RISKS/BLOCKERS:
- None
NEXT_3_TASKS:
1) T-20251215-043 Image quality optimization (in progress - add color/contrast checks or integrate into generation pipeline next)
2) T-20251215-009 Dashboard shows system status + logs
3) T-20251215-044 +18 content generation system

---

## Current System State

### What Works
- ✅ Backend FastAPI server (`backend/app/main.py`) with installer, system checks, ComfyUI manager
- ✅ Frontend Next.js dashboard (`frontend/src/app/page.tsx`) with basic pages
- ✅ System check service (`backend/app/services/system_check.py`) - detects OS, Python, Node, GPU, disk
- ✅ Installer service (`backend/app/services/installer_service.py`) - installs deps, creates dirs, runs checks
- ✅ Dev scripts exist (`backend/run_dev.sh`, `backend/run_dev.ps1`) + unified launcher files exist (validate idempotency + health-check behavior)

### What's Missing
- ❌ ComfyUI service orchestration (start/stop/health)

### Architecture Notes
- Backend: FastAPI on port 8000
- Frontend: Next.js on port 3000
- Data dir: `.ainfluencer/` (gitignored)
- Logs dir: `.ainfluencer/logs/` (current)
- Target logs: `.ainfluencer/runs/<timestamp>/` (created by launcher/autopilot; `latest` points to newest run when enabled)

---

## Version Info
- Backend: Python 3.12/3.13 required
- Frontend: Node.js LTS required
- Last updated: 2025-01-27 (bootstrap phase)


## One-Word Operation (Recommended)

Use these commands in Cursor chat:

- `STATUS` → Read-only status check (cheap verification)
- `SCAN` → Extract tasks from docs incrementally
- `PLAN` → Auto-select next task (no user decision)
- `DO` or `CONTINUE` → Execute selected task (one atomic step)
- `SAVE` → Checkpoint state + tasks + logs
- `AUTO` → Full autonomous cycle (STATUS → PLAN → DO → SAVE)
- `NEXT` → Force-select next task (rare)

**Fastest path:** Use one writer chat and type `AUTO` repeatedly. Avoid manual SAVE; AUTO handles it automatically (pre-save if dirty, and always post-save). Only open extra chats for read-only STATUS checks.

Safety + reliability rules:
- Never delete tasks. Only change status: TODO → DOING → DONE.
- DONE requires: Evidence (changed files) + Tests (commands + results).
- CONTINUE/DO is ONLY allowed to work on the currently selected task in `docs/00_STATE.md`.
- If anything fails, stop, write blocker into `docs/00_STATE.md`, and propose smallest fix.
- If `NEEDS_SAVE` becomes true, the AI must SAVE before moving on.


### Autonomy + Auto-Prioritization (Mandatory)

- The AI must treat `docs/00_STATE.md` as the single source of truth.
- On every new chat: read `docs/00_STATE.md` first.
- On every new chat: run cheap reconciliation (`git status --porcelain`, `git diff --name-only`).
- RESUME must auto-select Task #1 using the AUTO_POLICY in `docs/00_STATE.md` (no user decision required).
- CONTINUE must execute only `SELECTED_TASK_1`. If missing, auto-run RESUME.
- If execution changes code, the AI must set `NEEDS_SAVE: false` and run SAVE (or instruct the user to run SAVE).
- Prioritize foundation tasks (launcher + logging) before UX features.
- Never run full inventory scans unless the user explicitly types `INVENTORY` or STATE_ID starts with BOOTSTRAP and inventory is missing.

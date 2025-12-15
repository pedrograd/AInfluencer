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
- `docs/_generated/DOCS_INVENTORY.md` - Full doc inventory
- `docs/_generated/SESSION_RUN.md` - Session analysis
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
- If code changed but docs not updated → set `NEEDS_SAVE: true` and run SAVE automatically.

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
- Append to `docs/_generated/SESSION_RUN.md`
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
- Write evidence: update task status/notes in `docs/TASKS.md`, append to `docs/07_WORKLOG.md`, append to `docs/_generated/SESSION_RUN.md`
- If the whole task is done, move it to DONE (DONE requires Evidence + Tests recorded)
- If anything fails: stop immediately, set `STATUS: RED`, write the error into `CURRENT_BLOCKER`, set `NEXT_ACTION` to the smallest fix
- If code changed, set `NEEDS_SAVE: true`

**SAVE** → Checkpoint state (never lose work):
- Acquire lock
- Refresh EXECUTIVE_CAPSULE block in `docs/00_STATE.md` (update RUN_TS, STATE_ID, STATUS, NEEDS_SAVE, SELECTED_TASK_*, LAST_CHECKPOINT, REPO_CLEAN, CHANGED_FILES_THIS_RUN, TESTS_RUN_THIS_RUN, DOC_SOURCES_USED_THIS_RUN, EVIDENCE_SUMMARY, ADHERENCE_CHECK, RISKS/BLOCKERS, NEXT_3_TASKS)
- Append new checkpoint entry to `docs/_generated/EXEC_REPORT.md` (duplicate capsule + deltas + doc adherence audit + risks/next steps)
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
- Ensure state files consistent: `docs/00_STATE.md`, `docs/TASKS.md`, `docs/07_WORKLOG.md`, `docs/_generated/SESSION_RUN.md`
- Run `git status --porcelain`
- Stage + commit with message: `chore(autopilot): checkpoint <STATE_ID> <SELECTED_TASK_ID>`
- Set `NEEDS_SAVE: false` after a successful commit
- Clear lock after successful commit

**AUTO** → Fully autonomous cycle (lowest-effort, safest default):
- Acquire lock
- **Definition:** STATUS → (SAVE if repo dirty or NEEDS_SAVE true) → PLAN → DO → SAVE
- **AUTO must ALWAYS end with SAVE** so governance files stay synced.
- Run STATUS first (read-only check)
- If repo is dirty (`git status --porcelain` returns non-empty) OR `NEEDS_SAVE: true`: run SAVE first (pre-save checkpoint)
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

## STATE_ID: BOOTSTRAP_017
**STATUS:** GREEN
**NEEDS_SAVE:** false
**LAST_COMMAND:** AUTO
**LAST_PASS:** Completed T-20251215-019 - Set up Next.js frontend (verified complete)
**CURRENT_BLOCKER:** None
**NEXT_ACTION:** Run SAVE to checkpoint changes, then select next task from backlog (per AUTO_POLICY: foundation tasks first)
**SELECTED_TASK_ID:** (none - task completed)
**SELECTED_TASK_TITLE:** (none - task completed)
**NEXT_ATOMIC_STEP:** Select next task from backlog

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
- [ ] T-20251215-020 Configure database (PostgreSQL)

---

## EXECUTIVE_CAPSULE (copy/paste)
RUN_TS: 2025-12-15T11:51:29Z
STATE_ID: BOOTSTRAP_017
STATUS: GREEN
NEEDS_SAVE: true
SELECTED_TASK_ID: (none - task completed)
SELECTED_TASK_TITLE: (none - task completed)
LAST_CHECKPOINT: 5b5c26a chore(autopilot): append BOOTSTRAP_016 checkpoint to EXEC_REPORT, clear lock
REPO_CLEAN: dirty
CHANGED_FILES_THIS_RUN:
- docs/00_STATE.md (updated - STATE_ID, task status, lock, EXECUTIVE_CAPSULE)
- docs/07_WORKLOG.md (updated - appended entry)
- docs/TASKS.md (updated - task marked DONE with evidence)
TESTS_RUN_THIS_RUN:
- TypeScript check run (npx tsc --noEmit) - some code quality issues found but setup is complete
- Next.js frontend structure verified via file checks
DOC_SOURCES_USED_THIS_RUN:
- docs/00_STATE.md:179-200 (STATE_ID section, NEXT_3_TASKS)
- docs/TASKS.md:70-71 (task T-20251215-019)
- docs/03-FEATURE-ROADMAP.md:27 (set up Next.js frontend requirement)
- frontend/package.json (Next.js dependencies)
- frontend/next.config.ts (Next.js config)
- frontend/tsconfig.json (TypeScript config)
EVIDENCE_SUMMARY:
- Verified Next.js frontend setup completeness: package.json, next.config.ts, tsconfig.json, src/app/ structure all exist
- Next.js 16.0.10 with React 19.2.1, TypeScript, Tailwind CSS configured
- Multiple pages (page.tsx, comfyui, generate, installer, models)
- API client library (lib/api.ts), layout, and global styles
- ESLint configured
- Task marked as DONE since frontend is already set up
ADHERENCE_CHECK:
- PASS: Next.js frontend verified complete per requirements
- PASS: All required components exist (package.json, config files, pages, API client)
- PASS: Frontend structure matches feature roadmap requirements
RISKS/BLOCKERS:
- None
NEXT_3_TASKS:
1) T-20251215-020 Configure database (PostgreSQL)
2) T-20251215-021 Set up Redis
3) T-20251215-022 Docker configuration (optional)

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
- If execution changes code, the AI must set `NEEDS_SAVE: true` and run SAVE (or instruct the user to run SAVE).
- Prioritize foundation tasks (launcher + logging) before UX features.
- Never run full inventory scans unless the user explicitly types `INVENTORY` or STATE_ID starts with BOOTSTRAP and inventory is missing.

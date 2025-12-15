# AUTOPILOT ONE-WORD COMMAND PROTOCOL (Repo Standard)

**Purpose:** This rule enforces a reliable, low-cost, one-word command protocol with zero hallucinations and strong safety rails.

---

## Source of Truth

- `docs/00_STATE.md` is the canonical state machine.
- `docs/TASKS.md` is the canonical backlog (never delete tasks).
- `docs/07_WORKLOG.md` is append-only evidence log.
- `docs/_generated/SESSION_RUN.md` (or `.ainfluencer/runs/...`) is append-only run log.

---

## Default Read Policy (Low Cost)

**MUST READ on every chat:**
- `docs/00_STATE.md`

**OPTIONAL (Only when task selection/execution needs it):**
- `docs/TASKS.md`
- `docs/07_WORKLOG.md`

**NEVER read all docs unless:**
- User explicitly runs `SCAN` (incremental)
- User explicitly runs `INVENTORY` (rare)
- STATE_ID starts with `BOOTSTRAP` and inventory is missing

**Rule:** In any new chat, read ONLY `docs/00_STATE.md` first. Read additional files ONLY if the task requires them.

---

## Single Writer Lock (Anti-Conflict)

**Lock fields live in `docs/00_STATE.md`:**
- `LOCKED_BY` - Unique session identifier (timestamp or session ID)
- `LOCK_REASON` - Why the lock was acquired (e.g., "DO command", "AUTO cycle")
- `LOCK_TIMESTAMP` - When the lock was acquired

**Lock Rules:**
- Only ONE active session may write changes.
- Before editing any file, acquire the lock:
  - If `LOCKED_BY` is empty OR lock is stale (>2 hours), set `LOCKED_BY` to unique session id and proceed
  - If `LOCKED_BY` is set by another session and not stale (>2h):
    - Output: "READ-ONLY MODE: locked by <id>"
    - Do NOT edit any file
    - Only STATUS command is allowed (read-only)

**Multi-chat rule:** You may open multiple chats, but only ONE chat is allowed to acquire the lock and write changes. All other chats must stay in READ-ONLY MODE and may only run STATUS (or explain what they see). Do not run AUTO/DO/SAVE in multiple chats at once.

---

## One-Word Commands (Strict Behavior)

### STATUS
- **Read-only.** Do not modify files.
- Print: `STATE_ID`, `STATUS`, `NEEDS_SAVE`, `SELECTED_TASK_ID`, counts from TASKS (TODO/DOING/DONE).
- Run cheap checks: `git status --porcelain`, `git diff --name-only`.
- If repo is locked by another session, still OK (read-only).

### SCAN
- **Incremental task extraction only.**
- Read SCAN state from `docs/00_STATE.md`: `SCAN_CURSOR`, `SCAN_LIST`.
- Read next 2–4 docs from `SCAN_LIST` starting at cursor.
- Extract tasks ONLY if explicitly stated (checkboxes, TODO markers, "missing" lists, requirements).
- Every new task MUST include `Source: <file>:<section or line-range>`.
- De-duplicate: if task already exists, append new sources under "Related Sources".
- Advance `SCAN_CURSOR` and persist it back into `docs/00_STATE.md`.
- Append summary into `docs/_generated/SESSION_RUN.md` (or run log file).
- **Never invent tasks.** Only extract what is explicitly written.

### PLAN
- **Must acquire lock.**
- If there is already a DOING task, keep it selected.
- Otherwise auto-select next TODO task using `AUTO_POLICY` inside `docs/00_STATE.md`:
  - foundation > UX accelerators > expansions
- Move selected task to DOING and persist:
  - `docs/00_STATE.md` (`SELECTED_TASK_ID`/`TITLE`/`NEXT_ATOMIC_STEP`)
  - `docs/TASKS.md` (status change + atomic sub-steps checklist)

### DO / CONTINUE
- **Must acquire lock.**
- Execute EXACTLY ONE atomic sub-step of the selected task.
- Keep it small, reversible, and testable.
- Run minimal verification: typecheck/lint + smallest smoke test.
- Record evidence in `docs/TASKS.md` + append to `docs/07_WORKLOG.md`.
- If failure: stop, set `STATUS: RED`, write error into `CURRENT_BLOCKER`, write smallest fix into `NEXT_ACTION`.
- If code changed, set `NEEDS_SAVE: true`.

### SAVE
- **Must acquire lock.**
- Ensure state/log files are consistent (`docs/00_STATE.md`, `docs/TASKS.md`, `docs/07_WORKLOG.md`, run log).
- Run `git status --porcelain` to verify changes.
- Refresh EXECUTIVE_CAPSULE block in `docs/00_STATE.md` (update RUN_TS, STATE_ID, STATUS, NEEDS_SAVE, SELECTED_TASK_*, LAST_CHECKPOINT, REPO_CLEAN, CHANGED_FILES_THIS_RUN, TESTS_RUN_THIS_RUN, DOC_SOURCES_USED_THIS_RUN, EVIDENCE_SUMMARY, ADHERENCE_CHECK, RISKS/BLOCKERS, NEXT_3_TASKS).
- Append new checkpoint entry to `docs/_generated/EXEC_REPORT.md` (duplicate capsule + deltas + doc adherence audit + risks/next steps).
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
- Commit with message: `chore(autopilot): checkpoint <STATE_ID> <SELECTED_TASK_ID>`
- Set `NEEDS_SAVE: false` only after successful commit.
- Clear lock after successful commit.

### AUTO
- **Must acquire lock.**
- **Definition:** STATUS → (SAVE if repo dirty or NEEDS_SAVE true) → PLAN → DO → SAVE
- **AUTO must ALWAYS end with SAVE** so governance files stay synced.
- The assistant must NOT tell the user to type SAVE unless:
  1. User made manual edits outside autopilot and wants a checkpoint without running a task
  2. A run aborted mid-cycle leaving repo dirty
  3. User explicitly requests "checkpoint now"
- Run STATUS first (read-only check).
- If repo is dirty (`git status --porcelain` returns non-empty) OR `NEEDS_SAVE=true`, run SAVE first (pre-save checkpoint).
- Then run: PLAN → DO → SAVE (post-save checkpoint).
- If blocked, stop and write blocker + smallest fix into `docs/00_STATE.md`.

### NEXT
- **Must acquire lock.**
- Force-select next task (rare).
- Only when no DOING tasks OR current task blocked.
- Persist new selection in `docs/00_STATE.md` and `docs/TASKS.md`.

### UNLOCK
- Only if lock is stale (>2h) or user confirms no other writer.
- Clears lock fields (`LOCKED_BY`, `LOCK_REASON`, `LOCK_TIMESTAMP`).
- Prints "UNLOCKED" and recommended next command (usually STATUS).

---

## Output Template (Always)

Every command must end with:
- **What changed (files):** ... (list of modified/created files)
- **Tests run:** ... (commands executed + results)
- **Next recommended one-word command:** ... (STATUS, AUTO, SAVE, etc.)

---

## Hallucination Firewall

**Non-Negotiable Rules:**
1. **Never fabricate tasks.** Only extract tasks explicitly present in docs (checkboxes, TODO markers, "missing" lists, requirements).
2. **Never delete tasks.** Only move status: TODO → DOING → DONE. Splits create new Task IDs and cross-link.
3. **Never invent file paths, endpoints, ports, or scripts.** If uncertain, use repo searches (`rg`, `ls`, `cat`) to confirm.
4. **If still ambiguous, ask exactly ONE question and stop.**

**Evidence & Tests Required:**
- A task is DONE only if it includes:
  - **Evidence:** changed file paths
  - **Tests:** commands + results

---

## Cost Discipline

**Never read all docs by default. Only:**
- Always read `docs/00_STATE.md`
- Read additional docs only when required by the current atomic step or SCAN chunk

**Automatic safety:**
- If `NEEDS_SAVE=true`, must SAVE before new work.

---

## Quick Start

**Fastest path:** Use a single chat and type `AUTO` repeatedly.

**Open extra chats only for STATUS (read-only).**

**Recommended workflow:**
1. Writer chat: `SAVE` → `STATUS` → `AUTO` (repeat)
2. Other chats: `STATUS` (read-only checks)

---

## Integration with Other Rules

This protocol is the primary workflow for this repository. All other rule files should reference this protocol and enforce:
- Lock rule and cost discipline
- Multi-chat safety (only one writer session may use AUTO/DO/SAVE)
- Evidence-based task completion


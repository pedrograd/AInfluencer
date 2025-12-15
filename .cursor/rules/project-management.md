# Project Management Rules - Command Protocol

**Purpose:** This file defines how the AI must behave when using the command protocol system. These rules are MANDATORY.

**IMPORTANT:** This repository now uses the **Autopilot One-Word Command Protocol**. See `.cursor/rules/autopilot-protocol.md` for the complete, authoritative protocol. This file provides additional context and enforcement rules.

**Primary Protocol:** `.cursor/rules/autopilot-protocol.md`

---

## 🚨 HARD RULES (MANDATORY)

### 1. Low-Cost Reading Policy (MANDATORY)

**DO NOT read all docs every chat. This is expensive and slow.**

**MUST_READ (Always):**
- `docs/00_STATE.md` - Single source of truth (read FIRST in every new chat)

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

### 2. Command Protocol Behavior (MANDATORY)

**The AI MUST strictly follow the Autopilot One-Word Command Protocol defined in `.cursor/rules/autopilot-protocol.md` and `docs/00_STATE.md`.**

**Primary Commands (see autopilot-protocol.md for full details):**
- **STATUS** → Read-only status check (no file modifications)
- **SCAN** → Incremental task extraction from docs (2-4 docs per run)
- **PLAN** → Auto-select next task (must acquire lock)
- **DO / CONTINUE** → Execute one atomic step (must acquire lock)
- **SAVE** → Checkpoint state (must acquire lock, git commit)
- **AUTO** → Full autonomous cycle: STATUS → PLAN → DO → SAVE
- **NEXT** → Force-select next task (rare, must acquire lock)
- **UNLOCK** → Clear stale lock (only if >2h stale or user confirms)

**Key Requirements:**
- **Single Writer Lock:** Only ONE chat session may write changes. All other chats must be read-only (STATUS only).
- **No Hallucinations:** Never invent tasks. Only extract from docs.
- **No Task Loss:** Never delete tasks. Only change status: TODO → DOING → DONE.
- **Evidence & Tests:** DONE tasks must include evidence (files) + tests (commands + results).
- **Cost Discipline:** Always read `docs/00_STATE.md` first. Read additional docs only when needed.

**For complete command details, see:** `.cursor/rules/autopilot-protocol.md`

---

### 3. Status Update Requirements (MANDATORY)

**After DO / CONTINUE command, AI MUST update:**

1. **`docs/00_STATE.md`:**
   - Advance STATE_ID (e.g., BOOTSTRAP_000 → BOOTSTRAP_001)
   - Update STATUS (GREEN/YELLOW/RED)
   - Update CURRENT_BLOCKER (or set to "None")
   - Update NEXT_ACTION (what to do next)
   - Update SELECTED_TASK_ID / SELECTED_TASK_TITLE / NEXT_ATOMIC_STEP
   - Update LOCKED_BY / LOCK_REASON / LOCK_TIMESTAMP (if lock acquired)
   - Set NEEDS_SAVE: true if code changed

2. **`docs/TASKS.md`:**
   - Update task status (TODO → DOING → DONE)
   - Record evidence (changed file paths)
   - Record tests (commands + results)
   - Add atomic sub-steps checklist

3. **`docs/07_WORKLOG.md`:**
   - Append new entry with:
     - Date (YYYY-MM-DD)
     - State (STATE_ID)
     - Action (what was done)
     - What was done (detailed)
     - Why (reasoning)
     - Next (next steps)
     - Blockers (if any)

4. **`docs/_generated/SESSION_RUN.md`:**
   - Append run log entry

**After SAVE command, AI MUST:**
- Ensure state/log files are consistent
- Run `git status --porcelain` to verify changes
- Commit with message: `chore(autopilot): checkpoint <STATE_ID> <SELECTED_TASK_ID>`
- Set NEEDS_SAVE: false after successful commit

---

### 4. Inventory Generation Policy (MANDATORY)

**DO NOT auto-generate inventory unless:**
- User explicitly types "INVENTORY" command, OR
- STATE_ID begins with "BOOTSTRAP"

**DO NOT generate inventory on:**
- RESUME command
- CONTINUE command
- SAVE command
- NEXT command
- Any other command

**This reduces cost and increases speed.**

---

### 5. Deterministic State (MANDATORY)

**The repo state MUST be understandable from `docs/00_STATE.md` alone.**

- All critical state information must be in `docs/00_STATE.md`
- Other files are supplementary, not required for understanding state
- STATE_ID must be unique and advance with each task
- SELECTED_TASK_1 must be persisted in `docs/00_STATE.md`

---

## 🚫 What NOT To Do

### DO NOT:
- ❌ Read all docs on every chat (violates low-cost policy)
- ❌ Invent tasks (hallucination firewall - only extract from docs)
- ❌ Delete tasks (only change status: TODO → DOING → DONE)
- ❌ Skip status updates after DO/CONTINUE (mandatory)
- ❌ Write code without acquiring lock (single writer rule)
- ❌ Run AUTO/DO/SAVE in multiple chats (only one writer allowed)
- ❌ Mark task as DONE without evidence + tests
- ❌ Implement evasion/anti-detection features (see HARD RULES in user request)

### DO:
- ✅ Read only `docs/00_STATE.md` first
- ✅ Read additional files only if task needs them
- ✅ Acquire lock before editing files (check LOCKED_BY in docs/00_STATE.md)
- ✅ Update status files after DO/CONTINUE
- ✅ Record evidence (files) + tests (commands + results) for DONE tasks
- ✅ Keep work focused on reliability and UX
- ✅ Follow autopilot protocol strictly (see `.cursor/rules/autopilot-protocol.md`)

---

## 📋 Default Workflow

**Recommended workflow:** Use `AUTO` command repeatedly (fastest path)

**Standard loop:** `AUTO` → `AUTO` → `AUTO` (or `STATUS` → `PLAN` → `DO` → `SAVE`)

1. User types: **AUTO**
   - If NEEDS_SAVE=true: runs SAVE first
   - Runs: STATUS → PLAN → DO → SAVE
   - Full autonomous cycle

2. User types: **AUTO** (repeat)
   - Continues with next task
   - Full autonomous cycle

**Alternative manual workflow:**
1. User types: **STATUS**
   - Read-only status check
   - Shows current state, task counts, git status

2. User types: **PLAN**
   - Auto-selects next task
   - Moves task to DOING
   - Shows next atomic step

3. User types: **DO** or **CONTINUE**
   - Executes one atomic step
   - Updates all status files
   - Records evidence + tests

4. User types: **SAVE**
   - Checkpoints state
   - Git commit
   - Sets NEEDS_SAVE: false

**Multi-chat safety:**
- Only ONE chat may use AUTO/DO/SAVE (writer)
- All other chats must be read-only (STATUS only)

---

## 🎯 Single Source of Truth

**`docs/00_STATE.md` is the ONLY file that must be read first.**

All other files are optional and only read if the task needs them.

This makes the system:
- **Deterministic:** State is clear from one file
- **Fast:** Minimal file reads
- **Reliable:** No confusion about current state

---

## 📊 Cost Control

**Target:** Read 1-3 files per command (except INVENTORY)

| Command | Max Files | Cost Level |
|---------|-----------|------------|
| RESUME | 1-3 files | Very Low |
| CONTINUE | 2-5 files | Low-Medium |
| SAVE | 1-2 files | Low |
| NEXT | 1 file | Very Low |
| INVENTORY | All docs | High (rare) |

**Old system:** ~50+ files per cycle  
**New system:** ~5-8 files per cycle  
**Savings:** ~85% reduction in file reads

---

## ✅ Verification Checklist

After implementing this system, verify:

1. ✅ `docs/00_STATE.md` has READ_POLICY + COMMAND_PROTOCOL
2. ✅ RESUME command does NOT scan all docs
3. ✅ INVENTORY command generates DOCS_INVENTORY.md
4. ✅ CONTINUE command updates all required files
5. ✅ SAVE command only updates, doesn't create tasks

---

**Related Files:**
- `.cursor/rules/autopilot-protocol.md` - **PRIMARY PROTOCOL** (authoritative)
- `.cursor/rules/main.md` - Quick start guide
- `docs/00_STATE.md` - Single source of truth (read first)
- `docs/TASKS.md` - Master backlog (never delete tasks)
- `docs/07_WORKLOG.md` - Append-only evidence log
- `CURSOR-PROJECT-MANAGER.md` - Project context

---

**Last Updated:** 2025-01-27  
**Version:** 3.0 (Autopilot One-Word Command Protocol)

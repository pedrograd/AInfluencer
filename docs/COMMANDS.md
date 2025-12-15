# COMMANDS.md - Command Protocol Reference

**Purpose:** This is the single reference document for the command protocol system. It explains what each command does, what files it reads, and what outputs it must produce.

**Related Files:**
- `docs/00_STATE.md` - Contains READ_POLICY and COMMAND_PROTOCOL sections
- `QUICK-ACTIONS.md` - Simple "grandma-proof" command reference
- `AUTO-UPDATE-SYSTEM.md` - Workflow explanation
- `.cursor/rules/project-management.md` - Agent rules

---

## 📋 Command Overview

| Command | Mode | Reads | Outputs | Updates Files |
|---------|------|-------|---------|---------------|
| **RESUME** | Planner | `docs/00_STATE.md` + (max 2-3 needed) | Next 3 tasks, selects Task #1 | None |
| **CONTINUE** | Executor | State + task files (2-5 files) | Code diffs, commands, tests, logs | All status files |
| **SAVE** | Status | State files (1-2 files) | None | Status files only |
| **NEXT** | Planner | `docs/00_STATE.md` (1 file) | Short plan for next task | None |
| **INVENTORY** | Generator | All docs | DOCS_INVENTORY.md, SESSION_RUN.md | Generated files |

---

## 🔍 RESUME Command

### What It Does
Planner mode - shows what to do next without writing code.

### Files It Reads
1. **MUST read:** `docs/00_STATE.md` (always)
2. **OPTIONAL read:** Max 2-3 additional files if needed for context
   - `PROJECT-STATUS.md` (if needed)
   - `CURSOR-PROJECT-MANAGER.md` (if needed)
   - `docs/07_WORKLOG.md` (if needed)

### What It Outputs
1. **Next 3 tasks** from `docs/00_STATE.md` → NEXT_3_TASKS
2. **Selected Task #1** - marks it as SELECTED_TASK_1
3. **Short summary** of current state

### What It Does NOT Do
- ❌ Write code
- ❌ Implement anything
- ❌ Read all docs
- ❌ Generate inventory
- ❌ Update status files

### Example
```
User: RESUME
AI: [Reads docs/00_STATE.md]
    [Shows 3 tasks, selects Task #1]
    "Next 3 tasks:
    1. [SELECTED] Create canonical docs structure
    2. Create cross-platform launcher
    3. Create unified logging system"
```

---

## ⚙️ CONTINUE Command

### What It Does
Executor mode - implements the previously selected Task #1.

### Files It Reads
1. **MUST read:** `docs/00_STATE.md` (to get SELECTED_TASK_1)
2. **OPTIONAL read:** 2-5 files needed for the task
   - Task-specific files (code files, configs, etc.)
   - `PROJECT-STATUS.md` (if needed for context)
   - `CURSOR-PROJECT-MANAGER.md` (if needed for context)

### What It Outputs
1. **Code changes** (diffs, file edits)
2. **Commands** (if needed to run tests, etc.)
3. **Smoke tests** (if applicable)
4. **Run logs** (if commands were executed)

### Files It MUST Update
1. **`docs/00_STATE.md`:**
   - Advance STATE_ID (e.g., BOOTSTRAP_000 → BOOTSTRAP_001)
   - Update STATUS (GREEN/YELLOW/RED)
   - Update CURRENT_BLOCKER (or "None")
   - Update NEXT_ACTION (what to do next)
   - Update SELECTED_TASK_1 (mark completed task, select next if needed)
   - Update NEXT_3_TASKS (remove completed, add new if needed)

2. **`docs/07_WORKLOG.md`:**
   - Append new entry with:
     ```
     ## YYYY-MM-DD - Task Description
     **State:** STATE_ID
     **Action:** What was done
     **What was done:** [Detailed description]
     **Why:** [Reasoning]
     **Next:** [Next steps]
     **Blockers:** [If any, or "None"]
     ```

3. **`PROJECT-STATUS.md`:**
   - Update "Recently Completed" section
   - Update "Next Priority Tasks"
   - Add entry to "Change Log"

4. **`CURSOR-PROJECT-MANAGER.md`:**
   - Update "What's Built & Shipped"
   - Update "What Remains" (mark completed tasks)
   - Update "Recommended Next Tasks"

### Example
```
User: CONTINUE
AI: [Reads docs/00_STATE.md, gets SELECTED_TASK_1]
    [Implements Task #1: Create canonical docs structure]
    [Updates docs/00_STATE.md, docs/07_WORKLOG.md, PROJECT-STATUS.md, CURSOR-PROJECT-MANAGER.md]
    "Task #1 completed. Updated all status files."
```

---

## 💾 SAVE Command

### What It Does
Status update only - updates status files without doing new work.

### Files It Reads
1. **MUST read:** `docs/00_STATE.md` (current state)
2. **OPTIONAL read:** `PROJECT-STATUS.md`, `CURSOR-PROJECT-MANAGER.md` (if needed)

### What It Outputs
- None (just updates files)

### Files It MUST Update
1. **`docs/00_STATE.md`** - Ensure state is current
2. **`PROJECT-STATUS.md`** - Update status
3. **`CURSOR-PROJECT-MANAGER.md`** - Update context

### What It Does NOT Do
- ❌ Create new tasks
- ❌ Write code
- ❌ Implement anything
- ❌ Generate inventory

### Example
```
User: SAVE
AI: [Reads current state]
    [Updates docs/00_STATE.md, PROJECT-STATUS.md, CURSOR-PROJECT-MANAGER.md]
    "Status files updated."
```

---

## ➡️ NEXT Command

### What It Does
Task selection - moves to the next task and shows a short plan.

### Files It Reads
1. **MUST read:** `docs/00_STATE.md` (to get NEXT_3_TASKS)

### What It Outputs
1. **Selected next task** (from NEXT_3_TASKS)
2. **Short plan** for that task (no code, just plan)

### Files It Updates
- None (only reads, doesn't update)

### What It Does NOT Do
- ❌ Write code
- ❌ Implement anything
- ❌ Update status files
- ❌ Read all docs

### Example
```
User: NEXT
AI: [Reads docs/00_STATE.md]
    [Selects Task #2 from NEXT_3_TASKS]
    "Selected Task #2: Create cross-platform launcher
     Plan: Create Windows .bat and macOS .command files that start backend + frontend"
```

---

## 📦 INVENTORY Command

### What It Does
Generates full documentation inventory (rare use).

### When To Run
- User explicitly types "INVENTORY" command, OR
- STATE_ID begins with "BOOTSTRAP"

### Files It Reads
- **All docs** in the repository (full scan)

### What It Outputs
1. **`docs/_generated/DOCS_INVENTORY.md`** - Full inventory of all docs
2. **`docs/_generated/SESSION_RUN.md`** - Session analysis

### Files It Updates
- Generated files only (doesn't update status files)

### What It Does NOT Do
- ❌ Run automatically on other commands
- ❌ Update status files
- ❌ Write code

### Example
```
User: INVENTORY
AI: [Scans all docs]
    [Generates docs/_generated/DOCS_INVENTORY.md]
    [Generates docs/_generated/SESSION_RUN.md]
    "Full inventory generated."
```

---

## 🔄 Default Workflow

**Standard loop:** `RESUME → CONTINUE → SAVE → NEXT`

### Step-by-Step

1. **RESUME**
   - User types: `RESUME`
   - AI reads: `docs/00_STATE.md` (only)
   - AI outputs: 3 tasks, selects Task #1
   - Cost: Very low (1 file)

2. **CONTINUE**
   - User types: `CONTINUE`
   - AI reads: State + task files (2-5 files)
   - AI implements: Task #1
   - AI updates: All status files
   - Cost: Low-medium (2-5 files)

3. **SAVE** (optional)
   - User types: `SAVE`
   - AI reads: State files (1-2 files)
   - AI updates: Status files
   - Cost: Low (1-2 files)

4. **NEXT**
   - User types: `NEXT`
   - AI reads: `docs/00_STATE.md` (1 file)
   - AI outputs: Next task plan
   - Cost: Very low (1 file)

5. **CONTINUE** (repeat)
   - User types: `CONTINUE`
   - AI implements: Task #2
   - ... repeat ...

---

## 📊 Cost Comparison

| Command | Files Read | Cost Level | When To Use |
|---------|-----------|------------|-------------|
| RESUME | 1-3 files | Very Low | Start of chat, see what's next |
| CONTINUE | 2-5 files | Low-Medium | After RESUME, do the work |
| SAVE | 1-2 files | Low | Save progress (optional) |
| NEXT | 1 file | Very Low | After CONTINUE, see next task |
| INVENTORY | All docs | High | Rare - only when needed |

**Total per cycle (RESUME → CONTINUE → SAVE → NEXT):**
- Files read: ~5-8 files
- Old system: ~50+ files
- **Savings: ~85% reduction**

---

## ✅ Verification Checklist

After implementing a command, verify:

### RESUME
- [ ] Only read `docs/00_STATE.md` + (max 2-3 files)
- [ ] Showed 3 tasks
- [ ] Selected Task #1
- [ ] Did NOT write code
- [ ] Did NOT read all docs

### CONTINUE
- [ ] Implemented SELECTED_TASK_1
- [ ] Updated `docs/00_STATE.md` (STATE_ID advanced, status updated)
- [ ] Updated `docs/07_WORKLOG.md` (appended entry)
- [ ] Updated `PROJECT-STATUS.md` (recently completed, change log)
- [ ] Updated `CURSOR-PROJECT-MANAGER.md` (what's built, what remains)

### SAVE
- [ ] Updated status files
- [ ] Did NOT create new tasks
- [ ] Did NOT write code

### NEXT
- [ ] Selected next task
- [ ] Showed short plan
- [ ] Did NOT write code
- [ ] Did NOT update files

### INVENTORY
- [ ] Generated `docs/_generated/DOCS_INVENTORY.md`
- [ ] Generated `docs/_generated/SESSION_RUN.md`
- [ ] Only run when requested or BOOTSTRAP state

---

## 🚫 Common Mistakes To Avoid

1. **Reading all docs on RESUME** ❌
   - Should read only `docs/00_STATE.md` + (max 2-3 files)

2. **Not updating status files after CONTINUE** ❌
   - Must update all 4 files: `docs/00_STATE.md`, `docs/07_WORKLOG.md`, `PROJECT-STATUS.md`, `CURSOR-PROJECT-MANAGER.md`

3. **Auto-generating inventory** ❌
   - Only generate on INVENTORY command or BOOTSTRAP state

4. **Writing code in RESUME mode** ❌
   - RESUME is planner only, no code

5. **Creating tasks in SAVE mode** ❌
   - SAVE only updates, doesn't create

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0 (Command Protocol Reference)


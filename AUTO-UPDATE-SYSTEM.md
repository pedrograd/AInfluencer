# AUTO-UPDATE-SYSTEM.md - Command Protocol Workflow

**Purpose:** This document explains how the low-cost command protocol system works.

---

## 🎯 Default Workflow

**The standard loop:** `RESUME → CONTINUE → SAVE → NEXT`

This workflow is designed to be:
- **Low-cost:** Doesn't read all docs every chat
- **Deterministic:** Repo state understandable from `docs/00_STATE.md` alone
- **Fast:** Only reads what's needed for the current task

---

## 📋 How It Works

### 1. RESUME (Planner Mode)
- **Reads:** Only `docs/00_STATE.md` + (max 2-3 needed files)
- **Outputs:** Next 3 tiny tasks and selects Task #1
- **Does NOT code** - only plans
- **Cost:** Very low (1-3 files read)

### 2. CONTINUE (Executor Mode)
- **Implements:** The previously selected Task #1
- **Produces:** Diffs + commands + smoke tests + run logs
- **Updates:** 
  - `docs/00_STATE.md` (advance STATE_ID, set next action)
  - `docs/07_WORKLOG.md` (append entry)
  - `PROJECT-STATUS.md` (update status)
  - `CURSOR-PROJECT-MANAGER.md` (update context)
- **Cost:** Medium (reads state + implements task)

### 3. SAVE (Status Update Only)
- **Updates:** Status files only (no new work)
- **Does NOT:** Create tasks or write code
- **Cost:** Low (reads current state, updates files)

### 4. NEXT (Task Selection)
- **Selects:** Next task from NEXT_3_TASKS
- **Produces:** Short plan only (no code)
- **Cost:** Very low (reads state only)

### 5. INVENTORY (Full Inventory - Rare)
- **Generates:** `docs/_generated/DOCS_INVENTORY.md` and `docs/_generated/SESSION_RUN.md`
- **Only run:** When explicitly requested or STATE_ID begins with BOOTSTRAP
- **Cost:** High (scans all docs)

---

## 🔄 Typical Session Flow

### Starting a New Chat
```
1. User: RESUME
   → AI reads docs/00_STATE.md (only)
   → AI shows 3 tasks, selects Task #1
   → No code written yet

2. User: CONTINUE
   → AI implements Task #1
   → AI updates docs/00_STATE.md, docs/07_WORKLOG.md, PROJECT-STATUS.md
   → Work is done and logged

3. User: SAVE (optional - CONTINUE already saves)
   → AI updates status files
   → Ensures everything is saved

4. User: NEXT
   → AI selects Task #2
   → Shows short plan

5. User: CONTINUE
   → AI implements Task #2
   → Updates all files
   → ... repeat ...
```

### Why This Is Low-Cost

**Old way (expensive):**
- Every chat reads all docs
- Scans entire codebase
- Generates full inventory
- **Cost:** High (many file reads)

**New way (low-cost):**
- RESUME reads only `docs/00_STATE.md` (1 file)
- CONTINUE reads only what's needed for the task (2-3 files)
- INVENTORY only when requested (rare)
- **Cost:** Low (1-3 files per command)

---

## 📁 File Update Policy

### After CONTINUE Command

**MUST update:**
1. `docs/00_STATE.md`
   - Advance STATE_ID
   - Update STATUS, CURRENT_BLOCKER, NEXT_ACTION
   - Update SELECTED_TASK_1
   - Update NEXT_3_TASKS

2. `docs/07_WORKLOG.md`
   - Append new entry with:
     - Date, State, Action
     - What was done
     - Why
     - Next steps
     - Blockers

3. `PROJECT-STATUS.md`
   - Update "Recently Completed"
   - Update "Next Priority Tasks"
   - Add to Change Log

4. `CURSOR-PROJECT-MANAGER.md`
   - Update "What's Built"
   - Update "What Remains"
   - Update "Recommended Next Tasks"

### After SAVE Command

**MUST update:**
- Same files as CONTINUE, but NO new work
- Only status updates

---

## 🚫 What NOT To Do

### DO NOT:
- ❌ Read all docs on every chat (low-cost policy)
- ❌ Auto-generate inventory unless INVENTORY command or BOOTSTRAP state
- ❌ Skip status updates after CONTINUE
- ❌ Create tasks in SAVE mode (only updates)
- ❌ Implement evasion/anti-detection features (see HARD RULES)

### DO:
- ✅ Read only `docs/00_STATE.md` first
- ✅ Read additional files only if task needs them
- ✅ Update status files after CONTINUE
- ✅ Keep work focused on reliability and UX

---

## 📊 Cost Comparison

| Command | Files Read | Cost Level |
|---------|-----------|------------|
| RESUME | 1-3 files | Very Low |
| CONTINUE | 2-5 files | Low-Medium |
| SAVE | 1-2 files | Low |
| NEXT | 1 file | Very Low |
| INVENTORY | All docs | High |

**Default workflow (RESUME → CONTINUE → SAVE → NEXT):**
- Total files read: ~5-8 files per cycle
- Old system: ~50+ files per cycle
- **Savings: ~85% reduction in file reads**

---

## 🎯 Single Source of Truth

**`docs/00_STATE.md` is the ONLY file that must be read first.**

All other files are optional and only read if the task needs them.

This makes the system:
- **Deterministic:** State is clear from one file
- **Fast:** Minimal file reads
- **Reliable:** No confusion about current state

---

## 💡 Tips

1. **Always start with RESUME** in a new chat
2. **CONTINUE does the work** - use it after RESUME
3. **SAVE is optional** - CONTINUE already saves, but use SAVE if needed
4. **NEXT moves forward** - use it to see the next task plan
5. **INVENTORY is rare** - only use when you need full doc inventory

---

## 🔍 Verification

After implementing this system:

1. ✅ Open `docs/00_STATE.md` - confirm READ_POLICY + COMMAND_PROTOCOL exists
2. ✅ Type RESUME - confirm it does NOT scan all docs
3. ✅ Type INVENTORY - confirm it generates DOCS_INVENTORY.md

---

**Last Updated:** 2025-01-XX  
**Version:** 2.0 (Command Protocol System)

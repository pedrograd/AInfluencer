# QUICK-ACTIONS.md - Simple Command Reference

**Purpose:** This file documents the 5 simple commands you can type in Cursor chat to control the AI assistant. Keep it simple.

**How to Use:** Just type the command word in Cursor chat. The AI will understand what to do.

---

## 🚀 The 5 Commands

### RESUME
**What it does:** Planner mode - shows you what to do next
- Reads only `docs/00_STATE.md` (and max 2-3 needed files)
- Shows you the next 3 tiny tasks
- Selects Task #1 for you
- **Does NOT write code** - only plans

**When to use:** Start of a new chat session, or when you want to see what's next

**Example:**
```
You: RESUME
AI: [Reads state, shows 3 tasks, selects Task #1]
```

---

### CONTINUE
**What it does:** Executor mode - does the work
- Implements the previously selected Task #1
- Produces code changes (diffs), runs commands, tests
- Updates status files automatically

**When to use:** After RESUME, when you want the AI to actually do the work

**Example:**
```
You: CONTINUE
AI: [Implements Task #1, updates docs/00_STATE.md, docs/07_WORKLOG.md, PROJECT-STATUS.md]
```

---

### SAVE
**What it does:** Updates status files only (no new work)
- Updates `docs/00_STATE.md`, `PROJECT-STATUS.md`, `CURSOR-PROJECT-MANAGER.md`
- Does NOT create new tasks or write code
- Just saves the current state

**When to use:** When you want to save progress without doing more work

**Example:**
```
You: SAVE
AI: [Updates all status files with current state]
```

---

### NEXT
**What it does:** Moves to the next task
- Selects the next task from the list
- Shows you a short plan for that task
- **Does NOT write code** - only plans

**When to use:** After CONTINUE, when you want to see the plan for the next task

**Example:**
```
You: NEXT
AI: [Selects Task #2, shows short plan]
```

---

### INVENTORY
**What it does:** Generates full documentation inventory (rare use)
- Creates `docs/_generated/DOCS_INVENTORY.md`
- Creates `docs/_generated/SESSION_RUN.md`
- Only run when you explicitly ask, or if STATE_ID starts with BOOTSTRAP

**When to use:** Rarely - only when you need a full doc inventory

**Example:**
```
You: INVENTORY
AI: [Generates full doc inventory files]
```

---

## 📋 Typical Workflow

**Normal day-to-day:**
```
1. You: RESUME
   → AI shows 3 tasks, selects Task #1

2. You: CONTINUE
   → AI does Task #1, updates files

3. You: SAVE (optional, CONTINUE already saves)
   → AI updates status files

4. You: NEXT
   → AI selects Task #2, shows plan

5. You: CONTINUE
   → AI does Task #2, updates files

... repeat ...
```

**Starting fresh:**
```
1. You: RESUME
   → AI reads docs/00_STATE.md, shows what's next
```

**Need full inventory:**
```
1. You: INVENTORY
   → AI generates full doc inventory (rare)
```

---

## 💡 Tips

1. **RESUME first** - Always start with RESUME in a new chat
2. **CONTINUE does the work** - After RESUME, use CONTINUE to actually implement
3. **SAVE is optional** - CONTINUE already saves, but you can use SAVE if needed
4. **NEXT moves forward** - Use NEXT to see the plan for the next task
5. **INVENTORY is rare** - Only use when you need full doc inventory

---

## 🎯 That's It!

These 5 commands are all you need. The system is designed to be simple and low-cost (doesn't read all docs every time).

**Related Files:**
- `docs/00_STATE.md` - Single source of truth (always read first)
- `docs/COMMANDS.md` - Detailed command reference
- `AUTO-UPDATE-SYSTEM.md` - How the system works

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0 (Command Protocol)

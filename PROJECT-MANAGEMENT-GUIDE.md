# Project Management System - User Guide

**Purpose:** This guide explains how to use the project management system to efficiently work on AInfluencer in Cursor.

---

## 🎯 What This System Does

This system allows you to:

1. **Start new chats instantly** - The AI understands the complete project state automatically
2. **Use quick commands** - Execute complex tasks with just two words
3. **Track progress** - Always know what's done, what's tested, and what's left
4. **Prioritize work** - Focus on highest-impact tasks first

---

## 📁 The Management Files

### 1. `CURSOR-PROJECT-MANAGER.md` (Main Document)
**What it is:** The complete executive context for the project. This is the "CEO/CTO/CPO" document that contains everything about the project state.

**When to use:** 
- The AI automatically reads this when you start a new chat
- Reference it when you need to understand what's built or what's left
- Copy relevant sections into chat if the AI needs more context

**Contains:**
- ✅ What's built and shipped (verified features)
- 🧪 What's tested and verified
- 🚧 What remains (pending tasks)
- 🎯 Recommended next tasks (priorities)
- 📋 Project standards and rules

### 2. `PROJECT-STATUS.md` (Real-Time Status)
**What it is:** A quick snapshot of current project state, updated after each session.

**When to use:**
- Check this first when starting a new session
- See what was completed in the last session
- Understand what's currently in progress

**Contains:**
- Recently completed tasks
- Currently in progress work
- Next priority tasks
- Testing status
- Notes and decisions

### 3. `QUICK-ACTIONS.md` (Quick Commands)
**What it is:** A reference guide for quick, two-word commands you can use in Cursor chat.

**When to use:**
- When you want to execute a task quickly
- When you know what you want but don't want to write a long prompt
- When you want to see all available quick commands

**Contains:**
- Quick command reference table
- Usage examples
- Command categories (high/medium/low priority)

### 4. `STATUS-CHECK.md` (Authoritative Status)
**What it is:** The ground-truth status document based on actual code and git history.

**When to use:**
- When you need to verify what's actually implemented
- When you need authoritative status (not just planned)
- When checking if something is truly done

---

## 🚀 How to Use This System

### Starting a New Chat Session

1. **Open Cursor Chat** (`Cmd/Ctrl + L`)

2. **Option A: Use a Quick Command** (Fastest)
   ```
   implement comfyui manager
   ```
   The AI will understand the full context and execute the complete task.

3. **Option B: Ask About Status** (When unsure)
   ```
   show project status
   ```
   The AI will read `PROJECT-STATUS.md` and give you a summary.

4. **Option C: Ask What's Left** (Planning)
   ```
   show what's left
   ```
   The AI will read `CURSOR-PROJECT-MANAGER.md` and show remaining tasks.

5. **Option D: Give a Specific Task** (Custom)
   ```
   Add a workflow preset system with portrait, fashion, and product presets
   ```
   The AI will check if it's already built, then implement it.

---

## 💡 Quick Command Examples

### High Priority Tasks

```bash
# Implement ComfyUI management page
implement comfyui manager

# Connect Model Manager to ComfyUI folders
wire model sync

# Add workflow presets
add workflow presets
```

### Status & Information

```bash
# See current project status
show project status

# See what's built
show what's built

# See what's left
show what's left

# See next tasks
show next tasks
```

### Quality Improvements

```bash
# Add LoRA selection
add lora selection

# Add VAE selection
add vae selection

# Improve job queueing
improve queueing
```

---

## 📋 Typical Workflow

### Example: Implementing a New Feature

1. **Check Status**
   ```
   show what's left
   ```

2. **Choose a Task**
   Based on the output, pick a high-priority task.

3. **Execute with Quick Command**
   ```
   implement comfyui manager
   ```

4. **AI Executes**
   - Reads `CURSOR-PROJECT-MANAGER.md` for context
   - Understands what "ComfyUI manager" means
   - Implements the complete feature
   - Updates status files automatically

5. **Verify**
   ```
   show project status
   ```
   Check that the task is marked as completed.

---

## 🎯 Best Practices

### 1. Start with Status
Always start a new session by checking status:
```
show project status
```

### 2. Use Quick Commands
When you know what you want, use quick commands from `QUICK-ACTIONS.md`:
```
wire model sync
```

### 3. Be Specific When Needed
If a quick command doesn't exist, be specific:
```
Add a feature to automatically sync downloaded models to ComfyUI checkpoints folder using symlinks on macOS and junctions on Windows
```

### 4. Verify After Completion
After completing a task, verify it's tracked:
```
show project status
```

### 5. Update Manually If Needed
If the AI doesn't update status files automatically, you can ask:
```
Update PROJECT-STATUS.md to mark ComfyUI manager as completed
```

---

## 🔄 How the System Updates

### Automatic Updates
The AI should automatically:
- Update `PROJECT-STATUS.md` after completing tasks
- Update `CURSOR-PROJECT-MANAGER.md` when major features are done
- Update `STATUS-CHECK.md` when verification status changes

### Manual Updates
If automatic updates don't happen, you can:
1. Ask the AI to update: "Update PROJECT-STATUS.md with completed tasks"
2. Manually edit the files (they're markdown, easy to edit)
3. Reference the files in chat: "Read PROJECT-STATUS.md and update it"

---

## 📚 File Relationships

```
CURSOR-PROJECT-MANAGER.md (Main Context)
    ↓
    ├──→ PROJECT-STATUS.md (Real-Time Updates)
    ├──→ QUICK-ACTIONS.md (Command Reference)
    └──→ STATUS-CHECK.md (Authoritative Truth)
```

**Flow:**
1. `CURSOR-PROJECT-MANAGER.md` is the source of truth
2. `PROJECT-STATUS.md` tracks real-time changes
3. `QUICK-ACTIONS.md` provides quick access
4. `STATUS-CHECK.md` verifies against code

---

## 🆘 Troubleshooting

### Problem: AI doesn't understand the quick command
**Solution:** 
- Check `QUICK-ACTIONS.md` for the exact command
- Or be more specific: "Add a ComfyUI management page with download, start, stop, and logs"

### Problem: Status files aren't updating
**Solution:**
- Ask explicitly: "Update PROJECT-STATUS.md with what we just completed"
- Or manually edit the files

### Problem: AI doesn't know project state
**Solution:**
- Reference the file: "Read CURSOR-PROJECT-MANAGER.md and tell me what's built"
- Or copy a section into chat

### Problem: Quick command doesn't exist
**Solution:**
- Use a descriptive command instead
- Or add it to `QUICK-ACTIONS.md` for future use

---

## 🎓 Advanced Usage

### Combining Commands
You can combine multiple quick commands:
```
implement comfyui manager and wire model sync
```

### Referencing Specific Files
You can reference specific sections:
```
Read the "What Remains" section from CURSOR-PROJECT-MANAGER.md and implement the first item
```

### Custom Context
You can provide custom context:
```
Based on CURSOR-PROJECT-MANAGER.md, implement the ComfyUI manager but also add automatic model syncing
```

---

## ✅ Checklist for New Sessions

- [ ] Open Cursor Chat (`Cmd/Ctrl + L`)
- [ ] Check status: `show project status`
- [ ] Review what's left: `show what's left`
- [ ] Pick a task from recommended next tasks
- [ ] Execute with quick command or specific instruction
- [ ] Verify completion: `show project status`

---

**Ready to start?** Open Cursor Chat and type: `show project status`

---

*Last Updated: [Auto-updated]*  
*Related Files: `CURSOR-PROJECT-MANAGER.md`, `PROJECT-STATUS.md`, `QUICK-ACTIONS.md`, `STATUS-CHECK.md`*

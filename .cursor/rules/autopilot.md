# Autopilot Rules (CONTROL_PLANE-First)

## Core Principle
**Single Source of Truth:** `docs/CONTROL_PLANE.md` is the ONLY governance/planning/logging source.

## File Access Rules
- ✅ **ALWAYS read:** `docs/CONTROL_PLANE.md`
- ✅ **ALWAYS read:** Code files needed for implementation
- ❌ **NEVER read:** TASKS.md, EXEC_REPORT.md, PRD, ROADMAP, etc. UNLESS:
  - `Deep Dive Needed: true` is set in CONTROL_PLANE ACTIVE_EPIC
  - Record in RUN LOG: why + which doc(s) read

## Command Behavior

### STATUS
- Read CONTROL_PLANE.md only
- Run `git status --porcelain` + `git log -1 --oneline`
- Update ONLY DASHBOARD fields (REPO_CLEAN, NEEDS_SAVE, LAST_CHECKPOINT, NEXT_MODE)
- Do NOT touch other files

### PLAN
- Read CONTROL_PLANE only
- Choose next task from "Backlog: Next 10"
- Create/Update ACTIVE_EPIC + ACTIVE_TASK in CONTROL_PLANE
- NEVER scan TASKS.md during PLAN (unless Deep Dive Needed: true)

### DO
- Implement only what ACTIVE_TASK/Subtasks require
- MUST modify code if task is coding task
- Record in CONTROL_PLANE RUN LOG (short, ≤15 lines)
- Do NOT expand governance docs

### BURST
- Complete 3–7 subtasks before SAVE
- Follow BURST POLICY in CONTROL_PLANE
- Stop on blockers (create BLOCKER entry, set STATUS=YELLOW)

### SAVE
- Run minimal tests per CONTROL_PLANE test policy
- Update CONTROL_PLANE only (DASHBOARD, RUN LOG, CHECKPOINT HISTORY)
- Commit with format: `chore(autopilot): checkpoint <STATE_ID> <ACTIVE_TASK_ID> - <short title>`
- Do NOT update multiple other docs during SAVE

## Anti-Hallucination
- Never invent requirements, tasks, or "what was changed"
- Only use: CONTROL_PLANE Backlog, actual code files, actual command outputs
- If requirement missing: create BLOCKER + set STATUS=YELLOW

## Speed Optimization
- Prefer BURST over micro-steps
- Batch docs work: update CONTROL_PLANE continuously, but defer heavy doc rewrites
- If AUTO produces only .md changes without code progress: mark STATUS=YELLOW + blocker

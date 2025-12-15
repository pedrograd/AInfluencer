# Cursor Rules - AInfluencer Project

**Primary Rule:** See `.cursor/rules/autopilot-protocol.md` for the complete one-word command protocol.

---

## Quick Start

**Fastest path:** Use a single chat and type `AUTO` repeatedly.

**One-word commands:**
- `STATUS` → Read-only status check
- `SCAN` → Extract tasks from docs incrementally
- `PLAN` → Auto-select next task
- `DO` / `CONTINUE` → Execute one atomic step
- `SAVE` → Checkpoint state
- `AUTO` → Full autonomous cycle (STATUS → [SAVE if dirty] → PLAN → DO → SAVE). AUTO always ends with SAVE.
- `NEXT` → Force-select next task (rare)
- `UNLOCK` → Clear stale lock (rare)

**Multi-chat safety:**
- Only ONE chat may write changes (AUTO/DO/SAVE)
- All other chats must be read-only (STATUS only)

---

## Core Principles

1. **No hallucinations:** Never invent tasks. Only extract from docs.
2. **No task loss:** Never delete tasks. Only change status: TODO → DOING → DONE.
3. **Evidence & Tests required:** DONE tasks must include evidence (files) + tests (commands + results).
4. **Single Writer Lock:** Only one chat session may modify files at a time.
5. **Cost discipline:** Always read `docs/00_STATE.md` first. Read additional docs only when needed.

---

## Source of Truth Files

- `docs/00_STATE.md` - Canonical state machine (MUST READ on every chat)
- `docs/TASKS.md` - Master backlog (never delete tasks)
- `docs/07_WORKLOG.md` - Append-only evidence log
- `docs/_generated/SESSION_RUN.md` - Append-only run log

---

## Lock Mechanism

Before editing any file, check `docs/00_STATE.md` for:
- `LOCKED_BY` - Session identifier
- `LOCK_REASON` - Why locked
- `LOCK_TIMESTAMP` - When locked

If locked by another session (and not stale >2h), output "READ-ONLY MODE: locked by <id>" and do not edit files.

---

## Default Behavior

**On every new chat:**
1. Read `docs/00_STATE.md` first
2. Run cheap checks: `git status --porcelain`, `git diff --name-only`
3. If `NEEDS_SAVE=true`, run SAVE before new work

**Never read all docs by default.** Only read what's needed for the current atomic step.

---

## Reference

For complete protocol details, see: `.cursor/rules/autopilot-protocol.md`


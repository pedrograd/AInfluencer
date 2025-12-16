# Cursor Rules - AInfluencer Project

**SINGLE SOURCE OF TRUTH:** `docs/CONTROL_PLANE.md` + `docs/SYNC_PLANE.md`

**One-writer lock enforced:** Only one machine/chat may write changes at a time.  
**Follower must be read-only:** Followers only pull, never commit.

---

## Quick Start

**On every new chat:**
1. Read `docs/CONTROL_PLANE.md` (this is the single pane of glass - ONLY governance file)
2. Run cheap checks: `git status --porcelain`, `git diff --name-only`, `git log -10 --oneline`
3. If repo is dirty, reconcile docs first, then proceed

**CRITICAL:** Do NOT read or write to `docs/00_STATE.md`, `docs/TASKS.md`, or `docs/07_WORKLOG.md` - these are deprecated. All governance is in `docs/CONTROL_PLANE.md` only.

**Commands (from CONTROL_PLANE):**
- `STATUS` → Read-only status check
- `BATCH_20` → Speed mode: 10–20 related atomic steps (mini-checks every 5 steps)
- `BLITZ` → Up to 50 micro-tasks (mini-checks every 10 items)
- `AUTO` → Safe default cycle (STATUS → SAVE if dirty → PLAN → DO → SAVE)
- `PLAN` → Auto-select next task
- `DO` / `CONTINUE` → Execute one atomic step
- `SAVE` → Checkpoint state

**Sync (cross-platform):**
- Sync is done ONLY via `SYNC` command: `./sync` (Mac/Linux) or `SYNC.bat` (Windows)
- Do not invent new sync scripts. See `docs/CONTROL_PLANE.md` SYNC section for details.

**Multi-chat safety:**
- Only ONE chat may write changes (single-writer lock)
- All other chats must be read-only (STATUS only)

---

## Core Rules

1. **Single Writer Lock:** Only one chat session may write changes at a time.
2. **Command Protocol:** All commands defined in `docs/CONTROL_PLANE.md`.
3. **Source of Truth:** All governance and state comes from `docs/CONTROL_PLANE.md`.
4. **Never mass-delete:** If consolidating, merge content first, update references, then delete/move safely.
5. **Stop on failure:** If any command/test fails → stop, set STATUS: RED, write CURRENT_BLOCKER.

---

## Reference

For complete protocol, commands, and project state, see: `docs/CONTROL_PLANE.md`


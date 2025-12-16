# 🔄 SYNC_PLANE — Cross-Platform Sync Governance

> **Single Source of Truth:** Git repository (origin/main)  
> **Last Updated:** 2025-12-16  
> **Purpose:** Conflict-proof syncing across Mac + Windows with one-writer lock
> **Canonical Command:** `./sync` (Mac/Linux) or `SYNC.bat` (Windows) — see `docs/CONTROL_PLANE.md` for quick reference

---

## Single-Command Sync System

**Primary Entry Point:**
- Mac/Linux: `./sync` (or `./sync --once` for one iteration)
- Windows: `SYNC.bat`

The sync system automatically:
- Detects role from `.sync-role` file, `SYNC_ROLE` env var, or CLI flags
- Shows status (branch, HEAD, upstream, ahead/behind, dirty/clean, role)
- Handles follower mode (continuous pull loop) or writer mode (one-shot sync)
- Creates backup branches on divergence/conflicts
- Never force-pushes or destructively resets without backup

## Roles

### Writer (One at a time)
- **Can:** Commit, push changes
- **Must:** Push after every commit
- **Must NOT:** Run if another machine is writing

### Follower (Read-only)
- **Can:** Pull latest changes
- **Must:** Use `git pull --ff-only` (never auto-merge)
- **Must NOT:** Commit or push changes
- **Must NOT:** Run if local changes exist

---

## Role Switching

### Set Role (Recommended)
- Mac/Linux: `./scripts/sync/set_role.sh WRITER` or `./scripts/sync/set_role.sh FOLLOWER`
- Windows: `.\scripts\sync\set_role.ps1 WRITER` or `.\scripts\sync\set_role.ps1 FOLLOWER`

### Alternative Methods
1. Create `.sync-role` file with content `WRITER` or `FOLLOWER`
2. Set env var: `SYNC_ROLE=WRITER` (Mac) / `set SYNC_ROLE=WRITER` (Windows)
3. CLI flag: `./sync --writer` or `./sync --follower`

---

## Emergency Procedures

### Emergency Resync (Non-destructive)
If follower is out of sync but has no local changes:
```bash
git fetch --all --prune
git reset --hard origin/main
```

### Nuke Local Changes (Destructive)
**⚠️ WARNING: This deletes all uncommitted local changes**
```bash
git fetch --all --prune
git reset --hard origin/main
git clean -fd
```

---

## Expected Loop Cadence

- **Follower:** Pulls every 5 seconds via `./sync` (continuous loop)
- **Writer:** One-shot sync via `SYNC_ROLE=WRITER ./sync` (pulls then pushes)

## Switch Machine (Writer Handoff)

**On old machine (current writer):**
1. Commit all changes: `git add -A && git commit -m "..."` (if needed)
2. Sync and push: `SYNC_ROLE=WRITER ./sync` (Mac) or `set SYNC_ROLE=WRITER && SYNC.bat` (Windows)
3. Set to follower: `./scripts/sync/set_role.sh FOLLOWER` (Mac) or `.\scripts\sync\set_role.ps1 FOLLOWER` (Windows)

**On new machine:**
1. Pull latest: `git pull origin main` (or run `./sync` once as follower)
2. Set to writer: `./scripts/sync/set_role.sh WRITER` (Mac) or `.\scripts\sync\set_role.ps1 WRITER` (Windows)
3. Verify: `SYNC_ROLE=WRITER ./sync --dry-run` (Mac) or `set SYNC_ROLE=WRITER && SYNC.bat --dry-run` (Windows)
4. Start working: `SYNC_ROLE=WRITER ./sync` after commits

## Git Configuration (Recommended)

**Mac/Linux:**
```bash
git config core.autocrlf input
git config pull.rebase false
git config fetch.prune true
```

**Windows:**
```bash
git config core.autocrlf true
git config pull.rebase false
git config fetch.prune true
```

These settings ensure:
- Line endings normalized (LF on Mac, CRLF on Windows)
- Pull uses merge (not rebase) by default
- Stale remote branches are pruned automatically

---

## Rules

1. **Never auto-merge** — Only `git pull --ff-only`
2. **One Writer at a time** — Writer commits & pushes; Followers only pull
3. **No silent destructive actions** — No `reset --hard` unless explicitly requested
4. **Repo config is truth** — `.cursor/rules/*` and `.vscode/*` tracked in Git


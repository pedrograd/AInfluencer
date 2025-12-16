# 🔄 SYNC_PLANE — Cross-Platform Sync Governance

> **Single Source of Truth:** Git repository (origin/main)  
> **Last Updated:** 2025-12-15  
> **Purpose:** Conflict-proof syncing across Mac + Windows with one-writer lock

---

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

### Switch to Writer
1. Stop follower loop if running (Ctrl+C)
2. Run: `./scripts/sync/switch-to-writer.sh` (Mac) or `scripts\sync\switch-to-writer.ps1` (Windows)
3. Verify clean status and upstream
4. Start making changes

### Switch to Follower
1. Ensure no local uncommitted changes
2. Run: `./scripts/sync/switch-to-follower.sh` (Mac) or `scripts\sync\switch-to-follower.ps1` (Windows)
3. Start pull loop: `./sync-follower.sh` (Mac) or `SYNC-FOLLOWER.bat` (Windows)

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

- **Follower:** Pulls every 5 seconds via `follower-pull` script
- **Writer:** Pushes immediately after each commit via `writer-push` script

---

## Rules

1. **Never auto-merge** — Only `git pull --ff-only`
2. **One Writer at a time** — Writer commits & pushes; Followers only pull
3. **No silent destructive actions** — No `reset --hard` unless explicitly requested
4. **Repo config is truth** — `.cursor/rules/*` and `.vscode/*` tracked in Git


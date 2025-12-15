# ROADMAP - Phases & Milestones

**Purpose:** High-level phases and milestones. Keep short and focused.

---

## MVP Goal
**"Double-click → Dashboard opens with logs and diagnostics"**

A cross-platform launcher that:
- One-click install/verify/repair/start
- One-click run (basic workflows)
- Fully logged (every action + error + fix guidance)
- Non-technical-user friendly dashboard
- Built in small, testable, idempotent steps

---

## Phase 1: Bootstrap (Current)
**Goal:** Canonical docs + unified launcher + logging

### Milestones
- [x] Backend + Frontend exist
- [ ] Canonical docs structure created
- [ ] Cross-platform launcher created
- [ ] Unified logging system created
- [ ] Dashboard shows system status + logs

**Done means:** User can double-click launcher → dashboard opens → see logs → see system status

---

## Phase 2: Core Services
**Goal:** All services start/stop cleanly with health checks

### Milestones
- [ ] Backend service orchestration (start/stop/health)
- [ ] Frontend service orchestration (start/stop/health)
- [ ] ComfyUI service orchestration (start/stop/health)
- [ ] Service status dashboard (all services + ports + health)

**Done means:** Dashboard shows all services, can start/stop each, health checks work

---

## Phase 3: Workflows (Later)
**Goal:** Basic workflow support

### Milestones
- [ ] Workflow catalog (curated workflow packs)
- [ ] Workflow validation (required nodes/models/extensions)
- [ ] One-click workflow run

**Done means:** User can select workflow → run → see results

---

## Out of Scope (Until MVP Works)
- User accounts
- Cloud sync
- Payments
- Mobile apps
- Plugins marketplace
- Advanced analytics


# Canonical Documentation Structure

**Purpose:** Defines the core canonical documentation files that serve as the foundation for the project. These are the essential documents that should be read first and maintained as the single source of truth for their respective domains.

**Last Updated:** 2025-01-16  
**Status:** Active

---

## 📋 Core Canonical Documents (Priority Order)

### Foundation Layer (00-09)

1. **`00-README.md`** - Documentation index and navigation hub
   - Purpose: Master index and starting point for all documentation
   - Status: ✅ Exists
   - Reading Order: Read first

2. **`01-PRD.md`** - Product Requirements Document
   - Purpose: Complete product requirements and feature specifications
   - Status: ✅ Exists
   - Reading Order: Read second (after 00-README.md)

3. **`02-PROJECT-OVERVIEW.md`** - Project vision and goals
   - Purpose: High-level vision, goals, and project overview
   - Status: ✅ Exists (also `01-PROJECT-OVERVIEW.md` exists - needs consolidation)
   - Reading Order: Read third

4. **`03-TECHNICAL-ARCHITECTURE.md`** - System architecture
   - Purpose: Technical architecture, system design, and component structure
   - Status: ✅ Exists (also `02-TECHNICAL-ARCHITECTURE.md` exists - needs consolidation)
   - Reading Order: Read fourth

5. **`04-DATABASE-SCHEMA.md`** - Database design
   - Purpose: Database schema, models, and data structure
   - Status: ✅ Exists (also `09-DATABASE-SCHEMA.md` exists - needs consolidation)
   - Reading Order: Read when implementing database features

6. **`05-API-DESIGN.md`** - API specification
   - Purpose: API endpoints, request/response formats, and API design patterns
   - Status: ✅ Exists (also `10-API-DESIGN.md` exists - needs consolidation)
   - Reading Order: Read when implementing API features

7. **`06-UI-UX-DESIGN-SYSTEM.md`** - Design system
   - Purpose: UI/UX design system, components, and design patterns
   - Status: ✅ Exists (also `08-UI-UX-DESIGN-SYSTEM.md` exists - needs consolidation)
   - Reading Order: Read when implementing frontend features

8. **`07-AI-MODELS-REALISM.md`** - AI models setup
   - Purpose: AI model integration, setup, and configuration
   - Status: ✅ Exists (also `04-AI-MODELS-REALISM.md` exists - needs consolidation)
   - Reading Order: Read when setting up AI models

9. **`08-DEVELOPMENT-ENVIRONMENT.md`** - Development environment setup
   - Purpose: How to set up the development environment
   - Status: ⚠️ Check if exists (may be `DEVELOPMENT-SETUP.md`)
   - Reading Order: Read when setting up development environment

10. **`09-TESTING-STRATEGY.md`** - Testing approach
    - Purpose: Testing strategy, test plans, and testing patterns
    - Status: ✅ Exists (also `14-TESTING-STRATEGY.md` exists - needs consolidation)
    - Reading Order: Read when implementing tests

---

## 🔄 Autopilot-Specific Canonical Docs

These are the core docs used by the autopilot system for project governance:

1. **`CONTROL_PLANE.md`** - Single source of truth for project state
   - Purpose: Project dashboard, task ledger, run logs, and autopilot governance
   - Status: ✅ Exists
   - Reading Order: Read first when resuming work (for autopilot)

2. **`SIMPLIFIED-ROADMAP.md`** - Simplified MVP roadmap
   - Purpose: High-level MVP roadmap with 6-week plan
   - Status: ✅ Exists
   - Reading Order: Read for project planning

3. **`QUICK-START.md`** - Quick start guide
   - Purpose: Quick start instructions for developers
   - Status: ✅ Exists
   - Reading Order: Read when starting development

---

## 📁 Supporting Documentation

These documents support the canonical docs but are not part of the core structure:

- **Planning & Roadmap:** `01_ROADMAP.md`, `03-FEATURE-ROADMAP.md`, `07-DEVELOPMENT-TIMELINE.md`
- **Architecture Details:** `02_ARCHITECTURE.md`, `04_WORKFLOWS_CATALOG.md`
- **Operations:** `03_INSTALL_MATRIX.md`, `05_TESTPLAN.md`, `06_ERROR_PLAYBOOK.md`
- **Features:** `11-COMPETITIVE-ANALYSIS.md`, `12-LEGAL-COMPLIANCE.md`, `13-CONTENT-STRATEGY.md`
- **Deployment:** `15-DEPLOYMENT-DEVOPS.md`
- **Guides:** `COMMANDS.md`, `SYNC_PLANE.md`, `CONTROL_PLANE.md`

---

## 🎯 Naming Convention

**Canonical docs should follow this pattern:**
- `NN-TITLE.md` where NN is a two-digit number (00-99) and TITLE is in Title-Case with hyphens
- Examples: `00-README.md`, `01-PRD.md`, `02-PROJECT-OVERVIEW.md`

**Supporting docs can use:**
- `NN_TITLE.md` (underscores for supporting docs)
- `TITLE.md` (no number prefix for guides/utilities)

---

## ✅ Consolidation Needed

The following duplicates need to be consolidated:

1. **Project Overview:**
   - `01-PROJECT-OVERVIEW.md` → merge into `02-PROJECT-OVERVIEW.md`

2. **Technical Architecture:**
   - `02-TECHNICAL-ARCHITECTURE.md` → merge into `03-TECHNICAL-ARCHITECTURE.md`

3. **Database Schema:**
   - `09-DATABASE-SCHEMA.md` → merge into `04-DATABASE-SCHEMA.md`

4. **API Design:**
   - `10-API-DESIGN.md` → merge into `05-API-DESIGN.md`

5. **UI/UX Design:**
   - `08-UI-UX-DESIGN-SYSTEM.md` → merge into `06-UI-UX-DESIGN-SYSTEM.md`

6. **AI Models:**
   - `04-AI-MODELS-REALISM.md` → merge into `07-AI-MODELS-REALISM.md`

7. **Testing:**
   - `14-TESTING-STRATEGY.md` → merge into `09-TESTING-STRATEGY.md`

8. **PRD:**
   - `PRD.md` → merge into `01-PRD.md`

---

## 📝 Maintenance Rules

1. **Canonical docs are the single source of truth** for their domain
2. **Supporting docs** can reference canonical docs but should not duplicate core information
3. **When updating:** Update canonical docs first, then update supporting docs if needed
4. **When creating new docs:** Check if it should be canonical (numbered 00-99) or supporting (other naming)

---

## 🔍 Verification Checklist

- [x] `00-README.md` exists and is up to date
- [x] `01-PRD.md` exists
- [x] `02-PROJECT-OVERVIEW.md` exists
- [x] `03-TECHNICAL-ARCHITECTURE.md` exists
- [x] `04-DATABASE-SCHEMA.md` exists
- [x] `05-API-DESIGN.md` exists
- [x] `06-UI-UX-DESIGN-SYSTEM.md` exists
- [x] `07-AI-MODELS-REALISM.md` exists
- [ ] `08-DEVELOPMENT-ENVIRONMENT.md` exists (or needs creation)
- [x] `09-TESTING-STRATEGY.md` exists
- [x] `CONTROL_PLANE.md` exists
- [x] `SIMPLIFIED-ROADMAP.md` exists
- [x] `QUICK-START.md` exists
- [ ] Duplicate consolidation completed (see Consolidation Needed section)

---

**Next Steps:**
1. Complete duplicate consolidation
2. Create `08-DEVELOPMENT-ENVIRONMENT.md` if it doesn't exist
3. Update `00-README.md` to reference this canonical structure document
4. Verify all canonical docs are properly linked and cross-referenced


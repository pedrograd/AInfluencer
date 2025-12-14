# Simplified MVP Roadmap - One-Click Dashboard

**Focus:** Build a working dashboard that installs, configures, and runs everything automatically.

---

## Phase 0: Foundation Setup (Week 1) 🎯 **START HERE**

### Goal
Set up project structure and basic infrastructure that works on Windows and Mac.

### Tasks

#### Day 1-2: Project Structure
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Set up Python FastAPI backend structure
- [ ] Configure ESLint, Prettier, Black, Ruff
- [ ] Set up Git repository with proper .gitignore
- [ ] Create basic folder structure:
  ```
  /backend
  /frontend
  /scripts (installer scripts)
  /docs
  ```

#### Day 3-4: Database & Basic API
- [ ] Set up PostgreSQL (Docker or local)
- [ ] Create basic database connection (SQLAlchemy)
- [ ] Create health check API endpoint
- [ ] Set up environment variable system (.env.example)

#### Day 5-7: One-Click Installer System
- [ ] Create system requirement checker (GPU, RAM, OS)
- [ ] Create installer script (Python + Node.js check/install)
- [ ] Create dependency downloader (models, packages)
- [ ] Create setup wizard UI component
- [ ] Test on Windows and Mac

**Deliverable:** One-click installer that checks system and installs dependencies

---

## Phase 1: Dashboard Core (Week 2) 🎯

### Goal
Working dashboard with model management (like Stability Matrix).

### Tasks

#### Day 1-3: Model Manager Backend
- [ ] Database schema for models (name, type, path, size, downloaded)
- [ ] API endpoints:
  - `GET /api/models` - List all models
  - `POST /api/models/download` - Download model
  - `GET /api/models/{id}/status` - Download progress
  - `DELETE /api/models/{id}` - Delete model
- [ ] Model downloader service (Hugging Face integration)
- [ ] Model storage organization system

#### Day 4-5: Model Manager UI
- [ ] Model list view (grid/list toggle)
- [ ] Model cards with metadata (size, quality, type)
- [ ] Download progress indicators
- [ ] Filter/search functionality
- [ ] Drag-and-drop model import

#### Day 6-7: Integration & Testing
- [ ] Connect UI to backend API
- [ ] Test model downloads (start with small models)
- [ ] Error handling and retry logic
- [ ] Logging system for errors

**Deliverable:** Working model manager where users can browse and download AI models

---

## Phase 2: Basic Content Generation (Week 3) 🎯

### Goal
Generate images with face consistency using downloaded models.

### Tasks

#### Day 1-2: Stable Diffusion Integration
- [ ] Set up ComfyUI or Automatic1111 API connection
- [ ] Image generation service (text-to-image)
- [ ] API endpoint: `POST /api/generate/image`
- [ ] Image storage system (save generated images)

#### Day 3-4: Face Consistency (InstantID)
- [ ] Face embedding extraction service
- [ ] InstantID integration for face consistency
- [ ] Face embedding storage in database
- [ ] API endpoint: `POST /api/generate/image` with face_embedding_id

#### Day 5-6: Basic Character System
- [ ] Database schema for characters (name, bio, face_embeddings)
- [ ] Character creation API
- [ ] Character selection in generation UI
- [ ] Basic character dashboard

#### Day 7: Testing & Polish
- [ ] Test image generation with face consistency
- [ ] Quality validation (basic checks)
- [ ] Error handling improvements
- [ ] UI improvements

**Deliverable:** Generate images with consistent character faces

---

## Phase 3: Content Library & UI Polish (Week 4) 🎯

### Goal
Organize generated content and improve UI/UX.

### Tasks

#### Day 1-2: Content Library Backend
- [ ] Database schema for content items
- [ ] API endpoints (list, view, delete, download)
- [ ] Content storage organization
- [ ] Thumbnail generation

#### Day 3-4: Content Library UI
- [ ] Grid view of generated content
- [ ] Content detail modal
- [ ] Filter by character, date, type
- [ ] Download functionality
- [ ] Delete/approval workflow

#### Day 5-7: Dashboard Polish
- [ ] Beautiful landing page
- [ ] Navigation system
- [ ] Error logging viewer
- [ ] System status panel
- [ ] Settings page
- [ ] Responsive design (mobile-ready)

**Deliverable:** Complete dashboard with content library, error logging, and polished UI

---

## Phase 4: Video Generation (Week 5) 🎯

### Goal
Add video generation capability.

### Tasks

#### Day 1-3: Video Generation Backend
- [ ] Integrate Kling AI 2.5 or Stable Video Diffusion
- [ ] Video generation service
- [ ] Face consistency in videos
- [ ] API endpoint: `POST /api/generate/video`
- [ ] Video storage system

#### Day 4-5: Video Generation UI
- [ ] Video generation form
- [ ] Video preview player
- [ ] Generation progress tracking
- [ ] Video library integration

#### Day 6-7: Testing & Optimization
- [ ] Test video generation
- [ ] Optimize generation time
- [ ] Quality improvements
- [ ] Error handling

**Deliverable:** Generate videos with character consistency

---

## Phase 5: Automation Foundation (Week 6) 🎯

### Goal
Basic automation - scheduled content generation.

### Tasks

#### Day 1-2: Scheduling System
- [ ] Celery task queue setup
- [ ] Scheduled task system
- [ ] API endpoints for scheduling
- [ ] Task status tracking

#### Day 3-4: Automation Rules
- [ ] Database schema for automation rules
- [ ] Rule creation API
- [ ] Rule execution engine
- [ ] Basic UI for creating rules

#### Day 5-7: Testing & Improvements
- [ ] Test scheduled generation
- [ ] Error recovery system
- [ ] Logging improvements
- [ ] UI improvements

**Deliverable:** Automated scheduled content generation

---

## Future Phases (After MVP)

### Phase 6: Social Media Integration
- Instagram, Twitter, TikTok, YouTube, OnlyFans
- Automated posting
- Engagement automation

### Phase 7: Advanced Features
- Text generation (LLM)
- Voice generation (TTS)
- Advanced anti-detection
- Analytics and insights

---

## Immediate Next Steps (Today)

1. **Set up project structure**
   ```bash
   # Use Cursor Chat to:
   "Create Next.js 14 project structure with TypeScript,
   FastAPI backend structure, and proper folder organization.
   Support Windows and Mac."
   ```

2. **Create installer system**
   ```bash
   # Use Cursor Composer to:
   "Create a one-click installer system that:
   - Checks system requirements (OS, GPU, RAM)
   - Downloads Python/Node.js if needed
   - Installs dependencies
   - Sets up database
   - Shows progress with logs
   - Works on Windows and Mac"
   ```

3. **Set up model manager**
   ```bash
   # Use Cursor Chat to plan:
   "Design model manager system similar to Stability Matrix.
   What components do I need?"
   ```

---

## Success Criteria for MVP

✅ **Week 1:** One-click installer works on Windows and Mac  
✅ **Week 2:** Users can browse and download AI models  
✅ **Week 3:** Generate images with face consistency  
✅ **Week 4:** Content library with polished UI  
✅ **Week 5:** Generate videos  
✅ **Week 6:** Basic automation works  

---

## Technology Stack (Simplified)

### Frontend
- Next.js 14 (App Router)
- TypeScript
- shadcn/ui + Tailwind CSS
- React Query (data fetching)

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Celery + Redis (for tasks)

### AI/ML
- ComfyUI or Automatic1111 (SD integration)
- InstantID (face consistency)
- Realistic Vision V6.0 (base model)
- Kling AI or SVD (video)

### Infrastructure
- Docker (optional, for PostgreSQL/Redis)
- Local file storage (images/videos)
- Environment-based configuration

---

## Key Principles

1. **Keep It Simple** - Only essential features for MVP
2. **Windows + Mac First** - Prioritize cross-platform
3. **One-Click Everything** - Zero manual configuration
4. **Error Logging** - Everything logged, visible in UI
5. **Progressive Enhancement** - Basic features first, polish later

---

## Using Cursor for Development

See `CURSOR-GUIDE.md` for detailed Cursor usage instructions.

**Quick Start:**
1. Open Cursor
2. Press `Cmd/Ctrl + L` for Chat
3. Ask: "Review this roadmap and help me start with Phase 0"
4. Use Composer (`Cmd/Ctrl + I`) for multi-file changes
5. Use Inline Edit (`Cmd/Ctrl + K`) for quick fixes

---

**Status:** 🟢 Ready to Start - Begin with Phase 0, Week 1

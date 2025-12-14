# 🚀 Quick Start Guide - CEO/CPO/CTO Level

**Your First Steps to Build the AInfluencer Platform**

---

## What We're Building

A **one-click dashboard** that:
1. ✅ Installs everything automatically (models, dependencies, tools)
2. ✅ Manages AI models (like Stability Matrix)
3. ✅ Generates ultra-realistic content (images, videos)
4. ✅ Maintains character consistency (face, voice, style)
5. ✅ Works on Windows and Mac
6. ✅ Requires zero technical knowledge from end users

---

## Step-by-Step: How to Start RIGHT NOW

### Step 1: Review Current State (5 minutes)

1. **Open Cursor IDE**
   ```bash
   cd /Users/pedram/AInfluencer
   cursor .
   ```

2. **Check Project Structure**
   - You have comprehensive documentation in `docs/`
   - You have Cursor rules in `.cursor/rules/`
   - You have a simplified roadmap in `docs/SIMPLIFIED-ROADMAP.md`

3. **Read Key Documents**
   - `CURSOR-GUIDE.md` - How to use Cursor effectively
   - `docs/SIMPLIFIED-ROADMAP.md` - What to build first
   - `docs/PRD.md` - What we're building (overview)

### Step 2: Set Up Development Environment (30 minutes)

#### Using Cursor Chat (`Cmd/Ctrl + L`):

```
"Help me set up the development environment:
1. Initialize Next.js 14 project in /frontend with TypeScript
2. Initialize FastAPI project in /backend with Python 3.11+
3. Set up proper folder structure
4. Configure ESLint, Prettier for frontend
5. Configure Black, Ruff for backend
6. Create .env.example files
7. Set up .gitignore properly

Make it work on both Windows and Mac."
```

#### Manual Setup (if preferred):

```bash
# Frontend
cd frontend
npx create-next-app@latest . --typescript --tailwind --app
npm install @radix-ui/react-* # shadcn/ui will install these

# Backend
cd ../backend
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy asyncpg

# Install Cursor rules (already done, but verify)
ls .cursor/rules/
```

### Step 3: Create One-Click Installer (Week 1 Priority)

#### Using Cursor Composer (`Cmd/Ctrl + I`):

```
"Create a one-click installer system:

Backend (Python):
1. Create installer.py script that:
   - Checks OS (Windows/Mac)
   - Checks system requirements (GPU, RAM, storage, Python, Node.js)
   - Downloads/installs Python if missing
   - Downloads/installs Node.js if missing
   - Installs Python dependencies
   - Installs Node.js dependencies
   - Sets up PostgreSQL (or checks if exists)
   - Creates .env file from .env.example
   - Runs database migrations
   - Tests installation

2. Create installer service in FastAPI:
   - GET /api/installer/check - Check system requirements
   - POST /api/installer/start - Start installation
   - GET /api/installer/status - Get installation progress
   - GET /api/installer/logs - Get installation logs

Frontend (Next.js):
1. Create installer dashboard page:
   - System requirements checklist
   - Installation progress indicator
   - Real-time log viewer
   - Error messages with solutions
   - Beautiful UI using shadcn/ui

2. Connect to backend API
3. Show installation steps progress
4. Handle errors gracefully

Make it work on Windows and Mac. Use beautiful, modern UI."
```

### Step 4: Test Installation System

1. **Test on Your System**
   ```bash
   cd backend
   python installer.py --check
   ```

2. **Run Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Verify**
   - Open http://localhost:3000
   - See installer dashboard
   - Click "Start Installation"
   - Watch progress

### Step 5: Build Model Manager (Week 2 Priority)

#### Using Cursor Chat:

```
"Design the model manager system similar to Stability Matrix.
What database schema, API endpoints, and UI components do I need?
Check existing docs for reference."
```

#### Then use Composer:

```
"Create model manager system:

Database:
1. Create models table (id, name, type, size, path, downloaded, metadata)

Backend:
1. Model service to:
   - List available models from Hugging Face
   - Download models with progress tracking
   - Store model metadata in database
   - Verify model checksums
   - Organize models by type (checkpoint, LoRA, embedding)

2. API endpoints:
   - GET /api/models - List all models
   - POST /api/models/download - Download model
   - GET /api/models/{id}/status - Get download progress
   - DELETE /api/models/{id} - Delete model
   - POST /api/models/import - Import model file

Frontend:
1. Model manager page:
   - Grid/list view toggle
   - Model cards with metadata
   - Download progress bars
   - Filter by type, size, quality
   - Search functionality
   - Drag-and-drop import

2. Connect to backend API
3. Real-time progress updates

Follow Stability Matrix design patterns."
```

---

## Best Practices While Building

### 1. Use Cursor Effectively

- **Chat** (`Cmd/Ctrl + L`) for planning and questions
- **Composer** (`Cmd/Ctrl + I`) for multi-file changes
- **Inline Edit** (`Cmd/Ctrl + K`) for quick fixes
- **Tab** for autocomplete suggestions

### 2. Follow Project Standards

- Check `.cursor/rules/project-standards.md` for coding conventions
- Follow TypeScript strict mode
- Use async/await for all I/O operations
- Add error handling everywhere
- Log everything for debugging

### 3. Test Frequently

- Test each feature as you build
- Test on both Windows and Mac
- Test error scenarios
- Test with real models (start with small ones)

### 4. Keep It Simple

- Only essential features for MVP
- Can add advanced features later
- Focus on one-click automation
- Beautiful, clean UI

---

## Common Tasks with Cursor

### Create a New API Endpoint

```
"Create a new API endpoint following FastAPI best practices:
- POST /api/characters
- Accept JSON body with name, bio, persona
- Validate with Pydantic
- Store in PostgreSQL using SQLAlchemy
- Return 201 with created character
- Add error handling and logging
- Follow patterns from existing endpoints"
```

### Create a React Component

```
"Create a React component using shadcn/ui:
- CharacterCard component
- Displays character name, bio, avatar
- Has edit and delete buttons
- Uses TypeScript with proper types
- Follows existing component patterns
- Add to components/ui/ folder"
```

### Debug an Issue

```
"Debug this error: [paste error]
Expected behavior: [what should happen]
File: [file path]

Investigate and fix following project standards."
```

### Refactor Code

```
"Refactor this code to:
- Extract reusable logic to a service
- Add proper error handling
- Improve type safety
- Add logging
- Follow project standards

Update all affected files and tests."
```

---

## Next Steps After MVP

Once you have:
1. ✅ One-click installer working
2. ✅ Model manager working
3. ✅ Basic image generation working
4. ✅ Content library working

Then move to:
- Video generation
- Social media integration
- Advanced automation
- Text and voice generation

See `docs/SIMPLIFIED-ROADMAP.md` for full roadmap.

---

## Getting Help

### With Cursor
- See `CURSOR-GUIDE.md` for detailed instructions
- Use Chat to ask questions: "How do I...?"
- Reference rules: `@project-standards.md`

### With Project
- Check `docs/` folder for detailed documentation
- See `docs/PRD.md` for product requirements
- See `docs/04-AI-MODELS-REALISM.md` for AI model info

### Common Questions

**Q: Which AI models should I use?**
A: See `.cursor/rules/ai-models-workflow.md` - Start with Realistic Vision V6.0 and InstantID.

**Q: How do I structure the code?**
A: See `.cursor/rules/project-standards.md` - Follow microservices pattern.

**Q: What UI library should I use?**
A: shadcn/ui + Tailwind CSS (already in roadmap).

**Q: How do I handle errors?**
A: Always use try-catch, log errors, return user-friendly messages. See project standards.

---

## Success Checklist

Before moving to next phase, ensure:

- [ ] Code follows project standards
- [ ] Works on Windows and Mac
- [ ] Error handling implemented
- [ ] Logging in place
- [ ] UI is polished and responsive
- [ ] Tests pass (when you add them)
- [ ] Documentation updated

---

## Remember

1. **Start Small** - Build MVP first, add features later
2. **Test Often** - Don't wait until the end
3. **Use Cursor** - Let AI help you code faster
4. **Follow Standards** - Check rules before coding
5. **Keep It Simple** - Only essential features for now

---

**Ready to Start?** 

1. Open Cursor
2. Press `Cmd/Ctrl + L`
3. Say: "Help me start with Phase 0 from the simplified roadmap"
4. Begin building! 🚀

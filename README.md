# AInfluencer Platform

> Create Unlimited AI Influencers. Fully Automated. Completely Free.

A fully automated, self-hosted platform for creating and managing AI-generated influencer characters across multiple social media platforms.

## 🚀 Quick Start

### ⚡ One-Command Setup (Recommended)

**Run the master setup script to do everything automatically:**

```powershell
.\MASTER-SETUP.ps1
```

Or double-click: **`MASTER-SETUP.bat`**

This single script will:
- ✅ Check all prerequisites (Python, Node.js, Git, GPU)
- ✅ Create virtual environment
- ✅ Setup ComfyUI (clone if needed)
- ✅ Install all dependencies (backend + frontend)
- ✅ Download all required AI models
- ✅ Run tests
- ✅ Start all services (ComfyUI, Backend, Frontend)
- ✅ Open web interface in browser

**That's it!** Everything is automated. 🎉

### 📋 Manual Setup (Alternative)

If you prefer step-by-step setup:

1. **Complete Setup**: Run `.\auto-complete-setup.ps1` to install everything
2. **Download Models**: Run `.\download-models-auto.ps1` to download required AI models
3. **Start Services**: Run `.\start-all.ps1` to start all services
4. **Read Documentation**: Check [`SETUP.md`](./SETUP.md) for detailed setup instructions

For complete details, see [`SETUP.md`](./SETUP.md) or [`docs/PRD.md`](./docs/PRD.md)

## 📚 Documentation

**⭐ START HERE:**
- **[docs/00-DOCUMENTATION-INDEX.md](./docs/00-DOCUMENTATION-INDEX.md)** - Complete documentation index
- **[docs/34-USER-GUIDE-COMPLETE-INSTRUCTIONS.md](./docs/34-USER-GUIDE-COMPLETE-INSTRUCTIONS.md)** - Complete user guide (how to use everything)
- **[SETUP.md](./SETUP.md)** - Complete setup guide
- **[README_DEPLOY.md](./README_DEPLOY.md)** - Free-tier oriented deployment guide
- **[README_DEMO_MODE.md](./README_DEMO_MODE.md)** - Demo-mode behavior on CPU/free tiers

**Essential Guides:**
- **[docs/PRD.md](./docs/PRD.md)** - Product Requirements Document
- **[docs/33-MODELS-AND-CHECKPOINTS-COMPLETE-GUIDE.md](./docs/33-MODELS-AND-CHECKPOINTS-COMPLETE-GUIDE.md)** - Complete model recommendations and guide
- **[docs/32-COMPREHENSIVE-IMPROVEMENT-ROADMAP.md](./docs/32-COMPREHENSIVE-IMPROVEMENT-ROADMAP.md)** - Strategic improvement plan
- **[docs/36-MEGA-PROMPT-FUTURE-DEVELOPMENT.md](./docs/36-MEGA-PROMPT-FUTURE-DEVELOPMENT.md)** - Mega prompt for AI-assisted development

**Feature Guides:**
- **[docs/20-ADVANCED-PROMPT-ENGINEERING.md](./docs/20-ADVANCED-PROMPT-ENGINEERING.md)** - Advanced prompt techniques
- **[docs/21-FACE-CONSISTENCY-MASTER-GUIDE.md](./docs/21-FACE-CONSISTENCY-MASTER-GUIDE.md)** - Face consistency guide
- **[docs/22-VIDEO-GENERATION-COMPLETE-GUIDE.md](./docs/22-VIDEO-GENERATION-COMPLETE-GUIDE.md)** - Video generation guide
- **[docs/23-POST-PROCESSING-MASTER-WORKFLOW.md](./docs/23-POST-PROCESSING-MASTER-WORKFLOW.md)** - Post-processing guide
- **[docs/24-ANTI-DETECTION-ADVANCED-TECHNIQUES.md](./docs/24-ANTI-DETECTION-ADVANCED-TECHNIQUES.md)** - Anti-detection strategies

**Planning & Development:**
- **[docs/35-ENHANCED-FEATURES-ROADMAP.md](./docs/35-ENHANCED-FEATURES-ROADMAP.md)** - 50+ new features roadmap
- **[docs/TECHNICAL-ARCHITECTURE.md](./docs/TECHNICAL-ARCHITECTURE.md)** - Technical architecture
- **[docs/30-TROUBLESHOOTING-COMPLETE.md](./docs/30-TROUBLESHOOTING-COMPLETE.md)** - Troubleshooting guide

All documentation is in the [`docs/`](./docs/) folder. See [docs/00-DOCUMENTATION-INDEX.md](./docs/00-DOCUMENTATION-INDEX.md) for complete index.

## ✨ Features

- ✅ **Fully Automated**: Zero manual intervention required
- ✅ **Free & Open-Source**: No costs, full source code access
- ✅ **Ultra-Realistic**: Indistinguishable from real content
- ✅ **Multi-Platform**: Instagram, Twitter, Facebook, Telegram, OnlyFans, YouTube
- ✅ **Character Consistency**: Advanced face/style consistency
- ✅ **Self-Hosted**: Privacy and data control
- ✅ **+18 Support**: Built-in adult content generation
- ✅ **Unified Dashboard**: Everything in one place
- ✅ **Persona System**: Create, manage, export character personas
- ✅ **Paid AI Tools**: Optional premium AI service integration
- ✅ **Educational Academy**: Learn AI face creation, face swaps, video generation
- ✅ **Automated Flirting**: Natural, undetectable engagement behavior

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Frontend**: Next.js 14+, TypeScript, shadcn/ui
- **Database**: PostgreSQL 15+
- **Cache/Queue**: Redis
- **AI/ML**: Stable Diffusion XL, Ollama (Llama 3), Coqui TTS
- **Automation**: Celery, Playwright

## 📋 Requirements

- **Minimum**: 4 cores, 16GB RAM, 8GB GPU VRAM, 500GB SSD
- **Recommended**: 8 cores, 32GB RAM, 24GB GPU VRAM, 1TB NVMe SSD
- **OS**: Ubuntu 22.04+ LTS

## 🔧 Environment

- Copy `env.example` to `.env` (or set env vars in your platform) and adjust:
  - `NEXT_PUBLIC_API_URL`, `BACKEND_URL`, `COMFYUI_URL`, `NEXT_PUBLIC_COMFYUI_URL`
  - `ALLOWED_ORIGINS`, `COMFYUI_SERVER`, `DATABASE_URL`
  - `DEMO_MODE`, `ENABLE_*`, `DEMO_MAX_*`, `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_PER_HOUR`, `MAX_REQUEST_SIZE_MB`, `MAX_CONCURRENT_JOBS`
- Backend respects `ALLOWED_ORIGINS` for CORS and `COMFYUI_SERVER` for pipeline connectivity.
- Local defaults (safe/demo mode) are prefilled in `backend/env.example` and `web/env.local.example`; copy them to `backend/.env` and `web/.env.local` to mirror the PowerShell session without retyping values. `NEXT_PUBLIC_*` stays browser-visible, non-prefixed vars stay server-only.

## 🧊 Low-Resource / Free-Tier Mode

- Frontend includes a **Low-resource mode** toggle on the Image Generator (768x768, 18 steps, fast sampler, batch 1).
- Backend serializes heavy jobs via `MAX_CONCURRENT_JOBS` (default 1) to avoid overloading free plans.
- Set `DEMO_MODE=true` for public demos; heavy actions return structured 503 responses and the UI shows CPU-tier limits.

## 📖 Documentation Structure

```
docs/
├── PRD.md                      # Product Requirements Document
├── 16-ENHANCED-FEATURES.md     # Enhanced features (NEW)
├── 00-README.md                # Documentation index
├── 01-PROJECT-OVERVIEW.md      # Project vision and goals
├── 02-TECHNICAL-ARCHITECTURE.md # Tech stack and architecture
├── 03-FEATURE-ROADMAP.md       # Development roadmap
├── 04-AI-MODELS-REALISM.md     # AI models and realism
├── 05-AUTOMATION-STRATEGY.md   # Automation strategies
├── 06-ANTI-DETECTION-STRATEGY.md # Anti-detection measures
├── 07-DEVELOPMENT-TIMELINE.md  # Detailed timeline
├── 08-UI-UX-DESIGN-SYSTEM.md   # Design system
├── 09-DATABASE-SCHEMA.md        # Database schema
├── 10-API-DESIGN.md            # API specification
├── 11-COMPETITIVE-ANALYSIS.md  # Market analysis
├── 12-LEGAL-COMPLIANCE.md      # Legal considerations
├── 13-CONTENT-STRATEGY.md      # Content strategies
├── 14-TESTING-STRATEGY.md      # Testing approach
└── 15-DEPLOYMENT-DEVOPS.md     # Deployment guide
```

## 🎯 Development Timeline

- **Total Duration**: 20 weeks (5 months)
- **Phase 1**: Foundation (Weeks 1-4)
- **Phase 2**: Content Generation (Weeks 5-8)
- **Phase 3**: Platform Integration (Weeks 9-12)
- **Phase 4**: Automation & Intelligence (Weeks 13-16)
- **Phase 5**: Polish & Scale (Weeks 17-20)

## ⚠️ Legal Disclaimer

This project is for educational and research purposes. Users are responsible for:
- Complying with all applicable laws and regulations
- Complying with platform Terms of Service
- Ensuring content compliance
- Obtaining necessary rights and permissions

**Review [`docs/12-LEGAL-COMPLIANCE.md`](./docs/12-LEGAL-COMPLIANCE.md) carefully and consult with a qualified attorney before production use.**

## 🤝 Contributing

Contributions welcome! This is an open-source project.

## 📄 License

[To be determined - likely AGPL-3.0 or MIT]

## 🔗 Quick Links

- **Setup Guide**: [`SETUP.md`](./SETUP.md)
- **Product Requirements**: [`docs/PRD.md`](./docs/PRD.md)
- **API Documentation**: http://localhost:8000/docs (when backend is running)

## 📝 Main Scripts

### ⚡ Master Setup (All-in-One)
- `.\MASTER-SETUP.ps1` or `.\MASTER-SETUP.bat` - **One script to do everything** (setup, install, test, start, open browser)

### 🔧 Individual Scripts
- `.\auto-complete-setup.ps1` - Complete automated setup
- `.\download-models-auto.ps1` - Download AI models
- `.\start-all.ps1` - Start all services
- `.\stop-all.ps1` - Stop all services
- `.\gen.ps1` - Generate images (see `.\gen.ps1 -Help`)
- `.\test-all.ps1` - Run all tests
- `.\health-check.ps1` - Check system health

---

**Status**: Active Development ✅

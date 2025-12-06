# Technical Architecture & Tech Stack

## 📋 Document Metadata

### Purpose
Defines HOW the system is built technically - architecture patterns, technology stack, component breakdown, and infrastructure requirements. Essential for understanding the technical foundation.

### Reading Order
**Read After:** [PRD.md](./PRD.md), [01-PROJECT-OVERVIEW.md](./01-PROJECT-OVERVIEW.md)  
**Read Before:** [09-DATABASE-SCHEMA.md](./09-DATABASE-SCHEMA.md), [10-API-DESIGN.md](./10-API-DESIGN.md), [04-AI-MODELS-REALISM.md](./04-AI-MODELS-REALISM.md)

### Related Documents
**Prerequisites:**
- [PRD.md](./PRD.md) - Product requirements
- [01-PROJECT-OVERVIEW.md](./01-PROJECT-OVERVIEW.md) - Project vision

**Dependencies (Use This Document For):**
- [09-DATABASE-SCHEMA.md](./09-DATABASE-SCHEMA.md) - Database design based on architecture
- [10-API-DESIGN.md](./10-API-DESIGN.md) - API design follows architecture
- [08-UI-UX-DESIGN-SYSTEM.md](./08-UI-UX-DESIGN-SYSTEM.md) - Frontend architecture
- [15-DEPLOYMENT-DEVOPS.md](./15-DEPLOYMENT-DEVOPS.md) - Deployment follows architecture

**Related:**
- [04-AI-MODELS-REALISM.md](./04-AI-MODELS-REALISM.md) - AI/ML stack details
- [05-AUTOMATION-STRATEGY.md](./05-AUTOMATION-STRATEGY.md) - Service implementation details

---

## Architecture Overview

### System Architecture Pattern
**Microservices Architecture** with modular components:
- Character Management Service
- Content Generation Service
- Platform Integration Service
- Scheduling & Automation Service
- Anti-Detection Service
- UI Dashboard Service

---

## Technology Stack Selection

### Backend Framework
**Python 3.11+ with FastAPI**
- **Why:** Best AI/ML ecosystem, async support, fast development
- **Alternatives Considered:** Node.js (less AI-friendly), Go (limited ML libraries)
- **Key Libraries:**
  - FastAPI (web framework)
  - SQLAlchemy (ORM)
  - Celery (task queue)
  - Redis (caching & message broker)

### AI/ML Stack

#### Image Generation
**Stable Diffusion XL (SDXL) / SD 1.5**
- **Model:** RunwayML Stable Diffusion XL, Realistic Vision, or DreamShaper
- **Framework:** Automatic1111 WebUI API or ComfyUI
- **Hardware:** Local NVIDIA GPU (CUDA)
- **Why:** Best quality, free, open-source, local processing

#### Video Generation
**AnimateDiff / Stable Video Diffusion**
- **Framework:** ComfyUI or custom pipeline
- **Why:** Free, open-source, good quality for shorts/reels

#### Text Generation (LLM)
**Llama 3 / Mistral 7B / Phi-3**
- **Framework:** Ollama (local LLM server)
- **Why:** Free, runs locally, no API costs, privacy
- **Use Cases:** Captions, comments, tweets, personality simulation

#### Voice Generation
**Coqui TTS / XTTS-v2**
- **Why:** Free, open-source, high-quality voice cloning
- **Alternative:** Bark (more natural but slower)

#### Face Consistency
**IP-Adapter / FaceID / InstantID**
- **Why:** Maintains character consistency across images
- **Framework:** ComfyUI nodes or custom implementation

### Database
**PostgreSQL 15+**
- **Why:** Reliable, free, handles complex relationships
- **Schema:** Character profiles, content library, scheduling, analytics

**Redis**
- **Why:** Caching, session management, task queue backend

### Frontend Framework
**Next.js 14+ (App Router) with TypeScript**
- **Why:** Modern, React-based, great DX, server components
- **UI Library:** shadcn/ui + Tailwind CSS
- **State Management:** Zustand or React Query
- **Why Not:** Vue (less ecosystem), Svelte (smaller community)

### Task Queue & Automation
**Celery + Redis**
- **Why:** Best Python task queue, handles scheduling, retries
- **Use Cases:** Content generation, posting, interactions

### Social Media Integration

#### Instagram
- **Library:** `instagrapi` (Python, unofficial API)
- **Alternative:** Browser automation (Playwright) if API fails

#### Twitter/X
- **Library:** `tweepy` (official API) or `twitter-api-v2` (unofficial)
- **Alternative:** Browser automation (Playwright)

#### Facebook
- **Library:** `facebook-sdk` (official Graph API)
- **Alternative:** Browser automation

#### Telegram
- **Library:** `python-telegram-bot` (official Bot API)
- **Why:** Official API, reliable, free

#### OnlyFans
- **Method:** Browser automation (Playwright)
- **Why:** No official API, requires browser simulation

#### YouTube
- **Library:** `google-api-python-client` (official API)
- **Alternative:** Browser automation for uploads

### Browser Automation
**Playwright**
- **Why:** Better than Selenium, faster, more reliable
- **Use Cases:** Platforms without APIs, complex interactions

### Anti-Detection
**undetected-chromedriver / Playwright Stealth**
- **Why:** Avoid bot detection
- **Additional:** Proxy rotation, fingerprint randomization

### Content Management
**MinIO or Local Storage**
- **Why:** Free S3-compatible storage for images/videos
- **Alternative:** Local filesystem with organized structure

### Monitoring & Logging
**Prometheus + Grafana** (optional, for production)
**Python Logging** (built-in, sufficient for MVP)

---

## System Components

### 1. Character Management Service
```
Responsibilities:
- Character profile creation and storage
- Personality traits and behavior patterns
- Content preferences and style guides
- Character consistency rules
```

### 2. Content Generation Service
```
Responsibilities:
- Image generation (Stable Diffusion)
- Video generation (AnimateDiff)
- Text generation (LLM)
- Voice generation (TTS)
- Content validation and quality checks
```

### 3. Platform Integration Service
```
Responsibilities:
- API clients for each platform
- Browser automation for platforms without APIs
- Authentication and session management
- Rate limiting and error handling
```

### 4. Scheduling & Automation Service
```
Responsibilities:
- Content scheduling
- Post timing optimization
- Interaction automation (likes, comments)
- Cross-platform content distribution
```

### 5. Anti-Detection Service
```
Responsibilities:
- Human-like timing patterns
- Behavior randomization
- Fingerprint management
- Proxy rotation
- Detection avoidance
```

### 6. UI Dashboard Service
```
Responsibilities:
- Character management interface
- Content preview and approval
- Analytics and reporting
- System monitoring
```

---

## Data Flow Architecture

```
User Action (UI)
    ↓
API Request (FastAPI)
    ↓
Task Queue (Celery)
    ↓
Content Generation Service
    ├── Image Generation (Stable Diffusion)
    ├── Text Generation (LLM)
    └── Video Generation (AnimateDiff)
    ↓
Content Storage (MinIO/Local)
    ↓
Platform Integration Service
    ├── Instagram
    ├── Twitter
    ├── Facebook
    ├── Telegram
    ├── OnlyFans
    └── YouTube
    ↓
Posting/Automation
    ↓
Analytics & Logging
```

---

## Infrastructure Requirements

### Hardware
- **GPU:** NVIDIA GPU (8GB+ VRAM minimum, 16GB+ recommended)
- **RAM:** 32GB+ recommended
- **Storage:** 1TB+ SSD (for models and content)
- **CPU:** 8+ cores recommended

### Software
- **OS:** Linux (Ubuntu 22.04+) or macOS (for development)
- **Docker:** For containerization (optional but recommended)
- **CUDA:** For GPU acceleration
- **Python:** 3.11+
- **Node.js:** 20+ (for Next.js frontend)

---

## Security Considerations

1. **API Keys:** Environment variables, never commit
2. **Credentials:** Encrypted storage for social media accounts
3. **Content:** Secure storage, access controls
4. **Network:** VPN/proxy support for stealth
5. **Rate Limiting:** Respect platform limits to avoid bans

---

## Scalability Plan

### Phase 1: Single Server
- All services on one machine
- Local GPU for generation
- Single database instance

### Phase 2: Distributed
- Separate GPU server for generation
- Multiple worker nodes for automation
- Load balancer for API

### Phase 3: Cloud-Ready
- Kubernetes deployment
- Distributed GPU cluster
- Auto-scaling workers

---

## Development Environment Setup

See `SETUP.md` for detailed installation instructions.

---

## Next Steps

1. Set up development environment
2. Install and configure Stable Diffusion
3. Set up database schema
4. Create basic API structure
5. Implement first character generation

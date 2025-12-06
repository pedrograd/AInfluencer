# Technical Architecture & Tech Stack

**Version:** 2.0  
**Date:** January 2025  
**Last Updated:** January 2025  
**Status:** Production Ready  
**Document Owner:** CPO/CTO/CEO  
**Review Status:** ✅ Approved

---

## 📋 Document Metadata

### Purpose
Defines HOW the system is built technically - architecture patterns, technology stack, component breakdown, infrastructure requirements, and system design. Essential for understanding the technical foundation and making implementation decisions.

### Reading Order
**Read After:** [01-PRD.md](./01-PRD.md), [02-PROJECT-OVERVIEW.md](./02-PROJECT-OVERVIEW.md)  
**Read Before:** [04-DATABASE-SCHEMA.md](./04-DATABASE-SCHEMA.md), [05-API-DESIGN.md](./05-API-DESIGN.md), [07-AI-MODELS-REALISM.md](./07-AI-MODELS-REALISM.md)

### Related Documents
**Prerequisites:**
- [01-PRD.md](./01-PRD.md) - Product requirements inform architecture
- [02-PROJECT-OVERVIEW.md](./02-PROJECT-OVERVIEW.md) - Project vision and constraints

**Dependencies (Use This Document For):**
- [04-DATABASE-SCHEMA.md](./04-DATABASE-SCHEMA.md) - Database design based on architecture
- [05-API-DESIGN.md](./05-API-DESIGN.md) - API design follows architecture
- [06-UI-UX-DESIGN-SYSTEM.md](./06-UI-UX-DESIGN-SYSTEM.md) - Frontend architecture
- [20-DEPLOYMENT-DEVOPS.md](./20-DEPLOYMENT-DEVOPS.md) - Deployment follows architecture
- [08-DEVELOPMENT-ENVIRONMENT.md](./08-DEVELOPMENT-ENVIRONMENT.md) - Dev environment setup

**Related:**
- [07-AI-MODELS-REALISM.md](./07-AI-MODELS-REALISM.md) - AI/ML stack details
- [18-AUTOMATION-STRATEGY.md](./18-AUTOMATION-STRATEGY.md) - Service implementation details
- [22-MONITORING-ALERTING.md](./22-MONITORING-ALERTING.md) - Monitoring architecture
- [23-SCALING-OPTIMIZATION.md](./23-SCALING-OPTIMIZATION.md) - Scaling strategies
- [24-SECURITY-HARDENING.md](./24-SECURITY-HARDENING.md) - Security architecture

### Key Sections
1. System Architecture Overview
2. Technology Stack Selection with Comparisons
3. Detailed Component Architecture
4. Data Flow Diagrams
5. Infrastructure Architecture
6. Security Architecture
7. Monitoring Architecture
8. Scalability Architecture
9. Disaster Recovery Architecture
10. Development Environment

---

## 1. System Architecture Overview

### 1.1 Architecture Pattern

**Microservices Architecture** with modular, loosely coupled components:

```
┌─────────────────────────────────────────────────────────────┐
│                    AInfluencer Platform                      │
│                  Microservices Architecture                  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│  Frontend      │   │   API Gateway   │   │  WebSocket     │
│  (Next.js)     │   │   (FastAPI)     │   │  Server        │
└───────┬────────┘   └────────┬────────┘   └────────┬────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│ Character      │   │ Content         │   │ Platform        │
│ Management     │   │ Generation      │   │ Integration     │
│ Service        │   │ Service         │   │ Service         │
└───────┬────────┘   └────────┬────────┘   └────────┬────────┘
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│ Scheduling &   │   │ Anti-Detection  │   │ Analytics      │
│ Automation     │   │ Service         │   │ Service         │
│ Service        │   │                 │   │                 │
└────────────────┘   └─────────────────┘   └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│ PostgreSQL     │   │ Redis            │   │ Local Storage   │
│ (Database)     │   │ (Cache/Queue)    │   │ (Content)       │
└────────────────┘   └──────────────────┘   └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│ Stable         │   │ Ollama          │   │ Coqui TTS      │
│ Diffusion      │   │ (LLM)           │   │ (Voice)        │
│ (Images/Videos)│   │                 │   │                │
└────────────────┘   └──────────────────┘   └─────────────────┘
```

### 1.2 Architecture Principles

1. **Modularity**: Each service is independent and can be developed/deployed separately
2. **Scalability**: Services can scale independently based on load
3. **Resilience**: Failure in one service doesn't bring down entire system
4. **Maintainability**: Clear separation of concerns, easy to understand and modify
5. **Extensibility**: Easy to add new platforms, features, or services

---

## 2. Technology Stack Selection

### 2.1 Backend Framework Comparison

| Framework | Pros | Cons | Decision |
|-----------|------|------|----------|
| **FastAPI** ✅ | • Best AI/ML ecosystem<br>• Async support<br>• Fast development<br>• Auto OpenAPI docs<br>• Type safety | • Newer (less mature)<br>• Smaller community | **SELECTED** - Best fit for AI/ML |
| Flask | • Mature<br>• Large community<br>• Simple | • No async (without extensions)<br>• Less AI/ML focused<br>• Manual API docs | Not selected - lacks async |
| Django | • Very mature<br>• Large ecosystem<br>• Admin panel | • Heavier<br>• Less async support<br>• Overkill for API-only | Not selected - too heavy |
| Node.js | • Fast<br>• Large ecosystem | • Less AI/ML libraries<br>• Python better for AI | Not selected - Python better for AI |
| Go | • Very fast<br>• Great concurrency | • Limited ML libraries<br>• Less AI ecosystem | Not selected - limited AI support |

**Decision Rationale:**
- **FastAPI** selected because:
  1. Best Python AI/ML ecosystem integration
  2. Native async support (critical for concurrent operations)
  3. Automatic OpenAPI documentation
  4. Type safety with Pydantic
  5. High performance
  6. Modern and actively developed

### 2.2 Frontend Framework Comparison

| Framework | Pros | Cons | Decision |
|-----------|------|------|----------|
| **Next.js 14+** ✅ | • Modern React<br>• Server components<br>• Great DX<br>• Large ecosystem<br>• TypeScript support | • Learning curve<br>• React complexity | **SELECTED** - Best modern option |
| Vue 3 | • Simpler than React<br>• Good performance | • Smaller ecosystem<br>• Less server components | Not selected - smaller ecosystem |
| Svelte | • Very fast<br>• Simple syntax | • Smaller community<br>• Less server components | Not selected - smaller community |
| Remix | • Great DX<br>• Server components | • Smaller ecosystem<br>• Less mature | Not selected - less mature |
| Plain React | • Full control | • No server components<br>• More setup | Not selected - Next.js better |

**Decision Rationale:**
- **Next.js 14+** selected because:
  1. Server components for better performance
  2. Large ecosystem and community
  3. Excellent TypeScript support
  4. Great developer experience
  5. Built-in optimizations
  6. shadcn/ui compatibility

### 2.3 Database Comparison

| Database | Pros | Cons | Decision |
|----------|------|------|----------|
| **PostgreSQL 15+** ✅ | • Reliable<br>• Free<br>• Complex relationships<br>• Excellent JSON support<br>• ACID compliance | • Requires more setup<br>• More resource usage | **SELECTED** - Best for relational data |
| MySQL | • Very mature<br>• Large community | • Less JSON support<br>• Less advanced features | Not selected - less features |
| MongoDB | • Flexible schema<br>• Good for JSON | • Less relational<br>• Consistency concerns | Not selected - need relational |
| SQLite | • Simple<br>• No server needed | • Not for production<br>• Limited concurrency | Not selected - not for production |

**Decision Rationale:**
- **PostgreSQL** selected because:
  1. Excellent JSON support (for flexible schemas)
  2. Complex relationship handling
  3. ACID compliance (data integrity)
  4. Free and open-source
  5. Production-ready
  6. Great performance

### 2.4 AI Model Stack Comparison

#### Image Generation Models

| Model | Quality | Speed | VRAM | Cost | Decision |
|-------|---------|-------|------|------|----------|
| **Stable Diffusion XL** ✅ | 9/10 | Medium | 8GB+ | Free | **SELECTED** - Best balance |
| Stable Diffusion 1.5 | 8/10 | Fast | 6GB+ | Free | Alternative - faster |
| DALL-E 3 | 10/10 | Fast | N/A | Paid | Optional - paid integration |
| Midjourney | 10/10 | Fast | N/A | Paid | Optional - if API available |

**Decision Rationale:**
- **Stable Diffusion XL** selected because:
  1. Best free option for quality
  2. Runs locally (privacy)
  3. Open-source and customizable
  4. Good balance of quality and speed
  5. Active community and improvements

#### LLM Models

| Model | Quality | Speed | VRAM | Size | Decision |
|-------|---------|-------|------|------|----------|
| **Llama 3 8B** ✅ | 9/10 | Fast | 8GB+ | 4.7GB | **SELECTED** - Best balance |
| Llama 3 70B | 10/10 | Slow | 40GB+ | 40GB | Alternative - better quality |
| Mistral 7B | 8.5/10 | Very Fast | 6GB+ | 4.1GB | Alternative - faster |
| Phi-3 Mini | 8/10 | Very Fast | 4GB+ | 2.3GB | Alternative - lightweight |

**Decision Rationale:**
- **Llama 3 8B** selected because:
  1. Best quality-to-speed ratio
  2. Good for creative content
  3. Reasonable VRAM requirements
  4. Active development
  5. Good community support

### 2.5 Task Queue Comparison

| Solution | Pros | Cons | Decision |
|----------|------|------|----------|
| **Celery + Redis** ✅ | • Best Python task queue<br>• Scheduling support<br>• Retry logic<br>• Mature | • Requires Redis<br>• More setup | **SELECTED** - Best for Python |
| RQ (Redis Queue) | • Simpler<br>• Lightweight | • Less features<br>• No advanced scheduling | Not selected - less features |
| Dramatiq | • Modern<br>• Simple | • Smaller community<br>• Less features | Not selected - less mature |
| Bull (Node.js) | • Great features | • Node.js only | Not selected - Python needed |

**Decision Rationale:**
- **Celery + Redis** selected because:
  1. Industry standard for Python
  2. Advanced scheduling (cron, periodic tasks)
  3. Retry logic and error handling
  4. Mature and well-documented
  5. Great for long-running tasks

---

## 3. Detailed System Architecture

### 3.1 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web UI     │  │  Mobile Web  │  │   API Docs   │          │
│  │  (Next.js)   │  │  (Responsive)│  │  (Swagger)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      API Gateway Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FastAPI Application                         │   │
│  │  • Authentication & Authorization                        │   │
│  │  • Rate Limiting                                         │   │
│  │  • Request Validation                                    │   │
│  │  • Error Handling                                        │   │
│  │  • WebSocket Support                                     │   │
│  └───────────────────────┬──────────────────────────────────┘   │
└──────────────────────────┼──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐ ┌───────▼────────┐ ┌───────▼────────┐
│   REST API     │ │  WebSocket     │ │  Task Queue     │
│   Endpoints    │ │  Real-Time     │ │  (Celery)       │
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Business Logic Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Character   │  │   Content     │  │  Platform    │          │
│  │  Management  │  │  Generation  │  │  Integration │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐          │
│  │  Automation  │  │ Anti-Detection│  │  Analytics   │          │
│  │  & Scheduling│  │  Service      │  │  Service     │          │
│  └──────────────┘  └───────────────┘  └──────────────┘          │
└───────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                      Data & Storage Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │    Redis      │  │ Local Storage │          │
│  │  (Metadata)  │  │ (Cache/Queue)│  │  (Content)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────┬──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                    External Services Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Stable     │  │    Ollama    │  │  Coqui TTS    │          │
│  │  Diffusion   │  │    (LLM)     │  │   (Voice)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Instagram   │  │   Twitter    │  │   Facebook   │          │
│  │     API      │  │     API      │  │     API      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Telegram    │  │  OnlyFans    │  │   YouTube    │          │
│  │     API      │  │  (Browser)   │  │     API      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Architecture Details

#### Component 1: Character Management Service

```
┌─────────────────────────────────────────────────────────┐
│           Character Management Service                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Character CRUD Operations                       │  │
│  │  • Create, Read, Update, Delete                 │  │
│  │  • Character validation                         │  │
│  │  • Character search and filtering               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Persona Management                              │  │
│  │  • Persona creation and editing                  │  │
│  │  • Persona templates                             │  │
│  │  • Persona export                                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Appearance Management                           │  │
│  │  • Face reference processing                     │  │
│  │  • Appearance attributes                         │  │
│  │  • Style preferences                             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Character Statistics                            │  │
│  │  • Posts count                                   │  │
│  │  • Followers count                               │  │
│  │  • Engagement metrics                           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    PostgreSQL          Redis Cache        Local Storage
```

**Responsibilities:**
- Character profile creation and storage
- Personality traits and behavior patterns
- Content preferences and style guides
- Character consistency rules
- Character lifecycle management

**Key Operations:**
- `create_character()` - Create new character
- `update_character()` - Update character attributes
- `get_character()` - Retrieve character data
- `list_characters()` - List all characters with filters
- `delete_character()` - Soft delete character

---

#### Component 2: Content Generation Service

```
┌─────────────────────────────────────────────────────────┐
│           Content Generation Service                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Image Generation                                │  │
│  │  • Stable Diffusion integration                  │  │
│  │  • Face consistency (IP-Adapter, InstantID)      │  │
│  │  • Batch generation                              │  │
│  │  • Quality control                               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Video Generation                                │  │
│  │  • AnimateDiff / Stable Video Diffusion          │  │
│  │  • Face consistency in videos                    │  │
│  │  • Post-processing                               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Text Generation                                 │  │
│  │  • LLM integration (Ollama)                      │  │
│  │  • Persona-based prompts                         │  │
│  │  • Hashtag generation                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Voice Generation                                │  │
│  │  • TTS integration (Coqui TTS)                   │  │
│  │  • Voice cloning                                 │  │
│  │  • Emotion control                               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Content Validation                              │  │
│  │  • Quality scoring                               │  │
│  │  • Face detection                                │  │
│  │  • Artifact detection                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    Stable Diffusion      Ollama LLM         Coqui TTS
```

**Responsibilities:**
- Image generation (Stable Diffusion)
- Video generation (AnimateDiff)
- Text generation (LLM)
- Voice generation (TTS)
- Content validation and quality checks
- Content storage and organization

**Key Operations:**
- `generate_image()` - Generate image with character consistency
- `generate_video()` - Generate video with character consistency
- `generate_text()` - Generate text with persona
- `generate_voice()` - Generate voice with character voice
- `validate_content()` - Quality check and validation

---

#### Component 3: Platform Integration Service

```
┌─────────────────────────────────────────────────────────┐
│         Platform Integration Service                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Platform Adapters                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │  │Instagram│ │ Twitter  │ │ Facebook │         │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘         │  │
│  │  ┌────▼────┐ ┌────▼────┐ ┌────▼────┐         │  │
│  │  │Telegram │ │OnlyFans │ │ YouTube │         │  │
│  │  └─────────┘ └─────────┘ └─────────┘         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Authentication Manager                          │  │
│  │  • OAuth handling                                │  │
│  │  • Session management                            │  │
│  │  • Credential encryption                         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Rate Limit Manager                              │  │
│  │  • Rate limit tracking                           │  │
│  │  • Queue management                              │  │
│  │  • Throttling                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Browser Automation                               │  │
│  │  • Playwright integration                        │  │
│  │  • Stealth plugins                               │  │
│  │  • Proxy support                                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Responsibilities:**
- API clients for each platform
- Browser automation for platforms without APIs
- Authentication and session management
- Rate limiting and error handling
- Platform-specific optimizations

**Key Operations:**
- `connect_platform()` - Connect platform account
- `publish_post()` - Publish content to platform
- `like_post()` - Like a post
- `comment_post()` - Comment on a post
- `sync_engagement()` - Sync engagement metrics

---

#### Component 4: Scheduling & Automation Service

```
┌─────────────────────────────────────────────────────────┐
│      Scheduling & Automation Service                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Automation Rule Engine                          │  │
│  │  • Rule creation and management                  │  │
│  │  • Trigger evaluation                            │  │
│  │  • Action execution                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Scheduler                                       │  │
│  │  • Cron-based scheduling                        │  │
│  │  • Event-based triggers                         │  │
│  │  • Timezone handling                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Content Distribution                            │  │
│  │  • Cross-platform posting                        │  │
│  │  • Platform-specific adaptation                  │  │
│  │  • Optimal timing calculation                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Engagement Automation                          │  │
│  │  • Automated likes                              │  │
│  │  • Automated comments                           │  │
│  │  • Automated follows                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ▼
    Celery Workers
```

**Responsibilities:**
- Content scheduling
- Post timing optimization
- Interaction automation (likes, comments)
- Cross-platform content distribution
- Automation rule execution

**Key Operations:**
- `create_automation_rule()` - Create automation rule
- `schedule_post()` - Schedule post for future
- `execute_automation_rule()` - Execute automation rule
- `optimize_posting_time()` - Calculate optimal posting time

---

#### Component 5: Anti-Detection Service

```
┌─────────────────────────────────────────────────────────┐
│          Anti-Detection Service                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Behavioral Humanization                         │  │
│  │  • Human-like delays                             │  │
│  │  • Activity patterns                             │  │
│  │  • Sleep patterns                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Content Humanization                            │  │
│  │  • Content variation                             │  │
│  │  • Metadata removal                              │  │
│  │  • Natural imperfections                         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Technical Stealth                               │  │
│  │  • Browser fingerprinting                        │  │
│  │  • User agent rotation                           │  │
│  │  • Proxy rotation                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Detection Testing                               │  │
│  │  • AI detection testing                          │  │
│  │  • Reverse image search                          │  │
│  │  • Platform monitoring                           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Responsibilities:**
- Human-like timing patterns
- Behavior randomization
- Fingerprint management
- Proxy rotation
- Detection avoidance
- Detection testing

**Key Operations:**
- `get_human_delay()` - Calculate human-like delay
- `randomize_behavior()` - Randomize behavior patterns
- `rotate_fingerprint()` - Rotate browser fingerprint
- `test_detection()` - Test against detection tools

---

#### Component 6: UI Dashboard Service

```
┌─────────────────────────────────────────────────────────┐
│            UI Dashboard Service                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Next.js Application                             │  │
│  │  • Server Components                              │  │
│  │  • Client Components                              │  │
│  │  • API Integration                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Real-Time Updates                               │  │
│  │  • WebSocket client                              │  │
│  │  • Live activity feed                            │  │
│  │  • Real-time notifications                      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  State Management                                │  │
│  │  • React Query (server state)                    │  │
│  │  • Zustand (client state)                        │  │
│  │  • Local storage                                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ▼
    FastAPI Backend
```

**Responsibilities:**
- Character management interface
- Content preview and approval
- Analytics and reporting
- System monitoring
- Real-time updates

**Key Features:**
- Responsive design (mobile, tablet, desktop)
- Real-time activity feed
- Interactive charts and graphs
- Drag-and-drop scheduling
- Content preview and editing

---

## 4. Data Flow Architecture

### 4.1 Content Generation Flow

```
User Request (Create Character & Generate Content)
    │
    ▼
FastAPI Endpoint (/api/v1/characters/{id}/generate)
    │
    ▼
Character Management Service
    │
    ├──> Retrieve Character Data
    │       │
    │       ▼
    │   PostgreSQL (Character, Persona, Appearance)
    │
    └──> Create Generation Task
            │
            ▼
        Celery Task Queue (Redis)
            │
            ▼
        Content Generation Worker
            │
            ├──> Image Generation
            │       │
            │       ▼
            │   Stable Diffusion API
            │       │
            │       ▼
            │   Generated Image
            │       │
            │       ▼
            │   Quality Validation
            │       │
            │       ▼
            │   Face Consistency Check
            │       │
            │       ▼
            │   Post-Processing
            │       │
            │       ▼
            │   Local Storage
            │
            ├──> Text Generation
            │       │
            │       ▼
            │   Ollama LLM API
            │       │
            │       ▼
            │   Generated Text (with Persona)
            │       │
            │       ▼
            │   PostgreSQL (Content Metadata)
            │
            └──> Update Generation Status
                    │
                    ▼
                WebSocket Notification
                    │
                    ▼
                UI Update (Real-Time)
```

### 4.2 Platform Posting Flow

```
Scheduled Post (Automation Rule or Manual)
    │
    ▼
Scheduling Service
    │
    ├──> Check Schedule Time
    │       │
    │       ▼
    │   Execute at Scheduled Time
    │
    └──> Create Posting Task
            │
            ▼
        Celery Task Queue
            │
            ▼
        Platform Integration Worker
            │
            ├──> Retrieve Content
            │       │
            │       ▼
            │   Local Storage (Image/Video)
            │   PostgreSQL (Metadata, Caption)
            │
            ├──> Platform-Specific Adaptation
            │       │
            │       ├──> Resize Image (platform requirements)
            │       ├──> Adapt Caption (length, hashtags)
            │       └──> Format Content (platform format)
            │
            ├──> Anti-Detection Measures
            │       │
            │       ├──> Human-like Delay
            │       ├──> Fingerprint Rotation
            │       └──> Proxy Rotation (if configured)
            │
            ├──> Platform API Call
            │       │
            │       ├──> Primary: Official API (if available)
            │       └──> Fallback: Browser Automation
            │
            ├──> Handle Response
            │       │
            │       ├──> Success: Store Post ID, Update Status
            │       └──> Failure: Retry Logic, Error Logging
            │
            └──> Update Analytics
                    │
                    ▼
                PostgreSQL (Posts, Analytics)
                    │
                    ▼
                WebSocket Notification
                    │
                    ▼
                UI Update (Real-Time)
```

### 4.3 Engagement Automation Flow

```
Automation Rule (Engagement)
    │
    ▼
Automation Service
    │
    ├──> Evaluate Trigger
    │       │
    │       ├──> Schedule-based (cron)
    │       ├──> Event-based (new post detected)
    │       └──> Manual trigger
    │
    └──> Create Engagement Tasks
            │
            ├──> Like Task
            │       │
            │       ▼
            │   Anti-Detection Service
            │       │
            │       ├──> Calculate Human Delay
            │       ├──> Rotate Fingerprint
            │       └──> Select Target (hashtags, accounts)
            │
            ├──> Comment Task
            │       │
            │       ▼
            │   Text Generation Service
            │       │
            │       ├──> Generate Comment (Persona-based)
            │       └──> Ensure Uniqueness
            │
            └──> Execute Engagement
                    │
                    ▼
                Platform Integration Service
                    │
                    ├──> Like Post
                    ├──> Comment on Post
                    └──> Follow User
                            │
                            ▼
                        Update Analytics
                            │
                            ▼
                        WebSocket Notification
```

---

## 5. Infrastructure Architecture

### 5.1 Single Server Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────────┐
│              Ubuntu Server (Self-Hosted)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Application Layer                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │  Next.js     │  │  FastAPI     │                  │  │
│  │  │  Frontend    │  │  Backend     │                  │  │
│  │  │  Port: 3000  │  │  Port: 8000  │                  │  │
│  │  └──────────────┘  └──────┬───────┘                  │  │
│  └───────────────────────────┼──────────────────────────┘  │
│                                │                             │
│  ┌─────────────────────────────▼──────────────────────────┐  │
│  │  Task Queue Layer                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │  Celery      │  │  Redis       │                  │  │
│  │  │  Workers     │  │  Broker      │                  │  │
│  │  │  (4 workers) │  │  Port: 6379  │                  │  │
│  │  └──────────────┘  └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data Layer                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │ PostgreSQL   │  │ Local        │                  │  │
│  │  │ Port: 5432   │  │ Storage      │                  │  │
│  │  └──────────────┘  └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI Services Layer                                   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │  Stable      │  │  Ollama      │  │  Coqui   │  │  │
│  │  │  Diffusion   │  │  Port: 11434│  │  TTS     │  │  │
│  │  │  Port: 7860  │  │              │  │          │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Hardware Layer                                      │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  NVIDIA GPU (Shared by all AI services)      │   │  │
│  │  │  • Stable Diffusion                          │   │  │
│  │  │  • Video Generation                          │   │  │
│  │  │  • Face Consistency                          │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Network Layer                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │  Nginx       │  │  Firewall    │                  │  │
│  │  │  Reverse     │  │  (UFW)       │                  │  │
│  │  │  Proxy       │  │              │                  │  │
│  │  │  Port: 80/443│  │              │                  │  │
│  │  └──────────────┘  └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Distributed Architecture (Phase 2 - Future)

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
│                    (Nginx/HAProxy)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│  API Server  │ │  API Server  │ │  API Server  │
│   (FastAPI)  │ │   (FastAPI)  │ │   (FastAPI)  │
└───────┬──────┘ └──────┬──────┘ └──────┬──────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│   Celery     │ │   Celery     │ │   Celery     │
│   Workers    │ │   Workers    │ │   Workers    │
│  (Automation)│ │ (Generation)  │ │ (Platform)   │
└───────┬──────┘ └──────┬──────┘ └──────┬──────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│              GPU Server Cluster                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  GPU 1   │  │  GPU 2   │  │  GPU 3   │      │
│  │ Stable   │  │ Stable   │  │ Stable   │      │
│  │ Diffusion│  │ Diffusion│  │ Diffusion│      │
│  └──────────┘  └──────────┘  └──────────┘      │
└───────────────────────────────────────────────────┘
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│ PostgreSQL   │ │    Redis     │ │   Storage   │
│  (Primary)   │ │   (Cluster)  │ │   (S3/NFS)  │
│              │ │              │ │             │
│  ┌────────┐  │ │              │ │             │
│  │Replica │  │ │              │ │             │
│  └────────┘  │ │              │ │             │
└──────────────┘ └──────────────┘ └─────────────┘
```

---

## 6. Security Architecture

### 6.1 Security Layers

```
┌─────────────────────────────────────────────────────────┐
│              Security Architecture                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 1: Network Security                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  • Firewall (UFW)                                │  │
│  │  • HTTPS (Let's Encrypt)                        │  │
│  │  • Rate Limiting                                │  │
│  │  • DDoS Protection                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Layer 2: Application Security                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  • Authentication (JWT)                          │  │
│  │  • Authorization (RBAC)                        │  │
│  │  • Input Validation                             │  │
│  │  • SQL Injection Prevention                     │  │
│  │  • XSS Prevention                               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Layer 3: Data Security                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │  • Encryption at Rest (AES-256)                  │  │
│  │  • Encryption in Transit (TLS)                  │  │
│  │  • Secure Credential Storage                    │  │
│  │  • API Key Encryption                           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Layer 4: Infrastructure Security                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  • SSH Hardening                                 │  │
│  │  • System Updates                               │  │
│  │  • Access Controls                              │  │
│  │  • Audit Logging                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Authentication & Authorization Flow

```
User Login Request
    │
    ▼
FastAPI Authentication Endpoint
    │
    ├──> Validate Credentials
    │       │
    │       ▼
    │   PostgreSQL (User Table)
    │       │
    │       ├──> Verify Password (bcrypt)
    │       └──> Check User Status
    │
    ├──> Generate JWT Token
    │       │
    │       ├──> Access Token (short-lived)
    │       └──> Refresh Token (long-lived)
    │
    └──> Return Tokens
            │
            ▼
        Client Stores Tokens
            │
            ▼
        Subsequent Requests Include JWT
            │
            ▼
        FastAPI Validates JWT
            │
            ├──> Verify Signature
            ├──> Check Expiration
            └──> Authorize Request (RBAC)
                    │
                    ▼
                Allow/Deny Request
```

### 6.3 Data Encryption

#### Encryption at Rest
- **Sensitive Data**: API keys, passwords, credentials
- **Method**: AES-256 encryption
- **Storage**: Encrypted fields in PostgreSQL
- **Key Management**: Environment variables, secure key storage

#### Encryption in Transit
- **HTTPS**: TLS 1.3 for all API communication
- **Database**: SSL/TLS for PostgreSQL connections
- **Internal**: Encrypted communication between services

#### Credential Storage
- **Social Media Credentials**: Encrypted in `platform_accounts.auth_data`
- **API Keys**: Encrypted in user settings
- **Passwords**: Hashed with bcrypt (never stored plain text)

---

## 7. Monitoring Architecture

### 7.1 Monitoring Stack

```
┌─────────────────────────────────────────────────────────┐
│              Monitoring Architecture                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Application Monitoring                          │  │
│  │  • FastAPI metrics (request rate, latency)      │  │
│  │  • Celery metrics (task queue, worker status)   │  │
│  │  • Database metrics (query performance)         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  System Monitoring                               │  │
│  │  • CPU, RAM, Disk usage                         │  │
│  │  • GPU utilization                              │  │
│  │  • Network traffic                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Business Metrics                                │  │
│  │  • Character count                              │  │
│  │  • Content generation rate                      │  │
│  │  • Platform success rate                        │  │
│  │  • Engagement metrics                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Alerting                                        │  │
│  │  • Error rate alerts                            │  │
│  │  • Performance degradation                      │  │
│  │  • System health alerts                         │  │
│  │  • Platform integration failures                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ▼
    Prometheus (Metrics Collection)
         │
         ▼
    Grafana (Visualization & Dashboards)
```

### 7.2 Key Metrics to Monitor

#### Application Metrics
- API request rate (requests/second)
- API response time (P50, P95, P99)
- Error rate (errors/requests)
- Task queue length
- Worker utilization
- Database query performance

#### System Metrics
- CPU usage
- Memory usage
- Disk usage
- GPU utilization
- Network traffic
- System load

#### Business Metrics
- Active characters
- Content generation rate
- Posts published per day
- Platform success rate
- Engagement rate
- Follower growth

### 7.3 Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| API Response Time (P95) | > 300ms | > 500ms | Investigate performance |
| Error Rate | > 1% | > 5% | Investigate errors |
| System Uptime | < 99.5% | < 99% | Check system health |
| GPU Utilization | > 90% | > 95% | Check GPU load |
| Disk Usage | > 80% | > 90% | Clean up or expand |
| Platform API Success | < 98% | < 95% | Check platform integration |

---

## 8. Scalability Architecture

### 8.1 Horizontal Scaling Strategy

#### Phase 1: Single Server (Current)
- All services on one machine
- Local GPU for generation
- Single database instance
- **Capacity**: 5-10 characters

#### Phase 2: Distributed Services
- Separate GPU server for generation
- Multiple API servers (load balanced)
- Multiple Celery workers
- Database read replicas
- **Capacity**: 50-100 characters

#### Phase 3: Cloud-Ready
- Kubernetes deployment
- Distributed GPU cluster
- Auto-scaling workers
- Database sharding (if needed)
- **Capacity**: 1000+ characters

### 8.2 Scaling Components

#### API Servers
- **Scaling Method**: Horizontal (multiple instances)
- **Load Balancer**: Nginx/HAProxy
- **Session Management**: Stateless (JWT tokens)
- **Auto-Scaling**: Based on CPU/memory usage

#### Celery Workers
- **Scaling Method**: Horizontal (multiple workers)
- **Queue Management**: Redis
- **Worker Types**: 
  - Content generation workers (GPU-intensive)
  - Platform integration workers (I/O-intensive)
  - Automation workers (CPU-intensive)

#### Database
- **Scaling Method**: 
  - Vertical: More powerful server
  - Horizontal: Read replicas, sharding (future)
- **Connection Pooling**: SQLAlchemy pool
- **Query Optimization**: Indexing, query caching

#### AI Services
- **Scaling Method**: Multiple GPU servers
- **Load Distribution**: Round-robin or queue-based
- **GPU Utilization**: Optimize for maximum throughput

### 8.3 Performance Optimization

#### Database Optimization
- **Indexing**: All foreign keys, frequently queried columns
- **Query Optimization**: EXPLAIN ANALYZE, query caching
- **Connection Pooling**: SQLAlchemy connection pool
- **Partitioning**: Large tables (analytics, logs) by date

#### Caching Strategy
- **Redis Caching**: 
  - Character data (5 min TTL)
  - Content metadata (10 min TTL)
  - Platform account status (1 min TTL)
  - Analytics data (15 min TTL)

#### Content Storage Optimization
- **Compression**: Images and videos compressed
- **CDN**: Future - for content delivery
- **Storage Tiers**: Hot (recent) vs Cold (archived)

---

## 9. Disaster Recovery Architecture

### 9.1 Backup Strategy

```
┌─────────────────────────────────────────────────────────┐
│              Disaster Recovery Architecture              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Database Backups                                │  │
│  │  • Daily full backups (2 AM)                    │  │
│  │  • Hourly incremental (WAL archiving)           │  │
│  │  • Retention: 30 days daily, 7 days hourly     │  │
│  │  • Storage: Local + Remote (encrypted)          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Content Backups                                 │  │
│  │  • Daily content backups                        │  │
│  │  • Incremental backups (rsync)                 │  │
│  │  │  • Retention: 30 days                       │  │
│  │  │  • Storage: Local + Remote                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Configuration Backups                         │  │
│  │  • Version control (Git)                         │  │
│  │  • Environment variables backup                 │  │
│  │  • Service configuration backup                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 9.2 Recovery Procedures

#### Database Recovery
1. **Identify Failure**: Database corruption, data loss
2. **Stop Services**: Stop all services using database
3. **Restore Backup**: Restore from latest backup
4. **Verify Data**: Verify data integrity
5. **Restart Services**: Restart all services
6. **Monitor**: Monitor for issues

#### Content Recovery
1. **Identify Failure**: Content storage failure
2. **Restore from Backup**: Restore content files
3. **Verify Integrity**: Check file integrity
4. **Update Database**: Update content metadata if needed
5. **Resume Operations**: Resume content generation

#### Full System Recovery
1. **Infrastructure**: Restore server/VM
2. **Software**: Reinstall all software
3. **Database**: Restore database from backup
4. **Content**: Restore content from backup
5. **Configuration**: Restore configuration files
6. **Services**: Start all services
7. **Verification**: Verify all systems operational

### 9.3 High Availability (Future)

#### Database High Availability
- **Primary-Replica Setup**: PostgreSQL streaming replication
- **Automatic Failover**: Patroni or similar
- **Load Balancing**: Read queries to replicas

#### Application High Availability
- **Multiple API Servers**: Load balanced
- **Health Checks**: Automatic health monitoring
- **Failover**: Automatic failover on server failure

---

## 10. Development Environment

### 10.1 Local Development Setup

```
Development Machine
    │
    ├──> Python 3.11+ (Backend)
    │       ├──> FastAPI
    │       ├──> SQLAlchemy
    │       ├──> Celery
    │       └──> Platform libraries
    │
    ├──> Node.js 20+ (Frontend)
    │       ├──> Next.js 14+
    │       ├──> TypeScript
    │       ├──> shadcn/ui
    │       └──> Tailwind CSS
    │
    ├──> PostgreSQL 15+ (Local)
    │       └──> Development database
    │
    ├──> Redis 7+ (Local)
    │       └──> Cache and queue
    │
    └──> AI Models (Local)
            ├──> Stable Diffusion (if GPU available)
            ├──> Ollama (LLM)
            └──> Coqui TTS (optional)
```

### 10.2 Development Workflow

1. **Code Changes**: Edit code locally
2. **Testing**: Run tests locally
3. **Hot Reload**: FastAPI and Next.js hot reload
4. **Database Migrations**: Alembic migrations
5. **Git Workflow**: Feature branches, PRs

### 10.3 IDE Configuration

#### Recommended IDEs
- **VS Code**: Best for Python + TypeScript
- **PyCharm**: Excellent for Python
- **Cursor**: AI-assisted development

#### Recommended Extensions
- Python (Pylance, Black formatter)
- TypeScript/JavaScript
- PostgreSQL (database tools)
- Docker (if using containers)
- Git (version control)

---

## 11. Technology Stack Summary

### 11.1 Complete Stack Table

| Layer | Technology | Version | Purpose | License |
|-------|-----------|---------|---------|---------|
| **Backend** | Python | 3.11+ | Core language | Open Source |
| **Backend Framework** | FastAPI | Latest | Web framework | MIT |
| **ORM** | SQLAlchemy | 2.0+ | Database ORM | MIT |
| **Task Queue** | Celery | 5.3+ | Async tasks | BSD |
| **Cache/Queue** | Redis | 7+ | Caching, queue | BSD |
| **Database** | PostgreSQL | 15+ | Primary database | PostgreSQL |
| **Frontend** | Next.js | 14+ | React framework | MIT |
| **Frontend Language** | TypeScript | 5+ | Type safety | Apache 2.0 |
| **UI Library** | shadcn/ui | Latest | Component library | MIT |
| **Styling** | Tailwind CSS | 3+ | CSS framework | MIT |
| **Image Generation** | Stable Diffusion XL | Latest | AI image generation | CreativeML Open RAIL |
| **LLM** | Ollama (Llama 3) | Latest | Text generation | MIT |
| **TTS** | Coqui TTS | Latest | Voice generation | MPL 2.0 |
| **Browser Automation** | Playwright | Latest | Platform automation | Apache 2.0 |
| **Monitoring** | Prometheus | Latest | Metrics | Apache 2.0 |
| **Visualization** | Grafana | Latest | Dashboards | Apache 2.0 |

### 11.2 Dependency Management

#### Backend Dependencies
- **requirements.txt**: Python dependencies
- **Poetry** (optional): Advanced dependency management
- **Virtual Environment**: Python venv for isolation

#### Frontend Dependencies
- **package.json**: Node.js dependencies
- **npm/yarn/pnpm**: Package manager
- **Node Modules**: Isolated dependencies

---

## 12. Infrastructure Requirements

### 12.1 Hardware Requirements

#### Minimum (Development/Single Character)
- **CPU**: 4+ cores (Intel/AMD)
- **RAM**: 16GB
- **GPU**: NVIDIA GPU with 8GB+ VRAM (RTX 3060, etc.)
- **Storage**: 500GB SSD
- **Network**: Stable internet connection

**Estimated Cost**: $1,500 - $2,000

#### Recommended (Production/Multiple Characters)
- **CPU**: 8+ cores (Intel/AMD)
- **RAM**: 32GB+
- **GPU**: NVIDIA GPU with 24GB+ VRAM (RTX 4090, A6000, etc.)
- **Storage**: 1TB+ NVMe SSD
- **Network**: High-speed internet (100+ Mbps)

**Estimated Cost**: $3,500 - $4,500

#### Optimal (Scale/Enterprise)
- **CPU**: 16+ cores
- **RAM**: 64GB+
- **GPU**: Multiple GPUs or A100/H100
- **Storage**: 2TB+ NVMe SSD (or multiple drives)
- **Network**: Gigabit internet

**Estimated Cost**: $10,000+

### 12.2 Software Requirements

#### Operating System
- **Primary**: Ubuntu 22.04 LTS or 24.04 LTS
- **Alternatives**: Debian 12+, CentOS Stream 9+
- **Why**: Best NVIDIA driver support, stable, widely used

#### Core Software
- **Python**: 3.11+ (via pyenv or system package)
- **Node.js**: 20+ LTS (via nvm or system package)
- **PostgreSQL**: 15+ (via apt or Docker)
- **Redis**: 7+ (via apt or Docker)
- **Docker**: 24+ (optional, for containerization)
- **Docker Compose**: 2.20+ (optional)

#### NVIDIA Software
- **NVIDIA Drivers**: Latest stable (535+)
- **CUDA**: 12.0+ (for GPU acceleration)
- **cuDNN**: 8.9+ (for deep learning)
- **PyTorch**: 2.1+ (with CUDA support)

#### AI/ML Software
- **Stable Diffusion**: Automatic1111 WebUI or ComfyUI
- **Ollama**: Latest version (for LLM)
- **Coqui TTS**: Latest version (for voice)

---

## 13. Component Interaction Diagrams

### 13.1 Character Creation Flow

```
User (UI)
    │
    │ POST /api/v1/characters
    ▼
FastAPI Endpoint
    │
    ├──> Validate Request (Pydantic)
    │
    ├──> Character Management Service
    │       │
    │       ├──> Create Character Record
    │       │       │
    │       │       ▼
    │       │   PostgreSQL (characters table)
    │       │
    │       ├──> Create Persona Record
    │       │       │
    │       │       ▼
    │       │   PostgreSQL (character_personalities table)
    │       │
    │       ├──> Process Face Reference
    │       │       │
    │       │       ├──> Upload to Storage
    │       │       │       │
    │       │       │       ▼
    │       │       │   Local Storage
    │       │       │
    │       │       └──> Create Appearance Record
    │       │               │
    │       │               ▼
    │       │           PostgreSQL (character_appearances table)
    │       │
    │       └──> Generate Initial Content (Async)
    │               │
    │               ▼
    │           Celery Task Queue
    │               │
    │               ▼
    │           Content Generation Worker
    │               │
    │               ├──> Generate Profile Image
    │               │       │
    │               │       ▼
    │               │   Stable Diffusion
    │               │
    │               └──> Store Generated Content
    │                       │
    │                       ▼
    │                   Local Storage + PostgreSQL
    │
    └──> Return Character ID
            │
            ▼
        WebSocket Notification
            │
            ▼
        UI Update (Real-Time)
```

### 13.2 Content Generation & Posting Flow

```
Automation Rule Triggered
    │
    ▼
Scheduling Service
    │
    ├──> Evaluate Rule Conditions
    │
    ├──> Create Content Generation Task
    │       │
    │       ▼
    │   Celery Task Queue
    │       │
    │       ▼
    │   Content Generation Worker
    │       │
    │       ├──> Generate Image
    │       │       │
    │       │       ▼
    │       │   Stable Diffusion API
    │       │       │
    │       │       ├──> Apply Face Consistency
    │       │       │       │
    │       │       │       ▼
    │       │       │   IP-Adapter / InstantID
    │       │       │
    │       │       └──> Post-Processing
    │       │               │
    │       │               ▼
    │       │           Quality Validation
    │       │               │
    │       │               ▼
    │       │           Store Content
    │       │               │
    │       │               ▼
    │       │           Local Storage + PostgreSQL
    │       │
    │       ├──> Generate Caption
    │       │       │
    │       │       ▼
    │       │   Ollama LLM API
    │       │       │
    │       │       ├──> Inject Persona
    │       │       └──> Generate Text
    │       │               │
    │       │               ▼
    │       │           PostgreSQL (content table)
    │       │
    │       └──> Schedule Post
    │               │
    │               ▼
    │           PostgreSQL (scheduled_posts table)
    │
    └──> Execute Posting at Scheduled Time
            │
            ▼
        Platform Integration Worker
            │
            ├──> Retrieve Content
            │       │
            │       ▼
            │   Local Storage + PostgreSQL
            │
            ├──> Platform-Specific Adaptation
            │       │
            │       ├──> Resize Image
            │       ├──> Adapt Caption
            │       └──> Format Content
            │
            ├──> Anti-Detection Measures
            │       │
            │       ├──> Human Delay
            │       ├──> Fingerprint Rotation
            │       └──> Proxy Rotation
            │
            ├──> Publish to Platform
            │       │
            │       ├──> Primary: Platform API
            │       └──> Fallback: Browser Automation
            │
            └──> Update Status & Analytics
                    │
                    ▼
                PostgreSQL (posts, analytics tables)
                    │
                    ▼
                WebSocket Notification
                    │
                    ▼
                UI Update (Real-Time)
```

---

## 14. Technology Selection Rationale (Detailed)

### 14.1 Backend Framework: FastAPI

#### Why FastAPI Over Alternatives?

**vs Flask:**
- ✅ Native async support (critical for concurrent operations)
- ✅ Automatic OpenAPI documentation
- ✅ Type safety with Pydantic
- ✅ Better performance
- ✅ Modern Python features

**vs Django:**
- ✅ Lighter weight (API-only, no admin needed)
- ✅ Better async support
- ✅ Faster development
- ✅ More flexible

**vs Node.js:**
- ✅ Better AI/ML ecosystem (Python)
- ✅ More AI/ML libraries available
- ✅ Better for data processing

**Decision**: FastAPI is the best choice for an AI/ML-focused API.

### 14.2 Frontend Framework: Next.js

#### Why Next.js Over Alternatives?

**vs Plain React:**
- ✅ Server components (better performance)
- ✅ Built-in optimizations
- ✅ Less boilerplate
- ✅ Better SEO

**vs Vue:**
- ✅ Larger ecosystem
- ✅ Better server components
- ✅ More React libraries available

**vs Svelte:**
- ✅ Larger community
- ✅ More resources and tutorials
- ✅ Better ecosystem

**Decision**: Next.js provides the best modern React development experience.

### 14.3 Database: PostgreSQL

#### Why PostgreSQL Over Alternatives?

**vs MySQL:**
- ✅ Better JSON support (needed for flexible schemas)
- ✅ More advanced features
- ✅ Better for complex queries

**vs MongoDB:**
- ✅ Better for relational data (characters, posts, etc.)
- ✅ ACID compliance (data integrity)
- ✅ Better consistency guarantees

**Decision**: PostgreSQL is the best choice for relational data with JSON support.

---

## 15. Next Steps

### Immediate Actions
1. ✅ Review and approve this architecture
2. ⏳ Set up development environment (see [08-DEVELOPMENT-ENVIRONMENT.md](./08-DEVELOPMENT-ENVIRONMENT.md))
3. ⏳ Install and configure Stable Diffusion (see [07-AI-MODELS-REALISM.md](./07-AI-MODELS-REALISM.md))
4. ⏳ Set up database schema (see [04-DATABASE-SCHEMA.md](./04-DATABASE-SCHEMA.md))
5. ⏳ Create basic API structure (see [05-API-DESIGN.md](./05-API-DESIGN.md))
6. ⏳ Implement first character generation

### Architecture Decisions
- ✅ Microservices architecture approved
- ✅ Technology stack approved
- ⏳ Infrastructure setup pending
- ⏳ Monitoring setup pending
- ⏳ Security hardening pending

---

**Document Status**: ✅ Complete - Production Ready

**Related Documents:**
- [04-DATABASE-SCHEMA.md](./04-DATABASE-SCHEMA.md) - Database design
- [05-API-DESIGN.md](./05-API-DESIGN.md) - API specification
- [07-AI-MODELS-REALISM.md](./07-AI-MODELS-REALISM.md) - AI model details
- [20-DEPLOYMENT-DEVOPS.md](./20-DEPLOYMENT-DEVOPS.md) - Deployment guide
- [22-MONITORING-ALERTING.md](./22-MONITORING-ALERTING.md) - Monitoring setup
- [23-SCALING-OPTIMIZATION.md](./23-SCALING-OPTIMIZATION.md) - Scaling strategies
- [24-SECURITY-HARDENING.md](./24-SECURITY-HARDENING.md) - Security details

# AInfluencer Pipeline & Workflow Architecture (Master Specification)

> **STATUS:** APPROVED FOR IMPLEMENTATION  
> **TARGET AUDIENCE:** Senior Engineering & Product  
> **ENTRYPOINT:** `node scripts/one.mjs` (unchanged)  
> **VERSION:** 1.0  
> **DATE:** 2025-01-27

---

## Table of Contents

1. [North Star & Vision](#1-north-star--vision)
2. [System Architecture: The "Engine Adapter" Pattern](#2-system-architecture-the-engine-adapter-pattern)
3. [Provider Types & Integration Strategy](#3-provider-types--integration-strategy)
4. ["One-Click Install/Connect" UX (Without Unsafe Auto-Discovery)](#4-one-click-installconnect-ux-without-unsafe-auto-discovery)
5. [Workflow Presets (The Real Product)](#5-workflow-presets-the-real-product)
6. [Data Contracts (No 422/Schema Drift)](#6-data-contracts-no-422schema-drift)
7. [Catalog Design (Curated + User)](#7-catalog-design-curated--user)
8. [Reliability & Observability](#8-reliability--observability)
9. [Security & Compliance](#9-security--compliance)
10. [Phased Roadmap (No Scope Creep)](#10-phased-roadmap-no-scope-creep)
11. [Smoke Test Matrix](#11-smoke-test-matrix)

---

## 1. North Star & Vision

### 1.1 Core Principle

**"Hollywood-grade results come from pipelines, not buttons."**

We are not building a simple "wrapper." We are building a **Multi-Modal Orchestration Engine** that chains best-in-class tools (Local ComfyUI + Remote APIs) into seamless production lines.

### 1.2 User Experience Goal (TTFS - Time to First Shot)

**Target:** New user → first usable output under 10 minutes (with at least one preset)

**Non-technical flow:**

1. **Setup** → Install/connect at least one engine (local ComfyUI OR one remote API key)
2. **Choose Preset** → Select from curated presets (e.g., "Cinematic Talking Head")
3. **Run** → Upload inputs (photo + audio) → Click "Generate"
4. **View Result** → See output in gallery within 5 minutes
5. **Export** → Download or share result

**Example Success Path:**

- User installs local ComfyUI (or pastes Fal.ai API key)
- User selects "Cinematic Talking Head" preset
- User uploads 1 photo + 1 audio file
- **Result:** < 5 minutes, receiving a broadcast-ready video with perfect lip-sync and no "plastic" look

### 1.3 Quality Standards

- **No "AI smooth skin"** → Anti-plastic workflows with natural texture
- **Identity consistency** → Face/character lock across shots
- **Production-ready** → Export formats optimized for TikTok/IG/YouTube
- **Graceful degradation** → If engine missing, show clear CTA (not server error)

---

## 2. System Architecture: The "Engine Adapter" Pattern

### 2.1 Core Components

To support the massive list of models (Nano Banana, Kling, Flux, Veo, etc.) without spaghetti code, we use a strict **Adapter Pattern**.

#### 2.1.1 `PipelineManager` (The Brain)

**Location:** `backend/app/services/pipeline_manager.py`

**Responsibilities:**

- Receives a job request (preset + inputs)
- Selects the correct engine strategy (local/remote/hybrid)
- Orchestrates multi-step pipelines (e.g., image → video → lipsync)
- Manages job state and progress
- Handles failures with retry logic

**Interface:**

```python
class PipelineManager:
    async def execute_preset(
        self,
        preset_id: str,
        inputs: PresetInputs,
        user_tier: str,
    ) -> PipelineJob:
        """Execute a workflow preset and return job tracking object."""

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get current status of a pipeline job."""

    async def cancel_job(self, job_id: str) -> None:
        """Cancel a running pipeline job."""
```

#### 2.1.2 `EngineAdapter` (Interface)

**Location:** `backend/app/services/engines/base.py`

**Standardizes all providers (local and remote):**

```python
from abc import ABC, abstractmethod
from typing import Any

class EngineAdapter(ABC):
    """Base interface for all engine adapters (local and remote)."""

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Unique engine identifier (e.g., 'local_comfy', 'provider_kling')."""

    @property
    @abstractmethod
    def engine_type(self) -> str:
        """Engine type: 'local' or 'remote'."""

    @abstractmethod
    async def verify_identity(self, credentials: dict[str, Any]) -> bool:
        """Verify API key/credentials are valid. Returns True if valid."""

    @abstractmethod
    async def check_balance(self) -> dict[str, Any]:
        """Check account balance/credits (for remote APIs). Returns balance info."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if engine is reachable and ready. Returns True if healthy."""

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate image. Returns dict with 'output_path' or 'output_url'."""

    @abstractmethod
    async def generate_video(
        self,
        image_path: str | None,
        prompt: str | None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate video. Returns dict with 'output_path' or 'output_url'."""

    @abstractmethod
    async def apply_lipsync(
        self,
        video_path: str,
        audio_path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Apply lip-sync to video. Returns dict with 'output_path' or 'output_url'."""

    @abstractmethod
    async def upscale(
        self,
        image_path: str | None,
        video_path: str | None,
        scale: int = 2,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Upscale image or video. Returns dict with 'output_path' or 'output_url'."""
```

**Concrete Implementations:**

- `LocalComfyAdapter` → Wraps existing `ComfyUiClient`
- `KlingAdapter` → Remote API for Kling 2.6 / Kling O1
- `FalAdapter` → Remote API for Flux.1 Pro, Minimax Hailuo, Wan 2.6
- `RunwareAdapter` → Remote API for Flux.1 Schnell, Fast Upscalers
- `SyncLabsAdapter` → Remote API for lip-sync
- `LivePortraitAdapter` → Local Python env for expression transfer

#### 2.1.3 `WorkflowPreset` (Schema)

**Location:** `backend/app/models/workflow_preset.py`

**JSON definition of a specific task:**

```python
from pydantic import BaseModel
from typing import Literal

class WorkflowPreset(BaseModel):
    """Workflow preset definition."""

    id: str
    name: str
    description: str
    category: Literal[
        "image_generation",
        "video_generation",
        "character_performance",
        "post_processing",
        "hybrid_pipeline",
    ]

    # Input requirements
    required_inputs: dict[str, Any]  # e.g., {"prompt": "str", "image": "file", "audio": "file"}
    optional_inputs: dict[str, Any] = {}

    # Engine requirements
    engine_requirements: list[str]  # e.g., ["local_comfy", "provider_kling"]
    engine_preference_order: list[str] = []  # Preferred order if multiple available

    # Quality knobs
    quality_levels: dict[str, dict[str, Any]] = {
        "low": {"steps": 20, "cfg": 6.0},
        "standard": {"steps": 30, "cfg": 7.0},
        "pro": {"steps": 50, "cfg": 8.0},
    }

    # Pipeline steps (for multi-step workflows)
    pipeline_steps: list[dict[str, Any]] = []  # e.g., [{"step": "generate_image", "engine": "local_comfy"}, ...]

    # Safety notes
    safety_notes: list[str] = []
    requires_consent: bool = False  # For identity-based workflows

    # Failure modes + remediation
    failure_modes: dict[str, str] = {}  # Error code → user-facing message
```

#### 2.1.4 `ProviderRegistry` (The "Bring Your Own Key" Hub)

**Location:** `backend/app/services/provider_registry.py`

**Manages configured providers:**

```python
class ProviderRegistry:
    """Registry for configured remote API providers."""

    def register_provider(
        self,
        provider_id: str,
        api_key: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Register a remote provider with API key."""

    def get_provider(self, provider_id: str) -> EngineAdapter | None:
        """Get configured provider adapter."""

    def list_providers(self) -> list[dict[str, Any]]:
        """List all registered providers with status."""

    def test_provider(self, provider_id: str) -> dict[str, Any]:
        """Test provider connection and return balance/status."""
```

**Provider Table:**

| Provider ID             | Type   | Models Supported                      | Auth Strategy    | Balance Endpoint       |
| :---------------------- | :----- | :------------------------------------ | :--------------- | :--------------------- |
| `local_comfy`           | Local  | Nano Banana, Flux.1 Dev, Custom Loras | Localhost check  | N/A (free)             |
| `provider_kling`        | Remote | Kling 2.6, Kling O1 (Pro)             | API Key (JWT)    | `GET /v1/user/balance` |
| `provider_fal`          | Remote | Flux.1 Pro, Minimax Hailuo, Wan 2.6   | API Key (Secret) | `GET /v1/user/balance` |
| `provider_runware`      | Remote | Flux.1 Schnell, Fast Upscalers        | API Key          | `GET /api/v1/balance`  |
| `provider_synclabs`     | Remote | Lip-Sync (High Fidelity)              | API Key          | `GET /api/v1/account`  |
| `provider_liveportrait` | Local  | Expression Transfer, Lip-Sync         | Local Python Env | N/A (free)             |

**ASSUMED:** Provider API endpoints and authentication methods. **TODO:** Verify actual API endpoints and auth flows during implementation.

#### 2.1.5 `ArtifactStore` (Centralized File Handling)

**Location:** `backend/app/services/artifact_store.py`

**Manages output files:**

```python
class ArtifactStore:
    """Centralized artifact storage (local or S3)."""

    def save_artifact(
        self,
        job_id: str,
        artifact_type: str,  # "image", "video", "audio"
        file_path: str,
        metadata: dict[str, Any] = {},
    ) -> str:
        """Save artifact and return URL/path."""

    def get_artifact_url(self, job_id: str, artifact_type: str) -> str | None:
        """Get URL/path to artifact."""

    def list_artifacts(self, job_id: str) -> list[dict[str, Any]]:
        """List all artifacts for a job."""
```

**Storage Strategy:**

- **MVP:** Local filesystem (`data_dir() / "artifacts" / {job_id}`)
- **Production:** S3-compatible storage (configurable)

#### 2.1.6 `CreditLedger` (Internal Accounting)

**Location:** `backend/app/services/credit_ledger.py`

**Maps user actions to pricing tiers:**

```python
class CreditLedger:
    """Internal credit accounting system."""

    def calculate_cost(
        self,
        preset_id: str,
        quality_level: str,
        engine_id: str,
    ) -> int:
        """Calculate credit cost for a job. Returns credits required."""

    def check_balance(self, user_id: str) -> int:
        """Get user's current credit balance."""

    def deduct_credits(
        self,
        user_id: str,
        amount: int,
        job_id: str,
    ) -> bool:
        """Deduct credits. Returns True if successful."""

    def refund_credits(
        self,
        user_id: str,
        amount: int,
        job_id: str,
    ) -> None:
        """Refund credits (e.g., if job fails)."""
```

**Credit Cost Table (ASSUMED - TODO: Verify with actual provider pricing):**

| Engine              | Operation              | Quality  | Credits                |
| :------------------ | :--------------------- | :------- | :--------------------- |
| `local_comfy`       | Image generation       | Any      | 0 (hardware cost only) |
| `local_comfy`       | Video generation       | Any      | 0 (hardware cost only) |
| `provider_kling`    | Video (Kling 2.6)      | Standard | 50                     |
| `provider_kling`    | Video (Kling O1 Pro)   | Pro      | 100                    |
| `provider_fal`      | Image (Flux Pro)       | Standard | 2                      |
| `provider_fal`      | Video (Minimax Hailuo) | Standard | 30                     |
| `provider_synclabs` | Lip-sync               | Standard | 10                     |
| `provider_runware`  | Upscale                | Standard | 5                      |

**ASSUMED:** Credit costs. **TODO:** Verify actual pricing from provider APIs during implementation.

#### 2.1.7 `JobQueue` (Abstraction)

**Location:** `backend/app/services/job_queue.py`

**Even if current MVP is synchronous, define abstraction for future async:**

```python
class JobQueue:
    """Job queue abstraction (MVP: synchronous, future: async with Redis)."""

    def enqueue(
        self,
        job: PipelineJob,
        priority: int = 0,
    ) -> str:
        """Enqueue job and return job_id."""

    def get_job(self, job_id: str) -> PipelineJob | None:
        """Get job by ID."""

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: float = 0.0,
    ) -> None:
        """Update job status and progress."""
```

**MVP Implementation:** In-memory dict with file persistence  
**Future:** Redis-backed queue with workers

---

## 3. Provider Types & Integration Strategy

### 3.1 Local Engines

#### 3.1.1 ComfyUI Workflow Runner (Primary)

**Status:** ✅ Already implemented (`ComfyUiClient`, `ComfyUiManager`)

**Enhancements Needed:**

- Wrap in `LocalComfyAdapter` to implement `EngineAdapter` interface
- Add workflow template system for presets
- Support custom checkpoint/LoRA selection per preset

**Location:** `backend/app/services/engines/local_comfy_adapter.py`

#### 3.1.2 Optional Local Tools (User-Installed Only)

**Rule:** Only as "user-installed" modules. System does NOT auto-install.

**Examples:**

- LivePortrait (Python package) → User installs via pip, system detects
- Topaz Video Enhance AI (CLI) → User installs, system detects binary path

**Detection Strategy:**

- Check for Python packages: `pip list | grep liveportrait`
- Check for binaries: `which topaz-video-enhance-ai`
- Health check: Run test command, verify output

### 3.2 Remote APIs

#### 3.2.1 "Bring Your Own Key" (BYOK) Strategy

**Rules:**

- Providers must be "bring-your-own-key"
- User pastes API key in Setup Hub
- System stores key securely (encrypted in `.env` or vault)
- System tests connection and shows balance
- Keys are redacted in logs

**API Key Storage:**

- **MVP:** `.env` file with `AINFLUENCER_PROVIDER_{PROVIDER_ID}_API_KEY=...`
- **Production:** Encrypted vault (e.g., AWS Secrets Manager, HashiCorp Vault)

**Redaction in Logs:**

- All API keys must be redacted: `api_key=***REDACTED***`
- Use `redact_secrets()` utility function

#### 3.2.2 Remote Provider Adapters

**Implementation Pattern:**

```python
class KlingAdapter(EngineAdapter):
    """Adapter for Kling AI API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.klingai.com/v1"

    async def verify_identity(self, credentials: dict[str, Any]) -> bool:
        """Test API key by calling /user/balance."""
        # ASSUMED endpoint - TODO: Verify actual endpoint
        response = await httpx.get(
            f"{self.base_url}/user/balance",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        return response.status_code == 200

    async def check_balance(self) -> dict[str, Any]:
        """Get account balance."""
        # ASSUMED endpoint - TODO: Verify actual endpoint
        response = await httpx.get(
            f"{self.base_url}/user/balance",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        return response.json()  # ASSUMED format - TODO: Verify

    async def generate_video(
        self,
        image_path: str | None,
        prompt: str | None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate video via Kling API."""
        # ASSUMED endpoint - TODO: Verify actual API contract
        # ...
```

**ASSUMED:** API endpoints, request/response formats. **TODO:** Verify during implementation by:

1. Reading provider API documentation
2. Testing with sandbox API keys
3. Updating adapter code with actual contracts

### 3.3 Hybrid Pipelines

**Example:** Local generation → Remote upscale → Local postprocess

**Pipeline Definition:**

```json
{
  "pipeline_steps": [
    {
      "step_id": "generate_image",
      "engine": "local_comfy",
      "inputs": { "prompt": "..." },
      "outputs": { "image": "step_1_image.png" }
    },
    {
      "step_id": "upscale",
      "engine": "provider_runware",
      "inputs": { "image": "{{step_1_image.png}}" },
      "outputs": { "image": "step_2_upscaled.png" }
    },
    {
      "step_id": "apply_grain",
      "engine": "local_comfy",
      "inputs": { "image": "{{step_2_upscaled.png}}" },
      "outputs": { "image": "final.png" }
    }
  ]
}
```

**Implementation:** `PipelineManager` orchestrates steps, passes outputs between engines.

---

## 4. "One-Click Install/Connect" UX (Without Unsafe Auto-Discovery)

### 4.1 Setup Hub Page

**Location:** `frontend/src/app/setup/page.tsx` (new page)

**Layout:**

- Grid of "Connect Provider" cards
- Grid of "Install Local Engine" cards
- "Add Model Source" section
- Healthcheck matrix
- Diagnostics export button

### 4.2 "Connect Provider" Cards

**UI Component:** Card for each remote provider (Kling, Fal, Runware, SyncLabs)

**Fields:**

- Provider name + logo
- Input: API Key (masked)
- Button: "Test Connection"
- Status: "Not Connected" | "Connected (Balance: 1200 Credits)" | "Error: Invalid API Key"

**Backend Endpoint:**

```
POST /api/providers/{provider_id}/connect
Body: {"api_key": "..."}
Response: {"ok": true, "balance": 1200, "message": "Connected successfully"}
```

**Validation:**

- Test API key by calling `verify_identity()`
- Show balance from `check_balance()`
- Store key securely (redacted in logs)

### 4.3 "Install Local Engine" Cards

**UI Component:** Card for "AInfluencer Local Core (ComfyUI)"

**Fields:**

- Engine name + description
- Status: "Not Installed" | "Installed (Not Running)" | "Running"
- Button: "Install" | "Start" | "Stop" | "Restart"
- Logs: Collapsible log viewer

**Backend Endpoints:**

- `POST /api/comfyui/manager/install` (already exists)
- `POST /api/comfyui/manager/start` (already exists)
- `POST /api/comfyui/manager/stop` (already exists)
- `GET /api/comfyui/manager/logs` (already exists)

**Enhancement:** Add healthcheck status to existing endpoints.

### 4.4 "Add Model Source" (Strict Rules)

**UI Component:** Form for adding custom model

**Fields:**

- Model Name (required)
- Model Type (dropdown: checkpoint, lora, embedding, controlnet, other)
- Download URL (required, must be http/https)
- Filename (required)
- **License** (required dropdown: "MIT", "Apache 2.0", "CC0", "Custom", "Unknown")
- **Checksum (SHA256)** (optional, but recommended)
- Tags (optional)
- Notes (optional)

**Validation Rules:**

- URL must start with `http://` or `https://`
- Filename must be safe (no path traversal)
- If checksum missing: Show warning "Download at your risk" (OFF by default)
- If license is "Unknown": Require explicit acknowledgment checkbox

**Backend Endpoint:**

```
POST /api/models/custom
Body: {
  "name": "...",
  "type": "checkpoint",
  "url": "https://...",
  "filename": "...",
  "license": "MIT",
  "sha256": "..." (optional),
  "tags": [...],
  "notes": "..."
}
```

**Safety Gate:**

- If checksum missing AND license unknown: Show confirmation dialog
- User must check "I understand the risks" before proceeding

### 4.5 Healthcheck Matrix

**UI Component:** Table showing health status of all engines

| Engine          | Status           | Balance/Credits | Last Check | Action     |
| :-------------- | :--------------- | :-------------- | :--------- | :--------- |
| ComfyUI (Local) | ✅ Running       | Free            | 2s ago     | Stop       |
| Kling AI        | ✅ Connected     | 1,200 Credits   | 5s ago     | Disconnect |
| Fal.ai          | ❌ Not Connected | -               | -          | Connect    |
| Runware         | ⚠️ Error         | -               | 10s ago    | Retry      |

**Backend Endpoint:**

```
GET /api/setup/healthcheck
Response: {
  "engines": [
    {
      "engine_id": "local_comfy",
      "status": "running",
      "balance": null,
      "last_check": "2025-01-27T10:00:00Z",
      "error": null
    },
    {
      "engine_id": "provider_kling",
      "status": "connected",
      "balance": 1200,
      "last_check": "2025-01-27T10:00:05Z",
      "error": null
    },
    ...
  ]
}
```

**Healthcheck Logic:**

- **Engine reachable:** Call `health_check()` on adapter
- **Disk space:** Check free space on `data_dir()`
- **GPU available:** Check `nvidia-smi` (if relevant for local engines)
- **Permissions:** Check write permissions on `data_dir()`

### 4.6 Diagnostics Export Bundle

**UI Component:** Button "Export Diagnostics"

**Backend Endpoint:**

```
GET /api/setup/diagnostics
Response: {
  "system_info": {
    "os": "darwin 25.3.0",
    "python_version": "3.11.0",
    "disk_space": {"free_gb": 50, "total_gb": 500},
    "gpu": {"available": false, "model": null},
  },
  "engines": [...],
  "providers": [...],
  "models_installed": [...],
  "logs": ["..."] (last 100 lines, secrets redacted)
}
```

**Export Format:** JSON file download

---

## 5. Workflow Presets (The Real Product)

### 5.1 Preset Schema

Each preset must specify:

- **Goal** (what user gets)
- **Inputs** (prompt, image, video, audio, identity reference)
- **Engine requirements** (local/remote)
- **Quality knobs** (simple: Low/Standard/Pro)
- **Safety notes** (consent, content restrictions)
- **Failure modes + remediation CTAs**

### 5.2 Preset Catalog (12+ Presets)

#### Category A: Image Generation (The "Base")

##### Preset 1: Photoreal Portrait (Anti-Plastic)

**ID:** `photoreal_portrait_v1`

**Goal:** Zero "AI smooth skin" look. Natural skin texture with visible pores.

**Inputs:**

- `prompt` (required): Text description
- `identity_reference` (optional): 1-3 reference photos for face consistency
- `seed` (optional): Random seed

**Engine Requirements:**

- Primary: `local_comfy` (with Flux.1 Dev or Nano Banana checkpoint)
- Fallback: `provider_fal` (Flux.1 Pro)

**Quality Levels:**

- **Low:** 25 steps, CFG 6.5, no post-processing
- **Standard:** 40 steps, CFG 7.5, face restoration enabled
- **Pro:** 50 steps, CFG 8.0, face restoration + upscale 2x

**Pipeline Steps:**

1. Generate image with anti-plastic prompt
2. Apply face restoration (GFPGAN) if enabled
3. Upscale if quality level is "Pro"

**Safety Notes:**

- If `identity_reference` provided: Requires consent checkbox
- Content restrictions: No NSFW generation

**Failure Modes:**

- `ENGINE_OFFLINE`: "ComfyUI is not running. Click 'Start ComfyUI' in Setup."
- `DEPENDENCY_MISSING`: "Required checkpoint not found. Install model in Model Manager."
- `INSUFFICIENT_FUNDS`: "Not enough credits. Upgrade plan or use local engine."

**ASSUMED:** Anti-plastic prompt engineering. **TODO:** Test and refine prompt during implementation.

##### Preset 2: Cinematic Portrait (Film Look)

**ID:** `cinematic_portrait_v1`

**Goal:** Film grain, cinematic color grading, anamorphic lens look.

**Inputs:**

- `prompt` (required)
- `identity_reference` (optional)
- `seed` (optional)

**Engine Requirements:**

- Primary: `local_comfy`
- Fallback: `provider_fal`

**Quality Levels:**

- **Low:** 30 steps, basic film grain
- **Standard:** 35 steps, film grain + tone mapping
- **Pro:** 40 steps, film grain + tone mapping + color grading

**Pipeline Steps:**

1. Generate image with cinematic prompt
2. Apply film grain overlay (post-processing)
3. Apply tone mapping (Reinhard method)
4. Apply color grading (if Pro)

**Safety Notes:**

- Same as Preset 1

**ASSUMED:** Film grain and tone mapping implementation. **TODO:** Implement post-processing nodes in ComfyUI or use PIL/OpenCV.

##### Preset 3: Identity Lock Portrait (Consistency)

**ID:** `identity_lock_portrait_v1`

**Goal:** Consistent face across different scenes/outfits using IP-Adapter or InstantID.

**Inputs:**

- `prompt` (required)
- `identity_reference` (required): 1-3 reference photos
- `seed` (optional)

**Engine Requirements:**

- Primary: `local_comfy` (with IP-Adapter or InstantID extension)
- Fallback: None (requires local engine)

**Quality Levels:**

- **Low:** IP-Adapter weight 0.6
- **Standard:** IP-Adapter Plus weight 0.75
- **Pro:** InstantID weight 0.8 + face restoration

**Pipeline Steps:**

1. Load identity reference images
2. Generate image with identity lock enabled
3. Apply face restoration (if Pro)

**Safety Notes:**

- **REQUIRES CONSENT:** User must checkbox "I have permission to use this face"
- Content restrictions: No NSFW generation

**Failure Modes:**

- `DEPENDENCY_MISSING`: "IP-Adapter or InstantID extension not installed. Install in ComfyUI."
- `CONSENT_MISSING`: "Identity-based workflows require consent. Check the consent box."

**ASSUMED:** IP-Adapter/InstantID integration. **TODO:** Verify ComfyUI extensions and workflow nodes.

#### Category B: Video Generation (The "Motion")

##### Preset 4: Image-to-Video (Short Motion)

**ID:** `image_to_video_v1`

**Goal:** Convert static image to short video (2-5 seconds) with natural motion.

**Inputs:**

- `image` (required): Source image file
- `prompt` (optional): Motion description (e.g., "slow camera pan, wind in hair")
- `duration` (optional): Video duration in seconds (default: 3)

**Engine Requirements:**

- Primary: `provider_kling` (Kling 2.6)
- Fallback: `provider_fal` (Minimax Hailuo)

**Quality Levels:**

- **Low:** 2 seconds, standard quality
- **Standard:** 3 seconds, high quality
- **Pro:** 5 seconds, 4K quality

**Pipeline Steps:**

1. Validate input image (format, size)
2. Upload image to provider (if remote)
3. Generate video via API
4. Download video to artifact store

**Safety Notes:**

- Content restrictions: No NSFW generation
- Video length limits: Max 5 seconds (provider-dependent)

**Failure Modes:**

- `ENGINE_OFFLINE`: "Kling AI not connected. Add API key in Setup."
- `INSUFFICIENT_FUNDS`: "Not enough credits. Upgrade plan."
- `FILE_NOT_FOUND`: "Input image not found. Re-upload image."

**ASSUMED:** Kling API video generation contract. **TODO:** Verify API request/response format.

##### Preset 5: Talking Clip (Lip-Sync)

**ID:** `talking_clip_v1`

**Goal:** Perfect mouth match between video and audio.

**Inputs:**

- `video` (required): Source video file (from Preset 4 or user upload)
- `audio` (required): Audio file (WAV/MP3)
- `identity_reference` (optional): Face reference for consistency

**Engine Requirements:**

- Primary: `provider_synclabs` (Cloud, high fidelity)
- Fallback: `provider_liveportrait` (Local, if installed)

**Quality Levels:**

- **Low:** Standard lip-sync
- **Standard:** High-fidelity lip-sync
- **Pro:** Ultra-high-fidelity + face consistency

**Pipeline Steps:**

1. Validate video and audio formats
2. Upload video + audio to provider (if remote)
3. Apply lip-sync via API
4. Download result to artifact store

**Safety Notes:**

- **REQUIRES CONSENT:** If identity reference provided
- Audio content: No copyrighted music (user responsibility)

**Failure Modes:**

- `ENGINE_OFFLINE`: "SyncLabs not connected. Add API key in Setup."
- `FILE_NOT_FOUND`: "Video or audio file not found."
- `VALIDATION_ERROR`: "Unsupported video/audio format. Use MP4/WAV."

**ASSUMED:** SyncLabs API contract. **TODO:** Verify API request/response format.

##### Preset 6: Video Face/Identity Consistency Pass

**ID:** `video_identity_consistency_v1`

**Goal:** Apply face consistency across video frames.

**Inputs:**

- `video` (required): Source video file
- `identity_reference` (required): Face reference image

**Engine Requirements:**

- Primary: `local_comfy` (with face consistency nodes)
- Fallback: None (requires local engine)

**Quality Levels:**

- **Low:** Basic face consistency
- **Standard:** High-quality face consistency
- **Pro:** Ultra-high-quality + frame interpolation

**Pipeline Steps:**

1. Extract frames from video
2. Apply face consistency to each frame
3. Reconstruct video from frames

**Safety Notes:**

- **REQUIRES CONSENT:** Identity-based workflow

**Failure Modes:**

- `ENGINE_OFFLINE`: "ComfyUI not running."
- `DEPENDENCY_MISSING`: "Face consistency extension not installed."

**ASSUMED:** Face consistency workflow in ComfyUI. **TODO:** Verify workflow nodes.

#### Category C: Post-Processing (The "Polish")

##### Preset 7: Upscale + De-Noise (Image)

**ID:** `upscale_denoise_image_v1`

**Goal:** Upscale image 2x-4x with noise reduction.

**Inputs:**

- `image` (required): Source image file

**Engine Requirements:**

- Primary: `provider_runware` (Fast upscalers)
- Fallback: `local_comfy` (Real-ESRGAN)

**Quality Levels:**

- **Low:** 2x upscale, basic denoise
- **Standard:** 2x upscale, advanced denoise
- **Pro:** 4x upscale, ultra denoise

**Pipeline Steps:**

1. Validate input image
2. Upscale via engine
3. Apply denoise filter
4. Save result

**Safety Notes:**

- None (post-processing only)

**Failure Modes:**

- `ENGINE_OFFLINE`: "Upscaler engine not available."
- `FILE_NOT_FOUND`: "Input image not found."

**ASSUMED:** Upscaler API contracts. **TODO:** Verify API endpoints.

##### Preset 8: Upscale + De-Flicker (Video)

**ID:** `upscale_deflicker_video_v1`

**Goal:** Upscale video 2x with flicker reduction.

**Inputs:**

- `video` (required): Source video file

**Engine Requirements:**

- Primary: `provider_runware` (Video upscaler)
- Fallback: `local_comfy` (if video upscale workflow exists)

**Quality Levels:**

- **Low:** 2x upscale, basic deflicker
- **Standard:** 2x upscale, advanced deflicker
- **Pro:** 4x upscale, ultra deflicker + frame interpolation

**Pipeline Steps:**

1. Validate input video
2. Upscale via engine
3. Apply deflicker algorithm
4. Save result

**Safety Notes:**

- None (post-processing only)

**Failure Modes:**

- Same as Preset 7

**ASSUMED:** Video upscaler availability. **TODO:** Verify if Runware supports video upscaling.

##### Preset 9: Color Grade + Film Grain Pass

**ID:** `color_grade_film_grain_v1`

**Goal:** Apply cinematic color grading and film grain to video.

**Inputs:**

- `video` (required): Source video file
- `style` (optional): Color grade style ("warm", "cool", "cinematic")

**Engine Requirements:**

- Primary: `local_comfy` (post-processing workflow)
- Fallback: Local FFmpeg (if ComfyUI not available)

**Quality Levels:**

- **Low:** Basic color grade
- **Standard:** Advanced color grade + light grain
- **Pro:** Professional color grade + heavy grain + tone mapping

**Pipeline Steps:**

1. Extract frames from video
2. Apply color grading to each frame
3. Apply film grain overlay
4. Reconstruct video

**Safety Notes:**

- None (post-processing only)

**Failure Modes:**

- `ENGINE_OFFLINE`: "ComfyUI not running or FFmpeg not installed."

**ASSUMED:** Color grading and film grain implementation. **TODO:** Implement or verify workflow.

#### Category D: Multi-Step Pipelines (The "Production")

##### Preset 10: Multi-Shot Storyboard Builder (Basic)

**ID:** `storyboard_builder_v1`

**Goal:** Generate multiple consistent shots for storyboard.

**Inputs:**

- `prompt_template` (required): Template with `{shot_number}` placeholder
- `shot_count` (required): Number of shots (2-10)
- `identity_reference` (optional): Character reference

**Engine Requirements:**

- Primary: `local_comfy`
- Fallback: `provider_fal`

**Quality Levels:**

- **Low:** 2 shots, standard quality
- **Standard:** 5 shots, high quality
- **Pro:** 10 shots, ultra quality + consistency pass

**Pipeline Steps:**

1. Generate shot 1 with identity lock (if reference provided)
2. Generate shots 2-N with same identity lock
3. Apply consistency pass (if Pro)
4. Package as storyboard (grid layout)

**Safety Notes:**

- **REQUIRES CONSENT:** If identity reference provided

**Failure Modes:**

- Same as Preset 3 (identity lock)

**ASSUMED:** Batch generation with identity consistency. **TODO:** Verify workflow supports batch with identity lock.

##### Preset 11: Product/UGC-Style Clip Builder (Basic)

**ID:** `ugc_clip_builder_v1`

**Goal:** Generate UGC-style product showcase clip.

**Inputs:**

- `product_image` (required): Product photo
- `prompt` (required): Scene description
- `audio` (optional): Voiceover audio

**Engine Requirements:**

- Primary: `local_comfy` (image generation) + `provider_kling` (video) + `provider_synclabs` (lipsync if audio provided)

**Quality Levels:**

- **Low:** Image → Video only
- **Standard:** Image → Video → Basic post-processing
- **Pro:** Image → Video → Lip-sync → Color grade → Upscale

**Pipeline Steps:**

1. Generate product scene image (if needed)
2. Convert image to video (Preset 4)
3. Apply lip-sync (if audio provided, Preset 5)
4. Apply color grade (Preset 9)
5. Upscale (Preset 8, if Pro)

**Safety Notes:**

- None (product showcase)

**Failure Modes:**

- Composite of failure modes from component presets

**ASSUMED:** Multi-step pipeline orchestration. **TODO:** Verify `PipelineManager` can chain presets.

##### Preset 12: "Repair Pipeline" Preset (Re-Run with Safer Settings)

**ID:** `repair_pipeline_v1`

**Goal:** Re-run failed job with safer settings (lower quality, different engine).

**Inputs:**

- `failed_job_id` (required): Reference to failed job
- `quality_override` (optional): Force quality level ("low")

**Engine Requirements:**

- Any available engine (auto-select)

**Quality Levels:**

- **Low:** Always uses "low" quality (forced)
- **Standard:** Uses original quality
- **Pro:** Not applicable (repair only)

**Pipeline Steps:**

1. Load failed job parameters
2. Override quality to "low" (if specified)
3. Select alternative engine (if original failed)
4. Re-run with safer settings

**Safety Notes:**

- None (repair only)

**Failure Modes:**

- `FILE_NOT_FOUND`: "Failed job not found."
- `ENGINE_OFFLINE`: "No engines available. Check Setup."

**ASSUMED:** Job history and re-run capability. **TODO:** Verify job persistence and retrieval.

---

## 6. Data Contracts (No 422/Schema Drift)

### 6.1 Strict JSON Schemas

All API endpoints must use Pydantic models with strict validation to prevent 422 errors and schema drift.

### 6.2 Create Character Contract

**Endpoint:** `POST /api/characters`

**Request Schema:**

```python
class CreateCharacterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    avatar_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "forbid"  # Reject unknown fields
```

**Response Schema:**

```python
class CharacterResponse(BaseModel):
    id: str
    name: str
    description: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
```

**Validation Rules:**

- `name` is required and 1-100 characters
- `description` is optional, max 1000 characters
- Unknown fields are rejected (`extra = "forbid"`)

### 6.3 Generate (Image/Video) Contract

**Endpoint:** `POST /api/generate/image` or `POST /api/generate/video`

**Request Schema:**

```python
class GenerateRequest(BaseModel):
    preset_id: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str | None = Field(default=None, max_length=2000)
    quality_level: Literal["low", "standard", "pro"] = "standard"
    seed: int | None = Field(default=None, ge=0, le=2**32)
    identity_reference: list[str] | None = None  # List of image file paths
    consent_given: bool = Field(default=False)  # Required if identity_reference provided

    class Config:
        extra = "forbid"
```

**Response Schema:**

```python
class GenerateResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    preset_id: str
    estimated_time_seconds: int | None = None
    output_url: str | None = None  # Available when status == "completed"
    error: str | None = None  # Available when status == "failed"
```

**Validation Rules:**

- `preset_id` must exist in preset catalog
- `prompt` is required, 1-2000 characters
- `quality_level` must be one of: "low", "standard", "pro"
- If `identity_reference` provided, `consent_given` must be `True`
- Unknown fields are rejected

### 6.4 Analytics Contract (Must Degrade Gracefully)

**Endpoint:** `GET /api/analytics/*`

**Response Schema:**

```python
class AnalyticsResponse(BaseModel):
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    message: str | None = None  # e.g., "Analytics not configured"
```

**Degradation Strategy:**

- If analytics service unavailable: Return `{"ok": False, "message": "Analytics not configured", "data": null}`
- **Never hard-500 the UI:** Always return 200 with `ok: false`
- Frontend shows "Not configured" message instead of error

### 6.5 Model Manager Operations Contract

**Endpoint:** `POST /api/models/custom`, `GET /api/models/catalog`, etc.

**Request Schema (Add Custom Model):**

```python
class AddCustomModelRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: Literal["checkpoint", "lora", "embedding", "controlnet", "other"]
    url: str = Field(..., pattern=r"^https?://")  # Must be http/https
    filename: str = Field(..., min_length=1)
    license: Literal["MIT", "Apache 2.0", "CC0", "Custom", "Unknown"]
    sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")  # 64-char hex
    tags: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=1000)

    class Config:
        extra = "forbid"
```

**Validation Rules:**

- `url` must start with `http://` or `https://`
- `sha256` must be 64-character hex string (if provided)
- `license` must be one of allowed values
- Unknown fields are rejected

### 6.6 "Contract Mismatch" Error Category

**Error Code:** `CONTRACT_MISMATCH` (already defined in `error_taxonomy.py`)

**When to Use:**

- Request body doesn't match schema (422 validation error)
- Missing required fields
- Invalid field types
- Unknown fields (if `extra = "forbid"`)

**User-Facing Message:**

```
"The request format doesn't match the API contract.
Check the API documentation for the correct format.
Field 'xyz' is invalid: [specific error]"
```

**UI Display:**

- Show error message with "Copy details" button
- Show remediation steps from `REMEDIATION_STEPS[ErrorCode.CONTRACT_MISMATCH]`
- Highlight invalid fields in form (if applicable)

---

## 7. Catalog Design (Curated + User)

### 7.1 Curated Catalog Entries

**Location:** `backend/app/services/model_manager.py` (already exists, enhance)

**Required Fields:**

- `id`: Unique identifier (e.g., `"sdxl-base-1.0"`)
- `name`: Human-readable name
- `type`: Model type (`"checkpoint"`, `"lora"`, etc.)
- `size_mb`: File size in megabytes (if known)
- `license`: License type (`"MIT"`, `"Apache 2.0"`, `"CC0"`, etc.)
- `source`: Source URL (HuggingFace, CivitAI, etc.)
- `checksum`: SHA256 checksum (required for curated entries)
- `recommended_use`: Description of when to use this model
- `hardware_notes`: GPU/RAM requirements (if relevant)

**Example:**

```python
CatalogModel(
    id="sdxl-base-1.0",
    name="SDXL Base 1.0",
    type="checkpoint",
    tier=1,
    tags=["sdxl", "base", "photoreal"],
    url="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
    filename="sd_xl_base_1.0.safetensors",
    size_mb=6939,
    sha256="abc123...",  # REQUIRED for curated
    license="MIT",
    source="HuggingFace",
    recommended_use="High quality, versatile. Recommended for most use cases.",
    hardware_notes="Requires 8GB+ VRAM for inference.",
)
```

**No Placeholders:**

- If a curated entry is only an example, label it `"Example"` in name
- Do not show as "recommended" by default if it's just an example
- All curated entries must have valid `url`, `checksum`, and `license`

### 7.2 User Catalog Entries

**Required Fields:**

- Same as curated, but:
  - `license` can be `"Unknown"` (with acknowledgment)
  - `checksum` is optional (with warning)

**Validation Rules:**

- If `license == "Unknown"`: Require explicit acknowledgment
- If `checksum` missing: Show warning "Download at your risk" (user must acknowledge)
- User entries are prefixed with `"custom-"` in ID

**Storage:**

- Saved to `config_dir() / "custom_models.json"` (already implemented)

### 7.3 Catalog API Endpoints

**Already Exists:**

- `GET /api/models/catalog` → List all models (curated + custom)
- `POST /api/models/custom` → Add custom model
- `GET /api/models/custom` → List custom models only

**Enhancements Needed:**

- Add `license` field to schema (if not already present)
- Add `recommended_use` and `hardware_notes` fields
- Validate `checksum` format (64-char hex)
- Require acknowledgment for unknown license/missing checksum

---

## 8. Reliability & Observability

### 8.1 Run History Structure

**Location:** `backend/app/models/job_history.py` (new)

**Schema:**

```python
class JobHistory(BaseModel):
    job_id: str
    preset_id: str
    user_id: str | None
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    inputs: dict[str, Any]  # Preset inputs (secrets redacted)
    outputs: dict[str, Any]  # Output artifacts (paths/URLs)
    engine_used: str | None  # Engine adapter ID
    quality_level: str
    credit_cost: int
    error: str | None
    error_code: str | None  # From ErrorCode enum
    remediation: list[str] | None  # From REMEDIATION_STEPS
    logs: list[str] = []  # Log entries (secrets redacted)
```

**Storage:**

- **MVP:** JSON files in `data_dir() / "jobs" / {job_id}.json`
- **Future:** Database table

**API Endpoint:**

```
GET /api/jobs/{job_id}
Response: JobHistory dict
```

### 8.2 Logs Per Run (Redacted Secrets)

**Location:** `backend/app/services/job_logger.py` (new)

**Function:**

```python
def log_job_event(
    job_id: str,
    level: str,  # "info", "warning", "error"
    message: str,
    metadata: dict[str, Any] = {},
) -> None:
    """Log job event with secret redaction."""
    # Redact secrets from metadata
    redacted = redact_secrets(metadata)
    # Append to job log file
    # Format: JSONL (one JSON object per line)
```

**Redaction Rules:**

- API keys: `api_key=***REDACTED***`
- Tokens: `token=***REDACTED***`
- Passwords: `password=***REDACTED***`

**Log File:**

- `data_dir() / "jobs" / {job_id} / "logs.jsonl"`

### 8.3 Error Taxonomy (Extended)

**Location:** `backend/app/core/error_taxonomy.py` (already exists, extend)

**Additional Error Codes Needed:**

- `LICENSE_UNKNOWN`: User added model with unknown license
- `CHECKSUM_MISSING`: User added model without checksum
- `CONSENT_MISSING`: Identity-based workflow without consent
- `INSUFFICIENT_FUNDS`: Not enough credits for job
- `ENGINE_TIMEOUT`: Engine didn't respond in time
- `SAFETY_FILTER`: Provider blocked prompt (NSFW/violence)

**Add to `ErrorCode` enum:**

```python
class ErrorCode(str, Enum):
    # ... existing codes ...
    LICENSE_UNKNOWN = "LICENSE_UNKNOWN"
    CHECKSUM_MISSING = "CHECKSUM_MISSING"
    CONSENT_MISSING = "CONSENT_MISSING"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    ENGINE_TIMEOUT = "ENGINE_TIMEOUT"
    SAFETY_FILTER = "SAFETY_FILTER"
```

**Add Remediation Steps:**

```python
REMEDIATION_STEPS[ErrorCode.LICENSE_UNKNOWN] = [
    "Model has unknown license. Verify license before using.",
    "If unsure, contact model creator or use a different model.",
]

REMEDIATION_STEPS[ErrorCode.CONSENT_MISSING] = [
    "Identity-based workflows require consent.",
    "Check the 'I have permission to use this face' checkbox.",
]

REMEDIATION_STEPS[ErrorCode.INSUFFICIENT_FUNDS] = [
    "Not enough credits for this operation.",
    "Upgrade your plan or use a local engine (free).",
    "Check your credit balance in Settings.",
]
```

### 8.4 User-Facing Remediation Copy Standards

**Format:**

1. **Clear problem statement:** "ComfyUI is not running."
2. **Actionable steps:** "Click 'Start ComfyUI' in Setup."
3. **Alternative options:** "Or use a remote engine (add API key)."
4. **"Copy details" button:** Shows full error + logs (secrets redacted)

**Example:**

```json
{
  "error": "ENGINE_OFFLINE",
  "message": "ComfyUI is not running.",
  "remediation": [
    "Install ComfyUI if not installed: Use the 'Install ComfyUI' button",
    "Start ComfyUI if installed: Use the 'Start ComfyUI' button",
    "Check that ComfyUI is accessible at the configured URL"
  ],
  "detail": "Connection refused: localhost:8188",
  "copy_details": "Full error details available (click 'Copy details' button)"
}
```

### 8.5 "Copy Details" Button

**UI Component:** Button in error message

**Action:** Copies to clipboard:

```
Error: ENGINE_OFFLINE
Message: ComfyUI is not running.
Detail: Connection refused: localhost:8188
Job ID: abc123
Timestamp: 2025-01-27T10:00:00Z
Logs: [last 10 lines, secrets redacted]
```

---

## 9. Security & Compliance

### 9.1 API Key Handling Rules

**Storage:**

- **MVP:** `.env` file with `AINFLUENCER_PROVIDER_{PROVIDER_ID}_API_KEY=...`
- **Production:** Encrypted vault (AWS Secrets Manager, HashiCorp Vault)

**Access:**

- Only backend services can read API keys
- Never expose keys in API responses
- Never log keys (always redact)

**Rotation:**

- User can update API key in Setup Hub
- Old key is immediately invalidated

### 9.2 Download Verification Rules

**Checksum Verification:**

- If `sha256` provided: Compute hash after download, verify match
- If mismatch: Delete file, return `CHECKSUM_MISMATCH` error

**URL Validation:**

- Only `http://` and `https://` URLs allowed
- No `file://`, `ftp://`, or other protocols
- Validate URL format before download

**File Type Validation:**

- Check file extension matches expected type (`.safetensors`, `.ckpt`, etc.)
- Reject executable files (`.exe`, `.sh`, `.bat`)

### 9.3 No Executing Untrusted Scripts

**Rule:** System never executes user-provided scripts or code.

**Allowed Operations:**

- Download model files (`.safetensors`, `.ckpt`, etc.)
- Load models into ComfyUI (via API)
- Run ComfyUI workflows (via API)

**Forbidden Operations:**

- Execute Python scripts from user URLs
- Run shell commands from user input
- Install packages from user-provided requirements.txt

### 9.4 Sandboxing Assumptions

**Local Engines:**

- ComfyUI runs in separate process (already implemented)
- Python scripts run in dedicated `venv` (if applicable)

**Remote APIs:**

- All requests go through HTTPS
- No local code execution from remote responses

**File System:**

- All user files stored in `data_dir()` (isolated from system)
- No access to system directories

### 9.5 Consent Checkbox for Identity-Based Operations

**UI Component:** Checkbox in preset form

**Label:** "I have permission to use this face/identity for generation"

**Validation:**

- Required if `identity_reference` is provided
- Backend rejects request if `consent_given: false` and `identity_reference` provided

**Storage:**

- Consent status stored in job history
- Can be audited for compliance

**Ethics Checklist Section:**

Add to Setup Hub or Preset selection:

```
Ethics & Safety Checklist

☐ I have permission to use any faces/identities in my content
☐ I understand that AI-generated content may be detected as synthetic
☐ I will not use this tool to create misleading or harmful content
☐ I have read and agree to the Terms of Service

[Required for identity-based workflows]
```

---

## 10. Phased Roadmap (No Scope Creep)

### Phase 0: Spec + Contracts + UX States

**Duration:** 1-2 days

**Deliverables:**

- ✅ This specification document (complete)
- Data contract schemas (Pydantic models)
- UX mockups/wireframes for Setup Hub
- Error taxonomy extensions

**Acceptance Criteria:**

- [ ] All schemas defined in code (even if not used yet)
- [ ] Error codes added to taxonomy
- [ ] UX flow documented

**Smoke Tests:**

- [ ] Schemas validate correctly (test with sample data)
- [ ] Error taxonomy covers all failure modes

### Phase 1: One Local Engine (ComfyUI) + 3 Presets End-to-End

**Duration:** 3-5 days

**Deliverables:**

- `LocalComfyAdapter` implementing `EngineAdapter` interface
- `PipelineManager` (basic, synchronous)
- 3 presets: Photoreal Portrait, Cinematic Portrait, Identity Lock Portrait
- Preset execution API endpoint
- Job history (basic, file-based)

**Acceptance Criteria:**

- [ ] User can select preset and generate image
- [ ] Job status is tracked
- [ ] Output appears in gallery
- [ ] Errors show user-friendly messages (not 500)

**Smoke Tests:**

- [ ] Setup: ComfyUI detected or clear CTA to install
- [ ] Generate: No 422 errors
- [ ] If engine missing: UI blocks with CTA (not server error)
- [ ] Job history: Can view past runs

### Phase 2: Provider Adapter Framework + Remote Provider Connect (BYOK)

**Duration:** 5-7 days

**Deliverables:**

- `ProviderRegistry` service
- `KlingAdapter` (or one remote adapter as proof-of-concept)
- Setup Hub page (Connect Provider cards)
- API key storage and testing
- Healthcheck matrix

**Acceptance Criteria:**

- [ ] User can add API key for remote provider
- [ ] System tests connection and shows balance
- [ ] User can select remote engine in preset
- [ ] Remote generation works end-to-end

**Smoke Tests:**

- [ ] Auth: Add Kling key, system shows correct balance
- [ ] Generate: Run preset with remote engine, image appears
- [ ] Fail: Bad API key shows "Auth Failed" (not 500)

### Phase 3: Model Catalog + Checksum Downloader

**Duration:** 3-4 days

**Deliverables:**

- Enhanced model catalog (license, checksum, recommended use)
- "Add Model Source" form with safety gates
- Checksum verification on download
- User acknowledgment for unknown license/missing checksum

**Acceptance Criteria:**

- [ ] User can add custom model with URL
- [ ] System warns if checksum missing
- [ ] System verifies checksum after download
- [ ] Unknown license requires acknowledgment

**Smoke Tests:**

- [ ] Safe URL: Model added successfully
- [ ] Risky URL: System warns user before downloading
- [ ] Checksum: Mismatch detected and file deleted

### Phase 4: More Presets + Quality Pipelines

**Duration:** 7-10 days

**Deliverables:**

- Remaining 9 presets (video, lipsync, upscale, etc.)
- Multi-step pipeline orchestration
- Quality level support (Low/Standard/Pro)
- Credit ledger (basic)

**Acceptance Criteria:**

- [ ] All 12 presets available and working
- [ ] User can select quality level
- [ ] Multi-step pipelines execute correctly
- [ ] Credit costs calculated and deducted

**Smoke Tests:**

- [ ] Video preset: Image → Video works
- [ ] Lip-sync preset: Video + Audio → Lip-sync works
- [ ] Multi-step: Image → Video → Lip-sync → Upscale works
- [ ] Credits: Balance decreases after job

---

## 11. Smoke Test Matrix

### 11.1 Setup Tests

| Test                 | Pass Criteria                                        |
| :------------------- | :--------------------------------------------------- |
| **Engine Detection** | ComfyUI detected OR clear CTA to install (not error) |
| **Provider Connect** | Add API key → System shows balance from API          |
| **Healthcheck**      | All engines show status (running/connected/error)    |

### 11.2 Create Tests

| Test                 | Pass Criteria                                    |
| :------------------- | :----------------------------------------------- |
| **Create Character** | Endpoints work without friction (no random 401)  |
| **Add Custom Model** | Model added with safety warnings (if applicable) |

### 11.3 Generate Tests

| Test               | Pass Criteria                                           |
| :----------------- | :------------------------------------------------------ |
| **No 422 Errors**  | All requests validate correctly (no schema drift)       |
| **Engine Missing** | UI blocks with CTA (not server error)                   |
| **Output Appears** | Generated image/video appears in gallery within timeout |
| **Job History**    | Past runs visible in job history                        |

### 11.4 Analytics Tests

| Test                     | Pass Criteria                                                 |
| :----------------------- | :------------------------------------------------------------ |
| **Never Hard-500s**      | Analytics unavailable → Shows "Not configured" (200 response) |
| **Graceful Degradation** | UI shows message instead of error                             |

### 11.5 Navigation Tests

| Test                     | Pass Criteria                               |
| :----------------------- | :------------------------------------------ |
| **No Broken Links**      | All nav links work (no 404)                 |
| **Setup Hub Accessible** | `/setup` page loads and shows engine status |

### 11.6 Error Handling Tests

| Test                       | Pass Criteria                                           |
| :------------------------- | :------------------------------------------------------ |
| **User-Friendly Messages** | Errors show remediation steps (not stack traces)        |
| **Copy Details**           | "Copy details" button works (secrets redacted)          |
| **Consent Validation**     | Identity workflow without consent → Clear error message |

---

## Appendix A: Assumptions & TODOs

### Assumptions (Require Verification)

1. **Provider API Endpoints:**

   - Kling API: `https://api.klingai.com/v1` (ASSUMED)
   - Fal API: `https://fal.ai/api/v1` (ASSUMED)
   - Runware API: `https://api.runware.ai/v1` (ASSUMED)
   - SyncLabs API: `https://api.synclabs.ai/v1` (ASSUMED)
   - **TODO:** Verify actual endpoints and authentication methods

2. **Provider API Contracts:**

   - Request/response formats (ASSUMED)
   - **TODO:** Read provider documentation and test with sandbox keys

3. **Credit Costs:**

   - Pricing table in Section 2.1.6 (ASSUMED)
   - **TODO:** Verify actual pricing from provider APIs

4. **Anti-Plastic Prompt Engineering:**

   - Prompt templates in presets (ASSUMED)
   - **TODO:** Test and refine prompts during implementation

5. **ComfyUI Extensions:**

   - IP-Adapter, InstantID, FaceDetailer nodes (ASSUMED)
   - **TODO:** Verify extensions exist and node class names

6. **Post-Processing Implementation:**
   - Film grain, tone mapping, color grading (ASSUMED)
   - **TODO:** Implement or verify workflow nodes

### Verification Steps

For each assumption, during implementation:

1. Read official provider documentation
2. Test with sandbox/test API keys
3. Update code with actual contracts
4. Document any discrepancies in code comments

---

## Appendix B: Entrypoint Unchanged

**CRITICAL:** The entrypoint `node scripts/one.mjs` remains unchanged. This specification is planning only. No changes to startup scripts.

---

**END OF SPECIFICATION**

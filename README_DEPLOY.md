# Deployment (Free-Tier Friendly)

This repo is heavy on GPU for real generations. Free tiers can host the UI and a CPU-only/demo backend. Below are pragmatic paths.

## Stack Snapshot
- Frontend: Next.js 16 (app router), TypeScript, Tailwind.
- Backend: FastAPI (Python 3.11), ComfyUI client, SQLite by default.
- Runtime ports: frontend 3000, backend 8000, ComfyUI 8188.

## Environment Variables
Copy `env.example` to `.env` (or configure in platform settings):

- Frontend: `NEXT_PUBLIC_API_URL`, `BACKEND_URL`, `NEXT_PUBLIC_COMFYUI_URL`, `COMFYUI_URL`
- Backend: `API_HOST`, `API_PORT`, `ALLOWED_ORIGINS`, `COMFYUI_SERVER`, `DATABASE_URL`
- Safety: `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_PER_HOUR`, `MAX_REQUEST_SIZE_MB`, `MAX_CONCURRENT_JOBS`
- Optional: `REDIS_URL`, `REDIS_PASSWORD`, `HIVE_API_KEY`, `SENSITY_API_KEY`, `AI_OR_NOT_API_KEY`

**Local dev, Windows-friendly defaults (keeps public vs server split sane):**
- Copy `backend/env.example` → `backend/.env`
- Copy `web/env.local.example` → `web/.env.local` (or set `NEXT_PUBLIC_*` in root `.env`)
- Both mirror the PowerShell session defaults and stay in demo-safe mode by default.

## Primary Free Plan (Recommended)
**Frontend on Vercel Hobby, Backend on Render Free Web Service (CPU).**

### Frontend: Vercel
1. Import repo in Vercel.
2. Set project root to `web`.
3. Build command: `npm run build`
4. Output: `.next`
5. Env vars:
   ```
   NEXT_PUBLIC_API_URL=https://<render-backend>.onrender.com
   BACKEND_URL=https://<render-backend>.onrender.com
   NEXT_PUBLIC_COMFYUI_URL=http://localhost:8188
   NEXT_PUBLIC_DEMO_MODE=true
   NEXT_PUBLIC_ENABLE_ADVANCED=false
   NEXT_PUBLIC_ENABLE_UPSCALE=false
   NEXT_PUBLIC_ENABLE_FACE_RESTORE=false
   NEXT_PUBLIC_ENABLE_BATCH=false
   NEXT_PUBLIC_ENABLE_HIGH_RES=false
   NEXT_PUBLIC_DEMO_MAX_WIDTH=1024
   NEXT_PUBLIC_DEMO_MAX_HEIGHT=1024
   NEXT_PUBLIC_DEMO_MAX_BATCH=1
   ```
6. Deploy. Use Vercel domains in `ALLOWED_ORIGINS` on backend.

### Backend: Render Free
1. Connect repo in Render → New Web Service.
2. Root: `/` ; Workdir: `backend`.
3. Runtime: Python 3.11, Build: `pip install --no-cache-dir -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Env vars:
   ```
   API_HOST=0.0.0.0
   API_PORT=8000
   ALLOWED_ORIGINS=https://<your-vercel-domain>
   MAX_CONCURRENT_JOBS=1
   DEMO_MODE=true
   ENABLE_ADVANCED=false
   ENABLE_UPSCALE=false
   ENABLE_FACE_RESTORE=false
   ENABLE_BATCH=false
   ENABLE_HIGH_RES=false
   DEMO_MAX_WIDTH=1024
   DEMO_MAX_HEIGHT=1024
   DEMO_MAX_BATCH=1
   DATABASE_URL=sqlite:///./ainfluencer.db
   COMFYUI_SERVER=127.0.0.1:8188
   ```
6. Apply the provided `render.yaml` for IaC if preferred.

**Limitations:** Render free instances sleep and use CPU; expect slow/queued generations. Use the UI “Low-resource mode” toggle for fast presets.

## Secondary (Fallback) Plan
**Hugging Face Spaces (CPU) with minimal Gradio/Streamlit wrapper.**

- Create a new Space (Gradio/Streamlit, `Python 3.10+`).
- Copy the backend demo logic or expose a limited demo notebook; use CPU-friendly models.
- Set env vars: `COMFYUI_SERVER` (if reachable) or adapt to a lightweight diffusers model.
- Expect slow performance; cap steps/resolution and enforce `MAX_CONCURRENT_JOBS=1`.

## Local Docker (parity)
```
docker compose -f docker-compose.yml up --build
```
Ensure `COMFYUI` models are available locally; free hosts won’t provide GPU.

## Health Checks
- Backend: `curl -fsSL https://<render-backend>.onrender.com/api/health`
- Local script: `scripts/healthcheck.sh`
- Preflight before deploy: `scripts/deploy-preflight.sh` (or `.ps1` on Windows) to verify envs, build, and imports. Start the backend first if you want `/api/health` to pass; otherwise the preflight will warn (expected for CI-only runs).

## Failure Modes (common)
- Render sleeping: first request cold-starts (20–60s). Retry once.
- CPU timeout/413: increase `REQUEST_TIMEOUT_SECONDS` or reduce steps/resolution (toggle low-resource).
- CORS blocked: ensure `ALLOWED_ORIGINS` matches your Vercel domain.
- Missing models: ComfyUI must have models locally; free plans do not download automatically.

## Paid Upgrade Notes
- Swap Render to paid GPU host (RunPod/Modal/Lambda) and set `NEXT_PUBLIC_API_URL` accordingly.
- Add persistent Postgres/Redis when durability is needed.

## What’s Free vs. Paid GPU
- **Free (CPU tiers):** UI + API reachable, but generation is slow; use low-resource presets, single concurrency, and expect cold starts.
- **Paid GPU:** Required for realistic throughput, higher resolutions/steps, real-time video, and advanced post-processing.


# AInfluencer Push-to-Deploy Automation

## Automated Architecture
- Frontend: Next.js (app router) → deploy via Vercel Hobby using CLI in GitHub Actions. Root `web/`, build `npm run build`, start `next start`.
- Backend: FastAPI → deploy via Render Free Web Service using `render.yaml` + Render Deploy API. Entrypoint `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Demo mode defaults: safe CPU limits, ComfyUI optional. When ComfyUI is unreachable, backend returns HTTP 503 with `COMFYUI_UNAVAILABLE`.
- Single source of truth for env templates: `env.example` (local), `env.deploy.example` (cloud-safe), `web/env.local.example`, `backend/env.example`.

## Required GitHub Secrets (set once)
- Vercel: `VERCEL_TOKEN`, `VERCEL_ORG_ID` (if org scoped), `VERCEL_PROJECT_ID` (if already created).
- Render: `RENDER_API_KEY`, `RENDER_SERVICE_ID`.
- Runtime (mirrors env.deploy.example; set as GitHub secrets for automation and as provider env): `NEXT_PUBLIC_API_URL`, `DEMO_MODE`, `ENABLE_ADVANCED`, `ENABLE_UPSCALE`, `ENABLE_FACE_RESTORE`, `ENABLE_BATCH`, `ENABLE_HIGH_RES`, `DEMO_MAX_WIDTH`, `DEMO_MAX_HEIGHT`, `DEMO_MAX_BATCH`.

## One-Time Bootstrap (minimal manual)
1) Create backend service on Render (free web service) using existing `render.yaml`. Copy its Service ID and generate an API key.  
2) Create frontend project on Vercel (Hobby). Configure project root `/web`.  
3) Run `scripts/bootstrap-deploy.sh` (or `.ps1`) to push secrets into GitHub (requires `gh auth login`). Provide Vercel/Render tokens when prompted. The script also prints a ready-to-copy block if you prefer manual entry.

After these steps, pushing to `main` triggers both deploys automatically.

## How Deploy Automation Works
- Workflow: `.github/workflows/deploy.yml`
  - `preflight` job: builds web, compile-checks backend.
  - `deploy_backend_render`: triggers Render deploy via API using `RENDER_API_KEY` + `RENDER_SERVICE_ID`.
  - `deploy_frontend_vercel`: uses Vercel CLI to build and `vercel deploy --prod` from `/web`.
- Secrets validation: jobs fail fast with explicit missing-secret messages.
- Env consistency: templates in `env.deploy.example`, `web/env.local.example`, `backend/env.example`.

## Unavoidable Manual Steps (kept minimal)
1) Obtain provider tokens (Vercel token, Render API key) and create the initial Vercel project + Render service. Providers do not allow non-interactive project creation with public tokens.  
2) Add the generated IDs/secrets once via `scripts/bootstrap-deploy.(sh|ps1)` (automates `gh secret set` if `gh` is authenticated).

## Demo Mode / Free Tier Notes
- Defaults keep `DEMO_MODE=true`, `ENABLE_*` flags disabled, and batch/size caps to avoid heavy GPU needs.
- ComfyUI not required for UI exploration; when absent, backend responds with 503 and UI should show demo-only behavior.

## Failure Modes & Checks
- Missing secrets: GitHub Actions fails early, listing the exact secret names.
- Render API errors: deploy job surfaces the HTTP response; verify `RENDER_SERVICE_ID` and that the service exists.
- Vercel deploy errors: ensure `VERCEL_TOKEN` has access to the project and env vars are set in Vercel.
- Local build issues: run `scripts/deploy-preflight.sh` (or `.ps1`) to validate env + builds before pushing.

## Render shows “Ruby” (runtime mismatch)
- Root cause: a Render service created with the wrong runtime/commands (UI defaulted to Ruby or root/build/start were not pinned). `render.yaml` already declares Python + `rootDir: backend`; anything else is misconfigured.
- Detection: `scripts/provision-deploy.(sh|ps1)` now refuse to continue if the service env/type/start/build do not look like a Python uvicorn backend and will warn explicitly.

### Plan A (recommended: safest)
1) In Render UI, create a **new Web Service**  
   - Name: `ainfluencer-backend`  
   - Runtime/Env: `python`  
   - Root Directory: `backend`  
   - Build Command: `pip install --no-cache-dir -r requirements.txt`  
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`  
   - Plan: `free`, Region: `oregon`
2) Copy the new `Service ID` into `env.deploy` as `RENDER_SERVICE_ID`.
3) Rerun `scripts/provision-deploy.(sh|ps1)`; it will sync env, set `NEXT_PUBLIC_API_URL`, and trigger deploys.

### Plan B (only if you must reuse the existing service)
1) In Render UI > your service > Settings: set `Root Directory = backend`, `Build Command = pip install --no-cache-dir -r requirements.txt`, `Start Command = uvicorn main:app --host 0.0.0.0 --port $PORT`, Runtime/Env = Python (if editable).  
2) If Runtime cannot be changed (e.g., stuck on Ruby), switch to Plan A.  
3) Set `RENDER_SERVICE_ID` in `env.deploy`, rerun the provision script.

### One-time UI step, then automation
After Plan A/B, the provision script expects only `RENDER_SERVICE_ID` (and tokens). It writes `.deploy/state.json` with `render_backend_service_id|name|url` and fails fast if the service drifts from Python/uvicorn.

## Env sync (Render ↔ Vercel) and CORS
- `NEXT_PUBLIC_API_URL` is mandatory (Next build now fails if missing). The provision script auto-fills it from the Render service URL when possible and syncs it to Render/Vercel.
- `ALLOWED_ORIGINS` should match your Vercel hostname (e.g., `https://<project>.vercel.app`). The script will warn if it cannot infer a value; tighten after you know the domain.
- Demo safety defaults remain: `DEMO_MODE=true`, feature flags off, `MAX_CONCURRENT_JOBS=1`.

## Ultra-short runbook (copy/paste)
1) Create/confirm Render Web Service as above (Python, backend root).  
2) Copy Service ID → put in `env.deploy` (`RENDER_SERVICE_ID=...`).  
3) Ensure tokens in `env.deploy` (`RENDER_API_KEY`, `VERCEL_TOKEN`).  
4) Run `pwsh scripts/provision-deploy.ps1` (or `bash scripts/provision-deploy.sh`).  
5) Push to `main` → GitHub Actions auto-deploys Render + Vercel.

## One-time auth, then one command
1) Authenticate CLIs once:
   - `gh auth login`
   - `vercel login` (and export `VERCEL_TOKEN`)
2) Create tokens:
   - Render: create API key → set `RENDER_API_KEY`
   - Vercel: create token → set `VERCEL_TOKEN` (and optional `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`)
3) Run provisioning (auto-creates/links, syncs envs, triggers first deploy):
   - Bash: `bash scripts/provision-deploy.sh`
   - PowerShell: `pwsh scripts/provision-deploy.ps1`

After this succeeds, `git push origin main` triggers the existing `.github/workflows/deploy.yml` (Render deploy + Vercel deploy).


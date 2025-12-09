# Demo Mode (Free CPU Tiers)

`DEMO_MODE=true` enables a safe, honest public demo when GPU/ComfyUI/models are unavailable or running on free CPU tiers.

## What Demo Mode Does
- Caps resolution to `DEMO_MAX_WIDTH/DEMO_MAX_HEIGHT` (defaults 1024x1024).
- Disables batch sizes > `DEMO_MAX_BATCH` (default 1).
- Blocks heavy options: upscaling, face restoration, and video generation.
- Enforces concurrency cap via `MAX_CONCURRENT_JOBS` (default 1).
- UI auto-enables Low-resource mode and shows a CPU-tier banner.
- If ComfyUI is unreachable, generation endpoints return `503 COMFYUI_UNAVAILABLE` with a friendly message.

## Enabling Full Features
- Deploy on a GPU host with ComfyUI and models available.
- Set `DEMO_MODE=false` and relax flags:
  - `ENABLE_ADVANCED`, `ENABLE_UPSCALE`, `ENABLE_FACE_RESTORE`, `ENABLE_BATCH`, `ENABLE_HIGH_RES`
  - Increase `DEMO_MAX_WIDTH/HEIGHT` and `DEMO_MAX_BATCH` as appropriate.
- Ensure `COMFYUI_SERVER` points to a reachable ComfyUI instance.

## Recommended Free-Tier Settings
```
DEMO_MODE=true
MAX_CONCURRENT_JOBS=1
ENABLE_UPSCALE=false
ENABLE_FACE_RESTORE=false
ENABLE_BATCH=false
ENABLE_HIGH_RES=false
DEMO_MAX_WIDTH=1024
DEMO_MAX_HEIGHT=1024
DEMO_MAX_BATCH=1
```

For frontend (Vercel) mirror with `NEXT_PUBLIC_DEMO_MODE` and the corresponding `NEXT_PUBLIC_ENABLE_*` flags.


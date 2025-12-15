from __future__ import annotations

import io
import json
import zipfile

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.paths import images_dir
from app.services.generation_service import generation_service

router = APIRouter()


class GenerateImageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    negative_prompt: str | None = Field(default=None, max_length=2000)
    seed: int | None = None
    checkpoint: str | None = Field(default=None, max_length=512)
    width: int = Field(default=1024, ge=256, le=4096)
    height: int = Field(default=1024, ge=256, le=4096)
    steps: int = Field(default=25, ge=1, le=200)
    cfg: float = Field(default=7.0, ge=0.0, le=30.0)
    sampler_name: str = Field(default="euler", max_length=64)
    scheduler: str = Field(default="normal", max_length=64)
    batch_size: int = Field(default=1, ge=1, le=8)


@router.post("/image")
def generate_image(req: GenerateImageRequest) -> dict:
    job = generation_service.create_image_job(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        seed=req.seed,
        checkpoint=req.checkpoint,
        width=req.width,
        height=req.height,
        steps=req.steps,
        cfg=req.cfg,
        sampler_name=req.sampler_name,
        scheduler=req.scheduler,
        batch_size=req.batch_size,
    )
    return {"ok": True, "job": job.__dict__}


@router.get("/image/{job_id}")
def get_image_job(job_id: str) -> dict:
    job = generation_service.get_job(job_id)
    if not job:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "job": job.__dict__}


@router.get("/image/jobs")
def list_image_jobs() -> dict:
    return {"items": generation_service.list_jobs(limit=100)}


@router.post("/image/{job_id}/cancel")
def cancel_image_job(job_id: str) -> dict:
    ok = generation_service.request_cancel(job_id)
    return {"ok": ok}


@router.get("/image/{job_id}/download")
def download_image_job_bundle(job_id: str):
    job = generation_service.get_job(job_id)
    if not job:
        return {"ok": False, "error": "not_found"}

    files = job.image_paths or ([job.image_path] if job.image_path else [])
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        meta = {
            "id": job.id,
            "state": job.state,
            "message": job.message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "cancelled_at": job.cancelled_at,
            "params": job.params,
            "images": files,
        }
        zf.writestr("metadata.json", json.dumps(meta, indent=2, sort_keys=True))

        for name in files:
            if not name:
                continue
            p = images_dir() / name
            if p.exists():
                zf.write(p, arcname=f"images/{name}")

    mem.seek(0)
    filename = f"ainfluencer-job-{job_id}.zip"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(mem, media_type="application/zip", headers=headers)


@router.get("/storage")
def storage() -> dict:
    return generation_service.storage_stats()


@router.delete("/image/{job_id}")
def delete_image_job(job_id: str) -> dict:
    ok = generation_service.delete_job(job_id, delete_images=True)
    return {"ok": ok}


@router.post("/clear")
def clear_all() -> dict:
    return generation_service.clear_all(delete_images=True)


# Workflow presets
WORKFLOW_PRESETS = [
    {
        "id": "portrait",
        "name": "Portrait",
        "description": "High-quality portrait photography with focus on face and character",
        "defaults": {
            "width": 1024,
            "height": 1024,
            "steps": 30,
            "cfg": 7.5,
            "sampler_name": "euler",
            "scheduler": "normal",
            "batch_size": 1,
            "negative_prompt": "blurry, low quality, distorted face, bad anatomy, deformed, ugly, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, poorly drawn feet, long neck, cross-eyed, mutated eyes, bad anatomy, bad proportions, gross proportions, text, error, missing fingers, missing arms, missing legs, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name",
        },
    },
    {
        "id": "fashion",
        "name": "Fashion",
        "description": "Fashion photography with emphasis on clothing and style",
        "defaults": {
            "width": 1024,
            "height": 1536,
            "steps": 30,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "batch_size": 1,
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, deformed, ugly, disfigured, poorly drawn, mutation, mutated, extra limb, ugly, poorly drawn hands, poorly drawn feet, bad anatomy, bad proportions, gross proportions, text, error, missing fingers, missing arms, missing legs, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name",
        },
    },
    {
        "id": "product",
        "name": "Product",
        "description": "Product photography with clean backgrounds and professional lighting",
        "defaults": {
            "width": 1024,
            "height": 1024,
            "steps": 25,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "batch_size": 1,
            "negative_prompt": "blurry, low quality, distorted, bad lighting, shadows, reflections, background clutter, text, watermark, signature, username, artist name, people, human",
        },
    },
    {
        "id": "landscape",
        "name": "Landscape",
        "description": "Scenic landscape photography with natural environments",
        "defaults": {
            "width": 1536,
            "height": 1024,
            "steps": 30,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "batch_size": 1,
            "negative_prompt": "blurry, low quality, distorted, people, human, face, portrait, text, watermark, signature, username, artist name, buildings, urban",
        },
    },
    {
        "id": "cinematic",
        "name": "Cinematic",
        "description": "Cinematic style with dramatic lighting and composition",
        "defaults": {
            "width": 1024,
            "height": 1024,
            "steps": 35,
            "cfg": 8.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "batch_size": 1,
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, deformed, ugly, disfigured, poorly drawn, mutation, mutated, extra limb, ugly, poorly drawn hands, poorly drawn feet, bad anatomy, bad proportions, gross proportions, text, error, missing fingers, missing arms, missing legs, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, amateur, snapshot",
        },
    },
    {
        "id": "artistic",
        "name": "Artistic",
        "description": "Artistic and creative style with enhanced visual appeal",
        "defaults": {
            "width": 1024,
            "height": 1024,
            "steps": 30,
            "cfg": 7.5,
            "sampler_name": "euler",
            "scheduler": "normal",
            "batch_size": 1,
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, deformed, ugly, disfigured, poorly drawn, mutation, mutated, extra limb, ugly, poorly drawn hands, poorly drawn feet, bad anatomy, bad proportions, gross proportions, text, error, missing fingers, missing arms, missing legs, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name",
        },
    },
]


@router.get("/workflow-presets")
def list_workflow_presets() -> dict:
    """List all available workflow presets."""
    return {"ok": True, "presets": WORKFLOW_PRESETS}


@router.get("/workflow-presets/{preset_id}")
def get_workflow_preset(preset_id: str) -> dict:
    """Get a specific workflow preset by ID."""
    preset = next((p for p in WORKFLOW_PRESETS if p["id"] == preset_id), None)
    if not preset:
        return {"ok": False, "error": "preset_not_found"}
    return {"ok": True, "preset": preset}

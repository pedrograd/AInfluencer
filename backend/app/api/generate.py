from __future__ import annotations

import io
import json
import zipfile
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.paths import images_dir
from app.services.generation_service import generation_service
from app.services.text_generation_service import (
    TextGenerationRequest,
    text_generation_service,
)

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


class GenerateTextRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=5000)
    model: str = Field(default="llama3:8b", max_length=128)
    character_id: str | None = Field(default=None, max_length=128)
    character_persona: dict[str, Any] | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=8192)
    system_prompt: str | None = Field(default=None, max_length=2000)


@router.post("/text")
def generate_text(req: GenerateTextRequest) -> dict:
    """
    Generate text using Ollama.

    Generates text content using the specified LLM model with optional
    character persona injection for personality-consistent content.
    """
    try:
        request = TextGenerationRequest(
            prompt=req.prompt,
            model=req.model,
            character_id=req.character_id,
            character_persona=req.character_persona,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            system_prompt=req.system_prompt,
        )
        result = text_generation_service.generate_text(request)
        return {
            "ok": True,
            "text": result.text,
            "model": result.model,
            "prompt": result.prompt,
            "tokens_generated": result.tokens_generated,
            "generation_time_seconds": result.generation_time_seconds,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/text/models")
def list_text_models() -> dict:
    """List available Ollama models."""
    try:
        models = text_generation_service.list_models()
        return {"ok": True, "models": models}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/text/health")
def text_generation_health() -> dict:
    """Check Ollama service health."""
    health = text_generation_service.check_health()
    return {"ok": health.get("status") == "healthy", **health}

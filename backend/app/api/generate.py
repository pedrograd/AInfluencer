from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

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

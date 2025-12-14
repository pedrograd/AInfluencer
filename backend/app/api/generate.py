from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.generation_service import generation_service

router = APIRouter()


class GenerateImageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    negative_prompt: str | None = Field(default=None, max_length=2000)
    seed: int | None = None


@router.post("/image")
def generate_image(req: GenerateImageRequest) -> dict:
    job = generation_service.create_image_job(prompt=req.prompt, negative_prompt=req.negative_prompt, seed=req.seed)
    return {"ok": True, "job": job.__dict__}


@router.get("/image/{job_id}")
def get_image_job(job_id: str) -> dict:
    job = generation_service.get_job(job_id)
    if not job:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "job": job.__dict__}

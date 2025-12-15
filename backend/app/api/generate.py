"""Content generation API endpoints for images and text.

This module provides API endpoints for generating content including:
- Image generation using ComfyUI with configurable parameters
- Text generation using Ollama with character persona integration
- Job status tracking and result retrieval
- Batch download of generated content
"""

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
    """Request model for image generation with prompt and generation parameters."""

    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt describing the image to generate (1-2000 characters)")
    negative_prompt: str | None = Field(default=None, max_length=2000, description="Negative prompt describing what to avoid (optional, max 2000 characters)")
    seed: int | None = Field(default=None, description="Random seed for reproducibility (optional)")
    checkpoint: str | None = Field(default=None, max_length=512, description="Checkpoint model name override (optional, uses default if not specified)")
    width: int = Field(default=1024, ge=256, le=4096, description="Image width in pixels (256-4096, default: 1024)")
    height: int = Field(default=1024, ge=256, le=4096, description="Image height in pixels (256-4096, default: 1024)")
    steps: int = Field(default=25, ge=1, le=200, description="Number of sampling steps (1-200, default: 25)")
    cfg: float = Field(default=7.0, ge=0.0, le=30.0, description="Classifier-free guidance scale (0.0-30.0, default: 7.0)")
    sampler_name: str = Field(default="euler", max_length=64, description="Sampler algorithm name (e.g., 'euler', 'dpmpp_2m', 'ddim', default: 'euler')")
    scheduler: str = Field(default="normal", max_length=64, description="Scheduler name (e.g., 'normal', 'karras', 'exponential', default: 'normal')")
    batch_size: int = Field(default=1, ge=1, le=8, description="Number of images to generate in this batch (1-8, default: 1)")


@router.post("/image")
def generate_image(req: GenerateImageRequest) -> dict:
    """
    Generate an image using ComfyUI.
    
    Creates an image generation job with the specified parameters.
    The job is processed asynchronously and can be checked via GET /api/generate/image/{job_id}.
    
    Args:
        req: Image generation request with prompt, dimensions, and generation parameters
        
    Returns:
        dict: Response with job information including job ID and state
    """
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
    """
    Get image generation job status.
    
    Retrieves the current status and results of an image generation job.
    
    Args:
        job_id: Unique identifier for the generation job
        
    Returns:
        dict: Job information including state, image paths, and metadata.
            On success: {"ok": True, "job": {...}}
            On not found: {"ok": False, "error": "not_found"}
    """
    job = generation_service.get_job(job_id)
    if not job:
        return {"ok": False, "error": "not_found", "message": f"Image generation job '{job_id}' not found"}
    return {"ok": True, "job": job.__dict__}


@router.get("/image/jobs")
def list_image_jobs() -> dict:
    """
    List recent image generation jobs.
    
    Returns a list of the most recent image generation jobs (up to 100).
    
    Returns:
        dict: List of job items with their status and metadata
    """
    return {"items": generation_service.list_jobs(limit=100)}


@router.post("/image/{job_id}/cancel")
def cancel_image_job(job_id: str) -> dict:
    """
    Cancel a running image generation job.
    
    Requests cancellation of an in-progress image generation job.
    The job may not cancel immediately if generation has already started.
    
    Args:
        job_id: Unique identifier for the generation job to cancel
        
    Returns:
        dict: Success status of the cancel request
    """
    ok = generation_service.request_cancel(job_id)
    return {"ok": ok}


@router.get("/image/{job_id}/download")
def download_image_job_bundle(job_id: str):
    """
    Download image generation job results as ZIP bundle.
    
    Downloads all generated images and metadata for a completed job as a ZIP file.
    
    Args:
        job_id: Unique identifier for the generation job
        
    Returns:
        StreamingResponse: ZIP file containing images and metadata.json
    """
    job = generation_service.get_job(job_id)
    if not job:
        return {"ok": False, "error": "not_found", "message": f"Image generation job '{job_id}' not found"}

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
    """
    Get storage statistics for generated images.
    
    Returns information about stored images including count and total size.
    
    Returns:
        dict: Storage statistics with image count and total bytes
    """
    return generation_service.storage_stats()


@router.delete("/image/{job_id}")
def delete_image_job(job_id: str) -> dict:
    """
    Delete an image generation job and its associated images.
    
    Permanently deletes a job record and all generated image files.
    
    Args:
        job_id: Unique identifier for the generation job to delete
        
    Returns:
        dict: Success status of the deletion
    """
    ok = generation_service.delete_job(job_id, delete_images=True)
    return {"ok": ok}


@router.post("/clear")
def clear_all() -> dict:
    """
    Clear all image generation jobs and stored images.
    
    Permanently deletes all job records and generated image files.
    Use with caution as this operation cannot be undone.
    
    Returns:
        dict: Summary of cleared items (jobs and images deleted)
    """
    return generation_service.clear_all(delete_images=True)


class GenerateTextRequest(BaseModel):
    """Request model for text generation with character persona support."""

    prompt: str = Field(..., min_length=1, max_length=5000, description="Text prompt for generation (1-5000 characters)")
    model: str = Field(default="llama3:8b", max_length=128, description="Ollama model name (default: 'llama3:8b')")
    character_id: str | None = Field(default=None, max_length=128, description="Character ID to apply persona from (optional)")
    character_persona: dict[str, Any] | None = Field(default=None, description="Character persona dictionary to inject (optional, overrides character_id if provided)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature for text generation (0.0-2.0, default: 0.7)")
    max_tokens: int | None = Field(default=None, ge=1, le=8192, description="Maximum number of tokens to generate (1-8192, optional)")
    system_prompt: str | None = Field(default=None, max_length=2000, description="System prompt override (optional, max 2000 characters)")


@router.post("/text")
def generate_text(req: GenerateTextRequest) -> dict:
    """
    Generate text using Ollama.

    Generates text content using the specified LLM model with optional
    character persona injection for personality-consistent content.
    
    Args:
        req: Text generation request with prompt, model, and optional character persona
        
    Returns:
        dict: Response with generated text and metadata.
            On success: {"ok": True, "text": "...", "model": "...", ...}
            On error: {"ok": False, "error": "error message"}
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
        return {"ok": False, "error": str(exc), "message": f"Text generation failed: {str(exc)}"}


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

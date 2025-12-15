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
    """Request model for image generation with prompt and generation parameters.
    
    Supports both single image generation (batch_size=1) and batch generation
    (batch_size=2-8). For batch generation, all images are generated in a single
    ComfyUI workflow execution and returned in the job's image_paths array.
    
    For +18/NSFW content generation, set is_nsfw=True. This will modify prompts
    appropriately for adult content platforms (OnlyFans, Telegram, etc.).
    """

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
    batch_size: int = Field(default=1, ge=1, le=8, description="Number of images to generate in this batch (1-8, default: 1). For batch_size > 1, all images are generated in a single workflow execution and returned in job.image_paths array.")
    is_nsfw: bool = Field(default=False, description="Whether to generate +18/NSFW content (default: False). When True, prompts are modified for adult content platforms.")
    face_image_path: str | None = Field(default=None, max_length=512, description="Path to reference face image for face consistency (optional). When provided, uses IP-Adapter or InstantID to maintain face consistency across generated images.")
    face_consistency_method: str | None = Field(default=None, max_length=32, description="Face consistency method to use: 'ip_adapter', 'ip_adapter_plus', 'instantid', or 'faceid' (optional, defaults to 'ip_adapter' if face_image_path is provided).")


@router.post("/image")
def generate_image(req: GenerateImageRequest) -> dict:
    """
    Generate an image or batch of images using ComfyUI.
    
    Creates an image generation job with the specified parameters. When batch_size > 1,
    multiple images will be generated in a single job. The job is processed asynchronously
    and can be checked via GET /api/generate/image/{job_id}.
    
    Args:
        req: Image generation request with prompt, dimensions, and generation parameters.
            batch_size (1-8) controls how many images to generate in this batch.
        
    Returns:
        dict: Response with job information including job ID, state, and batch_size.
            For batch generation (batch_size > 1), the job will contain image_paths
            array when completed.
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
        is_nsfw=req.is_nsfw,
        face_image_path=req.face_image_path,
        face_consistency_method=req.face_consistency_method,
    )
    return {
        "ok": True,
        "job": job.__dict__,
        "batch_size": req.batch_size,
        "is_batch": req.batch_size > 1,
    }


@router.get("/image/{job_id}")
def get_image_job(job_id: str) -> dict:
    """
    Get image generation job status.
    
    Retrieves the current status and results of an image generation job.
    For batch generation jobs, the response includes image_paths array with all
    generated images when the job completes successfully.
    
    Args:
        job_id: Unique identifier for the generation job
        
    Returns:
        dict: Job information including state, image paths, and metadata.
            On success: {"ok": True, "job": {...}, "is_batch": bool, "image_count": int}
            On not found: {"ok": False, "error": "not_found"}
    """
    job = generation_service.get_job(job_id)
    if not job:
        return {"ok": False, "error": "not_found", "message": f"Image generation job '{job_id}' not found"}
    
    # Determine if this was a batch job and count images
    is_batch = job.image_paths is not None and len(job.image_paths) > 1
    image_count = len(job.image_paths) if job.image_paths else (1 if job.image_path else 0)
    
    return {
        "ok": True,
        "job": job.__dict__,
        "is_batch": is_batch,
        "image_count": image_count,
    }


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


class ABTestVariant(BaseModel):
    """A single prompt variant for A/B testing."""

    prompt: str = Field(..., min_length=1, max_length=2000, description="Prompt variation to test")
    negative_prompt: str | None = Field(default=None, max_length=2000, description="Negative prompt for this variant (optional)")
    variant_name: str | None = Field(default=None, max_length=100, description="Optional name for this variant (e.g., 'variant_a', 'with_lighting')")


class ABTestRequest(BaseModel):
    """Request model for A/B testing multiple prompt variations.
    
    Generates images for each prompt variation and tracks results for comparison.
    Useful for optimizing prompt engineering by testing different variations.
    """

    variants: list[ABTestVariant] = Field(..., min_length=2, max_length=10, description="List of prompt variations to test (2-10 variants)")
    base_negative_prompt: str | None = Field(default=None, max_length=2000, description="Base negative prompt applied to all variants (optional)")
    seed: int | None = Field(default=None, description="Random seed for reproducibility (optional, same seed used for all variants)")
    checkpoint: str | None = Field(default=None, max_length=512, description="Checkpoint model name override (optional)")
    width: int = Field(default=1024, ge=256, le=4096, description="Image width in pixels (256-4096, default: 1024)")
    height: int = Field(default=1024, ge=256, le=4096, description="Image height in pixels (256-4096, default: 1024)")
    steps: int = Field(default=25, ge=1, le=200, description="Number of sampling steps (1-200, default: 25)")
    cfg: float = Field(default=7.0, ge=0.0, le=30.0, description="Classifier-free guidance scale (0.0-30.0, default: 7.0)")
    sampler_name: str = Field(default="euler", max_length=64, description="Sampler algorithm name (default: 'euler')")
    scheduler: str = Field(default="normal", max_length=64, description="Scheduler name (default: 'normal')")
    is_nsfw: bool = Field(default=False, description="Whether to generate +18/NSFW content (default: False)")


@router.post("/image/ab-test")
def create_ab_test(req: ABTestRequest) -> dict:
    """
    Create an A/B test for image prompt variations.
    
    Generates images for each prompt variation and groups them together for comparison.
    Each variant gets its own generation job, and all jobs are linked to the same A/B test.
    Results can be compared by quality scores, user feedback, or other metrics.
    
    Args:
        req: ABTestRequest containing:
            - variants: List of 2-10 prompt variations to test
            - base_negative_prompt: Optional negative prompt applied to all variants
            - Other generation parameters (width, height, steps, etc.)
    
    Returns:
        dict: Response containing:
            - ok: True if A/B test created successfully
            - ab_test_id: Unique identifier for this A/B test
            - variant_jobs: List of job information for each variant
            - total_variants: Number of variants being tested
    
    Example:
        ```json
        {
            "ok": true,
            "ab_test_id": "ab-test-123",
            "variant_jobs": [
                {
                    "variant_name": "variant_a",
                    "job_id": "job-1",
                    "prompt": "A beautiful woman..."
                },
                {
                    "variant_name": "variant_b",
                    "job_id": "job-2",
                    "prompt": "A stunning woman..."
                }
            ],
            "total_variants": 2
        }
        ```
    """
    import uuid
    
    ab_test_id = f"ab-test-{uuid.uuid4().hex[:12]}"
    variant_jobs = []
    
    # Create a job for each variant
    for idx, variant in enumerate(req.variants):
        variant_name = variant.variant_name or f"variant_{idx + 1}"
        
        # Use variant-specific negative prompt or fall back to base
        negative_prompt = variant.negative_prompt or req.base_negative_prompt
        
        # Create job for this variant
        job = generation_service.create_image_job(
            prompt=variant.prompt,
            negative_prompt=negative_prompt,
            seed=req.seed,
            checkpoint=req.checkpoint,
            width=req.width,
            height=req.height,
            steps=req.steps,
            cfg=req.cfg,
            sampler_name=req.sampler_name,
            scheduler=req.scheduler,
            batch_size=1,  # One image per variant for A/B testing
            is_nsfw=req.is_nsfw,
        )
        
        # Store A/B test metadata in job params
        if not job.params:
            job.params = {}
        job.params["ab_test_id"] = ab_test_id
        job.params["variant_name"] = variant_name
        job.params["variant_index"] = idx
        job.params["total_variants"] = len(req.variants)
        generation_service._persist_jobs_to_disk()
        
        variant_jobs.append({
            "variant_name": variant_name,
            "variant_index": idx,
            "job_id": job.id,
            "prompt": variant.prompt,
            "negative_prompt": negative_prompt,
            "state": job.state,
        })
    
    return {
        "ok": True,
        "ab_test_id": ab_test_id,
        "variant_jobs": variant_jobs,
        "total_variants": len(req.variants),
    }


@router.get("/image/ab-test/{ab_test_id}")
def get_ab_test_results(ab_test_id: str) -> dict:
    """
    Get A/B test results and comparison.
    
    Retrieves all jobs for an A/B test and compares their results including
    quality scores, generation times, and image paths.
    
    Args:
        ab_test_id: Unique identifier for the A/B test
    
    Returns:
        dict: Response containing:
            - ok: True if A/B test found
            - ab_test_id: A/B test identifier
            - variants: List of variant results with:
                - variant_name: Name of the variant
                - job_id: Job ID for this variant
                - state: Job state
                - quality_score: Quality score if available
                - image_path: Path to generated image
                - generation_time: Time taken to generate
            - comparison: Summary comparison of all variants
            - error: Error message if A/B test not found
    
    Example:
        ```json
        {
            "ok": true,
            "ab_test_id": "ab-test-123",
            "variants": [
                {
                    "variant_name": "variant_a",
                    "job_id": "job-1",
                    "state": "succeeded",
                    "quality_score": 0.85,
                    "image_path": "image1.png"
                }
            ],
            "comparison": {
                "best_quality": "variant_a",
                "fastest": "variant_b"
            }
        }
        ```
    """
    # Find all jobs for this A/B test
    all_jobs = generation_service.list_jobs(limit=1000)
    ab_test_jobs = []
    
    for job_dict in all_jobs:
        job_params = job_dict.get("params") or {}
        if job_params.get("ab_test_id") == ab_test_id:
            ab_test_jobs.append(job_dict)
    
    if not ab_test_jobs:
        return {
            "ok": False,
            "error": "not_found",
            "message": f"A/B test '{ab_test_id}' not found",
        }
    
    # Build variant results
    variants = []
    quality_scores = {}
    generation_times = {}
    
    for job_dict in ab_test_jobs:
        job_params = job_dict.get("params") or {}
        variant_name = job_params.get("variant_name", "unknown")
        
        # Get quality score from quality_results if available
        quality_results = job_params.get("quality_results", [])
        quality_score = None
        if quality_results and len(quality_results) > 0:
            quality_score = quality_results[0].get("quality_score")
        
        # Calculate generation time
        generation_time = None
        if job_dict.get("started_at") and job_dict.get("finished_at"):
            generation_time = job_dict["finished_at"] - job_dict["started_at"]
        
        variant_result = {
            "variant_name": variant_name,
            "variant_index": job_params.get("variant_index", 0),
            "job_id": job_dict.get("id"),
            "state": job_dict.get("state"),
            "prompt": job_params.get("prompt"),
            "negative_prompt": job_params.get("negative_prompt"),
            "quality_score": quality_score,
            "image_path": job_dict.get("image_path"),
            "image_paths": job_dict.get("image_paths"),
            "generation_time": generation_time,
            "error": job_dict.get("error"),
        }
        variants.append(variant_result)
        
        # Track for comparison
        if quality_score is not None:
            quality_scores[variant_name] = quality_score
        if generation_time is not None:
            generation_times[variant_name] = generation_time
    
    # Build comparison summary
    comparison = {}
    if quality_scores:
        best_quality_variant = max(quality_scores.items(), key=lambda x: x[1] if x[1] is not None else 0)
        comparison["best_quality"] = best_quality_variant[0]
        comparison["best_quality_score"] = best_quality_variant[1]
    
    if generation_times:
        fastest_variant = min(generation_times.items(), key=lambda x: x[1] if x[1] is not None else float('inf'))
        comparison["fastest"] = fastest_variant[0]
        comparison["fastest_time"] = fastest_variant[1]
    
    # Sort variants by index
    variants.sort(key=lambda x: x.get("variant_index", 0))
    
    return {
        "ok": True,
        "ab_test_id": ab_test_id,
        "variants": variants,
        "comparison": comparison,
        "total_variants": len(variants),
    }

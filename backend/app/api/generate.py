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
from enum import Enum
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.middleware import limiter
from app.core.paths import images_dir
from app.services.face_consistency_service import (
    FaceConsistencyMethod,
    face_consistency_service,
)
from app.services.generation_service import generation_service
from app.services.gpu_optimizer import get_gpu_optimizer
from app.services.text_generation_service import (
    TextGenerationRequest,
    text_generation_service,
)
from app.services.video_generation_service import (
    VideoGenerationMethod,
    VideoGenerationService,
)
from app.services.model_3d_generation_service import (
    Model3DGenerationMethod,
    model_3d_generation_service,
)

video_generation_service = VideoGenerationService()

router = APIRouter()


def _get_batch_preset(preset_name: str) -> dict[str, Any] | None:
    """
    Get batch generation preset configuration.
    
    Args:
        preset_name: Preset name ('quick', 'quality', 'speed')
        
    Returns:
        dict with preset parameters or None if invalid
    """
    presets = {
        "quick": {
            "steps": 20,
            "cfg": 6.0,
            "sampler_name": "euler",
            "scheduler": "normal",
        },
        "quality": {
            "steps": 40,
            "cfg": 8.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
        },
        "speed": {
            "steps": 15,
            "cfg": 5.0,
            "sampler_name": "euler",
            "scheduler": "normal",
        },
    }
    return presets.get(preset_name.lower())


def _recommend_batch_size(width: int, height: int, estimated_memory_mb: float) -> int:
    """
    Recommend optimal batch size based on image dimensions and memory.
    
    Args:
        width: Image width
        height: Image height
        estimated_memory_mb: Estimated memory usage in MB
        
    Returns:
        Recommended batch size (1-8)
    """
    # Base memory per image (rough estimate)
    base_memory_per_image = (width * height * 4) / (1024 * 1024)  # MB
    
    # Memory thresholds (conservative estimates)
    if estimated_memory_mb <= 2000:  # < 2GB
        return min(8, int(2000 / base_memory_per_image))
    elif estimated_memory_mb <= 4000:  # < 4GB
        return min(4, int(4000 / base_memory_per_image))
    elif estimated_memory_mb <= 6000:  # < 6GB
        return min(2, int(6000 / base_memory_per_image))
    else:  # >= 6GB
        return 1


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
    face_embedding_id: str | None = Field(default=None, max_length=128, description="Existing face embedding ID to reuse for face consistency. When provided, the stored normalized image will be used and the saved method will be applied unless overridden.")
    auto_retry_on_low_quality: bool = Field(default=False, description="Whether to automatically retry generation for low-quality images (default: False). Requires quality_threshold to be set.")
    quality_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Quality score threshold for auto-retry (0.0-1.0, default: 0.6). Images below this threshold will be retried if auto_retry_on_low_quality is True.")
    max_auto_retries: int = Field(default=1, ge=0, le=3, description="Maximum number of auto-retry attempts for low-quality images (0-3, default: 1).")
    batch_preset: str | None = Field(default=None, max_length=32, description="Batch generation preset: 'quick' (fast, lower quality), 'quality' (slower, higher quality), 'speed' (fastest, basic quality), or None (use request parameters).")


@router.post("/image")
@limiter.limit("10/minute")
def generate_image(request: Request, req: GenerateImageRequest) -> dict:
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
            
    Raises:
        HTTPException: If validation fails or service error occurs.
    """
    try:
        # Apply batch preset if specified
        if req.batch_preset:
            preset_config = _get_batch_preset(req.batch_preset)
            if preset_config:
                # Override parameters with preset values
                req.steps = preset_config.get("steps", req.steps)
                req.cfg = preset_config.get("cfg", req.cfg)
                req.sampler_name = preset_config.get("sampler_name", req.sampler_name)
                req.scheduler = preset_config.get("scheduler", req.scheduler)
        
        # GPU-aware batch size optimization
        gpu_optimizer = get_gpu_optimizer()
        gpu_recommendation = gpu_optimizer.recommend_batch_size(
            width=req.width,
            height=req.height,
            batch_size=req.batch_size,
            conservative=True,
        )
        recommended_batch_size = gpu_recommendation["recommended_batch_size"]
        
        # Enhanced validation for batch generation
        if req.batch_size > 1:
            # Validate batch size constraints
            if req.batch_size > 8:
                return {
                    "ok": False,
                    "error": "validation_error",
                    "message": f"Batch size {req.batch_size} exceeds maximum of 8. Use batch_size between 1-8.",
                    "field": "batch_size",
                    "max_value": 8,
                    "recommended_batch_size": recommended_batch_size,
                    "gpu_recommendation": gpu_recommendation,
                }
            # Check if requested batch size is safe based on actual GPU memory
            if not gpu_recommendation["can_use_requested"]:
                return {
                    "ok": False,
                    "error": "gpu_memory_warning",
                    "message": gpu_recommendation["reason"],
                    "recommended_batch_size": recommended_batch_size,
                    "requested_batch_size": req.batch_size,
                    "gpu_memory_available_gb": gpu_recommendation.get("gpu_memory_available_gb"),
                    "gpu_memory_total_gb": gpu_recommendation.get("gpu_memory_total_gb"),
                    "estimated_memory_per_image_gb": gpu_recommendation.get("estimated_memory_per_image_gb"),
                    "suggestion": f"Try batch_size={recommended_batch_size} or reduce width/height",
                }
        
        # Resolve face embedding (if provided) to a concrete image path
        face_image_path = req.face_image_path
        face_consistency_method = req.face_consistency_method
        if req.face_embedding_id:
            metadata = face_consistency_service.get_face_embedding_metadata(req.face_embedding_id)
            if not metadata:
                return {
                    "ok": False,
                    "error": "embedding_not_found",
                    "message": f"Face embedding '{req.face_embedding_id}' not found",
                }
            
            face_image_path = metadata.get("normalized_image_path") or metadata.get("image_path")
            if not face_image_path:
                return {
                    "ok": False,
                    "error": "embedding_missing_image",
                    "message": f"Face embedding '{req.face_embedding_id}' is missing its stored image",
                }
            
            if not face_consistency_method:
                face_consistency_method = metadata.get("method")
            
            status = metadata.get("status")
            if status and status != "ready":
                return {
                    "ok": False,
                    "error": "embedding_not_ready",
                    "message": f"Face embedding '{req.face_embedding_id}' is not ready (status={status})",
                }
        
        # Store auto-retry settings in job params
        job_params_extra = {
            "auto_retry_on_low_quality": req.auto_retry_on_low_quality,
            "quality_threshold": req.quality_threshold,
            "max_auto_retries": req.max_auto_retries,
            "batch_preset": req.batch_preset,
        }
        
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
            face_image_path=face_image_path,
            face_consistency_method=face_consistency_method,
            face_embedding_id=req.face_embedding_id,
        )
        
        # Update job params with extra settings
        generation_service._update_job_params(job.id, **job_params_extra)
        
        response = {
            "ok": True,
            "job": job.__dict__,
            "batch_size": req.batch_size,
            "is_batch": req.batch_size > 1,
        }
        
        # Add recommendations if batch size might be suboptimal
        if req.batch_size > 1 and recommended_batch_size != req.batch_size:
            response["recommendation"] = {
                "recommended_batch_size": recommended_batch_size,
                "reason": f"Based on estimated memory usage ({estimated_memory_mb:.0f}MB), batch_size={recommended_batch_size} is recommended for optimal performance.",
            }
        
        # Add batch-specific metadata
        if req.batch_size > 1:
            response["batch_info"] = {
                "expected_images": req.batch_size,
                "estimated_time_seconds": req.batch_size * 30,  # Rough estimate: 30s per image
                "status_endpoint": f"/api/generate/image/{job.id}",
            }
        
        return response
        
    except ValueError as e:
        return {
            "ok": False,
            "error": "validation_error",
            "message": str(e),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "service_error",
            "message": f"Failed to create image generation job: {str(e)}",
        }


@router.get("/image/{job_id}")
def get_image_job(job_id: str) -> dict:
    """
    Get image generation job status.
    
    Retrieves the current status and results of an image generation job.
    For batch generation jobs, the response includes image_paths array with all
    generated images when the job completes successfully. Provides progress
    tracking for batch generation jobs.
    
    Args:
        job_id: Unique identifier for the generation job
        
    Returns:
        dict: Job information including state, image paths, and metadata.
            On success: {"ok": True, "job": {...}, "is_batch": bool, "image_count": int, "progress": {...}}
            On not found: {"ok": False, "error": "not_found"}
    """
    job = generation_service.get_job(job_id)
    if not job:
        return {"ok": False, "error": "not_found", "message": f"Image generation job '{job_id}' not found"}
    
    # Determine if this was a batch job and count images
    is_batch = job.image_paths is not None and len(job.image_paths) > 1
    image_count = len(job.image_paths) if job.image_paths else (1 if job.image_path else 0)
    
    response = {
        "ok": True,
        "job": job.__dict__,
        "is_batch": is_batch,
        "image_count": image_count,
    }
    
    # Add batch progress tracking
    if is_batch and job.params:
        batch_size = job.params.get("batch_size", image_count)
        if batch_size and batch_size > 0:
            progress_pct = min(100, round(100 * image_count / batch_size, 1))
            response["progress"] = {
                "completed": image_count,
                "total": batch_size,
                "percentage": progress_pct,
                "status": "complete" if job.state == "succeeded" else ("in_progress" if job.state == "running" else job.state),
            }
    
    return response


@router.get("/image/{job_id}/rank")
def rank_batch_images(job_id: str, min_quality: float = 0.0, limit: int = 10) -> dict:
    """
    Rank and filter batch images by quality score.
    
    Args:
        job_id: Job ID to rank images for
        min_quality: Minimum quality score threshold (0.0-1.0, default: 0.0)
        limit: Maximum number of top images to return (default: 10)
        
    Returns:
        dict: Ranked list of images with quality scores
    """
    job = generation_service.get_job(job_id)
    if not job:
        return {"ok": False, "error": "not_found", "message": f"Job '{job_id}' not found"}
    
    if not job.image_paths or len(job.image_paths) <= 1:
        return {"ok": False, "error": "not_batch", "message": "Job is not a batch job"}
    
    quality_results = job.params.get("quality_results", []) if job.params else []
    
    # Create image-quality mapping
    image_quality_map = {
        qr.get("image_path"): qr.get("quality_score")
        for qr in quality_results
        if qr.get("quality_score") is not None
    }
    
    # Rank images by quality score
    ranked_images = []
    for image_path in job.image_paths:
        quality_score = image_quality_map.get(image_path)
        if quality_score is not None and quality_score >= min_quality:
            ranked_images.append({
                "image_path": image_path,
                "quality_score": quality_score,
                "rank": 0,  # Will be set after sorting
            })
    
    # Sort by quality score (descending)
    ranked_images.sort(key=lambda x: x["quality_score"], reverse=True)
    
    # Assign ranks
    for idx, img in enumerate(ranked_images):
        img["rank"] = idx + 1
    
    # Apply limit
    top_images = ranked_images[:limit]
    
    return {
        "ok": True,
        "job_id": job_id,
        "total_images": len(job.image_paths),
        "filtered_count": len(ranked_images),
        "min_quality_threshold": min_quality,
        "top_images": top_images,
    }


@router.get("/image/stats")
def get_batch_statistics() -> dict:
    """
    Get batch generation statistics and analytics.
    
    Returns:
        dict: Statistics including total jobs, batch jobs, success rate, average quality scores, etc.
    """
    jobs = generation_service.list_jobs(limit=1000)  # Get more jobs for stats
    
    total_jobs = len(jobs)
    batch_jobs = [j for j in jobs if j.get("params", {}).get("batch_size", 1) > 1]
    single_jobs = [j for j in jobs if j.get("params", {}).get("batch_size", 1) == 1]
    
    # Calculate success rates
    succeeded = [j for j in jobs if j.get("state") == "succeeded"]
    failed = [j for j in jobs if j.get("state") == "failed"]
    success_rate = len(succeeded) / total_jobs if total_jobs > 0 else 0.0
    
    # Calculate average quality scores
    quality_scores = []
    for job in succeeded:
        quality_results = job.get("params", {}).get("quality_results", [])
        for qr in quality_results:
            score = qr.get("quality_score")
            if score is not None:
                quality_scores.append(score)
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None
    
    # Batch statistics
    batch_sizes = [j.get("params", {}).get("batch_size", 1) for j in batch_jobs]
    avg_batch_size = sum(batch_sizes) / len(batch_sizes) if batch_sizes else 0
    
    # Total images generated
    total_images = sum(
        len(j.get("image_paths", [])) if j.get("image_paths") else (1 if j.get("image_path") else 0)
        for j in succeeded
    )
    
    # Get batch queue statistics
    queue_stats = generation_service.get_batch_queue_stats()
    
    return {
        "ok": True,
        "statistics": {
            "total_jobs": total_jobs,
            "batch_jobs": len(batch_jobs),
            "single_jobs": len(single_jobs),
            "succeeded": len(succeeded),
            "failed": len(failed),
            "queue": queue_stats,
            "success_rate": round(success_rate, 3),
            "total_images_generated": total_images,
            "average_quality_score": round(avg_quality, 3) if avg_quality else None,
            "average_batch_size": round(avg_batch_size, 2) if avg_batch_size > 0 else None,
            "quality_scores_count": len(quality_scores),
        },
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


@router.get("/image/batch/queue")
def get_batch_queue_stats() -> dict:
    """
    Get batch processing queue statistics.
    
    Returns real-time statistics about batch jobs in the queue including:
    - Queue status (queued, running, completed, failed)
    - Total images queued, processing, and completed
    - Resource usage metrics
    
    Returns:
        dict: Queue statistics with job counts and image counts
    """
    stats = generation_service.get_batch_queue_stats()
    return {
        "ok": True,
        "queue_stats": stats,
    }


@router.get("/image/batch/{job_id}/summary")
def get_batch_job_summary(job_id: str) -> dict:
    """
    Get detailed summary for a batch generation job.
    
    Returns comprehensive information about a batch job including:
    - Progress tracking (completed, failed, processing)
    - Quality statistics for all images
    - Failure details if any images failed
    - Batch metadata
    
    Args:
        job_id: Job ID to get summary for
        
    Returns:
        dict: Batch job summary with progress, quality stats, and failure details
    """
    summary = generation_service.get_batch_job_summary(job_id)
    if summary is None:
        return {
            "ok": False,
            "error": "Job not found or not a batch job",
        }
    return {
        "ok": True,
        "summary": summary,
    }


@router.post("/image/{job_id}/cancel")
def cancel_image_job(job_id: str, preserve_partial: bool = False) -> dict:
    """
    Cancel a running image generation job.
    
    Requests cancellation of an in-progress image generation job.
    The job may not cancel immediately if generation has already started.
    
    Args:
        job_id: Unique identifier for the generation job to cancel
        preserve_partial: If True, preserve any partial results (for batch jobs)
        
    Returns:
        dict: Success status of the cancel request
    """
    ok = generation_service.request_cancel(job_id, preserve_partial=preserve_partial)
    return {
        "ok": ok,
        "preserve_partial": preserve_partial,
        "message": "Cancellation requested" + (" (partial results will be preserved)" if preserve_partial else ""),
    }


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
@limiter.limit("20/minute")
def generate_text(request: Request, req: GenerateTextRequest) -> dict:
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


class ExtractFaceEmbeddingRequest(BaseModel):
    """Request model for face embedding extraction."""

    face_image_path: str = Field(..., max_length=512, description="Path to reference face image for embedding extraction")
    method: str = Field(default="ip_adapter", max_length=32, description="Face consistency method: 'ip_adapter', 'ip_adapter_plus', 'instantid', or 'faceid' (default: 'ip_adapter')")


@router.post("/face-embedding/extract")
@limiter.limit("30/minute")
def extract_face_embedding(request: Request, req: ExtractFaceEmbeddingRequest) -> dict:
    """
    Extract face embedding from a reference image.
    
    Extracts face embeddings for use in face consistency image generation.
    The extracted embedding can be reused across multiple image generations
    to maintain consistent character faces.
    
    Args:
        req: Face embedding extraction request with image path and method
        
    Returns:
        dict: Response containing:
            - ok: True if extraction successful
            - embedding_id: Unique identifier for the extracted embedding
            - embedding_path: Path to saved embedding file
            - method: Method used for extraction
            - image_path: Original image path
            - validation: Face image validation result
            - status: Extraction status ('pending' for foundation, 'ready' when fully implemented)
            - metadata_saved: Whether metadata was successfully saved
            - error: Error message if extraction failed
    """
    try:
        # Validate and normalize path
        from pathlib import Path
        face_path = Path(req.face_image_path)
        
        # Check if path is absolute or relative to images directory
        if not face_path.is_absolute():
            from app.core.paths import images_dir
            face_path = images_dir() / face_path
        
        # Validate method
        try:
            method = FaceConsistencyMethod(req.method)
        except ValueError:
            valid_methods = [m.value for m in FaceConsistencyMethod]
            return {
                "ok": False,
                "error": "invalid_method",
                "message": f"Invalid face consistency method '{req.method}'. Valid methods: {', '.join(valid_methods)}",
                "valid_methods": valid_methods,
            }
        
        # Extract face embedding
        result = face_consistency_service.extract_face_embedding(
            face_image_path=str(face_path),
            method=method,
        )
        
        return {
            "ok": True,
            "embedding_id": result["embedding_id"],
            "embedding_path": result["embedding_path"],
            "method": result["method"],
            "image_path": result["image_path"],
            "validation": result["validation"],
            "status": result["status"],
            "metadata_saved": result.get("metadata_saved", False),
        }
    except FileNotFoundError as e:
        return {
            "ok": False,
            "error": "file_not_found",
            "message": str(e),
            "suggestion": "Ensure the face image path is correct and the file exists",
        }
    except ValueError as e:
        error_msg = str(e)
        suggestion = "Check that the image meets minimum requirements (256x256 resolution, valid format)"
        if "validation failed" in error_msg.lower():
            suggestion = "The face image failed validation. Check resolution, format, and file integrity"
        return {
            "ok": False,
            "error": "validation_failed",
            "message": error_msg,
            "suggestion": suggestion,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "extraction_failed",
            "message": f"Face embedding extraction failed: {str(e)}",
            "suggestion": "Check server logs for detailed error information",
        }


@router.get("/face-embedding/list")
def list_face_embeddings() -> dict:
    """
    List all saved face embeddings.
    
    Returns a list of all face embeddings that have been extracted and saved.
    
    Returns:
        dict: Response containing:
            - ok: True if successful
            - embeddings: List of embedding metadata dictionaries with:
                - embedding_id: Unique identifier
                - path: Path to embedding file
                - method: Method used (if available)
    """
    try:
        embeddings = face_consistency_service.list_face_embeddings()
        return {
            "ok": True,
            "embeddings": embeddings,
            "count": len(embeddings),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "list_failed",
            "message": f"Failed to list face embeddings: {str(e)}",
        }


@router.get("/face-embedding/health")
def face_embedding_health() -> dict:
    """
    Check face consistency service health.
    
    Returns health status of the face consistency service including:
    - Service availability
    - Embedding directory status
    - Supported methods
    - Statistics
    
    Returns:
        dict: Response containing:
            - ok: True if service is healthy
            - service: Service name
            - embeddings_dir: Path to embeddings directory
            - embeddings_dir_exists: Whether directory exists
            - embeddings_count: Number of saved embeddings
            - supported_methods: List of supported face consistency methods
            - pil_available: Whether PIL/Pillow is available for image validation
    """
    try:
        from app.services.face_consistency_service import PIL_AVAILABLE
        
        embeddings = face_consistency_service.list_face_embeddings()
        embeddings_dir = face_consistency_service._face_embeddings_dir
        
        return {
            "ok": True,
            "service": "face_consistency",
            "embeddings_dir": str(embeddings_dir),
            "embeddings_dir_exists": embeddings_dir.exists(),
            "embeddings_count": len(embeddings),
            "supported_methods": [method.value for method in FaceConsistencyMethod],
            "pil_available": PIL_AVAILABLE,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "health_check_failed",
            "message": f"Face consistency service health check failed: {str(e)}",
        }


@router.get("/face-embedding/{embedding_id}")
def get_face_embedding(embedding_id: str) -> dict:
    """
    Get face embedding by ID.
    
    Retrieves full metadata for a specific face embedding.
    
    Args:
        embedding_id: Unique identifier for the face embedding
        
    Returns:
        dict: Response containing:
            - ok: True if embedding found
            - embedding: Full embedding metadata (method, image_path, validation, created_at, etc.)
            - error: Error message if not found
    """
    try:
        metadata = face_consistency_service.get_face_embedding_metadata(embedding_id)
        if metadata:
            return {
                "ok": True,
                "embedding": metadata,
            }
        else:
            return {
                "ok": False,
                "error": "not_found",
                "message": f"Face embedding '{embedding_id}' not found",
            }
    except Exception as e:
        return {
            "ok": False,
            "error": "get_failed",
            "message": f"Failed to get face embedding: {str(e)}",
        }


@router.delete("/face-embedding/{embedding_id}")
def delete_face_embedding(embedding_id: str) -> dict:
    """
    Delete a face embedding by ID.
    
    Permanently deletes a face embedding and its metadata.
    
    Args:
        embedding_id: Unique identifier for the face embedding to delete
        
    Returns:
        dict: Response containing:
            - ok: True if deletion successful
            - message: Success or error message
            - error: Error code if deletion failed
    """
    try:
        deleted = face_consistency_service.delete_face_embedding(embedding_id)
        if deleted:
            return {
                "ok": True,
                "message": f"Face embedding '{embedding_id}' deleted successfully",
            }
        else:
            return {
                "ok": False,
                "error": "not_found_or_failed",
                "message": f"Face embedding '{embedding_id}' not found or deletion failed",
            }
    except Exception as e:
        return {
            "ok": False,
            "error": "delete_failed",
            "message": f"Failed to delete face embedding: {str(e)}",
        }


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


# Video Generation Endpoints

class ShortVideoPlatform(str, Enum):
    """Platform options for short video generation."""
    INSTAGRAM_REELS = "instagram_reels"
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    FACEBOOK_REELS = "facebook_reels"
    TWITTER = "twitter"
    GENERIC = "generic"


class GenerateVideoRequest(BaseModel):
    """Request model for video generation with prompt and generation parameters.
    
    Supports both regular video generation (1-60s) and short video generation (15-60s).
    For short videos optimized for social media (reels, shorts, TikTok), use duration
    between 15-60 seconds and specify the target platform for automatic optimizations.
    """

    method: str = Field(..., description="Video generation method: 'animatediff' or 'stable_video_diffusion'")
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt describing the video to generate (1-2000 characters)")
    negative_prompt: str | None = Field(default=None, max_length=2000, description="Negative prompt describing what to avoid (optional, max 2000 characters)")
    duration: int | None = Field(default=None, ge=1, le=60, description="Video duration in seconds (1-60, optional). For short videos (reels/shorts), use 15-60 seconds.")
    fps: int | None = Field(default=None, ge=8, le=60, description="Frames per second (8-60, optional). For short videos, 24-30 fps is recommended.")
    seed: int | None = Field(default=None, description="Random seed for reproducibility (optional)")
    is_short_video: bool = Field(default=False, description="Whether this is a short video (15-60s) optimized for social media platforms (default: False)")
    platform: str | None = Field(default=None, description="Target platform for short videos: 'instagram_reels', 'youtube_shorts', 'tiktok', 'facebook_reels', 'twitter', or 'generic' (optional). Automatically applies platform-specific optimizations.")


@router.post("/video")
@limiter.limit("5/minute")
def generate_video(request: Request, req: GenerateVideoRequest) -> dict:
    """
    Generate a video using AnimateDiff or Stable Video Diffusion.
    
    Creates a video generation job using the specified method (AnimateDiff or
    Stable Video Diffusion). The job is queued and processed asynchronously.
    
    Args:
        req: Video generation request with method, prompt, and parameters
        
    Returns:
        dict: Job information including job_id and status.
            On success: {"ok": True, "job_id": str, "status": str, "message": str}
            On error: {"ok": False, "error": str, "message": str}
    """
    try:
        # Validate method
        try:
            method = VideoGenerationMethod(req.method.lower())
        except ValueError:
            return {
                "ok": False,
                "error": "invalid_method",
                "message": f"Invalid method '{req.method}'. Must be 'animatediff' or 'stable_video_diffusion'",
            }
        
        # Validate short video constraints and apply platform optimizations
        platform_optimizations = {}
        if req.is_short_video:
            if req.duration is None:
                return {
                    "ok": False,
                    "error": "invalid_duration",
                    "message": "Short videos require duration to be specified (15-60 seconds)",
                }
            if req.duration < 15 or req.duration > 60:
                return {
                    "ok": False,
                    "error": "invalid_duration",
                    "message": f"Short videos must be 15-60 seconds, got {req.duration}",
                }
            
            # Apply platform-specific optimizations
            if req.platform:
                try:
                    platform = ShortVideoPlatform(req.platform.lower())
                    # Platform-specific settings
                    if platform == ShortVideoPlatform.INSTAGRAM_REELS:
                        # Instagram Reels: 9:16 aspect ratio, 30fps, 15-90s (we support 15-60s)
                        if req.fps is None:
                            req.fps = 30
                        platform_optimizations = {
                            "aspect_ratio": "9:16",
                            "recommended_resolution": "1080x1920",
                            "max_duration": 90,
                            "format": {
                                "container": "mp4",
                                "video_codec": "h264",
                                "audio_codec": "aac",
                                "video_bitrate": "3500k",
                                "audio_bitrate": "128k",
                                "profile": "high",
                                "level": "4.0",
                                "pixel_format": "yuv420p",
                            },
                        }
                    elif platform == ShortVideoPlatform.YOUTUBE_SHORTS:
                        # YouTube Shorts: 9:16 aspect ratio, 30fps, up to 60s
                        if req.fps is None:
                            req.fps = 30
                        platform_optimizations = {
                            "aspect_ratio": "9:16",
                            "recommended_resolution": "1080x1920",
                            "max_duration": 60,
                            "format": {
                                "container": "mp4",
                                "video_codec": "h264",
                                "audio_codec": "aac",
                                "video_bitrate": "8000k",
                                "audio_bitrate": "192k",
                                "profile": "high",
                                "level": "4.2",
                                "pixel_format": "yuv420p",
                            },
                        }
                    elif platform == ShortVideoPlatform.TIKTOK:
                        # TikTok: 9:16 aspect ratio, 30fps, 15-180s (we support 15-60s)
                        if req.fps is None:
                            req.fps = 30
                        platform_optimizations = {
                            "aspect_ratio": "9:16",
                            "recommended_resolution": "1080x1920",
                            "max_duration": 180,
                            "format": {
                                "container": "mp4",
                                "video_codec": "h264",
                                "audio_codec": "aac",
                                "video_bitrate": "5000k",
                                "audio_bitrate": "128k",
                                "profile": "high",
                                "level": "4.0",
                                "pixel_format": "yuv420p",
                            },
                        }
                    elif platform == ShortVideoPlatform.FACEBOOK_REELS:
                        # Facebook Reels: 9:16 aspect ratio, 30fps, 15-90s
                        if req.fps is None:
                            req.fps = 30
                        platform_optimizations = {
                            "aspect_ratio": "9:16",
                            "recommended_resolution": "1080x1920",
                            "max_duration": 90,
                            "format": {
                                "container": "mp4",
                                "video_codec": "h264",
                                "audio_codec": "aac",
                                "video_bitrate": "4000k",
                                "audio_bitrate": "128k",
                                "profile": "high",
                                "level": "4.0",
                                "pixel_format": "yuv420p",
                            },
                        }
                    elif platform == ShortVideoPlatform.TWITTER:
                        # Twitter: 16:9 or 9:16, 30fps, up to 140s (we support 15-60s)
                        if req.fps is None:
                            req.fps = 30
                        platform_optimizations = {
                            "aspect_ratio": "16:9 or 9:16",
                            "recommended_resolution": "1280x720 or 720x1280",
                            "max_duration": 140,
                            "format": {
                                "container": "mp4",
                                "video_codec": "h264",
                                "audio_codec": "aac",
                                "video_bitrate": "5000k",
                                "audio_bitrate": "128k",
                                "profile": "high",
                                "level": "4.0",
                                "pixel_format": "yuv420p",
                            },
                        }
                    else:  # GENERIC
                        # Generic short video: 9:16, 24fps
                        if req.fps is None:
                            req.fps = 24
                        platform_optimizations = {
                            "aspect_ratio": "9:16",
                            "recommended_resolution": "1080x1920",
                            "max_duration": 60,
                            "format": {
                                "container": "mp4",
                                "video_codec": "h264",
                                "audio_codec": "aac",
                                "video_bitrate": "3000k",
                                "audio_bitrate": "128k",
                                "profile": "high",
                                "level": "4.0",
                                "pixel_format": "yuv420p",
                            },
                        }
                except ValueError:
                    return {
                        "ok": False,
                        "error": "invalid_platform",
                        "message": f"Invalid platform '{req.platform}'. Must be one of: instagram_reels, youtube_shorts, tiktok, facebook_reels, twitter, generic",
                    }
            else:
                # Default short video settings if no platform specified
                if req.fps is None:
                    req.fps = 24
                platform_optimizations = {
                    "aspect_ratio": "9:16",
                    "recommended_resolution": "1080x1920",
                    "max_duration": 60,
                    "format": {
                        "container": "mp4",
                        "video_codec": "h264",
                        "audio_codec": "aac",
                        "video_bitrate": "3000k",
                        "audio_bitrate": "128k",
                        "profile": "high",
                        "level": "4.0",
                        "pixel_format": "yuv420p",
                    },
                }
        
        # Generate video
        result = video_generation_service.generate_video(
            method=method,
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            duration=req.duration,
            fps=req.fps,
            seed=req.seed,
            is_short_video=req.is_short_video,
            platform=req.platform,
            platform_optimizations=platform_optimizations if platform_optimizations else None,
        )
        
        return {
            "ok": True,
            "job_id": result.get("job_id", "pending"),
            "status": result.get("status", "pending"),
            "method": result.get("method"),
            "message": result.get("message", "Video generation job created"),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "generation_failed",
            "message": f"Failed to create video generation job: {str(e)}",
        }


@router.get("/video/{job_id}")
def get_video_job(job_id: str) -> dict:
    """
    Get video generation job status.
    
    Retrieves the current status and results of a video generation job.
    
    Args:
        job_id: Unique identifier for the generation job
        
    Returns:
        dict: Job information including status and metadata.
            On success: {"ok": True, "job": {...}}
            On not found: {"ok": False, "error": "not_found"}
    """
    status = video_generation_service.get_video_generation_status(job_id)
    
    if status.get("status") == "not_found":
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Video generation job '{job_id}' not found",
        }
    
    return {
        "ok": True,
        "job": status,
    }


@router.get("/video/jobs")
def list_video_jobs() -> dict:
    """
    List recent video generation jobs.
    
    Returns a list of the most recent video generation jobs.
    
    Returns:
        dict: List of job items with their status and metadata
    """
    jobs = video_generation_service.list_jobs(limit=100)
    return {
        "items": jobs,
        "total": len(jobs),
    }


@router.post("/video/{job_id}/cancel")
def cancel_video_job(job_id: str) -> dict:
    """
    Cancel a running video generation job.
    
    Requests cancellation of an in-progress video generation job.
    The job may not cancel immediately if generation has already started.
    
    Args:
        job_id: Unique identifier for the generation job to cancel
        
    Returns:
        dict: Success status of the cancel request
    """
    cancelled = video_generation_service.request_cancel(job_id)
    if not cancelled:
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Video generation job '{job_id}' not found or cannot be cancelled",
        }
    
    return {
        "ok": True,
        "job_id": job_id,
        "message": "Cancellation requested for video generation job",
    }


# Video presets for short video generation
VIDEO_PRESETS: dict[str, dict[str, Any]] = {
    "instagram_reels": {
        "id": "instagram_reels",
        "name": "Instagram Reels",
        "description": "Optimized for Instagram Reels (9:16, 30fps, 15-60s)",
        "category": "short_video",
        "platform": "instagram_reels",
        "is_short_video": True,
        "duration": 30,
        "fps": 30,
        "method": "animatediff",
        "prompt_template": "{subject}, engaging short video, vibrant colors, high quality, social media",
        "negative_prompt": "blurry, low quality, distorted, static",
    },
    "youtube_shorts": {
        "id": "youtube_shorts",
        "name": "YouTube Shorts",
        "description": "Optimized for YouTube Shorts (9:16, 30fps, up to 60s)",
        "category": "short_video",
        "platform": "youtube_shorts",
        "is_short_video": True,
        "duration": 30,
        "fps": 30,
        "method": "animatediff",
        "prompt_template": "{subject}, engaging short video, high quality, YouTube Shorts format",
        "negative_prompt": "blurry, low quality, distorted, static",
    },
    "tiktok": {
        "id": "tiktok",
        "name": "TikTok",
        "description": "Optimized for TikTok (9:16, 30fps, 15-60s)",
        "category": "short_video",
        "platform": "tiktok",
        "is_short_video": True,
        "duration": 30,
        "fps": 30,
        "method": "animatediff",
        "prompt_template": "{subject}, viral TikTok style, engaging, high quality, trending",
        "negative_prompt": "blurry, low quality, distorted, static, boring",
    },
    "facebook_reels": {
        "id": "facebook_reels",
        "name": "Facebook Reels",
        "description": "Optimized for Facebook Reels (9:16, 30fps, 15-60s)",
        "category": "short_video",
        "platform": "facebook_reels",
        "is_short_video": True,
        "duration": 30,
        "fps": 30,
        "method": "animatediff",
        "prompt_template": "{subject}, engaging short video, high quality, Facebook Reels format",
        "negative_prompt": "blurry, low quality, distorted, static",
    },
    "twitter": {
        "id": "twitter",
        "name": "Twitter/X Video",
        "description": "Optimized for Twitter/X (16:9 or 9:16, 30fps, 15-60s)",
        "category": "short_video",
        "platform": "twitter",
        "is_short_video": True,
        "duration": 30,
        "fps": 30,
        "method": "animatediff",
        "prompt_template": "{subject}, engaging short video, high quality, Twitter format",
        "negative_prompt": "blurry, low quality, distorted, static",
    },
    "generic_short": {
        "id": "generic_short",
        "name": "Generic Short Video",
        "description": "Generic short video preset (9:16, 24fps, 15-60s)",
        "category": "short_video",
        "platform": "generic",
        "is_short_video": True,
        "duration": 30,
        "fps": 24,
        "method": "animatediff",
        "prompt_template": "{subject}, engaging short video, high quality",
        "negative_prompt": "blurry, low quality, distorted, static",
    },
}


@router.get("/video/presets")
def list_video_presets(category: str | None = None) -> dict:
    """
    List all available video presets, optionally filtered by category.
    
    Returns presets for short video generation optimized for different platforms.
    Each preset includes platform-specific settings (duration, fps, aspect ratio).
    
    Args:
        category: Optional category filter (e.g., "short_video")
        
    Returns:
        dict: List of presets and available categories
    """
    items = list(VIDEO_PRESETS.values())
    if category:
        items = [p for p in items if p.get("category") == category]
    return {
        "ok": True,
        "items": items,
        "categories": sorted(set(p.get("category", "other") for p in VIDEO_PRESETS.values())),
    }


@router.get("/video/presets/{preset_id}")
def get_video_preset(preset_id: str) -> dict:
    """
    Get a specific video preset by ID.
    
    Returns the full preset configuration including platform settings,
    duration, fps, and prompt templates.
    
    Args:
        preset_id: Unique identifier for the preset (e.g., "instagram_reels")
        
    Returns:
        dict: Preset configuration or error if not found
    """
    preset = VIDEO_PRESETS.get(preset_id)
    if not preset:
        return {"ok": False, "error": "not_found", "message": f"Video preset '{preset_id}' not found"}
    return {"ok": True, "preset": preset}


@router.get("/video/health")
def get_video_generation_health() -> dict:
    """
    Check video generation service health.
    
    Returns the health status of the video generation service.
    
    Returns:
        dict: Health status information
    """
    health = video_generation_service.health_check()
    return {
        "ok": True,
        **health,
    }


# ============================================================================
# 3D Model Generation Endpoints
# ============================================================================

class GenerateModel3DRequest(BaseModel):
    """Request model for 3D model generation with text prompt or reference image.
    
    Supports text-to-3D (Shap-E, Point-E) and image-to-3D (TripoSR) generation.
    """

    method: str = Field(..., description="3D generation method: 'shape_e', 'triposr', or 'point_e'")
    prompt: str | None = Field(default=None, min_length=1, max_length=2000, description="Text prompt for text-to-3D generation (required for shape_e and point_e)")
    image_path: str | None = Field(default=None, description="Path to reference image for image-to-3D generation (required for triposr)")
    seed: int | None = Field(default=None, description="Random seed for reproducibility (optional)")
    resolution: int = Field(default=256, ge=128, le=1024, description="3D model resolution (128-1024, default: 256)")


@router.post("/model-3d")
@limiter.limit("5/minute")
def generate_model_3d(request: Request, req: GenerateModel3DRequest) -> dict:
    """
    Generate a 3D model from text prompt or reference image.
    
    Supports three methods:
    - Shap-E: Text-to-3D generation
    - TripoSR: Image-to-3D generation
    - Point-E: Text-to-3D generation
    
    Args:
        request: FastAPI request object
        req: Generation request with method, prompt/image, and parameters
        
    Returns:
        dict: Job information with job_id and status
    """
    try:
        # Validate method
        try:
            method = Model3DGenerationMethod(req.method.lower())
        except ValueError:
            return {
                "ok": False,
                "error": "validation_error",
                "message": f"Invalid method '{req.method}'. Must be one of: shape_e, triposr, point_e",
            }
        
        # Generate 3D model
        result = model_3d_generation_service.generate_model_3d(
            method=method,
            prompt=req.prompt,
            image_path=req.image_path,
            seed=req.seed,
            resolution=req.resolution,
        )
        
        return {
            "ok": True,
            **result,
        }
        
    except ValueError as e:
        return {
            "ok": False,
            "error": "validation_error",
            "message": str(e),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "generation_error",
            "message": str(e),
        }


@router.get("/model-3d/{job_id}")
def get_model_3d_job(job_id: str) -> dict:
    """
    Get status and details of a 3D model generation job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        dict: Job status and details
    """
    job = model_3d_generation_service.get_job(job_id)
    if not job:
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Job '{job_id}' not found",
        }
    
    return {
        "ok": True,
        "job": {
            "id": job.id,
            "state": job.state,
            "message": job.message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "cancelled_at": job.cancelled_at,
            "model_path": job.model_path,
            "error": job.error,
            "params": job.params,
            "prompt_id": job.prompt_id,
        },
    }


@router.get("/model-3d")
def list_model_3d_jobs(limit: int = 50, offset: int = 0) -> dict:
    """
    List recent 3D model generation jobs.
    
    Args:
        limit: Maximum number of jobs to return (default: 50)
        offset: Number of jobs to skip (default: 0)
        
    Returns:
        dict: List of jobs
    """
    jobs = model_3d_generation_service.list_jobs(limit=limit, offset=offset)
    return {
        "ok": True,
        "jobs": [
            {
                "id": job.id,
                "state": job.state,
                "message": job.message,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "finished_at": job.finished_at,
                "model_path": job.model_path,
                "params": job.params,
            }
            for job in jobs
        ],
        "total": len(jobs),
    }


@router.post("/model-3d/{job_id}/cancel")
def cancel_model_3d_job(job_id: str) -> dict:
    """
    Cancel a running 3D model generation job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        dict: Cancellation result
    """
    cancelled = model_3d_generation_service.cancel_job(job_id)
    if not cancelled:
        return {
            "ok": False,
            "error": "not_found_or_finished",
            "message": f"Job '{job_id}' not found or already finished",
        }
    
    return {
        "ok": True,
        "message": f"Job '{job_id}' cancelled",
    }

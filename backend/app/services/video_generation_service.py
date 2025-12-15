"""Video generation service for AnimateDiff and Stable Video Diffusion.

This service provides video generation functionality using AnimateDiff and
Stable Video Diffusion models through ComfyUI integration.

Implementation Status:
- ✅ Service foundation created
- ✅ ComfyUI client integration
- ✅ Basic workflow builder structure
- ⏳ AnimateDiff workflow implementation
- ⏳ Stable Video Diffusion workflow implementation
- ⏳ Video generation job management
- ✅ API endpoints for video generation

The service integrates with ComfyUI to generate videos using AnimateDiff
and Stable Video Diffusion models. Workflow building is structured and ready
for implementation.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Optional

from app.core.logging import get_logger
from app.core.paths import video_jobs_file
from app.services.comfyui_client import ComfyUiClient, ComfyUiError

logger = get_logger(__name__)

VideoJobState = Literal["queued", "running", "cancelled", "failed", "succeeded"]


@dataclass
class VideoJob:
    """Video generation job information.
    
    Attributes:
        id: Unique job identifier.
        state: Current job state (queued, running, cancelled, failed, succeeded).
        message: Human-readable status message describing the current state.
        created_at: Timestamp when job was created (Unix timestamp).
        started_at: Timestamp when job started processing (Unix timestamp), None if not started.
        finished_at: Timestamp when job finished (Unix timestamp), None if not finished.
        cancelled_at: Timestamp when job was cancelled (Unix timestamp), None if not cancelled.
        video_path: Path to the generated video file, None if not generated.
        error: Error message if job failed, None otherwise.
        params: Generation parameters used for this job (method, prompt, settings, etc.).
        prompt_id: ComfyUI prompt ID for tracking the workflow execution.
        cancel_requested: Whether cancellation has been requested for this job.
    """
    id: str
    state: VideoJobState = "queued"
    message: str | None = None
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    cancelled_at: float | None = None
    video_path: str | None = None
    error: str | None = None
    params: dict[str, Any] | None = None
    prompt_id: str | None = None
    cancel_requested: bool = False


class VideoGenerationMethod(str, Enum):
    """Video generation method options."""

    ANIMATEDIFF = "animatediff"
    STABLE_VIDEO_DIFFUSION = "stable_video_diffusion"


class VideoGenerationService:
    """Service for generating videos using AnimateDiff and Stable Video Diffusion."""

    def __init__(self, comfyui_client: Optional[ComfyUiClient] = None):
        """Initialize the video generation service.
        
        Args:
            comfyui_client: Optional ComfyUI client instance. If not provided,
                          creates a new client using default settings.
        """
        self.logger = get_logger(__name__)
        self.comfyui_client = comfyui_client or ComfyUiClient()
        self._lock = threading.Lock()
        self._jobs: dict[str, VideoJob] = {}
        video_jobs_file().parent.mkdir(parents=True, exist_ok=True)
        self._load_jobs_from_disk()

    def generate_video(
        self,
        method: VideoGenerationMethod,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: Optional[int] = None,
        fps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a video using the specified method.

        Args:
            method: Video generation method (AnimateDiff or Stable Video Diffusion)
            prompt: Text prompt for video generation
            negative_prompt: Negative prompt (optional)
            duration: Video duration in seconds (optional)
            fps: Frames per second (optional)
            seed: Random seed for reproducibility (optional)
            **kwargs: Additional generation parameters

        Returns:
            Dictionary with job information and status
        """
        self.logger.info(f"Video generation requested: method={method}, prompt={prompt[:50]}...")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = VideoJob(
            id=job_id,
            state="queued",
            message="Video generation job created",
            created_at=time.time(),
            params={
                "method": method.value,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "duration": duration,
                "fps": fps,
                "seed": seed,
                **kwargs,
            },
        )
        
        with self._lock:
            self._jobs[job_id] = job
        self._persist_jobs_to_disk()
        
        try:
            # Build workflow based on method
            workflow = self._build_video_workflow(
                method=method,
                prompt=prompt,
                negative_prompt=negative_prompt,
                duration=duration,
                fps=fps,
                seed=seed,
                **kwargs,
            )
            
            # Queue workflow in ComfyUI
            prompt_id = self.comfyui_client.queue_prompt(workflow)
            
            # Update job with prompt_id
            with self._lock:
                job.prompt_id = prompt_id
                job.message = f"Video generation job queued with {method.value}"
            self._persist_jobs_to_disk()
            
            self.logger.info(f"Video generation job queued: job_id={job_id}, prompt_id={prompt_id}, method={method.value}")
            
            return {
                "status": "queued",
                "method": method.value,
                "prompt_id": prompt_id,
                "job_id": job_id,
                "message": f"Video generation job queued with {method.value}",
            }
        except ComfyUiError as e:
            self.logger.error(f"ComfyUI error during video generation: {e}")
            with self._lock:
                job.state = "failed"
                job.error = str(e)
                job.message = f"Failed to queue video generation: {str(e)}"
            self._persist_jobs_to_disk()
            return {
                "status": "failed",
                "method": method.value,
                "job_id": job_id,
                "error": "comfyui_error",
                "message": f"Failed to queue video generation: {str(e)}",
            }
        except Exception as e:
            self.logger.error(f"Unexpected error during video generation: {e}")
            with self._lock:
                job.state = "failed"
                job.error = str(e)
                job.message = f"Video generation failed: {str(e)}"
            self._persist_jobs_to_disk()
            return {
                "status": "failed",
                "method": method.value,
                "job_id": job_id,
                "error": "generation_error",
                "message": f"Video generation failed: {str(e)}",
            }
    
    def _build_video_workflow(
        self,
        method: VideoGenerationMethod,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: Optional[int] = None,
        fps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build ComfyUI workflow for video generation.
        
        Args:
            method: Video generation method
            prompt: Text prompt
            negative_prompt: Negative prompt (optional)
            duration: Video duration in seconds (optional)
            fps: Frames per second (optional)
            seed: Random seed (optional)
            **kwargs: Additional parameters
            
        Returns:
            ComfyUI workflow dictionary
            
        Raises:
            NotImplementedError: If method workflow is not yet implemented
        """
        if method == VideoGenerationMethod.ANIMATEDIFF:
            return self._build_animatediff_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                duration=duration,
                fps=fps,
                seed=seed,
                **kwargs,
            )
        elif method == VideoGenerationMethod.STABLE_VIDEO_DIFFUSION:
            return self._build_stable_video_diffusion_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                duration=duration,
                fps=fps,
                seed=seed,
                **kwargs,
            )
        else:
            raise ValueError(f"Unknown video generation method: {method}")
    
    def _build_animatediff_workflow(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: Optional[int] = None,
        fps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build AnimateDiff ComfyUI workflow.
        
        Args:
            prompt: Text prompt
            negative_prompt: Negative prompt (optional)
            duration: Video duration in seconds (optional, default: 16 frames)
            fps: Frames per second (optional, default: 8)
            seed: Random seed (optional)
            **kwargs: Additional parameters
            
        Returns:
            ComfyUI workflow dictionary
            
        Note:
            This is a placeholder structure. Actual AnimateDiff workflow requires
            specific nodes and model files to be installed in ComfyUI.
        """
        # Placeholder workflow structure for AnimateDiff
        # TODO: Implement actual AnimateDiff workflow with required nodes:
        # - AnimateDiffLoader
        # - Video generation nodes
        # - Video save nodes
        seed_val = seed if seed is not None else 0
        neg = negative_prompt or ""
        frames = (duration or 2) * (fps or 8)  # Default: 2 seconds at 8 fps = 16 frames
        
        self.logger.warning("AnimateDiff workflow is a placeholder - actual implementation pending")
        
        # Basic structure - will be replaced with actual AnimateDiff nodes
        return {
            "1": {
                "class_type": "AnimateDiffLoader",
                "inputs": {
                    "model_name": "animatediff_model.safetensors",  # Placeholder
                    "beta_schedule": "linear",
                },
            },
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg}},
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": frames},
            },
            # TODO: Add actual AnimateDiff sampling and video generation nodes
            "5": {
                "class_type": "SaveVideo",
                "inputs": {"video": ["4", 0], "filename_prefix": "ainfluencer_video"},
            },
        }
    
    def _build_stable_video_diffusion_workflow(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: Optional[int] = None,
        fps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build Stable Video Diffusion ComfyUI workflow.
        
        Args:
            prompt: Text prompt
            negative_prompt: Negative prompt (optional)
            duration: Video duration in seconds (optional, default: 4 seconds)
            fps: Frames per second (optional, default: 6)
            seed: Random seed (optional)
            **kwargs: Additional parameters
            
        Returns:
            ComfyUI workflow dictionary
            
        Note:
            This is a placeholder structure. Actual Stable Video Diffusion workflow
            requires specific nodes and model files to be installed in ComfyUI.
        """
        # Placeholder workflow structure for Stable Video Diffusion
        # TODO: Implement actual Stable Video Diffusion workflow with required nodes:
        # - StableVideoDiffusionLoader
        # - Video generation nodes
        # - Video save nodes
        seed_val = seed if seed is not None else 0
        neg = negative_prompt or ""
        frames = (duration or 4) * (fps or 6)  # Default: 4 seconds at 6 fps = 24 frames
        
        self.logger.warning("Stable Video Diffusion workflow is a placeholder - actual implementation pending")
        
        # Basic structure - will be replaced with actual Stable Video Diffusion nodes
        return {
            "1": {
                "class_type": "StableVideoDiffusionLoader",
                "inputs": {
                    "model_name": "svd_model.safetensors",  # Placeholder
                },
            },
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg}},
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 1024, "height": 576, "batch_size": frames},
            },
            # TODO: Add actual Stable Video Diffusion sampling and video generation nodes
            "5": {
                "class_type": "SaveVideo",
                "inputs": {"video": ["4", 0], "filename_prefix": "ainfluencer_video"},
            },
        }

    def get_video_generation_status(self, job_id: str) -> dict[str, Any]:
        """Get the status of a video generation job.

        Args:
            job_id: Job identifier

        Returns:
            Dictionary with job status information
        """
        self.logger.info(f"Getting video generation status: job_id={job_id}")
        
        with self._lock:
            job = self._jobs.get(job_id)
        
        if not job:
            return {
                "job_id": job_id,
                "status": "not_found",
                "message": f"Video generation job '{job_id}' not found",
            }
        
        return {
            "job_id": job.id,
            "status": job.state,
            "message": job.message,
            "prompt_id": job.prompt_id,
            "video_path": job.video_path,
            "error": job.error,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "params": job.params,
        }
    
    def get_job(self, job_id: str) -> VideoJob | None:
        """Get video generation job by ID.
        
        Args:
            job_id: Job ID to retrieve.
            
        Returns:
            VideoJob if found, None otherwise.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else VideoJob(**job.__dict__)
    
    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent video generation jobs.
        
        Args:
            limit: Maximum number of jobs to return (default: 50).
            
        Returns:
            List of job dictionaries, sorted by creation time (newest first).
        """
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.__dict__ for j in jobs[:limit]]
    
    def request_cancel(self, job_id: str) -> bool:
        """Request cancellation of a video generation job.
        
        Args:
            job_id: Job ID to cancel.
            
        Returns:
            True if cancellation was requested, False if job not found.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.state in ("failed", "succeeded", "cancelled"):
                return True
            job.cancel_requested = True
            job.message = "Cancelling…"
            job.state = "cancelled"
            job.cancelled_at = time.time()
            self._persist_jobs_to_disk()
            return True

    def _load_jobs_from_disk(self) -> None:
        """
        Load video generation jobs from disk storage.
        
        Reads jobs from JSON file and populates in-memory job dictionary.
        Silently handles missing files, invalid JSON, or malformed data.
        """
        path = video_jobs_file()
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(raw, list):
            return
        loaded: dict[str, VideoJob] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            job_id = item.get("id")
            if not isinstance(job_id, str):
                continue
            try:
                loaded[job_id] = VideoJob(**item)
            except Exception:
                continue
        with self._lock:
            self._jobs = loaded

    def _persist_jobs_to_disk(self) -> None:
        """
        Persist video generation jobs to disk storage.
        
        Saves jobs to JSON file, keeping only the most recent 200 jobs
        to prevent unbounded growth. Uses atomic write (tmp file + replace).
        """
        path = video_jobs_file()
        tmp = path.with_suffix(".tmp")
        # Keep last N jobs to avoid unbounded growth
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        jobs = jobs[:200]
        tmp.write_text(json.dumps([j.__dict__ for j in jobs], indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)

    def health_check(self) -> dict[str, Any]:
        """Check service health.

        Returns:
            Dictionary with health status
        """
        return {
            "status": "healthy",
            "service": "video_generation",
            "methods_available": [method.value for method in VideoGenerationMethod],
            "message": "Video generation service foundation is operational",
        }


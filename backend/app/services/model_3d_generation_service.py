"""3D model generation service for text-to-3D and image-to-3D.

This service provides 3D model generation functionality using ComfyUI integration
with models like Shap-E, TripoSR, and Point-E for generating 3D meshes from
text prompts or reference images.

Implementation Status:
- ✅ Service foundation created
- ✅ ComfyUI client integration
- ✅ Basic workflow builder structure
- ⏳ Shap-E workflow implementation
- ⏳ TripoSR workflow implementation
- ⏳ 3D model generation job management
- ✅ API endpoints for 3D model generation
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

from app.core.logging import get_logger
from app.core.paths import content_dir
from app.services.comfyui_client import ComfyUiClient, ComfyUiError

logger = get_logger(__name__)

Model3DJobState = Literal["queued", "running", "cancelled", "failed", "succeeded"]


@dataclass
class Model3DJob:
    """3D model generation job information.
    
    Attributes:
        id: Unique job identifier.
        state: Current job state (queued, running, cancelled, failed, succeeded).
        message: Human-readable status message describing the current state.
        created_at: Timestamp when job was created (Unix timestamp).
        started_at: Timestamp when job started processing (Unix timestamp), None if not started.
        finished_at: Timestamp when job finished (Unix timestamp), None if not finished.
        cancelled_at: Timestamp when job was cancelled (Unix timestamp), None if not cancelled.
        model_path: Path to the generated 3D model file (.obj, .gltf, .ply), None if not generated.
        error: Error message if job failed, None otherwise.
        params: Generation parameters used for this job (method, prompt, settings, etc.).
        prompt_id: ComfyUI prompt ID for tracking the workflow execution.
        cancel_requested: Whether cancellation has been requested for this job.
    """
    id: str
    state: Model3DJobState = "queued"
    message: str | None = None
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    cancelled_at: float | None = None
    model_path: str | None = None
    error: str | None = None
    params: dict[str, Any] | None = None
    prompt_id: str | None = None
    cancel_requested: bool = False


class Model3DGenerationMethod(str, Enum):
    """3D model generation method options."""

    SHAPE_E = "shape_e"  # Text-to-3D using Shap-E
    TRIPOSR = "triposr"  # Image-to-3D using TripoSR
    POINT_E = "point_e"  # Text-to-3D using Point-E


def _model_3d_jobs_file() -> Path:
    """Get path to 3D model generation jobs JSON file."""
    return content_dir() / "model_3d_jobs.json"


class Model3DGenerationService:
    """Service for generating 3D models using Shap-E, TripoSR, and Point-E."""

    def __init__(self, comfyui_client: Optional[ComfyUiClient] = None):
        """Initialize the 3D model generation service.
        
        Args:
            comfyui_client: Optional ComfyUI client instance. If not provided,
                          creates a new client using default settings.
        """
        self.logger = get_logger(__name__)
        self.comfyui_client = comfyui_client or ComfyUiClient()
        self._lock = threading.Lock()
        self._jobs: dict[str, Model3DJob] = {}
        _model_3d_jobs_file().parent.mkdir(parents=True, exist_ok=True)
        self._load_jobs_from_disk()
        
        # Create directory for 3D models
        self.models_dir = content_dir() / "models_3d"
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def generate_model_3d(
        self,
        method: Model3DGenerationMethod,
        prompt: Optional[str] = None,
        image_path: Optional[str] = None,
        seed: Optional[int] = None,
        resolution: int = 256,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a 3D model using the specified method.

        Args:
            method: 3D generation method (Shap-E, TripoSR, or Point-E)
            prompt: Text prompt for text-to-3D generation (required for Shap-E and Point-E)
            image_path: Path to reference image for image-to-3D generation (required for TripoSR)
            seed: Random seed for reproducibility (optional)
            resolution: 3D model resolution (default: 256)
            **kwargs: Additional generation parameters

        Returns:
            Dictionary with job information and status
        """
        # Validate inputs based on method
        if method in (Model3DGenerationMethod.SHAPE_E, Model3DGenerationMethod.POINT_E):
            if not prompt:
                raise ValueError(f"{method.value} requires a text prompt")
        elif method == Model3DGenerationMethod.TRIPOSR:
            if not image_path:
                raise ValueError("TripoSR requires an image_path")
            if not os.path.exists(image_path):
                raise ValueError(f"Image path does not exist: {image_path}")

        self.logger.info(f"3D model generation requested: method={method}, prompt={prompt[:50] if prompt else 'N/A'}...")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = Model3DJob(
            id=job_id,
            state="queued",
            message="3D model generation job created",
            created_at=time.time(),
            params={
                "method": method.value,
                "prompt": prompt,
                "image_path": image_path,
                "seed": seed,
                "resolution": resolution,
                **kwargs,
            },
        )
        
        with self._lock:
            self._jobs[job_id] = job
        self._persist_jobs_to_disk()
        
        try:
            # Build workflow based on method
            workflow = self._build_3d_workflow(
                method=method,
                prompt=prompt,
                image_path=image_path,
                seed=seed,
                resolution=resolution,
                **kwargs,
            )
            
            # Queue workflow in ComfyUI
            prompt_id = self.comfyui_client.queue_prompt(workflow)
            
            # Update job with prompt_id
            with self._lock:
                job.prompt_id = prompt_id
                job.message = f"3D model generation job queued with {method.value}"
            self._persist_jobs_to_disk()
            
            self.logger.info(f"3D model generation job queued: job_id={job_id}, prompt_id={prompt_id}, method={method.value}")
            
            return {
                "status": "queued",
                "method": method.value,
                "prompt_id": prompt_id,
                "job_id": job_id,
                "message": f"3D model generation job queued with {method.value}",
            }
        except ComfyUiError as e:
            self.logger.error(f"ComfyUI error during 3D model generation: {e}")
            with self._lock:
                job.state = "failed"
                job.error = str(e)
                job.message = f"Failed to queue 3D model generation: {str(e)}"
            self._persist_jobs_to_disk()
            return {
                "status": "failed",
                "method": method.value,
                "job_id": job_id,
                "error": "comfyui_error",
                "message": f"Failed to queue 3D model generation: {str(e)}",
            }
        except Exception as e:
            self.logger.error(f"Unexpected error during 3D model generation: {e}")
            with self._lock:
                job.state = "failed"
                job.error = str(e)
                job.message = f"3D model generation failed: {str(e)}"
            self._persist_jobs_to_disk()
            return {
                "status": "failed",
                "method": method.value,
                "job_id": job_id,
                "error": "generation_error",
                "message": f"3D model generation failed: {str(e)}",
            }

    def get_job(self, job_id: str) -> Optional[Model3DJob]:
        """Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Model3DJob if found, None otherwise
        """
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 50, offset: int = 0) -> list[Model3DJob]:
        """List recent jobs.
        
        Args:
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of Model3DJob objects
        """
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
            return jobs[offset:offset + limit]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was cancelled, False if not found or already finished
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.state in ("succeeded", "failed", "cancelled"):
                return False
            job.cancel_requested = True
            job.state = "cancelled"
            job.cancelled_at = time.time()
            job.message = "Cancelled by user"
        self._persist_jobs_to_disk()
        return True

    def _build_3d_workflow(
        self,
        method: Model3DGenerationMethod,
        prompt: Optional[str] = None,
        image_path: Optional[str] = None,
        seed: Optional[int] = None,
        resolution: int = 256,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build ComfyUI workflow for 3D model generation.
        
        Args:
            method: 3D generation method
            prompt: Text prompt (for text-to-3D methods)
            image_path: Image path (for image-to-3D methods)
            seed: Random seed
            resolution: 3D model resolution
            **kwargs: Additional parameters
            
        Returns:
            ComfyUI workflow dictionary
        """
        # Base workflow structure
        workflow = {}
        
        if method == Model3DGenerationMethod.SHAPE_E:
            # Shap-E text-to-3D workflow
            # Note: This is a placeholder structure. Actual implementation requires
            # ComfyUI nodes for Shap-E model loading and inference
            workflow = {
                "1": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": prompt or "",
                        "clip": ["2", 0],
                    },
                },
                "2": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {
                        "ckpt_name": "shape_e.safetensors",  # Placeholder
                    },
                },
                "3": {
                    "class_type": "ShapEModelLoader",  # Placeholder node type
                    "inputs": {
                        "model": ["2", 0],
                        "text_embeds": ["1", 0],
                        "seed": seed or 0,
                        "resolution": resolution,
                    },
                },
                "4": {
                    "class_type": "SaveMesh",
                    "inputs": {
                        "mesh": ["3", 0],
                        "filename_prefix": f"model_3d_{int(time.time())}",
                    },
                },
            }
        elif method == Model3DGenerationMethod.TRIPOSR:
            # TripoSR image-to-3D workflow
            # Note: This is a placeholder structure. Actual implementation requires
            # ComfyUI nodes for TripoSR model loading and inference
            workflow = {
                "1": {
                    "class_type": "LoadImage",
                    "inputs": {
                        "image": image_path or "",
                    },
                },
                "2": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {
                        "ckpt_name": "triposr.safetensors",  # Placeholder
                    },
                },
                "3": {
                    "class_type": "TripoSRModelLoader",  # Placeholder node type
                    "inputs": {
                        "model": ["2", 0],
                        "image": ["1", 0],
                        "seed": seed or 0,
                        "resolution": resolution,
                    },
                },
                "4": {
                    "class_type": "SaveMesh",
                    "inputs": {
                        "mesh": ["3", 0],
                        "filename_prefix": f"model_3d_{int(time.time())}",
                    },
                },
            }
        elif method == Model3DGenerationMethod.POINT_E:
            # Point-E text-to-3D workflow
            # Note: This is a placeholder structure. Actual implementation requires
            # ComfyUI nodes for Point-E model loading and inference
            workflow = {
                "1": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": prompt or "",
                        "clip": ["2", 0],
                    },
                },
                "2": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {
                        "ckpt_name": "point_e.safetensors",  # Placeholder
                    },
                },
                "3": {
                    "class_type": "PointEModelLoader",  # Placeholder node type
                    "inputs": {
                        "model": ["2", 0],
                        "text_embeds": ["1", 0],
                        "seed": seed or 0,
                        "resolution": resolution,
                    },
                },
                "4": {
                    "class_type": "SaveMesh",
                    "inputs": {
                        "mesh": ["3", 0],
                        "filename_prefix": f"model_3d_{int(time.time())}",
                    },
                },
            }
        
        return workflow

    def _load_jobs_from_disk(self) -> None:
        """Load jobs from disk on service initialization."""
        jobs_file = _model_3d_jobs_file()
        if not jobs_file.exists():
            return
        
        try:
            with open(jobs_file, "r") as f:
                data = json.load(f)
                for job_data in data.get("jobs", []):
                    job = Model3DJob(**job_data)
                    self._jobs[job.id] = job
            self.logger.info(f"Loaded {len(self._jobs)} 3D model generation jobs from disk")
        except Exception as e:
            self.logger.warning(f"Failed to load jobs from disk: {e}")

    def _persist_jobs_to_disk(self) -> None:
        """Persist jobs to disk."""
        jobs_file = _model_3d_jobs_file()
        try:
            with self._lock:
                jobs_data = {
                    "jobs": [
                        {
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
                            "cancel_requested": job.cancel_requested,
                        }
                        for job in self._jobs.values()
                    ]
                }
            with open(jobs_file, "w") as f:
                json.dump(jobs_data, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to persist jobs to disk: {e}")


# Global service instance
model_3d_generation_service = Model3DGenerationService()

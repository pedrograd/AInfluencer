"""Image generation service with ComfyUI integration and job management."""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal, cast

from app.core.config import settings
from app.core.logging import get_logger
from app.core.paths import images_dir, jobs_file
from app.services.comfyui_client import ComfyUiClient, ComfyUiError
from app.services.face_consistency_service import (
    FaceConsistencyMethod,
    face_consistency_service,
)
from app.services.quality_validator import quality_validator

logger = get_logger(__name__)

JobState = Literal["queued", "running", "cancelled", "failed", "succeeded"]


@dataclass
class ImageJob:
    """Image generation job information.
    
    Attributes:
        id: Unique job identifier.
        state: Current job state (queued, running, completed, failed, cancelled).
        message: Human-readable status message describing the current state.
        created_at: Timestamp when job was created (Unix timestamp).
        started_at: Timestamp when job started processing (Unix timestamp), None if not started.
        finished_at: Timestamp when job finished (Unix timestamp), None if not finished.
        cancelled_at: Timestamp when job was cancelled (Unix timestamp), None if not cancelled.
        image_path: Path to the generated image file (single image), None if not generated.
        image_paths: List of paths to generated image files (batch generation), None if not generated.
        error: Error message if job failed, None otherwise.
        params: Generation parameters used for this job (prompt, settings, etc.).
        cancel_requested: Whether cancellation has been requested for this job.
    """
    id: str
    state: JobState = "queued"
    message: str | None = None
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    cancelled_at: float | None = None
    image_path: str | None = None
    image_paths: list[str] | None = None
    error: str | None = None
    params: dict[str, Any] | None = None
    cancel_requested: bool = False


class GenerationService:
    """Service for managing image generation jobs and workflows."""

    def __init__(self) -> None:
        """Initialize generation service with thread lock and job storage."""
        self._lock = threading.Lock()
        self._jobs: dict[str, ImageJob] = {}
        images_dir().mkdir(parents=True, exist_ok=True)
        jobs_file().parent.mkdir(parents=True, exist_ok=True)
        self._load_jobs_from_disk()

    def _load_jobs_from_disk(self) -> None:
        """
        Load image generation jobs from disk storage.
        
        Reads jobs from JSON file and populates in-memory job dictionary.
        Silently handles missing files, invalid JSON, or malformed data.
        """
        path = jobs_file()
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(raw, list):
            return
        loaded: dict[str, ImageJob] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            job_id = item.get("id")
            if not isinstance(job_id, str):
                continue
            try:
                loaded[job_id] = ImageJob(**item)
            except Exception:
                continue
        with self._lock:
            self._jobs = loaded

    def _persist_jobs_to_disk(self) -> None:
        """
        Persist image generation jobs to disk storage.
        
        Saves jobs to JSON file, keeping only the most recent 200 jobs
        to prevent unbounded growth. Uses atomic write (tmp file + replace).
        """
        path = jobs_file()
        tmp = path.with_suffix(".tmp")
        # Keep last N jobs to avoid unbounded growth
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        jobs = jobs[:200]
        tmp.write_text(json.dumps([j.__dict__ for j in jobs], indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)

    def create_image_job(
        self,
        *,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        checkpoint: str | None = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 25,
        cfg: float = 7.0,
        sampler_name: str = "euler",
        scheduler: str = "normal",
        batch_size: int = 1,
        is_nsfw: bool = False,
        face_image_path: str | None = None,
        face_consistency_method: str | None = None,
        face_embedding_id: str | None = None,
        workflow_pack: dict[str, Any] | None = None,
    ) -> ImageJob:
        """
        Create a new image generation job.

        Args:
            prompt: Text prompt for image generation.
            negative_prompt: Optional negative prompt.
            seed: Optional random seed for reproducibility.
            checkpoint: Optional checkpoint model name.
            width: Image width in pixels (default: 1024).
            height: Image height in pixels (default: 1024).
            steps: Number of sampling steps (default: 25).
            cfg: Classifier-free guidance scale (default: 7.0).
            sampler_name: Sampler name (default: "euler").
            scheduler: Scheduler name (default: "normal").
            batch_size: Number of images to generate (default: 1).
            is_nsfw: Whether to generate +18/NSFW content (default: False).
            face_image_path: Optional path to reference face image for face consistency.
            face_consistency_method: Optional face consistency method ('ip_adapter', 'ip_adapter_plus', 'instantid', 'faceid').
            face_embedding_id: Optional face embedding ID referencing stored embeddings.
            workflow_pack: Optional workflow pack metadata for traceability.

        Returns:
            ImageJob object with job ID and initial state.
        """
        # Modify prompts for +18 content if requested
        final_prompt = prompt
        final_negative_prompt = negative_prompt
        
        if is_nsfw:
            # Add +18 modifiers to prompt
            final_prompt = f"{prompt}, adult content, mature, explicit, nsfw, +18"
            # Build negative prompt for NSFW content
            # Start with base negative prompt or empty
            nsfw_negative_parts = []
            if final_negative_prompt:
                # Keep original negative prompt but remove any SFW restrictions
                nsfw_negative_parts.append(final_negative_prompt)
            # Add NSFW quality controls (always include quality controls)
            nsfw_quality_controls = "low quality, distorted, bad anatomy, bad proportions, extra limbs, mutated, deformed, blurry, artifacts"
            nsfw_negative_parts.append(nsfw_quality_controls)
            final_negative_prompt = ", ".join(nsfw_negative_parts)
        
        # Prefer explicit checkpoint, otherwise pick from workflow pack if available
        pack_checkpoint = self._extract_pack_checkpoint(workflow_pack)
        effective_checkpoint = checkpoint or pack_checkpoint

        job_id = str(uuid.uuid4())
        job = ImageJob(
            id=job_id,
            state="queued",
            created_at=time.time(),
            params={
                "prompt": prompt,  # Store original prompt
                "negative_prompt": negative_prompt,  # Store original negative prompt
                "seed": seed,
                "checkpoint": effective_checkpoint,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "batch_size": batch_size,
                "is_nsfw": is_nsfw,
                "face_image_path": face_image_path,
                "face_consistency_method": face_consistency_method,
                "face_embedding_id": face_embedding_id,
                "final_prompt": final_prompt,  # Store modified prompt
                "final_negative_prompt": final_negative_prompt,  # Store modified negative prompt
                "workflow_pack": self._summarize_pack(workflow_pack),
            },
        )
        with self._lock:
            self._jobs[job_id] = job
            self._persist_jobs_to_disk()

        t = threading.Thread(
            target=self._run_image_job,
            args=(
                job_id,
                final_prompt,  # Use modified prompt
                final_negative_prompt,  # Use modified negative prompt
                seed,
                effective_checkpoint,
                width,
                height,
                steps,
                cfg,
                sampler_name,
                scheduler,
                batch_size,
                face_image_path,
                face_consistency_method,
                face_embedding_id,
            ),
            name=f"image-job-{job_id}",
            daemon=True,
        )
        t.start()
        return job

    def get_job(self, job_id: str) -> ImageJob | None:
        """
        Get image generation job by ID.

        Args:
            job_id: Job ID to retrieve.

        Returns:
            ImageJob if found, None otherwise.
        """
        with self._lock:
            j = self._jobs.get(job_id)
            return None if j is None else ImageJob(**j.__dict__)

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        List recent image generation jobs.

        Args:
            limit: Maximum number of jobs to return (default: 50).

        Returns:
            List of job dictionaries, sorted by creation time (newest first).
        """
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.__dict__ for j in jobs[:limit]]
    
    def get_batch_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        List batch generation jobs (batch_size > 1).
        
        Args:
            limit: Maximum number of jobs to return (default: 50).
            
        Returns:
            List of batch job dictionaries, sorted by creation time (newest first).
        """
        with self._lock:
            jobs = list(self._jobs.values())
        # Filter for batch jobs
        batch_jobs = [j for j in jobs if j.params and j.params.get("batch_size", 1) > 1]
        batch_jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.__dict__ for j in batch_jobs[:limit]]
    
    def get_batch_queue_stats(self) -> dict[str, Any]:
        """
        Get statistics about batch processing queue.
        
        Returns:
            dict with queue statistics (queued, running, completed, failed, total resource usage)
        """
        with self._lock:
            jobs = list(self._jobs.values())
        
        batch_jobs = [j for j in jobs if j.params and j.params.get("batch_size", 1) > 1]
        
        stats = {
            "total_batch_jobs": len(batch_jobs),
            "queued": 0,
            "running": 0,
            "succeeded": 0,
            "failed": 0,
            "cancelled": 0,
            "total_images_queued": 0,
            "total_images_processing": 0,
            "total_images_completed": 0,
        }
        
        for job in batch_jobs:
            batch_size = job.params.get("batch_size", 1) if job.params else 1
            stats["total_images_queued"] += batch_size
            
            if job.state == "queued":
                stats["queued"] += 1
            elif job.state == "running":
                stats["running"] += 1
                # Count images currently processing
                progress = job.params.get("batch_progress", {}) if job.params else {}
                processing = progress.get("processing", 0)
                stats["total_images_processing"] += processing
            elif job.state == "succeeded":
                stats["succeeded"] += 1
                # Count completed images
                if job.image_paths:
                    stats["total_images_completed"] += len(job.image_paths)
                elif job.image_path:
                    stats["total_images_completed"] += 1
            elif job.state == "failed":
                stats["failed"] += 1
            elif job.state == "cancelled":
                stats["cancelled"] += 1
        
        return stats
    
    def get_batch_job_summary(self, job_id: str) -> dict[str, Any] | None:
        """
        Get summary information for a batch job.
        
        Args:
            job_id: Job ID to get summary for
            
        Returns:
            dict with batch summary (image count, quality stats, progress, etc.) or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None
        
        is_batch = (job.image_paths is not None and len(job.image_paths) > 1) or (
            job.params and job.params.get("batch_size", 1) > 1
        )
        if not is_batch:
            return None
        
        quality_results = job.params.get("quality_results", []) if job.params else []
        quality_scores = [qr.get("quality_score") for qr in quality_results if qr.get("quality_score") is not None]
        batch_failures = job.params.get("batch_failures", []) if job.params else []
        batch_progress = job.params.get("batch_progress", {}) if job.params else {}
        
        return {
            "job_id": job_id,
            "batch_size": job.params.get("batch_size", 0) if job.params else 0,
            "image_count": len(job.image_paths) if job.image_paths else 0,
            "state": job.state,
            "progress": batch_progress,
            "failures": {
                "count": len(batch_failures),
                "details": batch_failures,
            },
            "quality_stats": {
                "average_score": sum(quality_scores) / len(quality_scores) if quality_scores else None,
                "min_score": min(quality_scores) if quality_scores else None,
                "max_score": max(quality_scores) if quality_scores else None,
                "scores_count": len(quality_scores),
            },
            "created_at": job.created_at,
            "finished_at": job.finished_at,
        }

    def request_cancel(self, job_id: str, preserve_partial: bool = False) -> bool:
        """
        Request cancellation of an image generation job.

        Args:
            job_id: Job ID to cancel.
            preserve_partial: If True, preserve any partial results (for batch jobs).

        Returns:
            True if cancellation was requested, False if job not found.
        """
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return False
            if j.state in ("failed", "succeeded", "cancelled"):
                return True
            
            # If preserving partial results, save what we have
            if preserve_partial and j.state == "running":
                # Check if we have any partial images (this would be set during generation)
                # For now, just mark that we want to preserve
                if not isinstance(j.params, dict):
                    j.params = {}
                j.params["preserve_partial_on_cancel"] = True
            
            j.cancel_requested = True
            j.message = "Cancelling… (partial results will be preserved)" if preserve_partial else "Cancelling…"
            self._persist_jobs_to_disk()
            return True

    def _extract_pack_checkpoint(self, workflow_pack: dict[str, Any] | None) -> str | None:
        """Get the first checkpoint from workflow pack requirements, if provided."""
        if not workflow_pack:
            return None
        required_models = workflow_pack.get("required_models")
        if isinstance(required_models, dict):
            checkpoints = required_models.get("checkpoints")
            if isinstance(checkpoints, list) and checkpoints:
                first = checkpoints[0]
                if isinstance(first, str) and first:
                    return first
        return None

    def _summarize_pack(self, workflow_pack: dict[str, Any] | None) -> dict[str, Any] | None:
        """Return a compact, serializable summary of the workflow pack for job params."""
        if not workflow_pack:
            return None
        summary_fields = ("id", "name", "description", "category", "tier", "tags")
        summary = {key: workflow_pack.get(key) for key in summary_fields if workflow_pack.get(key) is not None}

        required_models = workflow_pack.get("required_models")
        if isinstance(required_models, dict):
            models_summary = {
                key: value
                for key, value in required_models.items()
                if isinstance(value, list) and len(value) > 0
            }
            if models_summary:
                summary["required_models"] = models_summary

        return summary or None

    def list_images(
        self,
        *,
        q: str | None = None,
        sort: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List generated images with filtering and pagination.

        Args:
            q: Optional search query to filter by filename.
            sort: Sort order - "newest", "oldest", or "name" (default: "newest").
            limit: Maximum number of images to return (default: 50).
            offset: Number of images to skip for pagination (default: 0).

        Returns:
            Dictionary with items list, total count, and pagination info.
        """
        root = images_dir()
        query = (q or "").strip().lower()

        paths = [p for p in root.glob("*.png") if p.is_file()]
        if query:
            paths = [p for p in paths if query in p.name.lower()]

        if sort == "oldest":
            paths.sort(key=lambda x: x.stat().st_mtime)
        elif sort == "name":
            paths.sort(key=lambda x: x.name.lower())
        else:
            paths.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        total = len(paths)
        if offset < 0:
            offset = 0
        if limit < 1:
            limit = 1
        page = paths[offset : offset + limit]

        items: list[dict[str, Any]] = []
        for p in page:
            st = p.stat()
            items.append({"path": p.name, "mtime": st.st_mtime, "size_bytes": st.st_size, "url": f"/content/images/{p.name}"})

        return {"items": items, "total": total, "limit": limit, "offset": offset, "sort": sort, "q": query}

    def storage_stats(self) -> dict[str, Any]:
        """
        Get storage statistics for generated images.

        Returns:
            Dictionary with images_count and images_bytes.
        """
        root = images_dir()
        total = 0
        count = 0
        for p in root.glob("*.png"):
            try:
                st = p.stat()
            except FileNotFoundError:
                continue
            total += st.st_size
            count += 1
        return {"images_count": count, "images_bytes": total}

    def delete_job(self, job_id: str, *, delete_images: bool = True) -> bool:
        """
        Delete an image generation job.

        Args:
            job_id: Job ID to delete.
            delete_images: Whether to delete associated image files (default: True).

        Returns:
            True if job was deleted, False if not found.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            # mark cancel for running jobs
            if job.state in ("queued", "running"):
                job.cancel_requested = True
            files = job.image_paths or ([job.image_path] if job.image_path else [])
            del self._jobs[job_id]
            self._persist_jobs_to_disk()

        if delete_images:
            for name in files:
                if not name:
                    continue
                p = images_dir() / name
                try:
                    p.unlink()
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
        return True

    def clear_all(self, *, delete_images: bool = True) -> dict[str, Any]:
        """
        Clear all image generation jobs.

        Args:
            delete_images: Whether to delete associated image files (default: True).

        Returns:
            Dictionary with count of deleted jobs and images.
        """
        with self._lock:
            jobs = list(self._jobs.values())
            self._jobs = {}
            self._persist_jobs_to_disk()
        deleted = 0
        if delete_images:
            for job in jobs:
                files = job.image_paths or ([job.image_path] if job.image_path else [])
                for name in files:
                    if not name:
                        continue
                    p = images_dir() / name
                    try:
                        p.unlink()
                        deleted += 1
                    except FileNotFoundError:
                        pass
                    except Exception:
                        pass
        return {"ok": True, "deleted_images": deleted, "deleted_jobs": len(jobs)}

    def _set_job(self, job_id: str, **kwargs: Any) -> None:
        """
        Update job attributes atomically and persist to disk.
        
        Args:
            job_id: Job ID to update
            **kwargs: Job attributes to set (e.g., state, message, image_path)
        """
        with self._lock:
            j = self._jobs[job_id]
            for k, v in kwargs.items():
                setattr(j, k, v)
            self._persist_jobs_to_disk()

    def _is_cancel_requested(self, job_id: str) -> bool:
        """
        Check if cancellation has been requested for a job.
        
        Args:
            job_id: Job ID to check
        
        Returns:
            True if job exists and cancel_requested is True, False otherwise
        """
        with self._lock:
            j = self._jobs.get(job_id)
            return bool(j and j.cancel_requested)

    def _update_job_params(self, job_id: str, **updates: Any) -> None:
        """
        Update job parameters dictionary and persist to disk.
        
        Args:
            job_id: Job ID to update
            **updates: Parameter key-value pairs to merge into job.params
        """
        with self._lock:
            j = self._jobs[job_id]
            if not isinstance(j.params, dict):
                j.params = {}
            j.params.update(updates)
            self._persist_jobs_to_disk()

    def _basic_sdxl_workflow(
        self,
        prompt: str,
        negative_prompt: str | None,
        seed: int | None,
        checkpoint: str,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        sampler_name: str,
        scheduler: str,
        batch_size: int,
    ) -> dict[str, Any]:
        """
        Build a minimal SDXL ComfyUI workflow dictionary.
        
        Creates a basic workflow with checkpoint loader, text encoders, sampler,
        and image save nodes. Checkpoint name must exist in ComfyUI.
        
        Args:
            prompt: Positive text prompt
            negative_prompt: Negative text prompt (optional)
            seed: Random seed (defaults to 0 if None)
            checkpoint: Checkpoint model name
            width: Image width in pixels
            height: Image height in pixels
            steps: Number of sampling steps
            cfg: Classifier-free guidance scale
            sampler_name: Sampler algorithm name
            scheduler: Scheduler name
            batch_size: Number of images to generate
        
        Returns:
            ComfyUI workflow dictionary with node connections
        """
        # Minimal ComfyUI workflow (SDXL checkpoint name must exist in ComfyUI).
        # Users can change the checkpoint inside ComfyUI; this is MVP only.
        seed_val = seed if seed is not None else 0
        neg = negative_prompt or ""
        return {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": batch_size},
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                    "seed": seed_val,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                },
            },
            "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
            "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "ainfluencer"}},
        }

    def _run_image_job(
        self,
        job_id: str,
        prompt: str,
        negative_prompt: str | None,
        seed: int | None,
        checkpoint: str | None,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        sampler_name: str,
        scheduler: str,
        batch_size: int,
        face_image_path: str | None = None,
        face_consistency_method: str | None = None,
        face_embedding_id: str | None = None,
    ) -> None:
        """
        Execute image generation job in background thread.
        
        Builds ComfyUI workflow, queues prompt, waits for images, downloads results,
        and saves to disk. Updates job state throughout process. Handles cancellation
        and errors gracefully. Optionally integrates face consistency when face_image_path is provided.
        
        Args:
            job_id: Job ID to execute
            prompt: Text prompt for image generation
            negative_prompt: Optional negative prompt
            seed: Optional random seed
            checkpoint: Optional checkpoint name (uses first available if None)
            width: Image width in pixels
            height: Image height in pixels
            steps: Number of sampling steps
            cfg: Classifier-free guidance scale
            sampler_name: Sampler algorithm name
            scheduler: Scheduler name
            batch_size: Number of images to generate
            face_image_path: Optional path to reference face image for face consistency
            face_consistency_method: Optional face consistency method ('ip_adapter', 'instantid', etc.)
            face_embedding_id: Optional face embedding ID referencing stored embeddings
        """
        self._set_job(job_id, state="running", started_at=time.time(), message="Queued in ComfyUI")
        client = ComfyUiClient()

        try:
            resolved_face_path = face_image_path
            resolved_method = face_consistency_method
            
            if face_embedding_id:
                metadata = face_consistency_service.get_face_embedding_metadata(face_embedding_id)
                if not metadata:
                    error_msg = f"Face embedding '{face_embedding_id}' not found"
                    self._set_job(job_id, state="failed", finished_at=time.time(), error=error_msg)
                    return
                
                resolved_face_path = metadata.get("normalized_image_path") or metadata.get("image_path")
                if not resolved_face_path:
                    error_msg = f"Face embedding '{face_embedding_id}' missing image data"
                    self._set_job(job_id, state="failed", finished_at=time.time(), error=error_msg)
                    return
                
                if not resolved_method:
                    resolved_method = metadata.get("method")
                
                self._update_job_params(
                    job_id,
                    face_embedding_id=face_embedding_id,
                    resolved_face_image_path=resolved_face_path,
                )

            # Early cancel (before any external calls)
            if self._is_cancel_requested(job_id):
                now = time.time()
                self._set_job(job_id, state="cancelled", finished_at=now, cancelled_at=now, message="Cancelled")
                return

            checkpoints = client.list_checkpoints()
            if not checkpoints:
                raise ComfyUiError("No checkpoints found in ComfyUI")
            # Use provided checkpoint, or default from config, or first available
            ckpt = checkpoint or settings.default_checkpoint or checkpoints[0]
            if ckpt not in checkpoints:
                raise ComfyUiError(f"Checkpoint not found in ComfyUI: {ckpt}")

            workflow = self._basic_sdxl_workflow(
                prompt,
                negative_prompt,
                seed,
                ckpt,
                width,
                height,
                steps,
                cfg,
                sampler_name,
                scheduler,
                batch_size,
            )
            
            # Integrate face consistency if provided
            if resolved_face_path:
                try:
                    # Validate face image first
                    validation = face_consistency_service.validate_face_image(resolved_face_path)
                    if not validation["is_valid"]:
                        error_msg = "; ".join(validation["errors"])
                        raise ValueError(f"Face image validation failed: {error_msg}")
                    
                    if validation["warnings"]:
                        for warning in validation["warnings"]:
                            logger.warning(f"Face image validation warning: {warning}")
                    
                    # Determine method (default to IP_ADAPTER if not specified)
                    method_str = resolved_method or "ip_adapter"
                    try:
                        method = FaceConsistencyMethod(method_str)
                    except ValueError:
                        logger.warning(f"Invalid face_consistency_method '{method_str}', using ip_adapter")
                        method = FaceConsistencyMethod.IP_ADAPTER
                    
                    # Apply face consistency to workflow
                    if method in (FaceConsistencyMethod.IP_ADAPTER, FaceConsistencyMethod.IP_ADAPTER_PLUS):
                        workflow = face_consistency_service.build_ip_adapter_workflow_nodes(
                            workflow,
                            resolved_face_path,
                            weight=0.75,
                        )
                        self._set_job(job_id, message=f"Face consistency enabled: {method.value}")
                    elif method == FaceConsistencyMethod.INSTANTID:
                        workflow = face_consistency_service.build_instantid_workflow_nodes(
                            workflow,
                            resolved_face_path,
                            weight=0.8,
                        )
                        self._set_job(job_id, message=f"Face consistency enabled: {method.value}")
                    else:
                        logger.warning(f"Face consistency method {method.value} not yet fully implemented")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Failed to integrate face consistency: {error_msg}")
                    self._set_job(job_id, state="failed", finished_at=time.time(), error=error_msg)
                    return
            
            prompt_id = client.queue_prompt(workflow)
            self._update_job_params(job_id, comfy_prompt_id=prompt_id)
            self._set_job(job_id, message=f"ComfyUI prompt_id={prompt_id}")

            def _should_cancel() -> bool:
                return self._is_cancel_requested(job_id)

            outs = client.wait_for_images(prompt_id, timeout_s=600, should_cancel=_should_cancel)
            saved: list[str] = []
            quality_results: list[dict[str, Any]] = []
            failed_images: list[dict[str, Any]] = []
            
            # Initialize batch progress tracking
            if batch_size > 1:
                self._update_job_params(job_id, batch_progress={
                    "total": batch_size,
                    "completed": 0,
                    "failed": 0,
                    "processing": 0,
                })
            
            for idx, out in enumerate(outs):
                # Update progress for batch jobs
                if batch_size > 1:
                    self._update_job_params(job_id, batch_progress={
                        "total": batch_size,
                        "completed": len(saved),
                        "failed": len(failed_images),
                        "processing": idx + 1,
                    })
                    self._set_job(job_id, message=f"Processing batch image {idx + 1}/{batch_size}")
                
                try:
                    filename = str(out.get("filename"))
                    subfolder = str(out.get("subfolder") or "")
                    image_type = str(out.get("type") or "output")
                    data = client.download_image_bytes(filename=filename, subfolder=subfolder, image_type=image_type)
                    out_name = f"{int(time.time())}-{job_id}-{idx}.png"
                    dest = images_dir() / out_name
                    dest.write_bytes(data)
                    saved.append(out_name)
                except Exception as img_exc:  # noqa: BLE001
                    # Track failed images in batch but continue processing
                    error_msg = str(img_exc)
                    logger.warning(
                        f"Failed to process batch image {idx + 1}: {error_msg}",
                        extra={"job_id": job_id, "image_index": idx, "error": error_msg},
                    )
                    failed_images.append({
                        "index": idx,
                        "error": error_msg,
                        "timestamp": time.time(),
                    })
                    # For batch jobs, continue processing remaining images
                    if batch_size > 1:
                        continue
                    else:
                        # For single image jobs, fail immediately
                        raise
                
                # Validate image quality
                try:
                    quality_result = quality_validator.validate_content(file_path=str(dest))
                    quality_data = {
                        "image_path": out_name,
                        "quality_score": float(quality_result.quality_score) if quality_result.quality_score else None,
                        "is_valid": quality_result.is_valid,
                        "checks_passed": quality_result.checks_passed,
                        "checks_failed": quality_result.checks_failed,
                        "warnings": quality_result.warnings,
                        "metadata": quality_result.metadata,
                    }
                    quality_results.append(quality_data)
                    
                    # Log quality results
                    if quality_result.quality_score is not None:
                        logger.info(
                            f"Image quality validated: {out_name}",
                            extra={
                                "job_id": job_id,
                                "image_path": out_name,
                                "quality_score": float(quality_result.quality_score),
                                "is_valid": quality_result.is_valid,
                                "checks_passed_count": len(quality_result.checks_passed),
                                "checks_failed_count": len(quality_result.checks_failed),
                            },
                        )
                    else:
                        logger.warning(
                            f"Image quality validation failed: {out_name}",
                            extra={
                                "job_id": job_id,
                                "image_path": out_name,
                                "errors": quality_result.errors,
                            },
                        )
                except Exception as qexc:  # noqa: BLE001
                    # Quality validation failure shouldn't fail the job
                    logger.warning(
                        f"Quality validation error for {out_name}: {qexc}",
                        extra={"job_id": job_id, "image_path": out_name, "error": str(qexc)},
                    )
                    quality_results.append({
                        "image_path": out_name,
                        "quality_score": None,
                        "is_valid": False,
                        "error": str(qexc),
                    })
            
            # Handle partial batch failures
            if batch_size > 1:
                total_processed = len(saved) + len(failed_images)
                if total_processed != batch_size:
                    logger.warning(
                        f"Batch size mismatch: expected {batch_size} images, got {total_processed} "
                        f"({len(saved)} succeeded, {len(failed_images)} failed)",
                        extra={
                            "job_id": job_id,
                            "expected": batch_size,
                            "succeeded": len(saved),
                            "failed": len(failed_images),
                            "total_processed": total_processed,
                        },
                    )
                
                # Determine final state for batch jobs with partial failures
                if len(saved) == 0:
                    # All images failed
                    raise ComfyUiError(f"Batch generation failed: all {batch_size} images failed to process")
                elif len(failed_images) > 0:
                    # Partial success - mark as succeeded but include failure info
                    logger.warning(
                        f"Batch generation partial success: {len(saved)}/{batch_size} images succeeded",
                        extra={
                            "job_id": job_id,
                            "succeeded": len(saved),
                            "failed": len(failed_images),
                            "total": batch_size,
                        },
                    )
                    # Update params with failure information
                    existing_params = self._jobs.get(job_id).params if self._jobs.get(job_id) else {}
                    updated_params = {**existing_params, "batch_failures": failed_images}
                    self._update_job_params(job_id, **updated_params)
            
            # Determine success message based on batch size and results
            if batch_size > 1:
                if len(failed_images) > 0:
                    message = f"Generated {len(saved)}/{batch_size} images ({len(failed_images)} failed)"
                else:
                    message = f"Generated {len(saved)} images (batch_size={batch_size})"
            elif len(saved) == 1:
                message = "Generated 1 image"
            else:
                message = "Done (no images generated)"
            
            # Get existing params or create new dict
            job = self._jobs.get(job_id)
            existing_params = job.params if job and job.params else {}
            
            # Update params with quality results and final batch progress
            updated_params = {**existing_params, "quality_results": quality_results}
            if batch_size > 1:
                updated_params["batch_progress"] = {
                    "total": batch_size,
                    "completed": len(saved),
                    "failed": len(failed_images),
                    "processing": batch_size,  # All processed
                }
            
            # Check for low-quality images and auto-retry if enabled
            auto_retry_enabled = existing_params.get("auto_retry_on_low_quality", False)
            quality_threshold = existing_params.get("quality_threshold", 0.6)  # Default threshold
            
            if auto_retry_enabled and len(saved) > 0:
                low_quality_images = [
                    qr for qr in quality_results
                    if qr.get("quality_score") is not None and qr.get("quality_score", 0) < quality_threshold
                ]
                
                if low_quality_images:
                    retry_count = existing_params.get("auto_retry_count", 0)
                    max_retries = existing_params.get("max_auto_retries", 1)
                    
                    if retry_count < max_retries:
                        logger.info(
                            f"Auto-retrying {len(low_quality_images)} low-quality images "
                            f"(retry {retry_count + 1}/{max_retries})",
                            extra={"job_id": job_id, "low_quality_count": len(low_quality_images)},
                        )
                        # Mark for retry (will be handled by caller or separate retry mechanism)
                        updated_params["auto_retry_count"] = retry_count + 1
                        updated_params["low_quality_images"] = [qr["image_path"] for qr in low_quality_images]
                        updated_params["needs_retry"] = True
            
            self._set_job(
                job_id,
                state="succeeded",
                finished_at=time.time(),
                message=message,
                image_path=saved[0] if saved else None,
                image_paths=saved if len(saved) > 1 else None,  # Only set image_paths for batches
                params=updated_params,
            )
        except ComfyUiError as exc:
            if str(exc) == "Cancelled":
                try:
                    client.interrupt()
                except Exception:
                    pass
                self._set_job(
                    job_id,
                    state="cancelled",
                    finished_at=time.time(),
                    cancelled_at=time.time(),
                    message="Cancelled",
                    error=None,
                )
            else:
                self._set_job(job_id, state="failed", finished_at=time.time(), error=str(exc), message="ComfyUI error")
        except Exception as exc:  # noqa: BLE001
            logger.error("Image generation failed", extra={"error": str(exc)})
            self._set_job(job_id, state="failed", finished_at=time.time(), error=str(exc), message="Failed")


generation_service = GenerationService()

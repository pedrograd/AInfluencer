"""Pipeline manager for orchestrating workflow preset execution.

This module provides the PipelineManager that executes workflow presets,
tracks job state, and manages artifacts.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.core.error_taxonomy import ErrorCode, create_error_response
from app.core.logging import get_logger
from app.models.pipeline_contracts import JobHistory
from app.models.workflow_preset import WorkflowPreset
from app.services.artifact_store import ArtifactStore
from app.services.engines.registry import engine_registry
from app.services.job_history import JobHistoryStore
from app.services.job_logger import JobLogger
from app.services.workflow_preset_registry import preset_registry

logger = get_logger(__name__)


class PipelineManager:
    """Manages pipeline job execution and tracking."""

    def __init__(self) -> None:
        """Initialize pipeline manager."""
        self.artifact_store = ArtifactStore()
        self.job_history = JobHistoryStore()
        self.job_logger = JobLogger()

    async def execute_preset(
        self,
        preset_id: str,
        inputs: dict[str, Any],
        quality_level: str = "standard",
        user_id: str | None = None,
    ) -> str:
        """Execute a workflow preset and return job ID.
        
        Args:
            preset_id: Preset identifier
            inputs: Preset inputs (prompt, identity_reference, etc.)
            quality_level: Quality level (low, standard, pro)
            user_id: Optional user ID
            
        Returns:
            Job ID string
            
        Raises:
            ValueError: If preset not found or validation fails
            RuntimeError: If engine is unavailable
        """
        # Get preset
        preset = preset_registry.get_preset(preset_id)
        if not preset:
            raise ValueError(f"Preset not found: {preset_id}")

        # Validate required inputs
        self._validate_inputs(preset, inputs)

        # Check consent if required
        if preset.requires_consent and not inputs.get("consent_given"):
            raise ValueError(
                "Consent required for identity-based workflows. "
                "Set consent_given=True in inputs."
            )

        # Create job
        job_id = str(uuid.uuid4())
        job = JobHistory(
            job_id=job_id,
            preset_id=preset_id,
            user_id=user_id,
            status="queued",
            created_at=datetime.utcnow(),
            quality_level=quality_level,
            inputs=inputs,
            outputs={},
        )
        self.job_history.save_job(job)
        self.job_logger.log_job_event(job_id, "info", f"Job queued for preset: {preset_id}")

        # Execute in background (for MVP, we'll do it synchronously)
        # In production, this would be queued to a worker
        try:
            await self._execute_job(job, preset, quality_level)
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            self.job_history.update_job_status(
                job_id=job_id,
                status="failed",
                error=str(e),
                error_code=ErrorCode.UNKNOWN_ERROR.value,
            )
            self.job_logger.log_job_event(job_id, "error", f"Job failed: {e}")

        return job_id

    def _validate_inputs(self, preset: WorkflowPreset, inputs: dict[str, Any]) -> None:
        """Validate preset inputs.
        
        Args:
            preset: WorkflowPreset instance
            inputs: Input dictionary
            
        Raises:
            ValueError: If validation fails
        """
        # Check required inputs
        for input_name, input_type in preset.required_inputs.items():
            if input_name not in inputs:
                raise ValueError(f"Missing required input: {input_name}")

    async def _execute_job(
        self,
        job: JobHistory,
        preset: WorkflowPreset,
        quality_level: str,
    ) -> None:
        """Execute a job with the given preset.
        
        Args:
            job: JobHistory instance
            preset: WorkflowPreset instance
            quality_level: Quality level
        """
        job_id = job.job_id

        # Update status to running
        self.job_history.update_job_status(job_id, "running")
        self.job_logger.log_job_event(job_id, "info", "Job started")

        # Get quality level config
        quality_config = preset.quality_levels.get(quality_level, preset.quality_levels.get("standard", {}))

        # Get engine
        engine_id = preset.engine_requirements[0] if preset.engine_requirements else "local_comfy"
        engine = engine_registry.get_engine(engine_id)
        if not engine:
            raise RuntimeError(f"Engine not available: {engine_id}")

        # Check engine health
        is_healthy = await engine.health_check()
        if not is_healthy:
            raise RuntimeError(
                f"Engine {engine_id} is not available. "
                "Check Setup Hub to start the engine."
            )

        # Execute pipeline steps
        # For Phase 1, we only support simple image generation
        if preset.category == "image_generation":
            # Extract generation parameters
            prompt = job.inputs.get("prompt", "")
            negative_prompt = job.inputs.get("negative_prompt")
            seed = job.inputs.get("seed")

            # Merge quality config into generation params
            generation_params = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "steps": quality_config.get("steps", 25),
                "cfg": quality_config.get("cfg", 7.0),
                **quality_config,  # Include other quality settings
            }

            self.job_logger.log_job_event(
                job_id,
                "info",
                f"Generating image with {engine_id}",
                {"params": generation_params},
            )

            # Generate image
            result = await engine.generate_image(**generation_params)
            output_path = result.get("output_path") or result.get("output_url")

            if not output_path:
                raise RuntimeError("Engine returned result without output path")

            # Save artifact
            artifact_path = self.artifact_store.save_artifact(
                job_id=job_id,
                artifact_type="image",
                file_path=output_path,
                metadata={
                    "preset_id": preset.id,
                    "quality_level": quality_level,
                    "engine_id": engine_id,
                },
            )

            # Update job with output
            self.job_history.update_job_status(
                job_id=job_id,
                status="completed",
                output_url=artifact_path,
            )
            job.outputs["image"] = artifact_path
            job.outputs["output_url"] = artifact_path
            self.job_history.save_job(job)

            self.job_logger.log_job_event(job_id, "info", "Job completed successfully")
        else:
            raise ValueError(f"Unsupported preset category: {preset.category}")

    async def get_job_status(self, job_id: str) -> JobHistory | None:
        """Get current status of a pipeline job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobHistory instance or None if not found
        """
        return self.job_history.get_job(job_id)

    async def cancel_job(self, job_id: str) -> None:
        """Cancel a running pipeline job.
        
        Args:
            job_id: Job identifier
        """
        job = self.job_history.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status in ("completed", "failed", "cancelled"):
            raise ValueError(f"Job {job_id} is already {job.status}")

        self.job_history.update_job_status(job_id, "cancelled")
        self.job_logger.log_job_event(job_id, "info", "Job cancelled by user")


# Global pipeline manager instance
pipeline_manager = PipelineManager()

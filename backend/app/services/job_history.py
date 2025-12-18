"""Job history persistence service.

This module provides file-based persistence for pipeline job history.
Each job is stored as a JSON file with complete execution details.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.paths import data_dir
from app.core.logging import get_logger
from app.models.pipeline_contracts import JobHistory
from app.services.job_logger import redact_secrets

logger = get_logger(__name__)


class JobHistoryStore:
    """File-based job history storage."""

    def __init__(self, jobs_dir: Path | None = None) -> None:
        """Initialize job history store.
        
        Args:
            jobs_dir: Base directory for job history (defaults to data_dir() / "jobs")
        """
        self.jobs_dir = jobs_dir or (data_dir() / "jobs")
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def save_job(self, job: JobHistory) -> None:
        """Save job history to file.
        
        Args:
            job: JobHistory model instance
        """
        # Redact secrets from inputs
        redacted_inputs = redact_secrets(job.inputs) if job.inputs else {}

        # Create job data dict
        job_data = job.model_dump()
        job_data["inputs"] = redacted_inputs

        # Save to JSON file
        job_file = self.jobs_dir / f"{job.job_id}.json"
        with open(job_file, "w") as f:
            json.dump(job_data, f, indent=2, default=str)

        logger.debug(f"Saved job history: {job_file}")

    def get_job(self, job_id: str) -> JobHistory | None:
        """Get job history by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobHistory instance or None if not found
        """
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None

        try:
            with open(job_file, "r") as f:
                job_data = json.load(f)
            return JobHistory(**job_data)
        except Exception as e:
            logger.error(f"Failed to load job history {job_id}: {e}")
            return None

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: float | None = None,
        error: str | None = None,
        error_code: str | None = None,
        remediation: list[str] | None = None,
        output_url: str | None = None,
    ) -> bool:
        """Update job status in history.
        
        Args:
            job_id: Job identifier
            status: New status
            progress: Optional progress (0.0 to 1.0)
            error: Optional error message
            error_code: Optional error taxonomy code
            remediation: Optional remediation steps
            output_url: Optional output URL
            
        Returns:
            True if job was found and updated, False otherwise
        """
        job = self.get_job(job_id)
        if not job:
            return False

        # Update fields
        job.status = status  # type: ignore[assignment]
        if progress is not None:
            # Store progress in inputs metadata for tracking
            if not isinstance(job.inputs, dict):
                job.inputs = {}
            if "metadata" not in job.inputs:
                job.inputs["metadata"] = {}
            job.inputs["metadata"]["progress"] = progress
        if error is not None:
            job.error = error
        if error_code is not None:
            job.error_code = error_code
        if remediation is not None:
            job.remediation = remediation
        if output_url is not None:
            job.outputs["output_url"] = output_url

        # Update timestamps
        now = datetime.utcnow()
        if status == "running" and job.started_at is None:
            job.started_at = now
        if status in ("completed", "failed", "cancelled") and job.finished_at is None:
            job.finished_at = now

        # Save updated job
        self.save_job(job)
        return True

    def list_jobs(
        self,
        limit: int = 100,
        status: str | None = None,
        preset_id: str | None = None,
    ) -> list[JobHistory]:
        """List recent jobs with optional filtering.
        
        Args:
            limit: Maximum number of jobs to return
            status: Optional status filter
            preset_id: Optional preset ID filter
            
        Returns:
            List of JobHistory instances, sorted by created_at descending
        """
        jobs: list[JobHistory] = []

        # Scan job files
        for job_file in self.jobs_dir.glob("*.json"):
            if job_file.name == "metadata.json":
                continue

            try:
                job = self.get_job(job_file.stem)
                if job:
                    # Apply filters
                    if status and job.status != status:
                        continue
                    if preset_id and job.preset_id != preset_id:
                        continue
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"Failed to load job from {job_file}: {e}")

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return jobs[:limit]

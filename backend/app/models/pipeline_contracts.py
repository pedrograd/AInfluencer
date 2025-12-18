"""Data contracts for pipeline and workflow system.

This module defines strict Pydantic models for pipeline-related API requests
and responses to prevent schema drift and 422 errors.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


class GenerateRequest(BaseModel):
    """Request model for generating content using a workflow preset.
    
    This is the new pipeline-based generation request that uses preset_id
    instead of individual generation parameters.
    """
    
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields
    
    preset_id: str = Field(..., min_length=1, description="Workflow preset identifier")
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt describing the content to generate")
    negative_prompt: str | None = Field(default=None, max_length=2000, description="Negative prompt describing what to avoid")
    quality_level: Literal["low", "standard", "pro"] = Field(default="standard", description="Quality level: low, standard, or pro")
    seed: int | None = Field(default=None, ge=0, le=2**32, description="Random seed for reproducibility")
    identity_reference: list[str] | None = Field(default=None, description="List of image file paths for identity consistency")
    consent_given: bool = Field(default=False, description="Required if identity_reference is provided")


class GenerateResponse(BaseModel):
    """Response model for generation job creation."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: Literal["queued", "running", "completed", "failed"] = Field(..., description="Current job status")
    preset_id: str = Field(..., description="Preset ID used for generation")
    estimated_time_seconds: int | None = Field(default=None, description="Estimated completion time in seconds")
    output_url: str | None = Field(default=None, description="Output file URL (available when status == 'completed')")
    error: str | None = Field(default=None, description="Error message (available when status == 'failed')")


class JobStatus(BaseModel):
    """Current status of a pipeline job."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: Literal["queued", "running", "completed", "failed", "cancelled"] = Field(..., description="Current job status")
    preset_id: str = Field(..., description="Preset ID used for generation")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Job progress (0.0 to 1.0)")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: datetime | None = Field(default=None, description="Job start timestamp")
    finished_at: datetime | None = Field(default=None, description="Job completion timestamp")
    estimated_time_seconds: int | None = Field(default=None, description="Estimated completion time in seconds")
    output_url: str | None = Field(default=None, description="Output file URL (available when completed)")
    error: str | None = Field(default=None, description="Error message (available when failed)")
    error_code: str | None = Field(default=None, description="Error taxonomy code (available when failed)")


class JobHistory(BaseModel):
    """Complete job history record with inputs and outputs."""
    
    job_id: str = Field(..., description="Unique job identifier")
    preset_id: str = Field(..., description="Preset ID used for generation")
    user_id: str | None = Field(default=None, description="User ID who created the job")
    status: Literal["queued", "running", "completed", "failed", "cancelled"] = Field(..., description="Final job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: datetime | None = Field(default=None, description="Job start timestamp")
    finished_at: datetime | None = Field(default=None, description="Job completion timestamp")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Preset inputs (secrets redacted)")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output artifacts (paths/URLs)")
    engine_used: str | None = Field(default=None, description="Engine adapter ID used")
    quality_level: str = Field(..., description="Quality level used (low, standard, pro)")
    credit_cost: int = Field(default=0, description="Credit cost for this job")
    error: str | None = Field(default=None, description="Error message (if failed)")
    error_code: str | None = Field(default=None, description="Error taxonomy code (if failed)")
    remediation: list[str] | None = Field(default=None, description="Remediation steps (if failed)")
    logs: list[str] = Field(default_factory=list, description="Log entries (secrets redacted)")

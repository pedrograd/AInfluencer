"""Workflow preset schema for pipeline system.

This module defines the WorkflowPreset model that describes executable
workflow presets with engine requirements, quality levels, and pipeline steps.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


class WorkflowPreset(BaseModel):
    """Workflow preset definition.
    
    Each preset defines a complete workflow configuration including:
    - Required inputs (prompt, image, audio, etc.)
    - Engine requirements (local_comfy, provider_kling, etc.)
    - Quality level mappings (low, standard, pro)
    - Pipeline steps for multi-step workflows
    - Safety notes and consent requirements
    """

    model_config = ConfigDict(extra="forbid")  # Reject unknown fields

    id: str = Field(..., description="Unique preset identifier")
    name: str = Field(..., description="Human-readable preset name")
    description: str = Field(..., description="Description of what the preset does")
    category: Literal[
        "image_generation",
        "video_generation",
        "character_performance",
        "post_processing",
        "hybrid_pipeline",
    ] = Field(..., description="Preset category")

    # Input requirements
    required_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Required inputs mapping (e.g., {'prompt': 'str', 'image': 'file'})",
    )
    optional_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional inputs mapping",
    )

    # Engine requirements
    engine_requirements: list[str] = Field(
        default_factory=list,
        description="List of required engine IDs (e.g., ['local_comfy', 'provider_kling'])",
    )
    engine_preference_order: list[str] = Field(
        default_factory=list,
        description="Preferred engine order if multiple available",
    )

    # Quality levels
    quality_levels: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Quality level configurations (e.g., {'low': {'steps': 20}, 'standard': {'steps': 30}})",
    )

    # Pipeline steps (for multi-step workflows)
    pipeline_steps: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Pipeline step definitions (e.g., [{'step': 'generate_image', 'engine': 'local_comfy'}])",
    )

    # Safety notes
    safety_notes: list[str] = Field(
        default_factory=list,
        description="Safety notes and warnings",
    )
    requires_consent: bool = Field(
        default=False,
        description="Whether this preset requires consent (for identity-based workflows)",
    )

    # Failure modes + remediation
    failure_modes: dict[str, str] = Field(
        default_factory=dict,
        description="Error code → user-facing message mapping",
    )

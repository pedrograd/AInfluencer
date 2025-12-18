"""Workflow preset registry.

This module provides a registry of curated workflow presets for Phase 1.
Presets are defined as Python dictionaries and loaded into WorkflowPreset models.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.models.workflow_preset import WorkflowPreset

logger = get_logger(__name__)


# Phase 1 Presets (Local ComfyUI only)
PHASE1_PRESETS: dict[str, dict[str, Any]] = {
    "photoreal_portrait_v1": {
        "id": "photoreal_portrait_v1",
        "name": "Photoreal Portrait (Anti-Plastic)",
        "description": "Zero 'AI smooth skin' look. Natural skin texture with visible pores.",
        "category": "image_generation",
        "required_inputs": {
            "prompt": "str",
        },
        "optional_inputs": {
            "identity_reference": "list[str]",  # 1-3 reference photos
            "seed": "int",
        },
        "engine_requirements": ["local_comfy"],
        "engine_preference_order": ["local_comfy"],
        "quality_levels": {
            "low": {
                "steps": 25,
                "cfg": 6.5,
                "face_restoration": False,
                "upscale": False,
            },
            "standard": {
                "steps": 40,
                "cfg": 7.5,
                "face_restoration": True,
                "upscale": False,
            },
            "pro": {
                "steps": 50,
                "cfg": 8.0,
                "face_restoration": True,
                "upscale": 2,
            },
        },
        "pipeline_steps": [
            {
                "step": "generate_image",
                "engine": "local_comfy",
                "description": "Generate image with anti-plastic prompt",
            },
            {
                "step": "apply_face_restoration",
                "engine": "local_comfy",
                "condition": "quality_level in ['standard', 'pro']",
                "description": "Apply GFPGAN face restoration if enabled",
            },
            {
                "step": "upscale",
                "engine": "local_comfy",
                "condition": "quality_level == 'pro'",
                "description": "Upscale 2x if quality level is pro",
            },
        ],
        "safety_notes": [
            "If identity_reference provided: Requires consent checkbox",
            "Content restrictions: No NSFW generation",
        ],
        "requires_consent": False,  # Only if identity_reference provided
        "failure_modes": {
            "ENGINE_OFFLINE": "ComfyUI is not running. Click 'Start ComfyUI' in Setup.",
            "DEPENDENCY_MISSING": "Required checkpoint not found. Install model in Model Manager.",
        },
    },
    "cinematic_portrait_v1": {
        "id": "cinematic_portrait_v1",
        "name": "Cinematic Portrait (Film Look)",
        "description": "Film grain, cinematic color grading, anamorphic lens look.",
        "category": "image_generation",
        "required_inputs": {
            "prompt": "str",
        },
        "optional_inputs": {
            "identity_reference": "list[str]",
            "seed": "int",
        },
        "engine_requirements": ["local_comfy"],
        "engine_preference_order": ["local_comfy"],
        "quality_levels": {
            "low": {
                "steps": 30,
                "cfg": 7.0,
                "film_grain": True,
                "tone_mapping": False,
                "color_grading": False,
            },
            "standard": {
                "steps": 35,
                "cfg": 7.5,
                "film_grain": True,
                "tone_mapping": True,
                "color_grading": False,
            },
            "pro": {
                "steps": 40,
                "cfg": 8.0,
                "film_grain": True,
                "tone_mapping": True,
                "color_grading": True,
            },
        },
        "pipeline_steps": [
            {
                "step": "generate_image",
                "engine": "local_comfy",
                "description": "Generate image with cinematic prompt",
            },
            {
                "step": "apply_film_grain",
                "engine": "local_comfy",
                "description": "Apply film grain overlay",
            },
            {
                "step": "apply_tone_mapping",
                "engine": "local_comfy",
                "condition": "quality_level in ['standard', 'pro']",
                "description": "Apply tone mapping (Reinhard method)",
            },
            {
                "step": "apply_color_grading",
                "engine": "local_comfy",
                "condition": "quality_level == 'pro'",
                "description": "Apply color grading",
            },
        ],
        "safety_notes": [
            "Same as Photoreal Portrait",
        ],
        "requires_consent": False,
        "failure_modes": {
            "ENGINE_OFFLINE": "ComfyUI is not running. Click 'Start ComfyUI' in Setup.",
            "DEPENDENCY_MISSING": "Required checkpoint not found. Install model in Model Manager.",
        },
    },
    "identity_lock_portrait_v1": {
        "id": "identity_lock_portrait_v1",
        "name": "Identity Lock Portrait (Consistency)",
        "description": "Consistent face across different scenes/outfits using IP-Adapter or InstantID.",
        "category": "image_generation",
        "required_inputs": {
            "prompt": "str",
            "identity_reference": "list[str]",  # 1-3 reference photos (required)
        },
        "optional_inputs": {
            "seed": "int",
        },
        "engine_requirements": ["local_comfy"],
        "engine_preference_order": ["local_comfy"],
        "quality_levels": {
            "low": {
                "steps": 30,
                "cfg": 7.0,
                "ip_adapter_weight": 0.6,
                "face_restoration": False,
            },
            "standard": {
                "steps": 35,
                "cfg": 7.5,
                "ip_adapter_weight": 0.75,
                "face_restoration": False,
            },
            "pro": {
                "steps": 40,
                "cfg": 8.0,
                "ip_adapter_weight": 0.8,
                "face_restoration": True,
            },
        },
        "pipeline_steps": [
            {
                "step": "load_identity_reference",
                "engine": "local_comfy",
                "description": "Load identity reference images",
            },
            {
                "step": "generate_image_with_identity",
                "engine": "local_comfy",
                "description": "Generate image with identity lock enabled",
            },
            {
                "step": "apply_face_restoration",
                "engine": "local_comfy",
                "condition": "quality_level == 'pro'",
                "description": "Apply face restoration if Pro quality",
            },
        ],
        "safety_notes": [
            "REQUIRES CONSENT: User must checkbox 'I have permission to use this face'",
            "Content restrictions: No NSFW generation",
        ],
        "requires_consent": True,  # Always required for identity lock
        "failure_modes": {
            "ENGINE_OFFLINE": "ComfyUI is not running. Click 'Start ComfyUI' in Setup.",
            "DEPENDENCY_MISSING": "IP-Adapter or InstantID extension not installed. Install in ComfyUI.",
            "CONSENT_MISSING": "Identity-based workflows require consent. Check the consent box.",
        },
    },
}


class WorkflowPresetRegistry:
    """Registry for workflow presets."""

    def __init__(self) -> None:
        """Initialize preset registry."""
        self._presets: dict[str, WorkflowPreset] = {}
        self._load_presets()

    def _load_presets(self) -> None:
        """Load presets from registry."""
        for preset_id, preset_data in PHASE1_PRESETS.items():
            try:
                preset = WorkflowPreset(**preset_data)
                self._presets[preset_id] = preset
                logger.debug(f"Loaded preset: {preset_id}")
            except Exception as e:
                logger.error(f"Failed to load preset {preset_id}: {e}")

    def get_preset(self, preset_id: str) -> WorkflowPreset | None:
        """Get preset by ID.
        
        Args:
            preset_id: Preset identifier
            
        Returns:
            WorkflowPreset instance or None if not found
        """
        return self._presets.get(preset_id)

    def list_presets(
        self,
        category: str | None = None,
        engine_requirement: str | None = None,
    ) -> list[WorkflowPreset]:
        """List all presets with optional filtering.
        
        Args:
            category: Optional category filter
            engine_requirement: Optional engine requirement filter
            
        Returns:
            List of WorkflowPreset instances
        """
        presets = list(self._presets.values())

        if category:
            presets = [p for p in presets if p.category == category]

        if engine_requirement:
            presets = [
                p
                for p in presets
                if engine_requirement in p.engine_requirements
            ]

        return presets

    def preset_exists(self, preset_id: str) -> bool:
        """Check if preset exists.
        
        Args:
            preset_id: Preset identifier
            
        Returns:
            True if preset exists, False otherwise
        """
        return preset_id in self._presets


# Global registry instance
preset_registry = WorkflowPresetRegistry()

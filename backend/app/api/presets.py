"""Image generation presets API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Preset(BaseModel):
    """Preset configuration for image generation with predefined settings."""
    id: str
    name: str
    description: str
    category: str
    prompt_template: str | None = None
    negative_prompt: str | None = None
    width: int | None = None
    height: int | None = None
    steps: int | None = None
    cfg: float | None = None
    sampler_name: str | None = None
    scheduler: str | None = None
    batch_size: int | None = None
    checkpoint: str | None = None


# Preset catalog - curated workflows
PRESETS: dict[str, dict[str, Any]] = {
    "portrait": {
        "id": "portrait",
        "name": "Portrait",
        "description": "High-quality portrait photography style",
        "category": "photography",
        "prompt_template": "portrait of {subject}, professional photography, high quality, detailed",
        "negative_prompt": "blurry, low quality, distorted, deformed",
        "width": 1024,
        "height": 1024,
        "steps": 30,
        "cfg": 7.0,
        "sampler_name": "euler",
        "scheduler": "normal",
        "batch_size": 1,
    },
    "fashion": {
        "id": "fashion",
        "name": "Fashion",
        "description": "Fashion photography and styling",
        "category": "photography",
        "prompt_template": "fashion photography, {subject}, stylish outfit, professional lighting, high quality",
        "negative_prompt": "casual clothing, low quality, amateur",
        "width": 1024,
        "height": 1536,
        "steps": 30,
        "cfg": 7.5,
        "sampler_name": "euler",
        "scheduler": "normal",
        "batch_size": 1,
    },
    "product": {
        "id": "product",
        "name": "Product",
        "description": "Product photography with clean backgrounds",
        "category": "commercial",
        "prompt_template": "product photography of {subject}, white background, studio lighting, professional, high quality",
        "negative_prompt": "cluttered background, shadows, low quality",
        "width": 1024,
        "height": 1024,
        "steps": 25,
        "cfg": 7.0,
        "sampler_name": "euler",
        "scheduler": "normal",
        "batch_size": 1,
    },
    "landscape": {
        "id": "landscape",
        "name": "Landscape",
        "description": "Scenic landscape photography",
        "category": "photography",
        "prompt_template": "landscape photography, {subject}, scenic view, natural lighting, high quality, detailed",
        "negative_prompt": "blurry, low quality, distorted",
        "width": 1536,
        "height": 1024,
        "steps": 30,
        "cfg": 7.0,
        "sampler_name": "euler",
        "scheduler": "normal",
        "batch_size": 1,
    },
    "artistic": {
        "id": "artistic",
        "name": "Artistic",
        "description": "Artistic and creative style",
        "category": "art",
        "prompt_template": "artistic style, {subject}, creative, unique composition, high quality",
        "negative_prompt": "generic, boring, low quality",
        "width": 1024,
        "height": 1024,
        "steps": 35,
        "cfg": 8.0,
        "sampler_name": "euler",
        "scheduler": "normal",
        "batch_size": 1,
    },
    "realistic": {
        "id": "realistic",
        "name": "Realistic",
        "description": "Ultra-realistic, photorealistic style",
        "category": "photography",
        "prompt_template": "photorealistic, {subject}, ultra realistic, highly detailed, 8k, professional photography",
        "negative_prompt": "cartoon, anime, painting, drawing, illustration, low quality",
        "width": 1024,
        "height": 1024,
        "steps": 40,
        "cfg": 7.0,
        "sampler_name": "euler",
        "scheduler": "normal",
        "batch_size": 1,
    },
    "instagram": {
        "id": "instagram",
        "name": "Instagram",
        "description": "Optimized for Instagram square format",
        "category": "social",
        "prompt_template": "{subject}, instagram style, vibrant colors, high quality, social media",
        "negative_prompt": "blurry, low quality, distorted",
        "width": 1024,
        "height": 1024,
        "steps": 25,
        "cfg": 7.0,
        "sampler_name": "euler",
        "scheduler": "normal",
        "batch_size": 1,
    },
    "story": {
        "id": "story",
        "name": "Story",
        "description": "Vertical format for Instagram Stories",
        "category": "social",
        "prompt_template": "{subject}, instagram story format, vertical, vibrant, high quality",
        "negative_prompt": "blurry, low quality, distorted",
        "width": 1024,
        "height": 1920,
        "steps": 25,
        "cfg": 7.0,
        "sampler_name": "euler",
        "scheduler": "normal",
        "batch_size": 1,
    },
}


@router.get("/presets")
def list_presets(category: str | None = None) -> dict:
    """List all available presets, optionally filtered by category."""
    items = list(PRESETS.values())
    if category:
        items = [p for p in items if p.get("category") == category]
    return {
        "ok": True,
        "items": items,
        "categories": sorted(set(p.get("category", "other") for p in PRESETS.values())),
    }


@router.get("/presets/{preset_id}")
def get_preset(preset_id: str) -> dict:
    """Get a specific preset by ID."""
    preset = PRESETS.get(preset_id)
    if not preset:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "preset": preset}


"""API router aggregation module.

This module aggregates all API routers from individual endpoint modules
and registers them with appropriate prefixes and tags for the main
FastAPI application.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.characters import router as characters_router
from app.api.comfyui import router as comfyui_router
from app.api.content import router as content_router
from app.api.errors import router as errors_router
from app.api.generate import router as generate_router
from app.api.health import router as health_router
from app.api.installer import router as installer_router
from app.api.logs import router as logs_router
from app.api.models import router as models_router
from app.api.presets import router as presets_router
from app.api.services import router as services_router
from app.api.scheduling import router as scheduling_router
from app.api.settings import router as settings_router
from app.api.status import router as status_router
from app.api.video_editing import router as video_editing_router
from app.api.video_storage import router as video_storage_router
from app.api.voice import router as voice_router
from app.api.workflows import router as workflows_router

router = APIRouter()
router.include_router(health_router, tags=["system"])
router.include_router(status_router, tags=["system"])
router.include_router(errors_router, tags=["system"])
router.include_router(logs_router, tags=["system"])
router.include_router(services_router, prefix="/services", tags=["services"])
router.include_router(installer_router, prefix="/installer", tags=["installer"])
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(generate_router, prefix="/generate", tags=["generate"])
router.include_router(presets_router, prefix="/generate", tags=["generate"])
router.include_router(content_router, prefix="/content", tags=["content"])
router.include_router(comfyui_router, prefix="/comfyui", tags=["comfyui"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])
router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
router.include_router(characters_router, prefix="/characters", tags=["characters"])
router.include_router(scheduling_router, prefix="/scheduling", tags=["scheduling"])
router.include_router(video_editing_router, prefix="/video", tags=["video"])
router.include_router(video_storage_router, prefix="/content", tags=["content"])
router.include_router(voice_router, prefix="/voice", tags=["voice"])

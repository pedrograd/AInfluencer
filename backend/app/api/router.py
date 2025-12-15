from __future__ import annotations

from fastapi import APIRouter

from app.api.comfyui import router as comfyui_router
from app.api.content import router as content_router
from app.api.errors import router as errors_router
from app.api.generate import router as generate_router
from app.api.health import router as health_router
from app.api.installer import router as installer_router
from app.api.logs import router as logs_router
from app.api.models import router as models_router
from app.api.presets import router as presets_router
from app.api.settings import router as settings_router
from app.api.status import router as status_router

router = APIRouter()
router.include_router(health_router, tags=["system"])
router.include_router(status_router, tags=["system"])
router.include_router(errors_router, prefix="/errors", tags=["system"])
router.include_router(logs_router, tags=["system"])
router.include_router(installer_router, prefix="/installer", tags=["installer"])
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(generate_router, prefix="/generate", tags=["generate"])
router.include_router(presets_router, prefix="/generate", tags=["generate"])
router.include_router(content_router, prefix="/content", tags=["content"])
router.include_router(comfyui_router, prefix="/comfyui", tags=["comfyui"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])

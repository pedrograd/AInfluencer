from __future__ import annotations

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.installer import router as installer_router
from app.api.models import router as models_router

router = APIRouter()
router.include_router(health_router, tags=["system"])
router.include_router(installer_router, prefix="/installer", tags=["installer"])
router.include_router(models_router, prefix="/models", tags=["models"])

from __future__ import annotations

from fastapi import APIRouter

from app.services.generation_service import generation_service

router = APIRouter()


@router.get("/images")
def list_images() -> dict:
    return {"items": generation_service.list_images(limit=100)}

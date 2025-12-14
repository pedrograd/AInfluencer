from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.services.comfyui_client import ComfyUiClient, ComfyUiError

router = APIRouter()


@router.get("/status")
def comfyui_status() -> dict:
    client = ComfyUiClient()
    try:
        stats = client.get_system_stats()
        return {"ok": True, "base_url": settings.comfyui_base_url, "stats": stats}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": settings.comfyui_base_url, "error": str(exc)}


@router.get("/checkpoints")
def comfyui_checkpoints() -> dict:
    client = ComfyUiClient()
    try:
        checkpoints = client.list_checkpoints()
        return {"ok": True, "base_url": settings.comfyui_base_url, "checkpoints": checkpoints}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": settings.comfyui_base_url, "error": str(exc), "checkpoints": []}


@router.get("/samplers")
def comfyui_samplers() -> dict:
    client = ComfyUiClient()
    try:
        samplers = client.list_samplers()
        return {"ok": True, "base_url": settings.comfyui_base_url, "samplers": samplers}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": settings.comfyui_base_url, "error": str(exc), "samplers": []}


@router.get("/schedulers")
def comfyui_schedulers() -> dict:
    client = ComfyUiClient()
    try:
        schedulers = client.list_schedulers()
        return {"ok": True, "base_url": settings.comfyui_base_url, "schedulers": schedulers}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": settings.comfyui_base_url, "error": str(exc), "schedulers": []}

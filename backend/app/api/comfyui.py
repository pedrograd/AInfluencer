from __future__ import annotations

from fastapi import APIRouter

from app.core.runtime_settings import get_comfyui_base_url
from app.services.comfyui_client import ComfyUiClient, ComfyUiError

router = APIRouter()


@router.get("/status")
def comfyui_status() -> dict:
    client = ComfyUiClient()
    base = get_comfyui_base_url()
    try:
        stats = client.get_system_stats()
        return {"ok": True, "base_url": base.value, "base_url_source": base.source, "stats": stats}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": base.value, "base_url_source": base.source, "error": str(exc)}


@router.get("/checkpoints")
def comfyui_checkpoints() -> dict:
    client = ComfyUiClient()
    base = get_comfyui_base_url()
    try:
        checkpoints = client.list_checkpoints()
        return {"ok": True, "base_url": base.value, "base_url_source": base.source, "checkpoints": checkpoints}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": base.value, "base_url_source": base.source, "error": str(exc), "checkpoints": []}


@router.get("/samplers")
def comfyui_samplers() -> dict:
    client = ComfyUiClient()
    base = get_comfyui_base_url()
    try:
        samplers = client.list_samplers()
        return {"ok": True, "base_url": base.value, "base_url_source": base.source, "samplers": samplers}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": base.value, "base_url_source": base.source, "error": str(exc), "samplers": []}


@router.get("/schedulers")
def comfyui_schedulers() -> dict:
    client = ComfyUiClient()
    base = get_comfyui_base_url()
    try:
        schedulers = client.list_schedulers()
        return {"ok": True, "base_url": base.value, "base_url_source": base.source, "schedulers": schedulers}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": base.value, "base_url_source": base.source, "error": str(exc), "schedulers": []}

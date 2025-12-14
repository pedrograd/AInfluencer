from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.runtime_settings import get_comfyui_base_url, read_settings, update_settings

router = APIRouter()


class SettingsResponse(BaseModel):
    comfyui_base_url: str
    comfyui_base_url_source: str
    persisted: dict


class SettingsUpdateRequest(BaseModel):
    comfyui_base_url: str | None = None


@router.get("")
def get_settings() -> SettingsResponse:
    base = get_comfyui_base_url()
    return SettingsResponse(
        comfyui_base_url=base.value,
        comfyui_base_url_source=base.source,
        persisted=read_settings(),
    )


@router.put("")
def put_settings(req: SettingsUpdateRequest) -> SettingsResponse:
    try:
        persisted = update_settings(comfyui_base_url=req.comfyui_base_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    base = get_comfyui_base_url()
    return SettingsResponse(
        comfyui_base_url=base.value,
        comfyui_base_url_source=base.source,
        persisted=persisted,
    )


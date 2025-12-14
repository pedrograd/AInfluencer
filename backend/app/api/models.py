from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.model_manager import model_manager

router = APIRouter()


class DownloadRequest(BaseModel):
    model_id: str


@router.get("/catalog")
def catalog() -> dict:
    return {"items": model_manager.catalog()}


@router.get("/installed")
def installed() -> dict:
    return {"items": model_manager.installed()}


@router.get("/downloads/status")
def download_status() -> dict:
    return model_manager.download_status()


@router.post("/downloads/start")
def start_download(req: DownloadRequest) -> dict:
    model_manager.start_download(req.model_id)
    return {"ok": True}

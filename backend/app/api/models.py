from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.model_manager import model_manager

router = APIRouter()


class DownloadRequest(BaseModel):
    model_id: str


class CancelRequest(BaseModel):
    download_id: str


@router.get("/catalog")
def catalog() -> dict:
    return {"items": model_manager.catalog()}


@router.get("/installed")
def installed() -> dict:
    return {"items": model_manager.installed()}


@router.get("/downloads/active")
def active() -> dict:
    return {"item": model_manager.active()}


@router.get("/downloads/queue")
def queue() -> dict:
    return {"items": model_manager.queue()}


@router.get("/downloads/items")
def items() -> dict:
    return {"items": model_manager.items()}


@router.post("/downloads/enqueue")
def enqueue(req: DownloadRequest) -> dict:
    item = model_manager.enqueue_download(req.model_id)
    return {"ok": True, "item": item}


@router.post("/downloads/cancel")
def cancel(req: CancelRequest) -> dict:
    item = model_manager.cancel(req.download_id)
    return {"ok": True, "item": item}

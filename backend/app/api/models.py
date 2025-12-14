from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi import File, Form, UploadFile
from pydantic import BaseModel
from typing import cast

from app.services.model_manager import ModelType, model_manager

router = APIRouter()


class DownloadRequest(BaseModel):
    model_id: str


class CancelRequest(BaseModel):
    download_id: str


class VerifyRequest(BaseModel):
    path: str


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


@router.post("/import")
async def import_model(
    file: UploadFile = File(...),
    model_type: str = Form("other"),
) -> dict:
    allowed = {"checkpoint", "lora", "embedding", "controlnet", "other"}
    if model_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid model_type. Allowed: {sorted(allowed)}")
    content = await file.read()
    imported = model_manager.import_file(
        file.filename or "model.bin",
        content=content,
        model_type=cast(ModelType, model_type),
    )
    return {"ok": True, "item": imported}


@router.post("/verify")
def verify(req: VerifyRequest) -> dict:
    try:
        result = model_manager.verify_sha256(req.path)
        return {"ok": True, "item": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

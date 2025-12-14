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


class AddCustomModelRequest(BaseModel):
    name: str
    type: str = "other"
    url: str
    filename: str
    tier: int = 3
    tags: list[str] | None = None
    sha256: str | None = None
    notes: str | None = None


@router.get("/catalog")
def catalog() -> dict:
    return {"items": model_manager.catalog()}


@router.get("/installed")
def installed() -> dict:
    return {"items": model_manager.installed()}


@router.get("/catalog/custom")
def custom_catalog() -> dict:
    return {"items": model_manager.custom_catalog()}


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
    try:
        item = model_manager.enqueue_download(req.model_id)
        return {"ok": True, "item": item}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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


@router.post("/catalog/custom")
def add_custom(req: AddCustomModelRequest) -> dict:
    allowed = {"checkpoint", "lora", "embedding", "controlnet", "other"}
    if req.type not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid type. Allowed: {sorted(allowed)}")
    try:
        item = model_manager.add_custom_model(
            name=req.name,
            model_type=cast(ModelType, req.type),
            url=req.url,
            filename=req.filename,
            tier=req.tier,
            tags=req.tags,
            sha256=req.sha256,
            notes=req.notes,
        )
        return {"ok": True, "item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/catalog/custom/{model_id}")
def delete_custom(model_id: str) -> dict:
    try:
        model_manager.delete_custom_model(model_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/catalog/custom/{model_id}")
def update_custom(model_id: str, req: AddCustomModelRequest) -> dict:
    allowed = {"checkpoint", "lora", "embedding", "controlnet", "other"}
    if req.type not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid type. Allowed: {sorted(allowed)}")
    try:
        item = model_manager.update_custom_model(
            model_id,
            name=req.name,
            model_type=cast(ModelType, req.type),
            url=req.url,
            filename=req.filename,
            tier=req.tier,
            tags=req.tags,
            sha256=req.sha256,
            notes=req.notes,
        )
        return {"ok": True, "item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

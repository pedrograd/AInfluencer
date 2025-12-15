"""Model management API endpoints for downloading, importing, and verifying models.

This module provides API endpoints for managing AI models including:
- Model catalog browsing and listing
- Model download queue management
- Model import from files
- Model verification (checksum validation)
- Model deletion and organization
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi import File, Form, UploadFile
from pydantic import BaseModel
from typing import cast

from app.services.model_manager import ModelType, model_manager

router = APIRouter()


class DownloadRequest(BaseModel):
    """Request model for enqueueing a model download."""

    model_id: str


class CancelRequest(BaseModel):
    """Request model for cancelling a model download."""

    download_id: str


class VerifyRequest(BaseModel):
    """Request model for verifying a model file's SHA256 checksum."""

    path: str


class AddCustomModelRequest(BaseModel):
    """Request model for adding a custom model to the catalog."""
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
    """
    Get the model catalog.
    
    Returns the complete catalog of available models including built-in and custom models.
    
    Returns:
        dict: List of catalog items with model metadata
    """
    return {"items": model_manager.catalog()}


@router.get("/installed")
def installed() -> dict:
    """
    Get list of installed models.
    
    Returns information about all models currently installed in the model directory.
    
    Returns:
        dict: List of installed model items with file paths and metadata
    """
    return {"items": model_manager.installed()}


@router.get("/catalog/custom")
def custom_catalog() -> dict:
    """
    Get custom model catalog.
    
    Returns only the custom models added by the user (not built-in catalog items).
    
    Returns:
        dict: List of custom catalog items
    """
    return {"items": model_manager.custom_catalog()}


@router.get("/downloads/active")
def active() -> dict:
    """
    Get currently active download.
    
    Returns the download that is currently in progress, if any.
    
    Returns:
        dict: Active download item or None if no download is active
    """
    return {"item": model_manager.active()}


@router.get("/downloads/queue")
def queue() -> dict:
    """
    Get download queue.
    
    Returns all downloads that are queued but not yet started.
    
    Returns:
        dict: List of queued download items
    """
    return {"items": model_manager.queue()}


@router.get("/downloads/items")
def items() -> dict:
    """
    Get all download items (active, queued, and history).
    
    Returns all download items including active, queued, completed, and failed downloads.
    
    Returns:
        dict: List of all download items with their status
    """
    return {"items": model_manager.items()}


@router.post("/downloads/enqueue")
def enqueue(req: DownloadRequest) -> dict:
    """
    Enqueue a model for download.
    
    Adds a model to the download queue. The download will start automatically
    when a slot becomes available.
    
    Args:
        req: Download request with model_id to download
        
    Returns:
        dict: Download item with status and metadata
        
    Raises:
        HTTPException: 409 if model is already queued or downloading
    """
    try:
        item = model_manager.enqueue_download(req.model_id)
        return {"ok": True, "item": item}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/downloads/cancel")
def cancel(req: CancelRequest) -> dict:
    """
    Cancel a queued or active download.
    
    Cancels a download that is in the queue or currently downloading.
    
    Args:
        req: Cancel request with download_id to cancel
        
    Returns:
        dict: Updated download item with cancelled status
    """
    item = model_manager.cancel(req.download_id)
    return {"ok": True, "item": item}


@router.post("/import")
async def import_model(
    file: UploadFile = File(...),
    model_type: str = Form("other"),
) -> dict:
    """
    Import a model file.
    
    Uploads and imports a model file into the model directory.
    The file is validated and placed in the appropriate subdirectory based on model type.
    
    Args:
        file: Model file to upload
        model_type: Type of model (checkpoint, lora, embedding, controlnet, other)
        
    Returns:
        dict: Imported model item with file path and metadata
        
    Raises:
        HTTPException: 400 if model_type is invalid
    """
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
    """
    Verify a model file's SHA256 checksum.
    
    Verifies that a model file matches its expected SHA256 hash if one is recorded.
    
    Args:
        req: Verify request with file path to verify
        
    Returns:
        dict: Verification result with checksum status
        
    Raises:
        HTTPException: 400 if file path is invalid or file not found
    """
    try:
        result = model_manager.verify_sha256(req.path)
        return {"ok": True, "item": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/catalog/custom")
def add_custom(req: AddCustomModelRequest) -> dict:
    """
    Add a custom model to the catalog.
    
    Adds a user-defined model entry to the custom catalog with download URL and metadata.
    
    Args:
        req: Custom model request with name, type, URL, filename, and optional metadata
        
    Returns:
        dict: Created custom model catalog item
        
    Raises:
        HTTPException: 400 if model type is invalid or request validation fails
    """
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
    """
    Delete a custom model from the catalog.
    
    Removes a custom model entry from the catalog. This does not delete the model file itself.
    
    Args:
        model_id: Unique identifier of the custom model to delete
        
    Returns:
        dict: Success status
        
    Raises:
        HTTPException: 400 if model_id is invalid or not found
    """
    try:
        model_manager.delete_custom_model(model_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/catalog/custom/{model_id}")
def update_custom(model_id: str, req: AddCustomModelRequest) -> dict:
    """
    Update a custom model in the catalog.
    
    Updates the metadata for an existing custom model entry.
    
    Args:
        model_id: Unique identifier of the custom model to update
        req: Updated model data with name, type, URL, filename, and optional metadata
        
    Returns:
        dict: Updated custom model catalog item
        
    Raises:
        HTTPException: 400 if model type is invalid, model_id not found, or validation fails
    """
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

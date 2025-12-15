"""Workflow catalog and execution API endpoints.

This module provides API endpoints for managing and executing ComfyUI workflow
packs including:
- Workflow pack CRUD operations (create, read, update, delete, list)
- Workflow validation (required nodes, models, extensions)
- One-click workflow execution with generation parameters
- Built-in and custom workflow pack management
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.generation_service import generation_service
from app.services.workflow_catalog import workflow_catalog
from app.services.workflow_validator import workflow_validator

router = APIRouter()


class WorkflowPackCreate(BaseModel):
    """Request model for creating a custom workflow pack."""

    id: str
    name: str
    description: str
    category: str | None = None
    required_nodes: list[str] | None = None
    required_models: dict[str, list[str]] | None = None
    required_extensions: list[str] | None = None
    workflow_file: str | None = None
    tags: list[str] | None = None
    tier: int = 3
    notes: str | None = None


class WorkflowPackUpdate(BaseModel):
    """Request model for updating a custom workflow pack."""

    name: str | None = None
    description: str | None = None
    category: str | None = None
    required_nodes: list[str] | None = None
    required_models: dict[str, list[str]] | None = None
    required_extensions: list[str] | None = None
    workflow_file: str | None = None
    tags: list[str] | None = None
    tier: int | None = None
    notes: str | None = None


class WorkflowRunRequest(BaseModel):
    """Request model for running a workflow pack with generation parameters."""

    pack_id: str = Field(..., description="Workflow pack ID to run")
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt describing the image to generate (1-2000 characters)")
    negative_prompt: str | None = Field(default=None, max_length=2000, description="Negative prompt describing what to avoid (optional)")
    seed: int | None = Field(default=None, description="Random seed for reproducibility (optional)")
    checkpoint: str | None = Field(default=None, max_length=512, description="Checkpoint model name override (optional)")
    width: int = Field(default=1024, ge=256, le=4096, description="Image width in pixels (256-4096, default: 1024)")
    height: int = Field(default=1024, ge=256, le=4096, description="Image height in pixels (256-4096, default: 1024)")
    steps: int = Field(default=25, ge=1, le=200, description="Number of sampling steps (1-200, default: 25)")
    cfg: float = Field(default=7.0, ge=0.0, le=30.0, description="Classifier-free guidance scale (0.0-30.0, default: 7.0)")
    sampler_name: str = Field(default="euler", max_length=64, description="Sampler algorithm name (default: 'euler')")
    scheduler: str = Field(default="normal", max_length=64, description="Scheduler name (default: 'normal')")
    batch_size: int = Field(default=1, ge=1, le=8, description="Number of images to generate in this batch (1-8, default: 1)")
    validate: bool = Field(default=True, description="Whether to validate workflow pack before execution (default: True)")


@router.get("/catalog")
def list_workflow_packs() -> dict:
    """List all workflow packs (built-in + custom)."""
    packs = workflow_catalog.catalog()
    return {"ok": True, "packs": packs}


@router.get("/catalog/{pack_id}")
def get_workflow_pack(pack_id: str) -> dict:
    """Get a specific workflow pack by ID."""
    pack = workflow_catalog.get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Workflow pack '{pack_id}' not found")
    return {"ok": True, "pack": pack}


@router.get("/catalog/custom")
def list_custom_workflow_packs() -> dict:
    """List only custom workflow packs."""
    packs = workflow_catalog.custom_catalog()
    return {"ok": True, "packs": packs}


@router.post("/catalog/custom")
def create_custom_workflow_pack(pack: WorkflowPackCreate) -> dict:
    """Create a custom workflow pack."""
    try:
        created = workflow_catalog.add_custom_pack(
            pack_id=pack.id,
            name=pack.name,
            description=pack.description,
            category=pack.category,
            required_nodes=pack.required_nodes,
            required_models=pack.required_models,
            required_extensions=pack.required_extensions,
            workflow_file=pack.workflow_file,
            tags=pack.tags,
            tier=pack.tier,
            notes=pack.notes,
        )
        return {"ok": True, "pack": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/catalog/custom/{pack_id}")
def update_custom_workflow_pack(pack_id: str, pack: WorkflowPackUpdate) -> dict:
    """Update a custom workflow pack."""
    try:
        updated = workflow_catalog.update_custom_pack(
            pack_id,
            name=pack.name,
            description=pack.description,
            category=pack.category,
            required_nodes=pack.required_nodes,
            required_models=pack.required_models,
            required_extensions=pack.required_extensions,
            workflow_file=pack.workflow_file,
            tags=pack.tags,
            tier=pack.tier,
            notes=pack.notes,
        )
        return {"ok": True, "pack": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/catalog/custom/{pack_id}")
def delete_custom_workflow_pack(pack_id: str) -> dict:
    """Delete a custom workflow pack."""
    try:
        workflow_catalog.delete_custom_pack(pack_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/validate/{pack_id}")
def validate_workflow_pack(pack_id: str) -> dict:
    """Validate a workflow pack by ID."""
    pack = workflow_catalog.get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Workflow pack '{pack_id}' not found")

    result = workflow_validator.validate_workflow_pack(pack)
    return {
        "ok": True,
        "pack_id": pack_id,
        "valid": result.valid,
        "missing_nodes": result.missing_nodes,
        "missing_models": result.missing_models,
        "missing_extensions": result.missing_extensions,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.post("/validate")
def validate_workflow_pack_body(pack: WorkflowPackCreate) -> dict:
    """Validate a workflow pack from request body."""
    pack_dict = {
        "id": pack.id,
        "name": pack.name,
        "description": pack.description,
        "category": pack.category,
        "required_nodes": pack.required_nodes,
        "required_models": pack.required_models,
        "required_extensions": pack.required_extensions,
        "workflow_file": pack.workflow_file,
        "tags": pack.tags,
        "tier": pack.tier,
        "notes": pack.notes,
    }

    result = workflow_validator.validate_workflow_pack(pack_dict)
    return {
        "ok": True,
        "pack_id": pack.id,
        "valid": result.valid,
        "missing_nodes": result.missing_nodes,
        "missing_models": result.missing_models,
        "missing_extensions": result.missing_extensions,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.post("/run")
def run_workflow_pack(req: WorkflowRunRequest) -> dict:
    """
    One-click workflow run: validate and execute a workflow pack.
    Creates a generation job using the workflow pack.
    """
    # Get workflow pack
    pack = workflow_catalog.get_pack(req.pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Workflow pack '{req.pack_id}' not found")

    # Optionally validate the pack
    validation_result = None
    if req.validate:
        validation_result = workflow_validator.validate_workflow_pack(pack)
        if not validation_result.valid:
            # Return validation errors but don't block execution
            # User can choose to proceed anyway
            return {
                "ok": False,
                "error": "validation_failed",
                "pack_id": req.pack_id,
                "validation": {
                    "valid": validation_result.valid,
                    "missing_nodes": validation_result.missing_nodes,
                    "missing_models": validation_result.missing_models,
                    "missing_extensions": validation_result.missing_extensions,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                },
                "message": "Workflow pack validation failed. Check missing dependencies.",
            }

    # Create generation job using the existing generation service
    job = generation_service.create_image_job(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        seed=req.seed,
        checkpoint=req.checkpoint,
        width=req.width,
        height=req.height,
        steps=req.steps,
        cfg=req.cfg,
        sampler_name=req.sampler_name,
        scheduler=req.scheduler,
        batch_size=req.batch_size,
    )

    return {
        "ok": True,
        "pack_id": req.pack_id,
        "pack_name": pack.get("name"),
        "job": job.__dict__,
        "validation": {
            "valid": validation_result.valid if validation_result else True,
            "warnings": validation_result.warnings if validation_result else [],
        } if validation_result else None,
    }


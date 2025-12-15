from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.generation_service import generation_service
from app.services.workflow_catalog import workflow_catalog
from app.services.workflow_validator import workflow_validator

router = APIRouter()


class WorkflowPackCreate(BaseModel):
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
    pack_id: str
    prompt: str
    negative_prompt: str | None = None
    seed: int | None = None
    checkpoint: str | None = None
    width: int = 1024
    height: int = 1024
    steps: int = 25
    cfg: float = 7.0
    sampler_name: str = "euler"
    scheduler: str = "normal"
    batch_size: int = 1
    validate: bool = True


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


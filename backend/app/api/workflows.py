from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.workflow_catalog import workflow_catalog

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


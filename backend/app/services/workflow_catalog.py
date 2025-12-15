from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import config_dir, data_dir

logger = get_logger(__name__)


@dataclass(frozen=True)
class WorkflowPack:
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


class WorkflowCatalog:
    """Manages workflow catalog (built-in and custom workflow packs)."""

    def __init__(self) -> None:
        """Initialize workflow catalog with thread lock and custom catalog path."""
        self._lock = threading.Lock()
        self._custom_catalog_path = config_dir() / "custom_workflows.json"
        config_dir().mkdir(parents=True, exist_ok=True)

        # Built-in workflow packs (minimal MVP)
        self._built_in_catalog: list[WorkflowPack] = [
            WorkflowPack(
                id="portrait-basic",
                name="Basic Portrait",
                description="Simple portrait generation workflow",
                category="portrait",
                required_nodes=["CheckpointLoaderSimple", "KSampler", "VAEDecode"],
                required_models={
                    "checkpoints": [],
                    "loras": [],
                    "vaes": [],
                },
                required_extensions=[],
                workflow_file=None,  # Will be created when workflow files are added
                tags=["portrait", "basic"],
                tier=2,
                notes="Basic portrait generation workflow. Requires a checkpoint model.",
            ),
            WorkflowPack(
                id="landscape-basic",
                name="Basic Landscape",
                description="Simple landscape generation workflow",
                category="landscape",
                required_nodes=["CheckpointLoaderSimple", "KSampler", "VAEDecode"],
                required_models={
                    "checkpoints": [],
                    "loras": [],
                    "vaes": [],
                },
                required_extensions=[],
                workflow_file=None,
                tags=["landscape", "basic"],
                tier=2,
                notes="Basic landscape generation workflow. Requires a checkpoint model.",
            ),
        ]

        self._custom_catalog: list[WorkflowPack] = self._load_custom_catalog()

    def catalog(self) -> list[dict[str, Any]]:
        """Get all workflow packs (built-in + custom)."""
        with self._lock:
            built_in = sorted(self._built_in_catalog, key=lambda x: (x.tier, x.name.lower()))
            custom = sorted(self._custom_catalog, key=lambda x: (x.tier, x.name.lower()))
            return [self._pack_to_dict(p) for p in (built_in + custom)]

    def get_pack(self, pack_id: str) -> dict[str, Any] | None:
        """Get a specific workflow pack by ID."""
        with self._lock:
            # Check built-in first
            for pack in self._built_in_catalog:
                if pack.id == pack_id:
                    return self._pack_to_dict(pack)
            # Check custom
            for pack in self._custom_catalog:
                if pack.id == pack_id:
                    return self._pack_to_dict(pack)
            return None

    def custom_catalog(self) -> list[dict[str, Any]]:
        """Get only custom workflow packs."""
        with self._lock:
            return [self._pack_to_dict(p) for p in sorted(self._custom_catalog, key=lambda x: (x.tier, x.name.lower()))]

    def add_custom_pack(
        self,
        *,
        pack_id: str,
        name: str,
        description: str,
        category: str | None = None,
        required_nodes: list[str] | None = None,
        required_models: dict[str, list[str]] | None = None,
        required_extensions: list[str] | None = None,
        workflow_file: str | None = None,
        tags: list[str] | None = None,
        tier: int = 3,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Add a custom workflow pack."""
        with self._lock:
            # Check if ID already exists
            if any(p.id == pack_id for p in self._built_in_catalog):
                raise ValueError(f"Workflow pack ID '{pack_id}' is reserved (built-in)")
            if any(p.id == pack_id for p in self._custom_catalog):
                raise ValueError(f"Workflow pack ID '{pack_id}' already exists")

            pack = WorkflowPack(
                id=pack_id,
                name=name,
                description=description,
                category=category,
                required_nodes=required_nodes,
                required_models=required_models,
                required_extensions=required_extensions,
                workflow_file=workflow_file,
                tags=tags,
                tier=tier,
                notes=notes,
            )

            self._custom_catalog.append(pack)
            self._save_custom_catalog()

            logger.info(f"Added custom workflow pack: {pack_id}")
            return self._pack_to_dict(pack)

    def update_custom_pack(
        self,
        pack_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        required_nodes: list[str] | None = None,
        required_models: dict[str, list[str]] | None = None,
        required_extensions: list[str] | None = None,
        workflow_file: str | None = None,
        tags: list[str] | None = None,
        tier: int | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update a custom workflow pack."""
        with self._lock:
            # Find the pack
            pack_idx = None
            for idx, pack in enumerate(self._custom_catalog):
                if pack.id == pack_id:
                    pack_idx = idx
                    break

            if pack_idx is None:
                raise ValueError(f"Workflow pack '{pack_id}' not found")

            old_pack = self._custom_catalog[pack_idx]

            # Create updated pack with new values or keep old ones
            updated_pack = WorkflowPack(
                id=old_pack.id,
                name=name if name is not None else old_pack.name,
                description=description if description is not None else old_pack.description,
                category=category if category is not None else old_pack.category,
                required_nodes=required_nodes if required_nodes is not None else old_pack.required_nodes,
                required_models=required_models if required_models is not None else old_pack.required_models,
                required_extensions=required_extensions if required_extensions is not None else old_pack.required_extensions,
                workflow_file=workflow_file if workflow_file is not None else old_pack.workflow_file,
                tags=tags if tags is not None else old_pack.tags,
                tier=tier if tier is not None else old_pack.tier,
                notes=notes if notes is not None else old_pack.notes,
            )

            self._custom_catalog[pack_idx] = updated_pack
            self._save_custom_catalog()

            logger.info(f"Updated custom workflow pack: {pack_id}")
            return self._pack_to_dict(updated_pack)

    def delete_custom_pack(self, pack_id: str) -> None:
        """Delete a custom workflow pack."""
        with self._lock:
            self._custom_catalog = [p for p in self._custom_catalog if p.id != pack_id]
            self._save_custom_catalog()
            logger.info(f"Deleted custom workflow pack: {pack_id}")

    def _load_custom_catalog(self) -> list[WorkflowPack]:
        """Load custom workflow catalog from disk."""
        if not self._custom_catalog_path.exists():
            return []

        try:
            with open(self._custom_catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return [self._dict_to_pack(item) for item in data if isinstance(item, dict)]
        except Exception as exc:
            logger.error(f"Failed to load custom workflow catalog: {exc}")
            return []

    def _save_custom_catalog(self) -> None:
        """Save custom workflow catalog to disk."""
        try:
            data = [self._pack_to_dict(p) for p in self._custom_catalog]
            with open(self._custom_catalog_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.error(f"Failed to save custom workflow catalog: {exc}")
            raise

    def _pack_to_dict(self, pack: WorkflowPack) -> dict[str, Any]:
        """Convert WorkflowPack to dictionary."""
        return {
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

    def _dict_to_pack(self, data: dict[str, Any]) -> WorkflowPack:
        """Convert dictionary to WorkflowPack."""
        return WorkflowPack(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category"),
            required_nodes=data.get("required_nodes"),
            required_models=data.get("required_models"),
            required_extensions=data.get("required_extensions"),
            workflow_file=data.get("workflow_file"),
            tags=data.get("tags"),
            tier=data.get("tier", 3),
            notes=data.get("notes"),
        )


# Global instance
workflow_catalog = WorkflowCatalog()


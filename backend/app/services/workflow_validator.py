"""Workflow validation service for checking workflow pack requirements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.services.comfyui_client import ComfyUiClient, ComfyUiError
from app.services.comfyui_manager import comfyui_manager
from app.services.model_manager import model_manager

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Workflow validation result.
    
    Attributes:
        valid: Whether the workflow is valid (all requirements met).
        missing_nodes: List of required ComfyUI node class names that are not installed.
        missing_models: Dictionary mapping model types to lists of missing model IDs (e.g., {"checkpoints": [...], "loras": [...], "vaes": [...]}).
        missing_extensions: List of required ComfyUI extension names that are not installed.
        errors: List of error messages describing validation failures.
        warnings: List of warning messages for non-critical issues.
    """
    valid: bool
    missing_nodes: list[str]
    missing_models: dict[str, list[str]]  # {"checkpoints": [...], "loras": [...], "vaes": [...]}
    missing_extensions: list[str]
    errors: list[str]
    warnings: list[str]


class WorkflowValidator:
    """Validates workflow packs against system state (nodes, models, extensions)."""

    def __init__(self) -> None:
        """Initialize workflow validator."""
        self._comfyui_client: ComfyUiClient | None = None

    def validate_workflow_pack(self, pack: dict[str, Any]) -> ValidationResult:
        """
        Validate a workflow pack against current system state.
        Checks required nodes, models, and extensions.
        """
        missing_nodes: list[str] = []
        missing_models: dict[str, list[str]] = {"checkpoints": [], "loras": [], "vaes": []}
        missing_extensions: list[str] = []
        errors: list[str] = []
        warnings: list[str] = []

        # Check if ComfyUI is running
        manager_status = comfyui_manager.status()
        if manager_status.state != "running":
            errors.append(f"ComfyUI is not running (state: {manager_status.state})")
            return ValidationResult(
                valid=False,
                missing_nodes=[],
                missing_models=missing_models,
                missing_extensions=[],
                errors=errors,
                warnings=warnings,
            )

        # Initialize ComfyUI client
        try:
            self._comfyui_client = ComfyUiClient(base_url=manager_status.base_url)
        except Exception as exc:
            errors.append(f"Failed to connect to ComfyUI: {exc}")
            return ValidationResult(
                valid=False,
                missing_nodes=[],
                missing_models=missing_models,
                missing_extensions=[],
                errors=errors,
                warnings=warnings,
            )

        # Validate required nodes
        required_nodes = pack.get("required_nodes")
        if required_nodes and isinstance(required_nodes, list):
            missing_nodes = self._validate_nodes(required_nodes)
            if missing_nodes:
                warnings.append(f"Some required nodes may not be available: {', '.join(missing_nodes)}")

        # Validate required models
        required_models = pack.get("required_models")
        if required_models and isinstance(required_models, dict):
            missing_models = self._validate_models(required_models)

        # Validate required extensions
        required_extensions = pack.get("required_extensions")
        if required_extensions and isinstance(required_extensions, list):
            missing_extensions = self._validate_extensions(required_extensions)
            if missing_extensions:
                warnings.append(f"Some required extensions may not be installed: {', '.join(missing_extensions)}")

        # Determine overall validity
        has_critical_missing = any(missing_models.values()) or len(errors) > 0
        valid = not has_critical_missing

        return ValidationResult(
            valid=valid,
            missing_nodes=missing_nodes,
            missing_models=missing_models,
            missing_extensions=missing_extensions,
            errors=errors,
            warnings=warnings,
        )

    def _validate_nodes(self, required_nodes: list[str]) -> list[str]:
        """
        Validate that required nodes are available in ComfyUI.
        Note: ComfyUI doesn't have a standard API to list all nodes.
        For now, we'll assume common nodes are available if ComfyUI is running.
        This can be enhanced later with actual node discovery.
        """
        missing: list[str] = []
        # Common ComfyUI nodes that should always be available
        common_nodes = {
            "CheckpointLoaderSimple",
            "CheckpointLoader",
            "KSampler",
            "KSamplerAdvanced",
            "VAEDecode",
            "VAEEncode",
            "CLIPTextEncode",
            "EmptyLatentImage",
            "SaveImage",
            "LoadImage",
            "ImageUpscaleWithModel",
        }

        for node in required_nodes:
            if node not in common_nodes:
                # For non-common nodes, we can't easily verify without node discovery
                # For now, we'll just warn but not fail
                missing.append(node)

        return missing

    def _validate_models(self, required_models: dict[str, list[str]]) -> dict[str, list[str]]:
        """Validate that required models are installed."""
        missing: dict[str, list[str]] = {"checkpoints": [], "loras": [], "vaes": []}

        # Get installed models from model manager
        installed_models = model_manager.installed()
        installed_paths = {item["path"] for item in installed_models}

        # Check checkpoints
        required_checkpoints = required_models.get("checkpoints", [])
        if required_checkpoints:
            # Also check ComfyUI's checkpoint list
            comfyui_checkpoints: list[str] = []
            try:
                if self._comfyui_client:
                    comfyui_checkpoints = self._comfyui_client.list_checkpoints()
            except ComfyUiError:
                pass

            for checkpoint in required_checkpoints:
                # Check if installed in our model manager
                found = any(checkpoint in path for path in installed_paths)
                # Also check ComfyUI's checkpoint list
                if not found:
                    found = checkpoint in comfyui_checkpoints or any(checkpoint in cp for cp in comfyui_checkpoints)
                if not found:
                    missing["checkpoints"].append(checkpoint)

        # Check LoRAs
        required_loras = required_models.get("loras", [])
        if required_loras:
            for lora in required_loras:
                found = any(lora in path for path in installed_paths)
                if not found:
                    missing["loras"].append(lora)

        # Check VAEs
        required_vaes = required_models.get("vaes", [])
        if required_vaes:
            for vae in required_vaes:
                found = any(vae in path for path in installed_paths)
                if not found:
                    missing["vaes"].append(vae)

        return missing

    def _validate_extensions(self, required_extensions: list[str]) -> list[str]:
        """
        Validate that required extensions are installed.
        Note: ComfyUI doesn't have a standard API to list extensions.
        This would require checking the ComfyUI custom_nodes directory.
        For now, we'll return all as potentially missing (warnings only).
        """
        # TODO: Implement extension checking by scanning ComfyUI custom_nodes directory
        # For now, we can't reliably check extensions without filesystem access
        return required_extensions.copy() if required_extensions else []


# Global instance
workflow_validator = WorkflowValidator()


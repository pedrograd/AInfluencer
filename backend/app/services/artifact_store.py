"""Artifact storage service for pipeline outputs.

This module provides centralized artifact storage (file-based MVP) for
pipeline job outputs including images, videos, and other generated content.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.core.paths import data_dir
from app.core.logging import get_logger

logger = get_logger(__name__)


class ArtifactStore:
    """Centralized artifact storage (file-based MVP).
    
    Stores artifacts in a structured directory:
    - Base: data_dir() / "artifacts" / {job_id} / {artifact_type} / {filename}
    - Metadata: data_dir() / "artifacts" / {job_id} / metadata.json
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize artifact store.
        
        Args:
            base_dir: Base directory for artifacts (defaults to data_dir() / "artifacts")
        """
        self.base_dir = base_dir or (data_dir() / "artifacts")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_artifact(
        self,
        job_id: str,
        artifact_type: str,
        file_path: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Save artifact and return relative path.
        
        Args:
            job_id: Job identifier
            artifact_type: Type of artifact ("image", "video", "audio", etc.)
            file_path: Path to source file to copy
            metadata: Optional metadata to store with artifact
            
        Returns:
            Relative path to saved artifact (from base_dir)
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            PermissionError: If unable to write to destination
        """
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        # Create job directory structure
        job_dir = self.base_dir / job_id
        artifact_dir = job_dir / artifact_type
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Copy file to artifact directory
        dest_path = artifact_dir / source_path.name
        shutil.copy2(source_path, dest_path)
        logger.info(f"Saved artifact: {dest_path}")

        # Save metadata if provided
        if metadata is not None:
            metadata_path = job_dir / "metadata.json"
            metadata_data: dict[str, Any] = {}
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r") as f:
                        metadata_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load existing metadata: {e}")

            # Update metadata for this artifact type
            if "artifacts" not in metadata_data:
                metadata_data["artifacts"] = {}
            metadata_data["artifacts"][artifact_type] = {
                "path": str(dest_path.relative_to(self.base_dir)),
                "filename": source_path.name,
                **metadata,
            }

            with open(metadata_path, "w") as f:
                json.dump(metadata_data, f, indent=2)

        # Return relative path from base_dir
        return str(dest_path.relative_to(self.base_dir))

    def get_artifact_url(self, job_id: str, artifact_type: str) -> str | None:
        """Get URL/path to artifact.
        
        Args:
            job_id: Job identifier
            artifact_type: Type of artifact
            
        Returns:
            Relative path to artifact or None if not found
        """
        artifact_dir = self.base_dir / job_id / artifact_type
        if not artifact_dir.exists():
            return None

        # Get first file in artifact directory (for MVP, assume single artifact per type)
        files = list(artifact_dir.iterdir())
        if not files:
            return None

        # Return relative path
        return str(files[0].relative_to(self.base_dir))

    def list_artifacts(self, job_id: str) -> list[dict[str, Any]]:
        """List all artifacts for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            List of artifact dictionaries with type, path, and metadata
        """
        job_dir = self.base_dir / job_id
        if not job_dir.exists():
            return []

        artifacts: list[dict[str, Any]] = []

        # Load metadata if available
        metadata_path = job_dir / "metadata.json"
        metadata_data: dict[str, Any] = {}
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    metadata_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")

        # Scan artifact directories
        for artifact_type_dir in job_dir.iterdir():
            if artifact_type_dir.is_dir() and artifact_type_dir.name != "metadata.json":
                artifact_type = artifact_type_dir.name
                for artifact_file in artifact_type_dir.iterdir():
                    if artifact_file.is_file():
                        artifact_info: dict[str, Any] = {
                            "type": artifact_type,
                            "path": str(artifact_file.relative_to(self.base_dir)),
                            "filename": artifact_file.name,
                        }

                        # Add metadata if available
                        if "artifacts" in metadata_data and artifact_type in metadata_data["artifacts"]:
                            artifact_meta = metadata_data["artifacts"][artifact_type]
                            if artifact_meta.get("filename") == artifact_file.name:
                                artifact_info.update({k: v for k, v in artifact_meta.items() if k != "path" and k != "filename"})

                        artifacts.append(artifact_info)

        return artifacts

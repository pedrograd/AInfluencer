"""Face consistency service for IP-Adapter and InstantID integration.

This service provides face consistency functionality for character image generation,
supporting both IP-Adapter and InstantID methods to maintain character face consistency
across generated images.
"""

from __future__ import annotations

import base64
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir

logger = get_logger(__name__)


class FaceConsistencyMethod(str, Enum):
    """Face consistency method options."""

    IP_ADAPTER = "ip_adapter"
    IP_ADAPTER_PLUS = "ip_adapter_plus"
    INSTANTID = "instantid"
    FACEID = "faceid"


class FaceConsistencyService:
    """Service for managing face consistency in image generation."""

    def __init__(self) -> None:
        """Initialize face consistency service."""
        self._face_embeddings_dir = images_dir() / "face_embeddings"
        self._face_embeddings_dir.mkdir(parents=True, exist_ok=True)

    def extract_face_embedding(
        self,
        face_image_path: str | Path,
        method: FaceConsistencyMethod = FaceConsistencyMethod.IP_ADAPTER,
    ) -> dict[str, Any]:
        """
        Extract face embedding from a reference image.
        
        This method prepares face embeddings for use in image generation workflows.
        For IP-Adapter, this typically involves preprocessing the image. For InstantID,
        this involves extracting face embeddings using a face recognition model.
        
        Args:
            face_image_path: Path to the reference face image
            method: Face consistency method to use
            
        Returns:
            dict: Face embedding data including:
                - embedding_path: Path to saved embedding file (if applicable)
                - embedding_data: Embedding data (base64 or file path)
                - method: Method used
                - image_path: Original image path
                
        Note:
            This is a foundation implementation. Full extraction requires:
            - IP-Adapter: Image preprocessing and embedding extraction
            - InstantID: Face detection and embedding model inference
        """
        face_path = Path(face_image_path)
        if not face_path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")
        
        logger.info(f"Extracting face embedding using {method.value} from {face_path}")
        
        # Placeholder: In full implementation, this would:
        # - For IP-Adapter: Preprocess image, extract features
        # - For InstantID: Run face detection, extract embeddings using InstantID model
        # - Save embedding to disk for reuse
        
        embedding_id = f"{method.value}_{face_path.stem}"
        embedding_path = self._face_embeddings_dir / f"{embedding_id}.json"
        
        # For now, return structure that will be used by workflow builder
        return {
            "embedding_id": embedding_id,
            "embedding_path": str(embedding_path),
            "method": method.value,
            "image_path": str(face_path),
            "status": "pending",  # Will be "ready" once extraction is implemented
        }

    def build_ip_adapter_workflow_nodes(
        self,
        workflow: dict[str, Any],
        face_image_path: str | Path,
        weight: float = 0.75,
        start_at: float = 0.0,
        end_at: float = 1.0,
    ) -> dict[str, Any]:
        """
        Add IP-Adapter nodes to a ComfyUI workflow.
        
        IP-Adapter uses reference images to guide generation while maintaining
        face consistency. This method adds the necessary nodes to integrate
        IP-Adapter into an existing workflow.
        
        Args:
            workflow: Existing ComfyUI workflow dictionary
            face_image_path: Path to reference face image
            weight: IP-Adapter strength (0.0-1.0, default: 0.75)
            start_at: Start step for IP-Adapter (0.0-1.0, default: 0.0)
            end_at: End step for IP-Adapter (0.0-1.0, default: 1.0)
            
        Returns:
            dict: Updated workflow with IP-Adapter nodes added
            
        Note:
            This requires IP-Adapter nodes to be installed in ComfyUI.
            Node structure may vary based on ComfyUI version and IP-Adapter implementation.
        """
        face_path = Path(face_image_path)
        if not face_path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")
        
        logger.info(f"Adding IP-Adapter nodes to workflow with weight={weight}")
        
        # Get next available node ID
        max_node_id = max(int(k) for k in workflow.keys() if k.isdigit()) if workflow else 0
        next_id = str(max_node_id + 1)
        
        # IP-Adapter node structure (placeholder - actual structure depends on ComfyUI setup)
        # In full implementation, this would:
        # 1. Load face image using LoadImage node
        # 2. Add IPAdapterModelLoader node
        # 3. Add IPAdapterApply node to connect to model and positive prompt
        # 4. Wire nodes into existing workflow
        
        ip_adapter_nodes = {
            f"{next_id}": {
                "class_type": "LoadImage",
                "inputs": {"image": str(face_path)},
            },
            # Additional IP-Adapter nodes would be added here
            # This is a foundation structure
        }
        
        workflow.update(ip_adapter_nodes)
        logger.warning(
            "IP-Adapter workflow nodes are placeholder. Full implementation requires "
            "ComfyUI IP-Adapter nodes and proper node wiring."
        )
        
        return workflow

    def build_instantid_workflow_nodes(
        self,
        workflow: dict[str, Any],
        face_image_path: str | Path,
        weight: float = 0.8,
        controlnet_strength: float = 0.9,
    ) -> dict[str, Any]:
        """
        Add InstantID nodes to a ComfyUI workflow.
        
        InstantID provides identity-preserving image generation with better
        face consistency than IP-Adapter. This method adds InstantID nodes
        to the workflow.
        
        Args:
            workflow: Existing ComfyUI workflow dictionary
            face_image_path: Path to reference face image
            weight: InstantID weight (0.0-1.0, default: 0.8)
            controlnet_strength: ControlNet strength (0.0-1.0, default: 0.9)
            
        Returns:
            dict: Updated workflow with InstantID nodes added
            
        Note:
            This requires InstantID nodes to be installed in ComfyUI.
            InstantID typically uses ControlNet for face consistency.
        """
        face_path = Path(face_image_path)
        if not face_path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")
        
        logger.info(f"Adding InstantID nodes to workflow with weight={weight}")
        
        # Get next available node ID
        max_node_id = max(int(k) for k in workflow.keys() if k.isdigit()) if workflow else 0
        next_id = str(max_node_id + 1)
        
        # InstantID node structure (placeholder - actual structure depends on ComfyUI setup)
        # In full implementation, this would:
        # 1. Load face image
        # 2. Run face detection and embedding extraction
        # 3. Add InstantID model loader
        # 4. Add InstantID apply node with ControlNet
        # 5. Wire into existing workflow
        
        instantid_nodes = {
            f"{next_id}": {
                "class_type": "LoadImage",
                "inputs": {"image": str(face_path)},
            },
            # Additional InstantID nodes would be added here
            # This is a foundation structure
        }
        
        workflow.update(instantid_nodes)
        logger.warning(
            "InstantID workflow nodes are placeholder. Full implementation requires "
            "ComfyUI InstantID nodes, face detection, and proper node wiring."
        )
        
        return workflow

    def get_face_embedding_path(self, embedding_id: str) -> Path | None:
        """
        Get path to saved face embedding.
        
        Args:
            embedding_id: Unique identifier for the face embedding
            
        Returns:
            Path to embedding file if exists, None otherwise
        """
        embedding_path = self._face_embeddings_dir / f"{embedding_id}.json"
        return embedding_path if embedding_path.exists() else None

    def list_face_embeddings(self) -> list[dict[str, Any]]:
        """
        List all saved face embeddings.
        
        Returns:
            List of face embedding metadata dictionaries
        """
        embeddings = []
        for embedding_file in self._face_embeddings_dir.glob("*.json"):
            try:
                # In full implementation, load and parse embedding metadata
                embeddings.append({
                    "embedding_id": embedding_file.stem,
                    "path": str(embedding_file),
                    "method": "unknown",  # Would be stored in metadata
                })
            except Exception as e:
                logger.warning(f"Failed to load embedding {embedding_file}: {e}")
        
        return embeddings


# Singleton instance
face_consistency_service = FaceConsistencyService()


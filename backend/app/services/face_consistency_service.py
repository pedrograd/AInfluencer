"""Face consistency service for IP-Adapter and InstantID integration.

This service provides face consistency functionality for character image generation,
supporting both IP-Adapter and InstantID methods to maintain character face consistency
across generated images.

Implementation Status:
- ✅ Service foundation with face image validation
- ✅ Integration with generation service and API endpoints
- ✅ Workflow node building for IP-Adapter and InstantID
- ✅ Face embedding metadata storage and retrieval
- ✅ Health check and error handling
- ⏳ Actual embedding extraction logic (placeholder - requires ComfyUI models)
- ⏳ Full ComfyUI workflow integration testing

The service currently provides a complete foundation for face consistency. The actual
embedding extraction requires ComfyUI IP-Adapter/InstantID extensions and models to be
installed. The workflow node building creates the proper structure for ComfyUI workflows,
but full functionality depends on ComfyUI setup.

API Endpoints (Full CRUD):
- POST /api/generate/face-embedding/extract - Extract face embedding (Create)
- GET /api/generate/face-embedding/list - List all embeddings (Read/List)
- GET /api/generate/face-embedding/{embedding_id} - Get embedding metadata (Read)
- DELETE /api/generate/face-embedding/{embedding_id} - Delete embedding (Delete)
- GET /api/generate/face-embedding/health - Service health check
"""

from __future__ import annotations

import base64
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir

logger = get_logger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available - face image validation will be limited")


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
        self._min_face_resolution = (256, 256)  # Minimum resolution for face images
        self._preferred_face_resolution = (512, 512)  # Preferred resolution for face images

    def _get_next_node_id(self, workflow: dict[str, Any]) -> str:
        """
        Get the next available node ID for a ComfyUI workflow.
        
        ComfyUI workflows use string node IDs (typically numeric strings like "1", "2", etc.).
        This helper finds the highest numeric node ID and returns the next one.
        
        Args:
            workflow: ComfyUI workflow dictionary
            
        Returns:
            str: Next available node ID
        """
        if not workflow:
            return "1"
        
        numeric_ids = [int(k) for k in workflow.keys() if k.isdigit()]
        if not numeric_ids:
            return "1"
        
        return str(max(numeric_ids) + 1)

    def _find_node_by_class(self, workflow: dict[str, Any], class_type: str) -> str | None:
        """
        Find a node ID by its class type in a ComfyUI workflow.
        
        Args:
            workflow: ComfyUI workflow dictionary
            class_type: Node class type to search for (e.g., "KSampler", "CLIPTextEncode")
            
        Returns:
            str: Node ID if found, None otherwise
        """
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == class_type:
                return node_id
        return None

    def validate_face_image(
        self,
        face_image_path: str | Path,
    ) -> dict[str, Any]:
        """
        Validate a face image for use in face consistency.
        
        Checks that the image exists, is readable, has valid format, and meets
        minimum resolution requirements for face consistency methods.
        
        Args:
            face_image_path: Path to the face image to validate
            
        Returns:
            dict: Validation result with:
                - is_valid: Boolean indicating if image is valid
                - errors: List of error messages
                - warnings: List of warning messages
                - metadata: Image metadata (width, height, format, etc.)
                
        Raises:
            FileNotFoundError: If image file does not exist
        """
        face_path = Path(face_image_path)
        if not face_path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")
        
        errors: list[str] = []
        warnings: list[str] = []
        metadata: dict[str, Any] = {}
        
        # Check file readability
        if not face_path.is_file():
            errors.append(f"Path is not a file: {face_image_path}")
            return {
                "is_valid": False,
                "errors": errors,
                "warnings": warnings,
                "metadata": metadata,
            }
        
        # Validate image format and dimensions if PIL is available
        if PIL_AVAILABLE:
            try:
                with Image.open(face_path) as img:
                    width, height = img.size
                    metadata["width"] = width
                    metadata["height"] = height
                    metadata["format"] = img.format
                    metadata["mode"] = img.mode
                    
                    # Check minimum resolution
                    if width < self._min_face_resolution[0] or height < self._min_face_resolution[1]:
                        errors.append(
                            f"Resolution below minimum: {width}x{height} "
                            f"(minimum: {self._min_face_resolution[0]}x{self._min_face_resolution[1]})"
                        )
                    elif width < self._preferred_face_resolution[0] or height < self._preferred_face_resolution[1]:
                        warnings.append(
                            f"Resolution below preferred: {width}x{height} "
                            f"(preferred: {self._preferred_face_resolution[0]}x{self._preferred_face_resolution[1]})"
                        )
                    
                    # Check if image format is supported
                    supported_formats = {"JPEG", "PNG", "WEBP"}
                    if img.format not in supported_formats:
                        warnings.append(
                            f"Image format '{img.format}' may not be fully supported. "
                            f"Preferred formats: {', '.join(supported_formats)}"
                        )
                    
            except Exception as e:
                errors.append(f"Failed to read image: {e}")
        else:
            warnings.append("PIL/Pillow not available - image validation limited to file existence")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata,
        }

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
                - validation: Face image validation result
                
        Raises:
            FileNotFoundError: If face image not found
            ValueError: If face image validation fails
                
        Note:
            This is a foundation implementation. Full extraction requires:
            - IP-Adapter: Image preprocessing and embedding extraction
            - InstantID: Face detection and embedding model inference
        """
        face_path = Path(face_image_path)
        if not face_path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")
        
        # Validate face image before processing
        validation = self.validate_face_image(face_image_path)
        if not validation["is_valid"]:
            error_msg = "; ".join(validation["errors"])
            raise ValueError(f"Face image validation failed: {error_msg}")
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                logger.warning(f"Face image validation warning: {warning}")
        
        logger.info(f"Extracting face embedding using {method.value} from {face_path}")
        
        # Placeholder: In full implementation, this would:
        # - For IP-Adapter: Preprocess image, extract features
        # - For InstantID: Run face detection, extract embeddings using InstantID model
        # - Save embedding to disk for reuse
        
        embedding_id = f"{method.value}_{face_path.stem}_{int(face_path.stat().st_mtime)}"
        embedding_path = self._face_embeddings_dir / f"{embedding_id}.json"
        
        # Save embedding metadata to disk for reuse
        import json
        from datetime import datetime
        
        embedding_metadata = {
            "embedding_id": embedding_id,
            "method": method.value,
            "image_path": str(face_path),
            "image_size": validation.get("metadata", {}).get("width", 0) * validation.get("metadata", {}).get("height", 0),
            "image_format": validation.get("metadata", {}).get("format", "unknown"),
            "validation": validation,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending",  # Will be "ready" once actual extraction is implemented
            "extraction_notes": "Foundation implementation - actual embedding extraction pending",
        }
        
        try:
            with open(embedding_path, "w") as f:
                json.dump(embedding_metadata, f, indent=2)
            logger.info(f"Saved face embedding metadata to {embedding_path}")
        except Exception as e:
            logger.warning(f"Failed to save embedding metadata: {e}")
        
        return {
            "embedding_id": embedding_id,
            "embedding_path": str(embedding_path),
            "method": method.value,
            "image_path": str(face_path),
            "validation": validation,
            "status": "pending",  # Will be "ready" once extraction is implemented
            "metadata_saved": embedding_path.exists(),
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
            
        Raises:
            FileNotFoundError: If face image not found
            ValueError: If face image validation fails
            
        Note:
            This requires IP-Adapter nodes to be installed in ComfyUI.
            Node structure may vary based on ComfyUI version and IP-Adapter implementation.
        """
        face_path = Path(face_image_path)
        if not face_path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")
        
        # Validate face image before adding to workflow
        validation = self.validate_face_image(face_image_path)
        if not validation["is_valid"]:
            error_msg = "; ".join(validation["errors"])
            raise ValueError(f"Face image validation failed: {error_msg}")
        
        logger.info(f"Adding IP-Adapter nodes to workflow with weight={weight}")
        
        # Get next available node IDs
        load_image_id = self._get_next_node_id(workflow)
        ip_adapter_model_id = self._get_next_node_id({**workflow, load_image_id: {}})
        ip_adapter_apply_id = self._get_next_node_id({**workflow, load_image_id: {}, ip_adapter_model_id: {}})
        
        # Find existing workflow nodes for wiring
        checkpoint_node_id = self._find_node_by_class(workflow, "CheckpointLoaderSimple")
        positive_prompt_node_id = self._find_node_by_class(workflow, "CLIPTextEncode")
        sampler_node_id = self._find_node_by_class(workflow, "KSampler")
        
        # IP-Adapter node structure (foundation - actual structure depends on ComfyUI setup)
        # Typical IP-Adapter workflow:
        # 1. LoadImage node - loads the face reference image
        # 2. IPAdapterModelLoader node - loads the IP-Adapter model
        # 3. IPAdapterApply node - applies IP-Adapter to the positive prompt
        #    - Connects to model output from checkpoint
        #    - Connects to positive prompt from CLIPTextEncode
        #    - Connects to face image from LoadImage
        #    - Outputs modified positive prompt to KSampler
        
        ip_adapter_nodes: dict[str, Any] = {
            load_image_id: {
                "class_type": "LoadImage",
                "inputs": {"image": str(face_path)},
            },
        }
        
        # Add IP-Adapter model loader (if checkpoint node exists, we can reference it)
        if checkpoint_node_id:
            ip_adapter_nodes[ip_adapter_model_id] = {
                "class_type": "IPAdapterModelLoader",
                "inputs": {
                    "model_name": "ip-adapter_sd15.safetensors",  # Default model name
                    # In full implementation, this would be configurable
                },
            }
            
            # Add IP-Adapter apply node (wires into existing workflow)
            if positive_prompt_node_id and sampler_node_id:
                ip_adapter_nodes[ip_adapter_apply_id] = {
                    "class_type": "IPAdapterApply",
                    "inputs": {
                        "model": [checkpoint_node_id, 0],  # Model from checkpoint
                        "positive": [positive_prompt_node_id, 0],  # Positive prompt
                        "negative": [positive_prompt_node_id, 0],  # Negative (same for now)
                        "ipadapter": [ip_adapter_model_id, 0],  # IP-Adapter model
                        "image": [load_image_id, 0],  # Face image
                        "weight": weight,
                        "weight_type": "linear",
                        "start_at": start_at,
                        "end_at": end_at,
                    },
                }
                
                # Update sampler to use IP-Adapter modified positive prompt
                if sampler_node_id in workflow:
                    workflow[sampler_node_id]["inputs"]["positive"] = [ip_adapter_apply_id, 0]
        
        workflow.update(ip_adapter_nodes)
        logger.info(
            f"IP-Adapter nodes added: LoadImage={load_image_id}, "
            f"ModelLoader={ip_adapter_model_id}, Apply={ip_adapter_apply_id}"
        )
        logger.warning(
            "IP-Adapter workflow nodes are foundation implementation. Full functionality requires "
            "ComfyUI IP-Adapter extension and proper model installation."
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
            
        Raises:
            FileNotFoundError: If face image not found
            ValueError: If face image validation fails
            
        Note:
            This requires InstantID nodes to be installed in ComfyUI.
            InstantID typically uses ControlNet for face consistency.
        """
        face_path = Path(face_image_path)
        if not face_path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")
        
        # Validate face image before adding to workflow
        validation = self.validate_face_image(face_image_path)
        if not validation["is_valid"]:
            error_msg = "; ".join(validation["errors"])
            raise ValueError(f"Face image validation failed: {error_msg}")
        
        logger.info(f"Adding InstantID nodes to workflow with weight={weight}")
        
        # Get next available node IDs
        load_image_id = self._get_next_node_id(workflow)
        instantid_model_id = self._get_next_node_id({**workflow, load_image_id: {}})
        instantid_apply_id = self._get_next_node_id({**workflow, load_image_id: {}, instantid_model_id: {}})
        controlnet_id = self._get_next_node_id({**workflow, load_image_id: {}, instantid_model_id: {}, instantid_apply_id: {}})
        
        # Find existing workflow nodes for wiring
        checkpoint_node_id = self._find_node_by_class(workflow, "CheckpointLoaderSimple")
        positive_prompt_node_id = self._find_node_by_class(workflow, "CLIPTextEncode")
        sampler_node_id = self._find_node_by_class(workflow, "KSampler")
        
        # InstantID node structure (foundation - actual structure depends on ComfyUI setup)
        # Typical InstantID workflow:
        # 1. LoadImage node - loads the face reference image
        # 2. InstantID model loader - loads InstantID model and ControlNet
        # 3. Face detection/embedding extraction (usually handled by InstantID nodes)
        # 4. InstantID apply node - applies face identity to generation
        #    - Connects to model, positive prompt, face image
        #    - Uses ControlNet for face consistency
        #    - Outputs modified conditioning to KSampler
        
        instantid_nodes: dict[str, Any] = {
            load_image_id: {
                "class_type": "LoadImage",
                "inputs": {"image": str(face_path)},
            },
        }
        
        # Add InstantID model loader (if checkpoint node exists)
        if checkpoint_node_id:
            instantid_nodes[instantid_model_id] = {
                "class_type": "InstantIDModelLoader",
                "inputs": {
                    "instantid_file": "ip-adapter.bin",  # Default InstantID model
                    # In full implementation, this would be configurable
                },
            }
            
            # Add ControlNet for InstantID
            instantid_nodes[controlnet_id] = {
                "class_type": "ControlNetLoader",
                "inputs": {
                    "control_net_name": "control_v11p_sd15_openpose.pth",  # Default ControlNet
                },
            }
            
            # Add InstantID apply node (wires into existing workflow)
            if positive_prompt_node_id and sampler_node_id:
                instantid_nodes[instantid_apply_id] = {
                    "class_type": "InstantIDApply",
                    "inputs": {
                        "model": [checkpoint_node_id, 0],  # Model from checkpoint
                        "positive": [positive_prompt_node_id, 0],  # Positive prompt
                        "negative": [positive_prompt_node_id, 0],  # Negative (same for now)
                        "instantid": [instantid_model_id, 0],  # InstantID model
                        "controlnet": [controlnet_id, 0],  # ControlNet
                        "image": [load_image_id, 0],  # Face image
                        "weight": weight,
                        "controlnet_strength": controlnet_strength,
                    },
                }
                
                # Update sampler to use InstantID modified conditioning
                if sampler_node_id in workflow:
                    workflow[sampler_node_id]["inputs"]["positive"] = [instantid_apply_id, 0]
        
        workflow.update(instantid_nodes)
        logger.info(
            f"InstantID nodes added: LoadImage={load_image_id}, "
            f"ModelLoader={instantid_model_id}, Apply={instantid_apply_id}, ControlNet={controlnet_id}"
        )
        logger.warning(
            "InstantID workflow nodes are foundation implementation. Full functionality requires "
            "ComfyUI InstantID extension, face detection models, and proper model installation."
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
        # Try exact match first
        embedding_path = self._face_embeddings_dir / f"{embedding_id}.json"
        if embedding_path.exists():
            return embedding_path
        
        # Try to find by embedding_id in metadata (in case filename doesn't match exactly)
        for embedding_file in self._face_embeddings_dir.glob("*.json"):
            try:
                import json
                with open(embedding_file, "r") as f:
                    metadata = json.load(f)
                    if metadata.get("embedding_id") == embedding_id:
                        return embedding_file
            except Exception:
                continue
        
        return None
    
    def get_face_embedding_metadata(self, embedding_id: str) -> dict[str, Any] | None:
        """
        Get full metadata for a face embedding.
        
        Args:
            embedding_id: Unique identifier for the face embedding
            
        Returns:
            Full embedding metadata dictionary if found, None otherwise
        """
        embedding_path = self.get_face_embedding_path(embedding_id)
        if not embedding_path:
            return None
        
        try:
            import json
            with open(embedding_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load embedding metadata from {embedding_path}: {e}")
            return None
    
    def embedding_exists(self, embedding_id: str) -> bool:
        """
        Check if a face embedding exists.
        
        Args:
            embedding_id: Unique identifier for the face embedding
            
        Returns:
            True if embedding exists, False otherwise
        """
        return self.get_face_embedding_path(embedding_id) is not None
    
    def delete_face_embedding(self, embedding_id: str) -> bool:
        """
        Delete a face embedding by ID.
        
        Args:
            embedding_id: Unique identifier for the face embedding to delete
            
        Returns:
            True if embedding was deleted successfully, False if not found or deletion failed
        """
        embedding_path = self.get_face_embedding_path(embedding_id)
        if not embedding_path:
            logger.warning(f"Face embedding '{embedding_id}' not found for deletion")
            return False
        
        try:
            embedding_path.unlink()
            logger.info(f"Deleted face embedding '{embedding_id}' from {embedding_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete face embedding '{embedding_id}': {e}")
            return False

    def list_face_embeddings(self) -> list[dict[str, Any]]:
        """
        List all saved face embeddings.
        
        Returns:
            List of face embedding metadata dictionaries with full metadata
        """
        embeddings = []
        for embedding_file in self._face_embeddings_dir.glob("*.json"):
            try:
                import json
                with open(embedding_file, "r") as f:
                    metadata = json.load(f)
                    embeddings.append({
                        "embedding_id": metadata.get("embedding_id", embedding_file.stem),
                        "path": str(embedding_file),
                        "method": metadata.get("method", "unknown"),
                        "image_path": metadata.get("image_path"),
                        "created_at": metadata.get("created_at"),
                        "status": metadata.get("status", "unknown"),
                        "image_size": metadata.get("image_size", 0),
                        "image_format": metadata.get("image_format", "unknown"),
                    })
            except Exception as e:
                logger.warning(f"Failed to load embedding {embedding_file}: {e}")
                # Fallback to basic info if metadata file is corrupted
                embeddings.append({
                    "embedding_id": embedding_file.stem,
                    "path": str(embedding_file),
                    "method": "unknown",
                    "error": str(e),
                })
        
        # Sort by creation date (newest first)
        embeddings.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return embeddings


# Singleton instance
face_consistency_service = FaceConsistencyService()


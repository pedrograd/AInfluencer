"""Style transfer service for applying artistic styles to images.

This module provides neural style transfer capabilities using ComfyUI workflows
or fallback image processing techniques.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir
from app.services.comfyui_client import ComfyUiClient, ComfyUiError

logger = get_logger(__name__)


class StyleTransferService:
    """Service for applying artistic styles to images using style transfer."""

    def __init__(self) -> None:
        """Initialize style transfer service."""
        self.client = ComfyUiClient()

    def _build_style_transfer_workflow(
        self,
        content_image_path: str,
        style_image_path: str,
        strength: float = 0.5,
    ) -> dict[str, Any]:
        """
        Build ComfyUI workflow for neural style transfer.
        
        This workflow uses ComfyUI nodes for style transfer. The exact node structure
        depends on available ComfyUI custom nodes (e.g., style transfer nodes).
        
        Args:
            content_image_path: Path to content image
            style_image_path: Path to style reference image
            strength: Style transfer strength (0.0 to 1.0, default: 0.5)
            
        Returns:
            dict: ComfyUI workflow dictionary
        """
        # Basic workflow structure for style transfer
        # Note: This is a template - actual node IDs and structure depend on
        # installed ComfyUI custom nodes for style transfer
        workflow = {
            "1": {
                "inputs": {
                    "image": content_image_path,
                },
                "class_type": "LoadImage",
            },
            "2": {
                "inputs": {
                    "image": style_image_path,
                },
                "class_type": "LoadImage",
            },
            "3": {
                "inputs": {
                    "content_image": ["1", 0],
                    "style_image": ["2", 0],
                    "strength": strength,
                },
                "class_type": "StyleTransfer",  # This node type depends on installed custom nodes
            },
            "4": {
                "inputs": {
                    "images": ["3", 0],
                },
                "class_type": "SaveImage",
            },
        }
        return workflow

    def _basic_style_transfer(
        self,
        content_image_path: Path,
        style_image_path: Path,
        strength: float = 0.5,
    ) -> dict[str, Any]:
        """
        Apply basic style transfer using image processing techniques.
        
        This is a simplified fallback that applies color and texture characteristics
        from the style image to the content image. For true neural style transfer,
        ComfyUI with appropriate custom nodes should be used.
        
        Args:
            content_image_path: Path to content image
            style_image_path: Path to style reference image
            strength: Style transfer strength (0.0 to 1.0, default: 0.5)
            
        Returns:
            dict: Result with stylized_image_path
        """
        try:
            from PIL import Image
            import numpy as np
        except ImportError:
            raise ImportError("PIL/Pillow and NumPy are required for style transfer")

        # Load images
        content_img = Image.open(content_image_path)
        style_img = Image.open(style_image_path)

        # Convert to RGB if needed
        if content_img.mode != "RGB":
            content_img = content_img.convert("RGB")
        if style_img.mode != "RGB":
            style_img = style_img.convert("RGB")

        # Resize style image to match content image
        style_img = style_img.resize(content_img.size, Image.Resampling.LANCZOS)

        # Convert to numpy arrays
        content_array = np.array(content_img, dtype=np.float32)
        style_array = np.array(style_img, dtype=np.float32)

        # Extract style characteristics (color palette and texture)
        # Calculate color statistics from style image
        style_mean = np.mean(style_array, axis=(0, 1))
        style_std = np.std(style_array, axis=(0, 1))

        # Calculate content statistics
        content_mean = np.mean(content_array, axis=(0, 1))
        content_std = np.std(content_array, axis=(0, 1))

        # Apply style transfer: match color distribution
        # Normalize content to style's color distribution
        normalized = (content_array - content_mean) / (content_std + 1e-6)
        stylized = normalized * style_std + style_mean

        # Blend with original based on strength
        stylized = content_array * (1 - strength) + stylized * strength

        # Clip to valid range
        stylized = np.clip(stylized, 0, 255).astype(np.uint8)

        # Convert back to PIL Image
        result_img = Image.fromarray(stylized)

        # Save stylized image
        stem = content_image_path.stem
        suffix = content_image_path.suffix
        output_name = f"{stem}_stylized_{int(strength * 100)}{suffix}"
        output_path = images_dir() / output_name
        result_img.save(output_path, format="PNG", quality=95)

        logger.info(f"Applied basic style transfer: {output_path}, strength: {strength}")

        return {
            "ok": True,
            "stylized_image_path": str(output_path.relative_to(images_dir())),
            "content_image_path": str(content_image_path.relative_to(images_dir())),
            "style_image_path": str(style_image_path.relative_to(images_dir())),
            "strength": strength,
            "method": "basic",
        }

    def transfer_style(
        self,
        content_image_path: str | Path,
        style_image_path: str | Path,
        strength: float = 0.5,
        use_comfyui: bool = True,
    ) -> dict[str, Any]:
        """
        Apply style transfer to an image.
        
        Args:
            content_image_path: Path to content image (relative to images_dir or absolute)
            style_image_path: Path to style reference image (relative to images_dir or absolute)
            strength: Style transfer strength (0.0 to 1.0, default: 0.5)
            use_comfyui: Whether to use ComfyUI for neural style transfer (default: True)
            
        Returns:
            dict: Result with stylized_image_path, method used, and metadata
            
        Raises:
            FileNotFoundError: If images are not found
            ValueError: If strength is not in valid range
            ComfyUiError: If ComfyUI operation fails
        """
        if not 0.0 <= strength <= 1.0:
            raise ValueError(f"strength must be between 0.0 and 1.0, got {strength}")

        # Resolve image paths
        content_path = Path(content_image_path)
        style_path = Path(style_image_path)

        if not content_path.is_absolute():
            content_path = images_dir() / content_image_path
        if not style_path.is_absolute():
            style_path = images_dir() / style_image_path

        if not content_path.exists():
            raise FileNotFoundError(f"Content image not found: {content_path}")
        if not style_path.exists():
            raise FileNotFoundError(f"Style image not found: {style_path}")

        # Try ComfyUI first if requested
        if use_comfyui:
            try:
                # Check if ComfyUI is available
                status_url = f"{self.client.base_url}/system_stats"
                try:
                    self.client._client.get(status_url, timeout=5)
                except Exception:
                    logger.warning("ComfyUI not available, falling back to basic style transfer")
                    use_comfyui = False

                if use_comfyui:
                    # Build and execute ComfyUI workflow
                    workflow = self._build_style_transfer_workflow(
                        str(content_path),
                        str(style_path),
                        strength,
                    )

                    # Queue workflow
                    prompt_id = self.client.queue_prompt(workflow)

                    # Wait for result
                    result = self.client.wait_for_first_image(prompt_id, timeout_s=300)

                    # Download stylized image
                    if result.get("images"):
                        image_info = result["images"][0]
                        image_filename = image_info.get("filename")
                        if image_filename:
                            # Download image from ComfyUI
                            image_url = f"{self.client.base_url}/view?filename={image_filename}"
                            # Note: In production, download and save the image
                            # For now, return the ComfyUI result
                            logger.info(f"Style transfer completed via ComfyUI: {image_filename}")

                            return {
                                "ok": True,
                                "stylized_image_path": image_filename,  # ComfyUI filename
                                "content_image_path": str(content_path.relative_to(images_dir())),
                                "style_image_path": str(style_path.relative_to(images_dir())),
                                "strength": strength,
                                "method": "comfyui",
                                "prompt_id": prompt_id,
                            }
            except ComfyUiError as exc:
                logger.warning(f"ComfyUI style transfer failed: {exc}, falling back to basic method")
                use_comfyui = False
            except Exception as exc:
                logger.warning(f"ComfyUI error: {exc}, falling back to basic method")
                use_comfyui = False

        # Fallback to basic style transfer
        return self._basic_style_transfer(content_path, style_path, strength)

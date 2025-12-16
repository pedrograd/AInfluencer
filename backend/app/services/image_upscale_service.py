"""Image upscaling service with ComfyUI integration.

This module provides image upscaling capabilities using ComfyUI upscaling models.
Supports 2x and 4x upscaling with various upscaling models.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir
from app.services.comfyui_client import ComfyUiClient, ComfyUiError

logger = get_logger(__name__)


class ImageUpscaleService:
    """Service for upscaling images using ComfyUI."""

    def __init__(self) -> None:
        """Initialize upscaling service."""
        self.client = ComfyUiClient()

    def upscale_image(
        self,
        image_path: str | Path,
        scale_factor: int = 2,
        upscaler_model: str | None = None,
    ) -> dict[str, Any]:
        """
        Upscale an image using ComfyUI.
        
        Args:
            image_path: Path to the image file to upscale
            scale_factor: Upscaling factor (2 for 2x, 4 for 4x, default: 2)
            upscaler_model: Optional upscaler model name (uses default if None)
            
        Returns:
            dict: Result with upscaled_image_path, original_size, upscaled_size, scale_factor
            
        Raises:
            ValueError: If scale_factor is not 2 or 4
            ComfyUiError: If upscaling fails
        """
        if scale_factor not in (2, 4):
            raise ValueError(f"scale_factor must be 2 or 4, got {scale_factor}")
        
        image_path_obj = Path(image_path)
        if not image_path_obj.is_absolute():
            image_path_obj = images_dir() / image_path
        
        if not image_path_obj.exists():
            raise FileNotFoundError(f"Image not found: {image_path_obj}")
        
        # Build upscaling workflow
        workflow = self._build_upscale_workflow(
            str(image_path_obj),
            scale_factor,
            upscaler_model,
        )
        
        # Queue and execute upscaling
        prompt_id = self.client.queue_prompt(workflow)
        logger.info(f"Queued upscale job: prompt_id={prompt_id}, scale={scale_factor}x")
        
        # Wait for completion
        result = self.client.wait_for_images(prompt_id, timeout=300)
        
        if not result or not result.get("images"):
            raise ComfyUiError("Upscaling failed: no images returned")
        
        # Save upscaled image
        upscaled_image_path = self._save_upscaled_image(
            result["images"][0],
            image_path_obj,
            scale_factor,
        )
        
        # Get dimensions
        from PIL import Image
        with Image.open(upscaled_image_path) as img:
            upscaled_size = img.size
        with Image.open(image_path_obj) as img:
            original_size = img.size
        
        return {
            "ok": True,
            "upscaled_image_path": str(upscaled_image_path.relative_to(images_dir())),
            "original_size": original_size,
            "upscaled_size": upscaled_size,
            "scale_factor": scale_factor,
        }
    
    def _build_upscale_workflow(
        self,
        image_path: str,
        scale_factor: int,
        upscaler_model: str | None,
    ) -> dict[str, Any]:
        """
        Build ComfyUI workflow for image upscaling.
        
        Args:
            image_path: Path to input image
            scale_factor: Upscaling factor (2 or 4)
            upscaler_model: Optional upscaler model name
            
        Returns:
            ComfyUI workflow dictionary
        """
        # Default upscaler models (ComfyUI built-in)
        default_upscaler = upscaler_model or "4x-UltraSharp"
        
        workflow = {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": image_path},
            },
            "2": {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {
                    "upscale_model": ["3", 0],
                    "image": ["1", 0],
                },
            },
            "3": {
                "class_type": "UpscaleModelLoader",
                "inputs": {"model_name": default_upscaler},
            },
            "4": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["2", 0],
                    "filename_prefix": "upscaled",
                },
            },
        }
        
        # For 4x upscaling, chain two 2x upscalers or use a 4x model
        if scale_factor == 4:
            workflow["5"] = {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {
                    "upscale_model": ["3", 0],
                    "image": ["2", 0],
                },
            }
            workflow["4"]["inputs"]["images"] = ["5", 0]
        
        return workflow
    
    def _save_upscaled_image(
        self,
        image_data: bytes,
        original_path: Path,
        scale_factor: int,
    ) -> Path:
        """
        Save upscaled image to disk.
        
        Args:
            image_data: Image bytes from ComfyUI
            original_path: Path to original image
            scale_factor: Upscaling factor used
            
        Returns:
            Path to saved upscaled image
        """
        from PIL import Image
        import io
        
        # Load image from bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Generate output filename
        stem = original_path.stem
        suffix = original_path.suffix
        output_name = f"{stem}_upscaled_{scale_factor}x{suffix}"
        output_path = images_dir() / output_name
        
        # Save image
        img.save(output_path, format="PNG", quality=95)
        logger.info(f"Saved upscaled image: {output_path}")
        
        return output_path


"""Image post-processing service for quality enhancement.

This module provides post-processing capabilities including:
- Sharpening
- Denoising
- Color correction
- Brightness/contrast adjustment
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir

logger = get_logger(__name__)


class ImagePostProcessService:
    """Service for post-processing images to enhance quality."""

    def __init__(self) -> None:
        """Initialize post-processing service."""
        pass

    def process_image(
        self,
        image_path: str | Path,
        *,
        sharpen: bool = False,
        denoise: bool = False,
        color_correct: bool = False,
        brightness: float | None = None,
        contrast: float | None = None,
    ) -> dict[str, Any]:
        """
        Apply post-processing to an image.
        
        Args:
            image_path: Path to the image file
            sharpen: Whether to apply sharpening (default: False)
            denoise: Whether to apply denoising (default: False)
            color_correct: Whether to apply color correction (default: False)
            brightness: Brightness adjustment (-1.0 to 1.0, None = no change)
            contrast: Contrast adjustment (-1.0 to 1.0, None = no change)
            
        Returns:
            dict: Result with processed_image_path and applied operations
        """
        try:
            from PIL import Image, ImageEnhance, ImageFilter
        except ImportError:
            raise ImportError("PIL/Pillow is required for image post-processing")
        
        image_path_obj = Path(image_path)
        if not image_path_obj.is_absolute():
            image_path_obj = images_dir() / image_path
        
        if not image_path_obj.exists():
            raise FileNotFoundError(f"Image not found: {image_path_obj}")
        
        # Load image
        img = Image.open(image_path_obj)
        original_mode = img.mode
        
        # Convert to RGB if needed (for processing)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        
        applied_ops: list[str] = []
        
        # Apply sharpening
        if sharpen:
            img = img.filter(ImageFilter.SHARPEN)
            applied_ops.append("sharpen")
        
        # Apply denoising (using median filter as simple denoise)
        if denoise:
            img = img.filter(ImageFilter.MedianFilter(size=3))
            applied_ops.append("denoise")
        
        # Apply brightness adjustment
        if brightness is not None:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.0 + brightness)  # brightness: -1.0 to 1.0 maps to 0.0 to 2.0
            applied_ops.append(f"brightness_{brightness:.2f}")
        
        # Apply contrast adjustment
        if contrast is not None:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.0 + contrast)  # contrast: -1.0 to 1.0 maps to 0.0 to 2.0
            applied_ops.append(f"contrast_{contrast:.2f}")
        
        # Apply color correction (auto white balance approximation)
        if color_correct:
            # Simple color correction: normalize color channels
            import numpy as np
            img_array = np.array(img, dtype=np.float32)
            
            # Calculate channel means
            r_mean = np.mean(img_array[:, :, 0])
            g_mean = np.mean(img_array[:, :, 1])
            b_mean = np.mean(img_array[:, :, 2])
            
            # Target: equalize means (simple white balance)
            target_mean = (r_mean + g_mean + b_mean) / 3.0
            
            if r_mean > 0:
                img_array[:, :, 0] = img_array[:, :, 0] * (target_mean / r_mean)
            if g_mean > 0:
                img_array[:, :, 1] = img_array[:, :, 1] * (target_mean / g_mean)
            if b_mean > 0:
                img_array[:, :, 2] = img_array[:, :, 2] * (target_mean / b_mean)
            
            # Clip to valid range
            img_array = np.clip(img_array, 0, 255)
            img = Image.fromarray(img_array.astype(np.uint8))
            applied_ops.append("color_correct")
        
        # Convert back to original mode if needed
        if original_mode != "RGB" and original_mode != img.mode:
            if original_mode == "RGBA" and img.mode == "RGB":
                # Add alpha channel back
                alpha = Image.new("L", img.size, 255)
                img = img.convert("RGBA")
                img.putalpha(alpha)
            else:
                img = img.convert(original_mode)
        
        # Save processed image
        stem = image_path_obj.stem
        suffix = image_path_obj.suffix
        output_name = f"{stem}_processed{suffix}"
        output_path = images_dir() / output_name
        
        img.save(output_path, format="PNG", quality=95)
        logger.info(f"Saved processed image: {output_path}, operations: {applied_ops}")
        
        return {
            "ok": True,
            "processed_image_path": str(output_path.relative_to(images_dir())),
            "applied_operations": applied_ops,
            "original_path": str(image_path_obj.relative_to(images_dir())),
        }


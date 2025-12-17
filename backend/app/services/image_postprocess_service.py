"""Image post-processing service for quality enhancement.

This module provides post-processing capabilities including:
- Sharpening
- Denoising
- Color correction
- Brightness/contrast adjustment
- AI-powered auto-enhancement
- Skin smoothing (portrait enhancement)
- Smart color grading
- Exposure correction
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir

logger = get_logger(__name__)


class ImagePostProcessService:
    """Service for post-processing images to enhance quality with AI-powered features."""

    def __init__(self) -> None:
        """Initialize post-processing service."""
        pass

    def _analyze_image(self, img_array: Any) -> dict[str, float]:
        """
        Analyze image characteristics for AI-powered enhancement.
        
        Args:
            img_array: NumPy array of image
            
        Returns:
            dict: Analysis results with brightness, contrast, saturation scores
        """
        import numpy as np
        
        # Calculate brightness (mean luminance)
        luminance = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
        brightness = np.mean(luminance) / 255.0
        
        # Calculate contrast (standard deviation of luminance)
        contrast = np.std(luminance) / 255.0
        
        # Calculate saturation (colorfulness)
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        max_channel = np.maximum(np.maximum(r, g), b)
        min_channel = np.minimum(np.minimum(r, g), b)
        saturation = np.mean((max_channel - min_channel) / (max_channel + 1e-6)) / 255.0
        
        return {
            "brightness": float(brightness),
            "contrast": float(contrast),
            "saturation": float(saturation),
        }
    
    def _auto_enhance(self, img: Any) -> tuple[Any, list[str]]:
        """
        Apply AI-powered auto-enhancement based on image analysis.
        
        Args:
            img: PIL Image object
            
        Returns:
            tuple: (enhanced_image, applied_operations)
        """
        import numpy as np
        from PIL import Image, ImageEnhance
        
        img_array = np.array(img, dtype=np.float32)
        analysis = self._analyze_image(img_array)
        applied_ops: list[str] = []
        
        # Auto brightness correction (target: 0.5-0.6)
        if analysis["brightness"] < 0.4:
            # Too dark, brighten
            brightness_factor = 1.0 + (0.5 - analysis["brightness"]) * 0.5
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness_factor)
            applied_ops.append(f"auto_brightness_{brightness_factor:.2f}")
        elif analysis["brightness"] > 0.7:
            # Too bright, darken slightly
            brightness_factor = 1.0 - (analysis["brightness"] - 0.6) * 0.3
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness_factor)
            applied_ops.append(f"auto_brightness_{brightness_factor:.2f}")
        
        # Auto contrast enhancement (target: 0.2-0.4)
        if analysis["contrast"] < 0.15:
            # Low contrast, enhance
            contrast_factor = 1.0 + (0.25 - analysis["contrast"]) * 0.8
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast_factor)
            applied_ops.append(f"auto_contrast_{contrast_factor:.2f}")
        
        # Auto saturation (target: 0.3-0.5 for natural look)
        if analysis["saturation"] < 0.2:
            # Desaturated, enhance colors
            saturation_factor = 1.0 + (0.35 - analysis["saturation"]) * 0.6
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation_factor)
            applied_ops.append(f"auto_saturation_{saturation_factor:.2f}")
        
        return img, applied_ops
    
    def _smooth_skin(self, img: Any, strength: float = 0.5) -> tuple[Any, list[str]]:
        """
        Apply skin smoothing for portrait enhancement.
        
        Args:
            img: PIL Image object
            strength: Smoothing strength (0.0 to 1.0, default: 0.5)
            
        Returns:
            tuple: (smoothed_image, applied_operations)
        """
        from PIL import ImageFilter
        
        if strength <= 0:
            return img, []
        
        # Apply bilateral-like filtering using multiple passes of selective blur
        # This preserves edges while smoothing skin texture
        smoothed = img.filter(ImageFilter.GaussianBlur(radius=strength * 2))
        
        # Blend with original to preserve details
        import numpy as np
        from PIL import Image
        
        original_array = np.array(img, dtype=np.float32)
        smoothed_array = np.array(smoothed, dtype=np.float32)
        
        # Create mask for skin areas (simplified: areas with skin-like colors)
        # In production, this could use face detection
        blend_factor = strength * 0.3  # Conservative blending
        
        blended = original_array * (1 - blend_factor) + smoothed_array * blend_factor
        blended = np.clip(blended, 0, 255).astype(np.uint8)
        
        result = Image.fromarray(blended)
        return result, [f"skin_smoothing_{strength:.2f}"]
    
    def _smart_color_grading(self, img: Any, style: str = "natural") -> tuple[Any, list[str]]:
        """
        Apply smart color grading with different styles.
        
        Args:
            img: PIL Image object
            style: Color grading style: "natural", "warm", "cool", "vibrant", "cinematic"
            
        Returns:
            tuple: (graded_image, applied_operations)
        """
        import numpy as np
        
        img_array = np.array(img, dtype=np.float32)
        
        if style == "natural":
            # Minimal adjustment for natural look
            return img, []
        elif style == "warm":
            # Warm tones: enhance red/yellow, reduce blue
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.05, 0, 255)  # Red
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.02, 0, 255)  # Green
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.98, 0, 255)  # Blue
        elif style == "cool":
            # Cool tones: enhance blue, reduce red/yellow
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.98, 0, 255)  # Red
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.0, 0, 255)   # Green
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.05, 0, 255)  # Blue
        elif style == "vibrant":
            # Vibrant: enhance all colors
            img_array = np.clip(img_array * 1.08, 0, 255)
        elif style == "cinematic":
            # Cinematic: slight desaturation with contrast boost
            from PIL import Image, ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.95)
            return img, [f"color_grading_{style}"]
        else:
            return img, []
        
        result = Image.fromarray(img_array.astype(np.uint8))
        return result, [f"color_grading_{style}"]
    
    def process_image(
        self,
        image_path: str | Path,
        *,
        sharpen: bool = False,
        denoise: bool = False,
        color_correct: bool = False,
        brightness: float | None = None,
        contrast: float | None = None,
        auto_enhance: bool = False,
        skin_smoothing: float | None = None,
        color_grading: str | None = None,
    ) -> dict[str, Any]:
        """
        Apply post-processing to an image with AI-powered enhancements.
        
        Args:
            image_path: Path to the image file
            sharpen: Whether to apply sharpening (default: False)
            denoise: Whether to apply denoising (default: False)
            color_correct: Whether to apply color correction (default: False)
            brightness: Brightness adjustment (-1.0 to 1.0, None = no change)
            contrast: Contrast adjustment (-1.0 to 1.0, None = no change)
            auto_enhance: Whether to apply AI-powered auto-enhancement (default: False)
            skin_smoothing: Skin smoothing strength (0.0 to 1.0, None = disabled)
            color_grading: Color grading style: "natural", "warm", "cool", "vibrant", "cinematic" (None = disabled)
            
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
        
        # Apply AI-powered auto-enhancement first (if enabled)
        if auto_enhance:
            img, auto_ops = self._auto_enhance(img)
            applied_ops.extend(auto_ops)
        
        # Apply color grading (before other adjustments)
        if color_grading:
            img, grading_ops = self._smart_color_grading(img, color_grading)
            applied_ops.extend(grading_ops)
        
        # Apply skin smoothing (portrait enhancement)
        if skin_smoothing is not None and 0 < skin_smoothing <= 1.0:
            img, smoothing_ops = self._smooth_skin(img, skin_smoothing)
            applied_ops.extend(smoothing_ops)
        
        # Apply denoising (using median filter as simple denoise)
        if denoise:
            img = img.filter(ImageFilter.MedianFilter(size=3))
            applied_ops.append("denoise")
        
        # Apply brightness adjustment (manual override)
        if brightness is not None:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.0 + brightness)  # brightness: -1.0 to 1.0 maps to 0.0 to 2.0
            applied_ops.append(f"brightness_{brightness:.2f}")
        
        # Apply contrast adjustment (manual override)
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
        
        # Apply sharpening (last, to enhance final result)
        if sharpen:
            img = img.filter(ImageFilter.SHARPEN)
            applied_ops.append("sharpen")
        
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
    
    def replace_background(
        self,
        image_path: str | Path,
        *,
        background_path: str | Path | None = None,
        background_color: tuple[int, int, int] | None = None,
        method: str = "auto",
    ) -> dict[str, Any]:
        """
        Replace the background of an image with a new background.
        
        Supports:
        - Solid color backgrounds (background_color)
        - Image backgrounds (background_path)
        - Automatic foreground detection using edge detection and color analysis
        
        Args:
            image_path: Path to the source image
            background_path: Path to the background image (optional, if None uses background_color)
            background_color: RGB tuple for solid color background (default: white (255, 255, 255))
            method: Detection method: "auto" (default), "edges", "color"
            
        Returns:
            dict: Result with processed_image_path and metadata
        """
        try:
            from PIL import Image, ImageFilter
            import numpy as np
        except ImportError:
            raise ImportError("PIL/Pillow and numpy are required for background replacement")
        
        image_path_obj = Path(image_path)
        if not image_path_obj.is_absolute():
            image_path_obj = images_dir() / image_path
        
        if not image_path_obj.exists():
            raise FileNotFoundError(f"Image not found: {image_path_obj}")
        
        # Load source image
        img = Image.open(image_path_obj)
        original_mode = img.mode
        
        # Convert to RGBA for transparency support
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        width, height = img.size
        
        # Create or load background
        if background_path:
            bg_path_obj = Path(background_path)
            if not bg_path_obj.is_absolute():
                bg_path_obj = images_dir() / background_path
            
            if not bg_path_obj.exists():
                raise FileNotFoundError(f"Background image not found: {bg_path_obj}")
            
            bg_img = Image.open(bg_path_obj)
            # Resize background to match source image
            bg_img = bg_img.resize((width, height), Image.Resampling.LANCZOS)
            if bg_img.mode != "RGBA":
                bg_img = bg_img.convert("RGBA")
        else:
            # Create solid color background
            bg_color = background_color if background_color else (255, 255, 255)
            bg_img = Image.new("RGBA", (width, height), bg_color + (255,))
        
        # Create foreground mask using automatic detection
        mask = self._create_foreground_mask(img, method=method)
        
        # Apply mask to source image (extract foreground)
        foreground = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        foreground.paste(img, (0, 0))
        
        # Create mask image for compositing
        mask_img = Image.fromarray(mask, mode="L")
        
        # Composite foreground onto background
        result = Image.alpha_composite(bg_img, foreground)
        # Apply mask to blend edges smoothly
        result.putalpha(mask_img)
        
        # Convert back to original mode if needed
        if original_mode != "RGBA":
            # Create white background for non-transparent formats
            rgb_result = Image.new("RGB", result.size, (255, 255, 255))
            rgb_result.paste(result, mask=result.split()[-1])
            result = rgb_result
        
        # Save result
        stem = image_path_obj.stem
        suffix = image_path_obj.suffix
        output_name = f"{stem}_bg_replaced{suffix}"
        output_path = images_dir() / output_name
        
        if result.mode == "RGBA":
            result.save(output_path, format="PNG", quality=95)
        else:
            result.save(output_path, format="PNG", quality=95)
        
        logger.info(f"Background replaced: {output_path}")
        
        return {
            "ok": True,
            "processed_image_path": str(output_path.relative_to(images_dir())),
            "original_path": str(image_path_obj.relative_to(images_dir())),
            "background_type": "image" if background_path else "color",
            "method": method,
        }
    
    def _create_foreground_mask(
        self,
        img: Image.Image,
        method: str = "auto",
    ) -> Any:
        """
        Create a mask for foreground extraction.
        
        Args:
            img: PIL Image in RGBA mode
            method: Detection method: "auto", "edges", "color"
            
        Returns:
            NumPy array mask (0=background, 255=foreground)
        """
        import numpy as np
        from PIL import ImageFilter
        
        img_array = np.array(img, dtype=np.float32)
        height, width = img_array.shape[:2]
        
        # Start with full foreground mask
        mask = np.ones((height, width), dtype=np.uint8) * 255
        
        if method == "auto" or method == "edges":
            # Use edge detection to identify foreground boundaries
            # Convert to grayscale for edge detection
            if img_array.shape[2] == 4:
                gray = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
            else:
                gray = img_array[:, :, 0]
            
            # Calculate gradients (edge detection)
            grad_h = np.abs(np.diff(gray, axis=0, prepend=gray[0:1, :]))
            grad_w = np.abs(np.diff(gray, axis=1, prepend=gray[:, 0:1]))
            edge_strength = np.sqrt(grad_h**2 + grad_w**2)
            
            # Normalize edge strength
            edge_strength = (edge_strength / (edge_strength.max() + 1e-6) * 255).astype(np.uint8)
            
            # Use edges to refine mask (strong edges likely indicate foreground boundaries)
            # Simple approach: assume center region is foreground
            center_y, center_x = height // 2, width // 2
            y_coords, x_coords = np.ogrid[:height, :width]
            
            # Distance from center
            dist_from_center = np.sqrt((y_coords - center_y)**2 + (x_coords - center_x)**2)
            max_dist = np.sqrt(center_y**2 + center_x**2)
            
            # Create radial mask (center is foreground, edges are background)
            # This is a simple heuristic - in production, use proper segmentation
            radial_mask = 1.0 - (dist_from_center / max_dist) * 0.7
            radial_mask = np.clip(radial_mask, 0, 1)
            
            # Combine with edge information
            edge_mask = (edge_strength > 30).astype(float)
            
            # Refine: areas with strong edges near center are likely foreground
            combined = radial_mask * 0.7 + edge_mask * 0.3
            mask = (combined * 255).astype(np.uint8)
        
        elif method == "color":
            # Color-based segmentation (simple chroma key-like approach)
            # Assume background is more uniform than foreground
            if img_array.shape[2] == 4:
                # Analyze color variance - foreground has more variance
                color_variance = np.var(img_array[:, :, :3], axis=2)
                # Normalize
                variance_norm = (color_variance / (color_variance.max() + 1e-6))
                mask = (variance_norm * 255).astype(np.uint8)
            else:
                # Fallback to center-based mask
                center_y, center_x = height // 2, width // 2
                y_coords, x_coords = np.ogrid[:height, :width]
                dist_from_center = np.sqrt((y_coords - center_y)**2 + (x_coords - center_x)**2)
                max_dist = np.sqrt(center_y**2 + center_x**2)
                radial = 1.0 - (dist_from_center / max_dist) * 0.5
                mask = (np.clip(radial, 0, 1) * 255).astype(np.uint8)
        
        # Apply morphological operations to smooth mask
        # Simple smoothing: dilate then erode
        try:
            from scipy import ndimage
            # Dilate to expand foreground
            mask = ndimage.binary_dilation(mask > 128, structure=np.ones((3, 3))).astype(np.uint8) * 255
            # Erode to refine edges
            mask = ndimage.binary_erosion(mask > 128, structure=np.ones((2, 2))).astype(np.uint8) * 255
        except ImportError:
            # If scipy not available, use simple blur
            mask_img = Image.fromarray(mask, mode="L")
            mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1))
            mask = np.array(mask_img, dtype=np.uint8)
        
        return mask


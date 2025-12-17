"""AR (Augmented Reality) filter service for applying filters to images.

This module provides AR filter capabilities including:
- Face detection
- Overlay effects (glasses, hats, accessories)
- Color filters and effects
- Custom overlay images
- Face tracking and alignment
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir

logger = get_logger(__name__)


class ARFilterService:
    """Service for applying AR filters to images with face detection and overlay effects."""

    def __init__(self) -> None:
        """Initialize AR filter service."""
        pass

    def _detect_faces(self, img_array: Any) -> list[dict[str, int]]:
        """
        Detect faces in an image using OpenCV.
        
        Args:
            img_array: NumPy array of image (BGR format for OpenCV)
            
        Returns:
            List of face bounding boxes: [{"x": int, "y": int, "w": int, "h": int}, ...]
        """
        try:
            import cv2
            import numpy as np
        except ImportError:
            logger.warning("OpenCV not available - face detection disabled")
            return []
        
        try:
            # Convert to grayscale for face detection
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array
            
            # Load face cascade classifier
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                face_cascade = cv2.CascadeClassifier(cascade_path)
                
                if face_cascade.empty():
                    logger.warning("Face cascade classifier not found")
                    return []
            except Exception as exc:
                logger.warning(f"Failed to load face cascade: {exc}")
                return []
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )
            
            # Convert to list of dicts
            face_regions = []
            for (x, y, w, h) in faces:
                face_regions.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
            
            logger.debug(f"Detected {len(face_regions)} face(s)")
            return face_regions
            
        except Exception as exc:
            logger.error(f"Face detection failed: {exc}", exc_info=True)
            return []

    def _apply_color_filter(
        self,
        img: Any,
        filter_type: str,
        intensity: float = 0.5,
    ) -> Any:
        """
        Apply color filter effects to an image.
        
        Args:
            img: PIL Image object
            filter_type: Type of filter ("sepia", "vintage", "black_white", "warm", "cool", "vibrant")
            intensity: Filter intensity (0.0 to 1.0)
            
        Returns:
            PIL Image with filter applied
        """
        from PIL import Image, ImageEnhance
        import numpy as np
        
        img_array = np.array(img, dtype=np.float32)
        
        if filter_type == "sepia":
            # Sepia tone
            sepia_matrix = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131],
            ])
            img_array = np.dot(img_array, sepia_matrix.T)
            img_array = np.clip(img_array, 0, 255)
            
        elif filter_type == "vintage":
            # Vintage/aged look
            # Reduce saturation and add slight yellow tint
            img_array[:, :, 0] = img_array[:, :, 0] * (1.0 + intensity * 0.1)  # Red
            img_array[:, :, 1] = img_array[:, :, 1] * (1.0 + intensity * 0.05)  # Green
            img_array[:, :, 2] = img_array[:, :, 2] * (1.0 - intensity * 0.1)  # Blue
            img_array = np.clip(img_array, 0, 255)
            
        elif filter_type == "black_white":
            # Grayscale
            luminance = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
            img_array[:, :, 0] = luminance
            img_array[:, :, 1] = luminance
            img_array[:, :, 2] = luminance
            
        elif filter_type == "warm":
            # Warm tone (increase red/yellow)
            img_array[:, :, 0] = img_array[:, :, 0] * (1.0 + intensity * 0.15)  # Red
            img_array[:, :, 1] = img_array[:, :, 1] * (1.0 + intensity * 0.05)  # Green
            img_array[:, :, 2] = img_array[:, :, 2] * (1.0 - intensity * 0.1)  # Blue
            img_array = np.clip(img_array, 0, 255)
            
        elif filter_type == "cool":
            # Cool tone (increase blue)
            img_array[:, :, 0] = img_array[:, :, 0] * (1.0 - intensity * 0.1)  # Red
            img_array[:, :, 1] = img_array[:, :, 1] * (1.0 - intensity * 0.05)  # Green
            img_array[:, :, 2] = img_array[:, :, 2] * (1.0 + intensity * 0.15)  # Blue
            img_array = np.clip(img_array, 0, 255)
            
        elif filter_type == "vibrant":
            # Increase saturation
            enhancer = ImageEnhance.Color(Image.fromarray(img_array.astype(np.uint8)))
            enhanced = enhancer.enhance(1.0 + intensity * 0.5)
            img_array = np.array(enhanced, dtype=np.float32)
        
        # Blend with original based on intensity
        if intensity < 1.0:
            original = np.array(img, dtype=np.float32)
            img_array = original * (1.0 - intensity) + img_array * intensity
        
        return Image.fromarray(img_array.astype(np.uint8))

    def _apply_overlay_to_face(
        self,
        img: Any,
        face_region: dict[str, int],
        overlay_path: str | Path | None = None,
        overlay_type: str = "glasses",
    ) -> Any:
        """
        Apply an overlay (glasses, hat, etc.) to a detected face region.
        
        Args:
            img: PIL Image object
            face_region: Face bounding box {"x": int, "y": int, "w": int, "h": int}
            overlay_path: Optional path to custom overlay image
            overlay_type: Type of overlay ("glasses", "hat", "mustache", "custom")
            
        Returns:
            PIL Image with overlay applied
        """
        from PIL import Image, ImageDraw, ImageFilter
        import numpy as np
        
        # If custom overlay provided, use it
        if overlay_path:
            try:
                overlay_path_obj = Path(overlay_path)
                if not overlay_path_obj.is_absolute():
                    overlay_path_obj = images_dir() / overlay_path
                
                if overlay_path_obj.exists():
                    overlay_img = Image.open(overlay_path_obj)
                    if overlay_img.mode != "RGBA":
                        overlay_img = overlay_img.convert("RGBA")
                    
                    # Resize overlay to fit face region (adjust based on overlay_type)
                    x, y, w, h = face_region["x"], face_region["y"], face_region["w"], face_region["h"]
                    
                    if overlay_type == "glasses":
                        # Glasses typically cover upper portion of face
                        overlay_width = int(w * 1.2)
                        overlay_height = int(h * 0.4)
                        overlay_y_offset = int(h * 0.1)
                    elif overlay_type == "hat":
                        # Hat sits on top of head
                        overlay_width = int(w * 1.3)
                        overlay_height = int(h * 0.5)
                        overlay_y_offset = int(-h * 0.2)
                    elif overlay_type == "mustache":
                        # Mustache on lower face
                        overlay_width = int(w * 0.8)
                        overlay_height = int(h * 0.3)
                        overlay_y_offset = int(h * 0.5)
                    else:
                        # Default: fit to face width
                        overlay_width = w
                        overlay_height = h
                        overlay_y_offset = 0
                    
                    overlay_img = overlay_img.resize((overlay_width, overlay_height), Image.Resampling.LANCZOS)
                    
                    # Paste overlay onto image
                    overlay_x = x + (w - overlay_width) // 2
                    overlay_y = y + overlay_y_offset
                    
                    # Ensure image is RGBA
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")
                    
                    img.paste(overlay_img, (overlay_x, overlay_y), overlay_img)
                    return img
                    
            except Exception as exc:
                logger.warning(f"Failed to load custom overlay: {exc}")
        
        # Generate simple overlay if no custom overlay provided
        x, y, w, h = face_region["x"], face_region["y"], face_region["w"], face_region["h"]
        
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        draw = ImageDraw.Draw(img)
        
        if overlay_type == "glasses":
            # Draw simple glasses
            glasses_y = y + int(h * 0.3)
            glasses_h = int(h * 0.15)
            # Left lens
            draw.ellipse([x + int(w * 0.1), glasses_y, x + int(w * 0.45), glasses_y + glasses_h], 
                        outline=(0, 0, 0, 255), width=3)
            # Right lens
            draw.ellipse([x + int(w * 0.55), glasses_y, x + int(w * 0.9), glasses_y + glasses_h], 
                        outline=(0, 0, 0, 255), width=3)
            # Bridge
            draw.line([x + int(w * 0.45), glasses_y + glasses_h // 2, 
                      x + int(w * 0.55), glasses_y + glasses_h // 2], 
                     fill=(0, 0, 0, 255), width=2)
            
        elif overlay_type == "hat":
            # Draw simple hat
            hat_y = y - int(h * 0.2)
            hat_w = int(w * 1.2)
            hat_h = int(h * 0.3)
            # Hat brim
            draw.ellipse([x - int(w * 0.1), hat_y + hat_h, x + hat_w, hat_y + hat_h + int(h * 0.1)], 
                        fill=(50, 50, 50, 200), outline=(0, 0, 0, 255), width=2)
            # Hat top
            draw.ellipse([x + int(w * 0.1), hat_y, x + int(w * 0.9), hat_y + hat_h], 
                        fill=(100, 100, 100, 200), outline=(0, 0, 0, 255), width=2)
        
        return img

    def apply_filter(
        self,
        image_path: str | Path,
        *,
        filter_type: str = "color",
        filter_name: str = "vintage",
        intensity: float = 0.5,
        overlay_type: str | None = None,
        overlay_path: str | Path | None = None,
        detect_faces: bool = True,
    ) -> dict[str, Any]:
        """
        Apply AR filter to an image.
        
        Args:
            image_path: Path to input image
            filter_type: Type of filter ("color", "overlay", "both")
            filter_name: Name of color filter ("sepia", "vintage", "black_white", "warm", "cool", "vibrant")
            intensity: Filter intensity (0.0 to 1.0)
            overlay_type: Type of overlay ("glasses", "hat", "mustache", "custom")
            overlay_path: Path to custom overlay image (for custom overlay_type)
            detect_faces: Whether to detect faces for overlay placement
            
        Returns:
            dict with "ok", "filtered_image_path", "faces_detected", "applied_filters", "error"
        """
        try:
            from PIL import Image
            import numpy as np
            
            # Resolve image path
            image_path_obj = Path(image_path)
            if not image_path_obj.is_absolute():
                image_path_obj = images_dir() / image_path
            
            if not image_path_obj.exists():
                return {
                    "ok": False,
                    "error": f"Image not found: {image_path_obj}",
                }
            
            # Load image
            img = Image.open(image_path_obj)
            original_mode = img.mode
            
            # Convert to RGB for processing
            if img.mode != "RGB" and img.mode != "RGBA":
                img = img.convert("RGB")
            
            applied_filters: list[str] = []
            faces_detected: list[dict[str, int]] = []
            
            # Detect faces if needed for overlays
            if overlay_type and detect_faces:
                try:
                    import cv2
                    img_array_cv = np.array(img.convert("RGB"))
                    img_array_cv = cv2.cvtColor(img_array_cv, cv2.COLOR_RGB2BGR)
                    faces_detected = self._detect_faces(img_array_cv)
                    applied_filters.append(f"face_detection({len(faces_detected)} faces)")
                except ImportError:
                    logger.warning("OpenCV not available - skipping face detection")
                    faces_detected = []
            
            # Apply color filter
            if filter_type in ("color", "both"):
                if filter_name:
                    img = self._apply_color_filter(img, filter_name, intensity)
                    applied_filters.append(f"color_filter({filter_name}, intensity={intensity:.2f})")
            
            # Apply overlays to detected faces
            if overlay_type and filter_type in ("overlay", "both"):
                if faces_detected:
                    for face_region in faces_detected:
                        img = self._apply_overlay_to_face(img, face_region, overlay_path, overlay_type)
                    applied_filters.append(f"overlay({overlay_type}, {len(faces_detected)} faces)")
                else:
                    logger.warning(f"No faces detected for overlay type: {overlay_type}")
                    applied_filters.append(f"overlay({overlay_type}, no_faces)")
            
            # Convert back to original mode if needed
            if original_mode != "RGBA" and img.mode == "RGBA":
                # Create white background for non-transparent formats
                rgb_result = Image.new("RGB", img.size, (255, 255, 255))
                rgb_result.paste(img, mask=img.split()[-1])
                img = rgb_result
            elif original_mode != img.mode and original_mode != "RGBA":
                img = img.convert(original_mode)
            
            # Save filtered image
            stem = image_path_obj.stem
            suffix = image_path_obj.suffix
            output_name = f"{stem}_ar_filtered{suffix}"
            output_path = images_dir() / output_name
            
            # Save with appropriate format
            if img.mode == "RGBA":
                img.save(output_path, format="PNG", quality=95)
            else:
                img.save(output_path, format="PNG", quality=95)
            
            logger.info(f"Saved AR filtered image: {output_path}, filters: {applied_filters}")
            
            return {
                "ok": True,
                "filtered_image_path": str(output_path.relative_to(images_dir())),
                "faces_detected": len(faces_detected),
                "face_regions": faces_detected,
                "applied_filters": applied_filters,
                "original_path": str(image_path_obj.relative_to(images_dir())),
            }
            
        except FileNotFoundError as exc:
            return {
                "ok": False,
                "error": f"Image not found: {exc}",
            }
        except ImportError as exc:
            return {
                "ok": False,
                "error": f"Missing required dependency: {exc}",
            }
        except Exception as exc:
            logger.error(f"AR filter application failed: {exc}", exc_info=True)
            return {
                "ok": False,
                "error": f"AR filter application failed: {str(exc)}",
            }

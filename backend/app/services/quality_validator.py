"""Quality validation service for generated content."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import content_dir

logger = get_logger(__name__)


@dataclass
class QualityResult:
    """Result of quality validation.
    
    Attributes:
        quality_score: Overall quality score (0.0 to 1.0, higher is better), None if score could not be calculated.
        is_valid: Whether the content passes all quality checks.
        checks_passed: List of quality check names that passed.
        checks_failed: List of quality check names that failed.
        warnings: List of warning messages for non-critical quality issues.
        errors: List of error messages for critical quality issues.
        metadata: Additional metadata about the validation (file size, dimensions, etc.).
    """

    quality_score: Decimal | None  # 0.0 to 1.0
    is_valid: bool
    checks_passed: list[str]
    checks_failed: list[str]
    warnings: list[str]
    errors: list[str]
    metadata: dict[str, Any]


class QualityValidator:
    """Validates quality of generated content."""

    def __init__(self) -> None:
        """Initialize quality validator."""
        self._min_resolution = (512, 512)  # Minimum acceptable resolution
        self._preferred_resolution = (1024, 1024)  # Preferred resolution

    def validate_content(
        self, content_id: str | None = None, file_path: str | None = None
    ) -> QualityResult:
        """
        Validate content quality.

        Args:
            content_id: Content ID (for database lookup, not implemented yet)
            file_path: Path to content file

        Returns:
            QualityResult with quality score and validation details
        """
        if not file_path:
            return QualityResult(
                quality_score=None,
                is_valid=False,
                checks_passed=[],
                checks_failed=[],
                warnings=[],
                errors=["file_path is required"],
                metadata={},
            )

        # Resolve file path
        file_path_obj = Path(file_path)
        if not file_path_obj.is_absolute():
            # Try relative to content directory
            file_path_obj = content_dir() / file_path

        return self._validate_file(file_path_obj)

    def _validate_file(self, file_path: Path) -> QualityResult:
        """Validate a single file."""
        checks_passed: list[str] = []
        checks_failed: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []
        metadata: dict[str, Any] = {}

        # Check file exists
        if not file_path.exists():
            errors.append(f"File does not exist: {file_path}")
            return QualityResult(
                quality_score=None,
                is_valid=False,
                checks_passed=[],
                checks_failed=[],
                warnings=[],
                errors=errors,
                metadata={},
            )

        checks_passed.append("file_exists")

        # Check file is readable
        if not os.access(file_path, os.R_OK):
            errors.append(f"File is not readable: {file_path}")
            return QualityResult(
                quality_score=None,
                is_valid=False,
                checks_passed=checks_passed,
                checks_failed=[],
                warnings=[],
                errors=errors,
                metadata={},
            )

        checks_passed.append("file_readable")

        # Get file size
        try:
            file_size = file_path.stat().st_size
            metadata["file_size"] = file_size

            # Check minimum file size (very small files might be corrupted)
            if file_size < 1024:  # Less than 1KB
                warnings.append(f"File size is very small: {file_size} bytes")
            else:
                checks_passed.append("file_size_valid")
        except OSError as exc:
            errors.append(f"Failed to get file size: {exc}")

        # Validate based on file type
        file_ext = file_path.suffix.lower()
        if file_ext in (".png", ".jpg", ".jpeg", ".webp"):
            return self._validate_image(file_path, checks_passed, checks_failed, warnings, errors, metadata)
        elif file_ext in (".mp4", ".webm", ".mov"):
            return self._validate_video(file_path, checks_passed, checks_failed, warnings, errors, metadata)
        else:
            # For other file types, do basic validation only
            warnings.append(f"File type {file_ext} validation not fully implemented")
            quality_score = self._calculate_basic_score(checks_passed, checks_failed, warnings, errors)
            return QualityResult(
                quality_score=quality_score,
                is_valid=len(errors) == 0,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                warnings=warnings,
                errors=errors,
                metadata=metadata,
            )

    def _validate_image(
        self,
        file_path: Path,
        checks_passed: list[str],
        checks_failed: list[str],
        warnings: list[str],
        errors: list[str],
        metadata: dict[str, Any],
    ) -> QualityResult:
        """Validate image file."""
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                width, height = img.size
                metadata["width"] = width
                metadata["height"] = height
                metadata["format"] = img.format
                metadata["mode"] = img.mode

                # Check resolution
                if width >= self._min_resolution[0] and height >= self._min_resolution[1]:
                    checks_passed.append("resolution_minimum")
                else:
                    checks_failed.append(
                        f"Resolution below minimum: {width}x{height} (min: {self._min_resolution[0]}x{self._min_resolution[1]})"
                    )

                # Check if resolution is preferred or better
                if width >= self._preferred_resolution[0] and height >= self._preferred_resolution[1]:
                    checks_passed.append("resolution_preferred")
                else:
                    warnings.append(
                        f"Resolution below preferred: {width}x{height} (preferred: {self._preferred_resolution[0]}x{self._preferred_resolution[1]})"
                    )

                # Blur detection using variance of Laplacian
                blur_score = self._detect_blur(img)
                if blur_score is not None:
                    metadata["blur_score"] = float(blur_score)
                    # Threshold: < 100 is likely blurry, > 200 is sharp
                    if blur_score >= 200:
                        checks_passed.append("blur_check_sharp")
                    elif blur_score >= 100:
                        warnings.append(f"Image may be slightly blurry (blur score: {blur_score:.2f})")
                    else:
                        checks_failed.append(f"Image appears blurry (blur score: {blur_score:.2f}, threshold: 100)")

                # Artifact detection
                artifact_score = self._detect_artifacts(img)
                if artifact_score is not None:
                    metadata["artifact_score"] = float(artifact_score)
                    # Threshold: < 0.3 = likely artifacts, 0.3-0.5 = possible artifacts, > 0.5 = clean
                    if artifact_score >= 0.5:
                        checks_passed.append("artifact_check_clean")
                    elif artifact_score >= 0.3:
                        warnings.append(f"Possible artifacts detected (artifact score: {artifact_score:.3f})")
                    else:
                        checks_failed.append(f"Significant artifacts detected (artifact score: {artifact_score:.3f}, threshold: 0.3)")

                # Face-specific artifact detection
                face_artifact_result = self._detect_face_artifacts(img)
                if face_artifact_result is not None:
                    face_artifact_score = face_artifact_result.get("score")
                    face_count = face_artifact_result.get("face_count", 0)
                    skin_texture_score = face_artifact_result.get("skin_texture_score")
                    
                    if face_artifact_score is not None:
                        metadata["face_artifact_score"] = float(face_artifact_score)
                        metadata["face_count"] = face_count
                        # Threshold: < 0.3 = likely face artifacts, 0.3-0.5 = possible, > 0.5 = clean
                        if face_count > 0:
                            if face_artifact_score >= 0.5:
                                checks_passed.append("face_artifact_check_clean")
                            elif face_artifact_score >= 0.3:
                                warnings.append(f"Possible face artifacts detected (face artifact score: {face_artifact_score:.3f}, faces: {face_count})")
                            else:
                                checks_failed.append(f"Significant face artifacts detected (face artifact score: {face_artifact_score:.3f}, threshold: 0.3, faces: {face_count})")
                        
                        # Skin texture realism check
                        if skin_texture_score is not None and face_count > 0:
                            metadata["skin_texture_score"] = float(skin_texture_score)
                            # Threshold: < 0.4 = unrealistic skin texture, 0.4-0.6 = acceptable, > 0.6 = realistic
                            if skin_texture_score >= 0.6:
                                checks_passed.append("skin_texture_realistic")
                            elif skin_texture_score >= 0.4:
                                warnings.append(f"Skin texture may be suboptimal (skin texture score: {skin_texture_score:.3f}, threshold: 0.6)")
                            else:
                                checks_failed.append(f"Unrealistic skin texture detected (skin texture score: {skin_texture_score:.3f}, threshold: 0.4)")
                        
                        # If no faces detected but image appears to be a portrait, warn
                        elif face_count == 0 and width > 0 and height > 0:
                            # Heuristic: if image is roughly square and medium-large, might be a portrait
                            aspect_ratio = width / height if height > 0 else 1.0
                            if 0.7 <= aspect_ratio <= 1.4 and min(width, height) >= 512:
                                warnings.append("No faces detected in image (may be a portrait without clear face)")

                # Color and contrast quality checks
                color_contrast_metrics = self._check_color_contrast(img)
                if color_contrast_metrics is not None:
                    metadata.update(color_contrast_metrics)
                    
                    # Check contrast
                    contrast = color_contrast_metrics.get("contrast", 0)
                    if contrast >= 0.3:  # Good contrast
                        checks_passed.append("contrast_good")
                    elif contrast >= 0.15:  # Acceptable contrast
                        warnings.append(f"Low contrast (contrast: {contrast:.3f}, threshold: 0.3)")
                    else:  # Poor contrast
                        checks_failed.append(f"Very low contrast (contrast: {contrast:.3f}, threshold: 0.15)")
                    
                    # Check brightness/exposure
                    brightness = color_contrast_metrics.get("brightness", 0.5)
                    if 0.2 <= brightness <= 0.8:  # Good exposure range
                        checks_passed.append("exposure_good")
                    elif 0.1 <= brightness <= 0.9:  # Acceptable range
                        warnings.append(f"Brightness may be suboptimal (brightness: {brightness:.3f}, ideal: 0.2-0.8)")
                    else:  # Over/under exposed
                        checks_failed.append(f"Poor exposure (brightness: {brightness:.3f}, ideal: 0.2-0.8)")
                    
                    # Check color saturation (only for color images)
                    if img.mode in ("RGB", "RGBA"):
                        saturation = color_contrast_metrics.get("saturation", 0)
                        if saturation >= 0.3:  # Good saturation
                            checks_passed.append("saturation_good")
                        elif saturation >= 0.15:  # Acceptable saturation
                            warnings.append(f"Low color saturation (saturation: {saturation:.3f}, threshold: 0.3)")
                        else:  # Washed out colors
                            checks_failed.append(f"Very low color saturation (saturation: {saturation:.3f}, threshold: 0.15)")

        except ImportError:
            warnings.append("PIL/Pillow not available, skipping image validation")
        except Exception as exc:
            errors.append(f"Failed to validate image: {exc}")

        quality_score = self._calculate_quality_score(checks_passed, checks_failed, warnings, errors, metadata)
        
        # Add upscale recommendations based on resolution
        upscale_recommendation = self._get_upscale_recommendation(metadata)
        if upscale_recommendation:
            metadata["upscale_recommendation"] = upscale_recommendation
            if upscale_recommendation.get("recommended"):
                warnings.append(f"Consider upscaling to {upscale_recommendation.get('target_size')} for better quality")

        return QualityResult(
            quality_score=quality_score,
            is_valid=len(errors) == 0,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            errors=errors,
            metadata=metadata,
        )

    def _validate_video(
        self,
        file_path: Path,
        checks_passed: list[str],
        checks_failed: list[str],
        warnings: list[str],
        errors: list[str],
        metadata: dict[str, Any],
    ) -> QualityResult:
        """Validate video file."""
        # Basic video validation - can be enhanced later
        warnings.append("Video validation is basic (file exists and readable)")
        checks_passed.append("video_file_valid")

        quality_score = self._calculate_basic_score(checks_passed, checks_failed, warnings, errors)

        return QualityResult(
            quality_score=quality_score,
            is_valid=len(errors) == 0,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            errors=errors,
            metadata=metadata,
        )

    def _calculate_quality_score(
        self,
        checks_passed: list[str],
        checks_failed: list[str],
        warnings: list[str],
        errors: list[str],
        metadata: dict[str, Any],
    ) -> Decimal | None:
        """Calculate quality score (0.0 to 1.0)."""
        if errors:
            return None

        total_checks = len(checks_passed) + len(checks_failed)
        if total_checks == 0:
            return Decimal("0.5")  # Default score if no checks

        # Base score from passed checks
        base_score = len(checks_passed) / total_checks

        # Deduct for warnings (small penalty)
        warning_penalty = len(warnings) * 0.05
        score = max(0.0, min(1.0, base_score - warning_penalty))

        # Bonus for preferred resolution (if image)
        if "resolution_preferred" in checks_passed:
            score = min(1.0, score + 0.1)
        
        # Bonus for sharp image (blur check passed)
        if "blur_check_sharp" in checks_passed:
            score = min(1.0, score + 0.1)
        
        # Bonus for artifact-free image
        if "artifact_check_clean" in checks_passed:
            score = min(1.0, score + 0.1)
        
        # Bonus for face artifact-free image (if faces detected)
        if "face_artifact_check_clean" in checks_passed:
            score = min(1.0, score + 0.1)
        
        # Bonus for realistic skin texture (if faces detected)
        if "skin_texture_realistic" in checks_passed:
            score = min(1.0, score + 0.1)
        
        # Bonus for good color/contrast quality
        color_bonus = 0
        if "contrast_good" in checks_passed:
            color_bonus += 0.05
        if "exposure_good" in checks_passed:
            color_bonus += 0.05
        if "saturation_good" in checks_passed:
            color_bonus += 0.05
        score = min(1.0, score + color_bonus)

        return Decimal(str(round(score, 2)))

    def _detect_artifacts(self, img: Image.Image) -> float | None:
        """
        Detect artifacts in image using edge and texture analysis.
        
        Common AI generation artifacts include:
        - Unnatural edges/patterns
        - Color banding
        - Texture inconsistencies
        - Compression artifacts
        
        Args:
            img: PIL Image object
            
        Returns:
            Artifact score (0.0 to 1.0, higher = cleaner). None if detection failed.
            Typical values: < 0.3 = likely artifacts, 0.3-0.5 = possible, > 0.5 = clean
        """
        try:
            import numpy as np
            from PIL import ImageFilter
            
            # Convert to grayscale if needed
            if img.mode != "L":
                gray = img.convert("L")
            else:
                gray = img
            
            # Convert to numpy array
            img_array = np.array(gray, dtype=np.float32)
            
            # Calculate edge strength using Sobel-like filter
            # Horizontal edges
            h_kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
            h_edges = self._apply_kernel(img_array, h_kernel)
            
            # Vertical edges
            v_kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
            v_edges = self._apply_kernel(img_array, v_kernel)
            
            # Calculate edge magnitude
            edge_magnitude = np.sqrt(h_edges**2 + v_edges**2)
            
            # Calculate statistics
            edge_mean = np.mean(edge_magnitude)
            edge_std = np.std(edge_magnitude)
            
            # Artifact detection heuristics:
            # 1. Very high edge variance might indicate artifacts (unnatural patterns)
            # 2. Very low edge variance might indicate over-smoothed/compressed images
            # 3. Normal images have moderate, consistent edge patterns
            
            # Normalize edge statistics (empirical thresholds)
            # Higher std relative to mean suggests inconsistent patterns (possible artifacts)
            if edge_mean > 0:
                consistency_ratio = edge_std / edge_mean
                # Lower consistency_ratio = more consistent = fewer artifacts
                # Convert to score: 0.0 (many artifacts) to 1.0 (clean)
                # Empirical: ratio < 0.5 is good, > 1.0 is suspicious
                artifact_score = max(0.0, min(1.0, 1.0 - (consistency_ratio - 0.5) * 0.5))
            else:
                # Very flat image, might be over-compressed or corrupted
                artifact_score = 0.2
            
            # Check for color banding (if color image)
            if img.mode in ("RGB", "RGBA"):
                banding_score = self._detect_color_banding(img)
                if banding_score is not None:
                    # Combine edge-based and color-based artifact scores
                    artifact_score = (artifact_score + banding_score) / 2.0
            
            return float(artifact_score)
        except ImportError:
            # numpy not available, skip artifact detection
            return None
        except Exception:
            # Any other error, return None
            return None

    def _detect_face_artifacts(self, img: Image.Image) -> dict[str, Any] | None:
        """
        Detect artifacts specifically in face regions of the image.
        
        This method detects faces in the image and analyzes those regions for
        face-specific AI generation artifacts such as:
        - Distorted facial features
        - Unnatural skin texture
        - Face blending issues
        - Asymmetrical features
        - Unnatural edges around face boundaries
        
        Args:
            img: PIL Image object
            
        Returns:
            dict with:
                - score: Face artifact score (0.0 to 1.0, higher = cleaner). None if detection failed.
                - face_count: Number of faces detected
                - face_regions: List of face bounding boxes (x, y, w, h)
            None if face detection is not available or failed.
            
        Note:
            Uses OpenCV for face detection if available. Falls back gracefully if not installed.
        """
        try:
            import numpy as np
            
            # Try to import OpenCV for face detection
            try:
                import cv2
                cv2_available = True
            except ImportError:
                cv2_available = False
                logger.debug("OpenCV not available - skipping face-specific artifact detection")
                return None
            
            # Convert PIL image to OpenCV format
            img_array = np.array(img.convert("RGB"))
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Load face cascade classifier (Haar Cascade)
            # Try to use OpenCV's built-in face detector
            try:
                # Try to load the default face cascade
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                face_cascade = cv2.CascadeClassifier(cascade_path)
                
                if face_cascade.empty():
                    # Fallback: try alternative path or skip
                    logger.debug("Face cascade classifier not found - skipping face detection")
                    return None
            except Exception:
                logger.debug("Failed to load face cascade classifier - skipping face detection")
                return None
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            face_count = len(faces)
            if face_count == 0:
                # No faces detected
                return {
                    "score": None,
                    "face_count": 0,
                    "face_regions": []
                }
            
            # Analyze each face region for artifacts
            face_scores = []
            skin_texture_scores = []
            face_regions = []
            
            for (x, y, w, h) in faces:
                face_regions.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
                
                # Extract face region
                face_roi = img_array[y:y+h, x:x+w]
                face_img = Image.fromarray(face_roi)
                
                # Analyze face region for artifacts
                # 1. Check for unnatural edges (distorted features)
                face_artifact_score = self._analyze_face_region_artifacts(face_img, img_array, x, y, w, h)
                if face_artifact_score is not None:
                    face_scores.append(face_artifact_score)
                
                # 2. Analyze skin texture specifically
                skin_texture_score = self._analyze_skin_texture(face_img)
                if skin_texture_score is not None:
                    skin_texture_scores.append(skin_texture_score)
            
            if not face_scores:
                # Couldn't analyze faces
                return {
                    "score": None,
                    "face_count": face_count,
                    "face_regions": face_regions,
                    "skin_texture_score": None
                }
            
            # Average score across all faces
            avg_score = float(np.mean(face_scores))
            
            # Average skin texture score across all faces
            avg_skin_texture_score = None
            if skin_texture_scores:
                avg_skin_texture_score = float(np.mean(skin_texture_scores))
            
            return {
                "score": avg_score,
                "face_count": face_count,
                "face_regions": face_regions,
                "skin_texture_score": avg_skin_texture_score
            }
            
        except ImportError:
            # Required libraries not available
            return None
        except Exception as exc:
            # Any other error, log and return None
            logger.debug(f"Face artifact detection failed: {exc}")
            return None

    def _analyze_face_region_artifacts(
        self,
        face_img: Image.Image,
        full_img_array: "np.ndarray",
        x: int,
        y: int,
        w: int,
        h: int
    ) -> float | None:
        """
        Analyze a specific face region for artifacts.
        
        Args:
            face_img: PIL Image of the face region
            full_img_array: Full image as numpy array
            x, y, w, h: Face bounding box coordinates
            
        Returns:
            Artifact score (0.0 to 1.0, higher = cleaner). None if analysis failed.
        """
        try:
            import numpy as np
            
            # Convert face to grayscale
            if face_img.mode != "L":
                face_gray = face_img.convert("L")
            else:
                face_gray = face_img
            
            face_array = np.array(face_gray, dtype=np.float32)
            
            # 1. Check for unnatural edge patterns in face region
            # Faces should have smooth transitions, not harsh edges (except at boundaries)
            # Calculate edge strength
            edge_scores = []
            
            # Horizontal edges
            h_kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
            h_edges = self._apply_kernel(face_array, h_kernel)
            
            # Vertical edges
            v_kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
            v_edges = self._apply_kernel(face_array, v_kernel)
            
            edge_magnitude = np.sqrt(h_edges**2 + v_edges**2)
            
            # Face regions should have moderate, consistent edge patterns
            # Very high variance suggests artifacts (unnatural patterns)
            edge_mean = np.mean(edge_magnitude)
            edge_std = np.std(edge_magnitude)
            
            if edge_mean > 0:
                consistency_ratio = edge_std / edge_mean
                # Lower ratio = more consistent = fewer artifacts
                # For faces, ratio should be moderate (0.3-0.7 is good)
                if consistency_ratio < 0.3:
                    # Too uniform (might be over-smoothed)
                    edge_score = 0.6
                elif consistency_ratio > 1.5:
                    # Too inconsistent (likely artifacts)
                    edge_score = 0.2
                else:
                    # Good consistency
                    edge_score = 0.8
            else:
                edge_score = 0.5
            
            edge_scores.append(edge_score)
            
            # 2. Check for color banding in face region (if color image)
            if face_img.mode in ("RGB", "RGBA"):
                banding_score = self._detect_color_banding(face_img)
                if banding_score is not None:
                    edge_scores.append(banding_score)
            
            # 3. Check for unnatural texture patterns
            # Face skin should have natural texture variation
            # Very uniform or very chaotic patterns suggest artifacts
            texture_variance = np.var(face_array)
            texture_mean = np.mean(face_array)
            
            if texture_mean > 0:
                texture_coefficient = texture_variance / texture_mean
                # Moderate texture variation is natural
                if 0.1 <= texture_coefficient <= 0.5:
                    texture_score = 0.8
                elif texture_coefficient < 0.05:
                    # Too uniform (unnatural)
                    texture_score = 0.4
                elif texture_coefficient > 1.0:
                    # Too chaotic (likely artifacts)
                    texture_score = 0.3
                else:
                    texture_score = 0.6
            else:
                texture_score = 0.5
            
            edge_scores.append(texture_score)
            
            # 4. Analyze skin texture specifically for realism
            skin_texture_score = self._analyze_skin_texture(face_img)
            if skin_texture_score is not None:
                edge_scores.append(skin_texture_score)
            
            # Average all scores
            final_score = float(np.mean(edge_scores))
            
            return max(0.0, min(1.0, final_score))
            
        except Exception:
            return None

    def _analyze_skin_texture(self, face_img: Image.Image) -> float | None:
        """
        Analyze skin texture in face region for realism.
        
        Realistic skin texture should have:
        - Natural micro-texture variation (pores, fine lines)
        - Appropriate smoothness (not too smooth/plastic, not too grainy)
        - Natural frequency distribution (not overly uniform patterns)
        - Avoid AI-generated artifacts like plastic-looking or overly uniform skin
        
        Args:
            face_img: PIL Image of the face region (can be RGB or grayscale)
            
        Returns:
            Skin texture realism score (0.0 to 1.0, higher = more realistic). None if analysis failed.
        """
        try:
            import numpy as np
            
            # Convert to grayscale for texture analysis
            if face_img.mode != "L":
                face_gray = face_img.convert("L")
            else:
                face_gray = face_img
            
            face_array = np.array(face_gray, dtype=np.float32)
            h, w = face_array.shape
            
            # Skip if face region is too small for meaningful analysis
            if h < 20 or w < 20:
                return None
            
            scores = []
            
            # 1. Analyze local texture variation (micro-texture)
            # Real skin has natural variation at small scales (pores, fine lines)
            # Use local standard deviation in small windows
            window_size = min(5, h // 4, w // 4)  # Adaptive window size
            if window_size >= 3:
                local_variations = []
                for i in range(0, h - window_size + 1, window_size // 2):
                    for j in range(0, w - window_size + 1, window_size // 2):
                        window = face_array[i:i+window_size, j:j+window_size]
                        local_std = np.std(window)
                        local_variations.append(local_std)
                
                if local_variations:
                    mean_variation = float(np.mean(local_variations))
                    std_variation = float(np.std(local_variations))
                    
                    # Real skin has moderate local variation with some consistency
                    # Too low = overly smooth/plastic (AI artifact)
                    # Too high = too grainy/noisy
                    # Good range: 5-20 for normalized 0-255 scale
                    if 5.0 <= mean_variation <= 20.0:
                        # Check consistency: real skin has consistent variation
                        if std_variation < mean_variation * 0.8:  # Consistent variation
                            micro_texture_score = 0.9
                        else:
                            micro_texture_score = 0.7
                    elif mean_variation < 2.0:
                        # Too smooth/plastic (common AI artifact)
                        micro_texture_score = 0.3
                    elif mean_variation > 30.0:
                        # Too grainy/noisy
                        micro_texture_score = 0.5
                    else:
                        micro_texture_score = 0.6
                    
                    scores.append(micro_texture_score)
            
            # 2. Analyze frequency domain for unnatural patterns
            # Real skin has natural frequency distribution
            # AI-generated skin often has unnatural frequency patterns
            try:
                # Compute 2D FFT
                fft = np.fft.fft2(face_array)
                fft_shifted = np.fft.fftshift(fft)
                magnitude = np.abs(fft_shifted)
                
                # Analyze frequency distribution
                # Real skin has energy distributed across frequencies
                # Overly uniform patterns show up as concentrated energy
                center_h, center_w = h // 2, w // 2
                
                # Calculate energy distribution
                # Low frequencies (center region)
                low_freq_radius = min(h, w) // 4
                low_freq_mask = np.zeros((h, w), dtype=bool)
                y, x = np.ogrid[:h, :w]
                mask = (x - center_w)**2 + (y - center_h)**2 <= low_freq_radius**2
                low_freq_energy = np.sum(magnitude[mask])
                
                # High frequencies (edges)
                high_freq_energy = np.sum(magnitude) - low_freq_energy
                
                total_energy = np.sum(magnitude)
                if total_energy > 0:
                    low_freq_ratio = low_freq_energy / total_energy
                    
                    # Real skin has balanced frequency distribution
                    # Too much low-frequency energy = overly smooth/plastic
                    # Too much high-frequency energy = too grainy
                    if 0.3 <= low_freq_ratio <= 0.7:
                        frequency_score = 0.8
                    elif low_freq_ratio > 0.85:
                        # Too smooth/plastic (AI artifact)
                        frequency_score = 0.3
                    elif low_freq_ratio < 0.15:
                        # Too grainy
                        frequency_score = 0.5
                    else:
                        frequency_score = 0.6
                    
                    scores.append(frequency_score)
            except Exception:
                # FFT analysis failed, skip this check
                pass
            
            # 3. Analyze smoothness vs. detail balance
            # Real skin has natural balance between smoothness and detail
            # AI-generated skin often errs on too smooth (plastic) or too detailed (uncanny)
            # Use gradient analysis to measure smoothness
            grad_h = np.abs(np.diff(face_array, axis=0))
            grad_w = np.abs(np.diff(face_array, axis=1))
            
            mean_gradient = float(np.mean(np.concatenate([grad_h.flatten(), grad_w.flatten()])))
            
            # Real skin has moderate gradients (not too smooth, not too sharp)
            # Normalized to 0-255 scale
            if 2.0 <= mean_gradient <= 8.0:
                smoothness_score = 0.9
            elif mean_gradient < 1.0:
                # Too smooth/plastic (AI artifact)
                smoothness_score = 0.3
            elif mean_gradient > 15.0:
                # Too sharp/detailed (uncanny)
                smoothness_score = 0.5
            else:
                smoothness_score = 0.6
            
            scores.append(smoothness_score)
            
            # 4. Check for unnatural uniformity
            # Real skin has natural variation, AI-generated skin can be too uniform
            # Analyze coefficient of variation (std/mean)
            texture_std = float(np.std(face_array))
            texture_mean = float(np.mean(face_array))
            
            if texture_mean > 0:
                cv = texture_std / texture_mean  # Coefficient of variation
                
                # Real skin has moderate variation (CV typically 0.15-0.35)
                if 0.15 <= cv <= 0.35:
                    uniformity_score = 0.9
                elif cv < 0.08:
                    # Too uniform (plastic-looking, AI artifact)
                    uniformity_score = 0.2
                elif cv > 0.5:
                    # Too variable (unnatural)
                    uniformity_score = 0.5
                else:
                    uniformity_score = 0.7
                
                scores.append(uniformity_score)
            
            # Average all scores
            if scores:
                final_score = float(np.mean(scores))
                return max(0.0, min(1.0, final_score))
            
            return None
            
        except Exception:
            return None

    def _apply_kernel(self, img_array: "np.ndarray", kernel: "np.ndarray") -> "np.ndarray":
        """Apply convolution kernel to image array (simple implementation)."""
        import numpy as np
        
        h, w = img_array.shape
        kh, kw = kernel.shape
        pad_h, pad_w = kh // 2, kw // 2
        
        # Pad image
        padded = np.pad(img_array, ((pad_h, pad_h), (pad_w, pad_w)), mode="edge")
        
        # Apply kernel
        result = np.zeros_like(img_array)
        for i in range(h):
            for j in range(w):
                result[i, j] = np.sum(padded[i:i+kh, j:j+kw] * kernel)
        
        return result

    def _check_color_contrast(self, img: Image.Image) -> dict[str, float] | None:
        """
        Check color and contrast quality metrics.
        
        Args:
            img: PIL Image object
            
        Returns:
            Dictionary with metrics: contrast, brightness, saturation (for color images).
            None if detection failed.
        """
        try:
            import numpy as np
            
            # Convert to grayscale for contrast/brightness
            if img.mode != "L":
                gray = img.convert("L")
            else:
                gray = img
            
            gray_array = np.array(gray, dtype=np.float32) / 255.0
            
            # Calculate contrast (standard deviation of pixel values)
            # Higher std = more contrast
            contrast = float(np.std(gray_array))
            
            # Calculate brightness (mean luminance)
            # 0.0 = black, 1.0 = white, 0.5 = mid-gray
            brightness = float(np.mean(gray_array))
            
            metrics: dict[str, float] = {
                "contrast": contrast,
                "brightness": brightness,
            }
            
            # Calculate color saturation (for color images)
            if img.mode in ("RGB", "RGBA"):
                rgb_array = np.array(img.convert("RGB"), dtype=np.float32) / 255.0
                
                # Calculate saturation using HSV-like approach
                # Saturation = std of RGB values per pixel, averaged
                # Higher std = more saturated colors
                pixel_saturations = []
                for i in range(rgb_array.shape[0]):
                    for j in range(rgb_array.shape[1]):
                        pixel_rgb = rgb_array[i, j]
                        # Saturation is the standard deviation of RGB values
                        # For a grayscale pixel, std = 0 (no saturation)
                        # For a pure color, std is high
                        pixel_std = float(np.std(pixel_rgb))
                        pixel_saturations.append(pixel_std)
                
                saturation = float(np.mean(pixel_saturations)) if pixel_saturations else 0.0
                metrics["saturation"] = saturation
            
            return metrics
        except ImportError:
            return None
        except Exception:
            return None

    def _detect_color_banding(self, img: Image.Image) -> float | None:
        """
        Detect color banding artifacts (unnatural color gradients).
        
        Args:
            img: PIL Image object (RGB/RGBA)
            
        Returns:
            Banding score (0.0 to 1.0, higher = less banding). None if detection failed.
        """
        try:
            import numpy as np
            
            # Convert to numpy array
            img_array = np.array(img.convert("RGB"), dtype=np.float32)
            
            # Calculate gradient in each color channel
            # Simple gradient: difference between adjacent pixels
            gradients = []
            for channel in range(3):  # R, G, B
                channel_data = img_array[:, :, channel]
                # Horizontal gradient
                h_grad = np.abs(np.diff(channel_data, axis=1))
                # Vertical gradient
                v_grad = np.abs(np.diff(channel_data, axis=0))
                gradients.extend([h_grad.flatten(), v_grad.flatten()])
            
            # Combine all gradients
            all_gradients = np.concatenate(gradients)
            
            # Calculate gradient distribution
            grad_mean = np.mean(all_gradients)
            grad_std = np.std(all_gradients)
            
            # Color banding shows up as very uniform gradients (low variance)
            # Normal images have varied gradients
            if grad_std > 0:
                # Higher std relative to mean = more natural variation = less banding
                variation_ratio = grad_std / (grad_mean + 1e-6)
                # Convert to score: more variation = higher score = less banding
                banding_score = min(1.0, variation_ratio / 2.0)  # Normalize
            else:
                # No variation = likely banding
                banding_score = 0.1
            
            return float(banding_score)
        except ImportError:
            return None
        except Exception:
            return None

    def _detect_blur(self, img: Image.Image) -> float | None:
        """
        Detect blur in image using variance of Laplacian.
        
        Args:
            img: PIL Image object
            
        Returns:
            Blur score (higher = sharper). None if detection failed.
            Typical values: < 100 = blurry, 100-200 = acceptable, > 200 = sharp
        """
        try:
            import numpy as np
            from PIL import ImageFilter
            
            # Convert to grayscale if needed
            if img.mode != "L":
                gray = img.convert("L")
            else:
                gray = img
            
            # Apply Laplacian filter
            laplacian = gray.filter(ImageFilter.Kernel(
                (3, 3),
                [0, -1, 0, -1, 4, -1, 0, -1, 0],
                scale=1
            ))
            
            # Convert to numpy array and calculate variance
            laplacian_array = np.array(laplacian)
            variance = float(np.var(laplacian_array))
            
            return variance
        except ImportError:
            # numpy not available, skip blur detection
            return None
        except Exception:
            # Any other error, return None
            return None

    def _calculate_basic_score(
        self,
        checks_passed: list[str],
        checks_failed: list[str],
        warnings: list[str],
        errors: list[str],
    ) -> Decimal | None:
        """
        Calculate basic quality score from check results without metadata bonuses.
        
        Args:
            checks_passed: List of passed check names
            checks_failed: List of failed check names
            warnings: List of warning messages
            errors: List of error messages
        
        Returns:
            Quality score as Decimal (0.0 to 1.0), or None if errors present.
            Score is based on passed/total checks ratio with warning penalties.
        """
        if errors:
            return None

        total_checks = len(checks_passed) + len(checks_failed)
        if total_checks == 0:
            return Decimal("0.5")

        base_score = len(checks_passed) / total_checks
        warning_penalty = len(warnings) * 0.05
        score = max(0.0, min(1.0, base_score - warning_penalty))

        return Decimal(str(round(score, 2)))
    
    def _get_upscale_recommendation(self, metadata: dict[str, Any]) -> dict[str, Any] | None:
        """
        Get upscaling recommendation based on image resolution and quality.
        
        Args:
            metadata: Quality validation metadata containing width/height
            
        Returns:
            dict with recommendation details, or None if no recommendation
        """
        width = metadata.get("width")
        height = metadata.get("height")
        
        if not width or not height:
            return None
        
        # Preferred resolution is 2048x2048 or higher
        preferred_min = 2048
        current_max = max(width, height)
        
        if current_max < preferred_min:
            # Recommend upscaling
            scale_factor = 2 if current_max < 1024 else 2  # 2x for images < 2048
            target_size = (width * scale_factor, height * scale_factor)
            
            return {
                "recommended": True,
                "current_size": (width, height),
                "target_size": target_size,
                "scale_factor": scale_factor,
                "reason": f"Current resolution ({width}x{height}) is below preferred minimum ({preferred_min}px). Upscaling to {target_size[0]}x{target_size[1]} would improve quality.",
            }
        
        return {
            "recommended": False,
            "current_size": (width, height),
            "reason": f"Current resolution ({width}x{height}) meets or exceeds preferred minimum ({preferred_min}px).",
        }


# Singleton instance
quality_validator = QualityValidator()


"""
Quality Assurance Service
Handles automated quality scoring, artifact detection, and realism validation
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

class QualityService:
    """Service for quality assurance and scoring"""
    
    def __init__(self):
        self.comfyui_models_path = Path(__file__).parent.parent.parent / "ComfyUI" / "models"
        self.face_detector = None
        self.artifact_detector = None
    
    def score_content(
        self,
        content_path: Path,
        content_type: str = "image"
    ) -> Dict[str, Any]:
        """Score content quality"""
        try:
            if content_type == "image":
                return self._score_image(content_path)
            elif content_type == "video":
                return self._score_video(content_path)
            else:
                return {"error": "Unsupported content type"}
                
        except Exception as e:
            logger.error(f"Quality scoring error: {e}")
            return {
                "overall": 0.0,
                "error": str(e)
            }
    
    def _score_image(self, image_path: Path) -> Dict[str, Any]:
        """Score image quality"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img)
            
            scores = {}
            
            # 1. Face Quality (if face detected)
            face_score = self._score_face(img, img_array)
            scores["face"] = face_score
            
            # 2. Technical Quality
            technical_score = self._score_technical(img, img_array)
            scores["technical"] = technical_score
            
            # 3. Realism Score
            realism_score = self._score_realism(img, img_array)
            scores["realism"] = realism_score
            
            # 4. Artifact Detection
            artifact_score = self._detect_artifacts(img, img_array)
            scores["artifacts"] = artifact_score
            
            # 5. Overall Score (weighted average)
            overall = (
                face_score["overall"] * 0.4 +
                technical_score["overall"] * 0.3 +
                realism_score * 0.2 +
                (1 - artifact_score["severity"]) * 0.1
            )
            scores["overall"] = overall
            
            # 6. Pass/Fail
            scores["passed"] = overall >= 8.0 and artifact_score["severity"] < 0.2
            scores["auto_approved"] = overall >= 9.0 and artifact_score["severity"] < 0.1
            
            return scores
            
        except Exception as e:
            logger.error(f"Image scoring error: {e}")
            return {
                "overall": 0.0,
                "error": str(e),
                "passed": False
            }
    
    def _score_face(self, img: Image.Image, img_array: np.ndarray) -> Dict[str, Any]:
        """Score face quality"""
        try:
            # Try to detect face
            face_detected = self._detect_face(img_array)
            
            if not face_detected:
                return {
                    "detected": False,
                    "overall": 0.0,
                    "sharpness": 0.0,
                    "symmetry": 0.0,
                    "lighting": 0.0,
                    "expression": 0.0
                }
            
            # Calculate face metrics
            sharpness = self._calculate_sharpness(img_array)
            symmetry = self._calculate_symmetry(img_array)
            lighting = self._calculate_lighting(img_array)
            expression = 0.8  # Placeholder - would need expression detection
            
            # Overall face score
            overall = (
                sharpness * 0.3 +
                symmetry * 0.2 +
                lighting * 0.3 +
                expression * 0.2
            )
            
            return {
                "detected": True,
                "overall": overall * 10,  # Scale to 0-10
                "sharpness": sharpness * 10,
                "symmetry": symmetry * 10,
                "lighting": lighting * 10,
                "expression": expression * 10
            }
            
        except Exception as e:
            logger.warning(f"Face scoring error: {e}")
            return {
                "detected": False,
                "overall": 0.0
            }
    
    def _score_technical(self, img: Image.Image, img_array: np.ndarray) -> Dict[str, Any]:
        """Score technical quality"""
        try:
            # Resolution score
            width, height = img.size
            resolution_score = min(1.0, (width * height) / (2048 * 2048))
            
            # Sharpness score
            sharpness = self._calculate_sharpness(img_array)
            
            # Color quality
            color_score = self._calculate_color_quality(img_array)
            
            # Composition (basic)
            composition_score = 0.8  # Placeholder
            
            # Overall technical score
            overall = (
                resolution_score * 0.3 +
                sharpness * 0.3 +
                color_score * 0.2 +
                composition_score * 0.2
            )
            
            return {
                "overall": overall * 10,
                "resolution": resolution_score * 10,
                "sharpness": sharpness * 10,
                "color": color_score * 10,
                "composition": composition_score * 10
            }
            
        except Exception as e:
            logger.warning(f"Technical scoring error: {e}")
            return {
                "overall": 0.0
            }
    
    def _score_realism(self, img: Image.Image, img_array: np.ndarray) -> float:
        """Score realism"""
        try:
            # Check for natural patterns
            natural_patterns = self._check_natural_patterns(img_array)
            
            # Check for realistic lighting
            realistic_lighting = self._check_realistic_lighting(img_array)
            
            # Check for natural colors
            natural_colors = self._check_natural_colors(img_array)
            
            # Overall realism
            realism = (
                natural_patterns * 0.4 +
                realistic_lighting * 0.3 +
                natural_colors * 0.3
            )
            
            return realism * 10  # Scale to 0-10
            
        except Exception as e:
            logger.warning(f"Realism scoring error: {e}")
            return 0.0
    
    def _detect_artifacts(self, img: Image.Image, img_array: np.ndarray) -> Dict[str, Any]:
        """Detect artifacts in image"""
        try:
            artifacts = []
            severity = 0.0
            
            # Check for common AI artifacts
            # 1. Check for extra/missing fingers (would need hand detection)
            # 2. Check for distorted faces
            # 3. Check for unnatural patterns
            # 4. Check for compression artifacts
            
            # Basic artifact detection
            if self._has_compression_artifacts(img_array):
                artifacts.append("compression_artifacts")
                severity += 0.1
            
            if self._has_unnatural_patterns(img_array):
                artifacts.append("unnatural_patterns")
                severity += 0.15
            
            severity = min(1.0, severity)
            
            return {
                "detected": len(artifacts) > 0,
                "artifacts": artifacts,
                "severity": severity,
                "count": len(artifacts)
            }
            
        except Exception as e:
            logger.warning(f"Artifact detection error: {e}")
            return {
                "detected": False,
                "artifacts": [],
                "severity": 0.0,
                "count": 0
            }
    
    def _detect_face(self, img_array: np.ndarray) -> bool:
        """Detect if face is present"""
        try:
            # Simple face detection using basic heuristics
            # In production, would use proper face detection library
            # For now, assume face is present if image is portrait-like
            height, width = img_array.shape[:2]
            aspect_ratio = height / width if width > 0 else 1.0
            
            # Portrait-like images likely have faces
            return 0.8 < aspect_ratio < 1.5
            
        except Exception as e:
            logger.warning(f"Face detection error: {e}")
            return False
    
    def _calculate_sharpness(self, img_array: np.ndarray) -> float:
        """Calculate image sharpness"""
        try:
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            # Calculate Laplacian variance (sharpness metric)
            from scipy import ndimage
            laplacian = ndimage.laplacian(gray.astype(float))
            variance = np.var(laplacian)
            
            # Normalize to 0-1 range
            sharpness = min(1.0, variance / 1000.0)
            
            return sharpness
            
        except Exception as e:
            logger.warning(f"Sharpness calculation error: {e}")
            return 0.5  # Default moderate sharpness
    
    def _calculate_symmetry(self, img_array: np.ndarray) -> float:
        """Calculate face symmetry"""
        try:
            # Simple symmetry check (would need proper face detection)
            # For now, return moderate score
            return 0.8
            
        except Exception as e:
            logger.warning(f"Symmetry calculation error: {e}")
            return 0.5
    
    def _calculate_lighting(self, img_array: np.ndarray) -> float:
        """Calculate lighting quality"""
        try:
            # Calculate brightness distribution
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            
            # Good lighting: mean around 128, std around 40-60
            brightness_score = 1.0 - abs(mean_brightness - 128) / 128
            contrast_score = min(1.0, std_brightness / 60)
            
            lighting = (brightness_score + contrast_score) / 2
            
            return lighting
            
        except Exception as e:
            logger.warning(f"Lighting calculation error: {e}")
            return 0.5
    
    def _calculate_color_quality(self, img_array: np.ndarray) -> float:
        """Calculate color quality"""
        try:
            if len(img_array.shape) != 3:
                return 0.5
            
            # Check color saturation
            # Convert to HSV and check saturation
            from PIL import Image
            img = Image.fromarray(img_array)
            hsv = img.convert("HSV")
            hsv_array = np.array(hsv)
            
            saturation = np.mean(hsv_array[:, :, 1]) / 255.0
            
            # Good saturation is around 0.3-0.7
            if 0.3 <= saturation <= 0.7:
                color_score = 1.0
            else:
                color_score = 1.0 - abs(saturation - 0.5) * 2
            
            return max(0.0, min(1.0, color_score))
            
        except Exception as e:
            logger.warning(f"Color quality calculation error: {e}")
            return 0.5
    
    def _check_natural_patterns(self, img_array: np.ndarray) -> float:
        """Check for natural patterns"""
        try:
            # Check for natural variation in pixel values
            # Real photos have more variation than AI-generated
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            # Calculate local variance
            variance = np.var(gray)
            
            # Normalize
            natural_score = min(1.0, variance / 500.0)
            
            return natural_score
            
        except Exception as e:
            logger.warning(f"Natural pattern check error: {e}")
            return 0.5
    
    def _check_realistic_lighting(self, img_array: np.ndarray) -> float:
        """Check for realistic lighting"""
        try:
            # Similar to lighting calculation
            return self._calculate_lighting(img_array)
            
        except Exception as e:
            logger.warning(f"Realistic lighting check error: {e}")
            return 0.5
    
    def _check_natural_colors(self, img_array: np.ndarray) -> float:
        """Check for natural colors"""
        try:
            # Similar to color quality
            return self._calculate_color_quality(img_array)
            
        except Exception as e:
            logger.warning(f"Natural color check error: {e}")
            return 0.5
    
    def _has_compression_artifacts(self, img_array: np.ndarray) -> bool:
        """Check for compression artifacts"""
        try:
            # Simple check for blocky patterns
            # In production, would use more sophisticated detection
            return False  # Placeholder
            
        except Exception as e:
            logger.warning(f"Compression artifact check error: {e}")
            return False
    
    def _has_unnatural_patterns(self, img_array: np.ndarray) -> bool:
        """Check for unnatural patterns"""
        try:
            # Check for repeating patterns (AI generation artifact)
            # Simple heuristic: check for high frequency patterns
            return False  # Placeholder
            
        except Exception as e:
            logger.warning(f"Unnatural pattern check error: {e}")
            return False
    
    def _score_video(self, video_path: Path) -> Dict[str, Any]:
        """Score video quality"""
        # TODO: Implement video scoring
        return {
            "overall": 0.0,
            "error": "Video scoring not yet implemented"
        }
    
    def validate_content(
        self,
        content_path: Path,
        content_type: str = "image",
        min_score: float = 8.0
    ) -> Dict[str, Any]:
        """Validate content meets quality standards"""
        scores = self.score_content(content_path, content_type)
        
        passed = scores.get("overall", 0.0) >= min_score
        artifacts_ok = scores.get("artifacts", {}).get("severity", 1.0) < 0.2
        
        return {
            "passed": passed and artifacts_ok,
            "scores": scores,
            "min_score": min_score,
            "meets_standards": passed and artifacts_ok
        }

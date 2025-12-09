"""
Quality Scorer Service
Comprehensive quality scoring system as per docs/28-QUALITY-ASSURANCE-SYSTEM.md
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from PIL import Image
import numpy as np
from scipy import ndimage

logger = logging.getLogger(__name__)


class FaceDetector:
    """Face detection and analysis"""
    
    def detect(self, image_path: Path) -> List[Dict[str, Any]]:
        """Detect faces in image"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert("RGB"))
            
            # Basic face detection (placeholder - would use proper face detection library)
            # For now, assume face is present if image is portrait-like
            height, width = img_array.shape[:2]
            aspect_ratio = height / width if width > 0 else 1.0
            
            if 0.8 < aspect_ratio < 1.5:
                # Calculate face metrics
                face = {
                    "sharpness": self._calculate_sharpness(img_array),
                    "symmetry": self._calculate_symmetry(img_array),
                    "lighting": self._calculate_lighting(img_array),
                    "expression": 0.8  # Placeholder
                }
                return [face]
            
            return []
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []
    
    def _calculate_sharpness(self, img_array: np.ndarray) -> float:
        """Calculate sharpness score"""
        try:
            gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
            laplacian = ndimage.laplacian(gray.astype(float))
            variance = np.var(laplacian)
            return min(1.0, variance / 1000.0)
        except:
            return 0.5
    
    def _calculate_symmetry(self, img_array: np.ndarray) -> float:
        """Calculate symmetry score"""
        try:
            # Simple symmetry check
            gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
            height, width = gray.shape
            mid = width // 2
            left = gray[:, :mid]
            right = np.fliplr(gray[:, mid:])
            if right.shape[1] != left.shape[1]:
                right = right[:, :left.shape[1]]
            diff = np.abs(left - right)
            symmetry = 1.0 - (np.mean(diff) / 255.0)
            return max(0.0, min(1.0, symmetry))
        except:
            return 0.8
    
    def _calculate_lighting(self, img_array: np.ndarray) -> float:
        """Calculate lighting quality"""
        try:
            gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            brightness_score = 1.0 - abs(mean_brightness - 128) / 128
            contrast_score = min(1.0, std_brightness / 60)
            return (brightness_score + contrast_score) / 2
        except:
            return 0.5


class ArtifactDetector:
    """Artifact detection"""
    
    def detect(self, image_path: Path) -> Dict[str, Any]:
        """Detect artifacts in image"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert("RGB"))
            
            artifacts = []
            severity = 0.0
            
            # Check for compression artifacts
            if self._has_compression_artifacts(img_array):
                artifacts.append("compression_artifacts")
                severity += 0.1
            
            # Check for unnatural patterns
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
            logger.error(f"Artifact detection error: {e}")
            return {
                "detected": False,
                "artifacts": [],
                "severity": 0.0,
                "count": 0
            }
    
    def _has_compression_artifacts(self, img_array: np.ndarray) -> bool:
        """Check for compression artifacts"""
        # Placeholder - would use more sophisticated detection
        return False
    
    def _has_unnatural_patterns(self, img_array: np.ndarray) -> bool:
        """Check for unnatural patterns"""
        # Placeholder - would use more sophisticated detection
        return False


class RealismScorer:
    """Realism scoring"""
    
    def score(self, image_path: Path) -> float:
        """Score realism (0-10)"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert("RGB"))
            
            # Check natural patterns
            natural_patterns = self._check_natural_patterns(img_array)
            
            # Check realistic lighting
            realistic_lighting = self._check_realistic_lighting(img_array)
            
            # Check natural colors
            natural_colors = self._check_natural_colors(img_array)
            
            # Overall realism
            realism = (
                natural_patterns * 0.4 +
                realistic_lighting * 0.3 +
                natural_colors * 0.3
            )
            
            return realism * 10  # Scale to 0-10
            
        except Exception as e:
            logger.error(f"Realism scoring error: {e}")
            return 0.0
    
    def _check_natural_patterns(self, img_array: np.ndarray) -> float:
        """Check for natural patterns"""
        try:
            gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
            variance = np.var(gray)
            return min(1.0, variance / 500.0)
        except:
            return 0.5
    
    def _check_realistic_lighting(self, img_array: np.ndarray) -> float:
        """Check for realistic lighting"""
        try:
            gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            brightness_score = 1.0 - abs(mean_brightness - 128) / 128
            contrast_score = min(1.0, std_brightness / 60)
            return (brightness_score + contrast_score) / 2
        except:
            return 0.5
    
    def _check_natural_colors(self, img_array: np.ndarray) -> float:
        """Check for natural colors"""
        try:
            if len(img_array.shape) != 3:
                return 0.5
            
            img = Image.fromarray(img_array)
            hsv = img.convert("HSV")
            hsv_array = np.array(hsv)
            saturation = np.mean(hsv_array[:, :, 1]) / 255.0
            
            if 0.3 <= saturation <= 0.7:
                return 1.0
            else:
                return max(0.0, 1.0 - abs(saturation - 0.5) * 2)
        except:
            return 0.5


class QualityScorer:
    """Comprehensive quality scorer as per QA document"""
    
    def __init__(self):
        self.face_detector = FaceDetector()
        self.artifact_detector = ArtifactDetector()
        self.realism_scorer = RealismScorer()
    
    def score(self, content_path: Path, content_type: str = "image") -> Dict[str, Any]:
        """Score content quality
        
        Returns:
            {
                'face': float (0-10),
                'technical': float (0-10),
                'realism': float (0-10),
                'overall': float (0-10),
                'passed': bool,
                'auto_approved': bool
            }
        """
        try:
            if content_type == "image":
                return self._score_image(content_path)
            elif content_type == "video":
                return self._score_video(content_path)
            else:
                return {
                    "error": "Unsupported content type",
                    "overall": 0.0,
                    "passed": False
                }
        except Exception as e:
            logger.error(f"Quality scoring error: {e}")
            return {
                "overall": 0.0,
                "error": str(e),
                "passed": False
            }
    
    def _score_image(self, image_path: Path) -> Dict[str, Any]:
        """Score image quality"""
        scores = {}
        
        # Face quality (0-10)
        scores['face'] = self.score_face(image_path)
        
        # Technical quality (0-10)
        scores['technical'] = self.score_technical(image_path)
        
        # Realism (0-10)
        scores['realism'] = self.score_realism(image_path)
        
        # Overall (weighted average)
        scores['overall'] = (
            scores['face'] * 0.4 +
            scores['technical'] * 0.3 +
            scores['realism'] * 0.3
        )
        
        # Check thresholds
        scores['passed'] = (
            scores['overall'] >= 8.0 and
            scores['face'] >= 8.0 and
            scores['technical'] >= 7.5 and
            scores['realism'] >= 8.0
        )
        
        scores['auto_approved'] = (
            scores['overall'] >= 9.0 and
            scores['face'] >= 8.5 and
            scores['technical'] >= 8.5 and
            scores['realism'] >= 8.5
        )
        
        return scores
    
    def score_face(self, image_path: Path) -> float:
        """Score face quality (0-10)"""
        faces = self.face_detector.detect(image_path)
        if not faces:
            return 0.0
        
        face = faces[0]
        score = 0.0
        score += face['sharpness'] * 0.3
        score += face['symmetry'] * 0.2
        score += face['lighting'] * 0.3
        score += face['expression'] * 0.2
        
        return score * 10
    
    def score_technical(self, image_path: Path) -> float:
        """Score technical quality (0-10)"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert("RGB"))
            
            # Resolution score
            width, height = img.size
            resolution_score = min(1.0, (width * height) / (2048 * 2048))
            
            # Sharpness score
            gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
            laplacian = ndimage.laplacian(gray.astype(float))
            variance = np.var(laplacian)
            sharpness = min(1.0, variance / 1000.0)
            
            # Artifact score (lower is better)
            artifact_result = self.artifact_detector.detect(image_path)
            artifact_score = 1.0 - artifact_result['severity']
            
            # Color quality
            img_pil = Image.fromarray(img_array)
            hsv = img_pil.convert("HSV")
            hsv_array = np.array(hsv)
            saturation = np.mean(hsv_array[:, :, 1]) / 255.0
            if 0.3 <= saturation <= 0.7:
                color_score = 1.0
            else:
                color_score = max(0.0, 1.0 - abs(saturation - 0.5) * 2)
            
            # Overall technical score
            overall = (
                resolution_score * 0.3 +
                sharpness * 0.3 +
                artifact_score * 0.2 +
                color_score * 0.2
            )
            
            return overall * 10
            
        except Exception as e:
            logger.error(f"Technical scoring error: {e}")
            return 0.0
    
    def score_realism(self, image_path: Path) -> float:
        """Score realism (0-10)"""
        return self.realism_scorer.score(image_path)
    
    def _score_video(self, video_path: Path) -> Dict[str, Any]:
        """Score video quality (placeholder)"""
        return {
            "overall": 0.0,
            "error": "Video scoring not yet implemented",
            "passed": False
        }

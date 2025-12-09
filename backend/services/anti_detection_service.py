"""
Anti-Detection Service
Comprehensive service for testing and avoiding AI detection
Implements all techniques from 24-ANTI-DETECTION-ADVANCED-TECHNIQUES.md
"""
import logging
import os
import base64
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from PIL import Image
import piexif
import requests
import json
from datetime import datetime
import numpy as np
from io import BytesIO

logger = logging.getLogger(__name__)


class DetectionTester:
    """Base class for detection tools"""
    
    def __init__(self, name: str):
        self.name = name
        self.api_key = None
    
    def detect(self, image_path: Path) -> Dict[str, Any]:
        """Detect AI content in image"""
        raise NotImplementedError
    
    def get_score(self, result: Dict[str, Any]) -> float:
        """Extract detection score from result (0.0 = human, 1.0 = AI)"""
        raise NotImplementedError


class HiveModeration(DetectionTester):
    """Hive Moderation API integration"""
    
    def __init__(self, api_key: Optional[str] = None, db_session=None):
        super().__init__("hive")
        self.api_key = api_key
        if not self.api_key:
            # Try environment variable
            self.api_key = os.getenv("HIVE_API_KEY")
        if not self.api_key and db_session:
            # Try database
            try:
                from models import DetectionToolConfig
                config = db_session.query(DetectionToolConfig).filter(
                    DetectionToolConfig.tool_name == "hive",
                    DetectionToolConfig.enabled == True
                ).first()
                if config:
                    self.api_key = config.api_key
            except:
                pass
        self.api_url = "https://api.thehive.ai/api/v2/task/sync"
    
    def detect(self, image_path: Path) -> Dict[str, Any]:
        """Test image with Hive Moderation"""
        if not self.api_key:
            logger.warning("Hive API key not configured")
            return {"error": "API key not configured", "score": 0.5}
        
        try:
            with open(image_path, "rb") as f:
                files = {"media": f}
                headers = {"Authorization": f"Token {self.api_key}"}
                response = requests.post(
                    self.api_url,
                    files=files,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_response(data)
                else:
                    logger.error(f"Hive API error: {response.status_code}")
                    return {"error": f"API error: {response.status_code}", "score": 0.5}
                    
        except Exception as e:
            logger.error(f"Hive detection error: {e}")
            return {"error": str(e), "score": 0.5}
    
    def _parse_response(self, data: Dict) -> Dict[str, Any]:
        """Parse Hive API response"""
        score = 0.5  # Default neutral
        
        if "status" in data and data["status"].get("response", []):
            for response_item in data["status"]["response"]:
                if "output" in response_item:
                    for output in response_item["output"]:
                        if "classes" in output:
                            for cls in output["classes"]:
                                if "class" in cls and "score" in cls:
                                    class_name = cls["class"].lower()
                                    if "ai" in class_name or "synthetic" in class_name or "deepfake" in class_name:
                                        score = max(score, cls["score"])
        
        return {
            "score": score,
            "raw": data,
            "detected": score > 0.3
        }
    
    def get_score(self, result: Dict[str, Any]) -> float:
        """Get detection score"""
        return result.get("score", 0.5)


class SensityAI(DetectionTester):
    """Sensity AI API integration"""
    
    def __init__(self, api_key: Optional[str] = None, db_session=None):
        super().__init__("sensity")
        self.api_key = api_key
        if not self.api_key:
            # Try environment variable
            self.api_key = os.getenv("SENSITY_API_KEY")
        if not self.api_key and db_session:
            # Try database
            try:
                from models import DetectionToolConfig
                config = db_session.query(DetectionToolConfig).filter(
                    DetectionToolConfig.tool_name == "sensity",
                    DetectionToolConfig.enabled == True
                ).first()
                if config:
                    self.api_key = config.api_key
            except:
                pass
        self.api_url = "https://api.sensity.ai/v1/detect"
    
    def detect(self, image_path: Path) -> Dict[str, Any]:
        """Test image with Sensity AI"""
        if not self.api_key:
            logger.warning("Sensity API key not configured")
            return {"error": "API key not configured", "score": 0.5}
        
        try:
            with open(image_path, "rb") as f:
                files = {"file": f}
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.post(
                    self.api_url,
                    files=files,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_response(data)
                else:
                    logger.error(f"Sensity API error: {response.status_code}")
                    return {"error": f"API error: {response.status_code}", "score": 0.5}
                    
        except Exception as e:
            logger.error(f"Sensity detection error: {e}")
            return {"error": str(e), "score": 0.5}
    
    def _parse_response(self, data: Dict) -> Dict[str, Any]:
        """Parse Sensity API response"""
        score = 0.5
        
        if "result" in data:
            result = data["result"]
            if "confidence" in result:
                score = result["confidence"]
            elif "score" in result:
                score = result["score"]
            elif "fake_probability" in result:
                score = result["fake_probability"]
        
        return {
            "score": score,
            "raw": data,
            "detected": score > 0.3
        }
    
    def get_score(self, result: Dict[str, Any]) -> float:
        """Get detection score"""
        return result.get("score", 0.5)


class AIOrNot(DetectionTester):
    """AI or Not API integration"""
    
    def __init__(self, api_key: Optional[str] = None, db_session=None):
        super().__init__("ai_or_not")
        self.api_key = api_key
        if not self.api_key:
            # Try environment variable
            self.api_key = os.getenv("AI_OR_NOT_API_KEY")
        if not self.api_key and db_session:
            # Try database
            try:
                from models import DetectionToolConfig
                config = db_session.query(DetectionToolConfig).filter(
                    DetectionToolConfig.tool_name == "ai_or_not",
                    DetectionToolConfig.enabled == True
                ).first()
                if config:
                    self.api_key = config.api_key
            except:
                pass
        self.api_url = "https://api.aiornot.com/v1/detect"
    
    def detect(self, image_path: Path) -> Dict[str, Any]:
        """Test image with AI or Not"""
        if not self.api_key:
            logger.warning("AI or Not API key not configured")
            return {"error": "API key not configured", "score": 0.5}
        
        try:
            with open(image_path, "rb") as f:
                files = {"image": f}
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.post(
                    self.api_url,
                    files=files,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_response(data)
                else:
                    logger.error(f"AI or Not API error: {response.status_code}")
                    return {"error": f"API error: {response.status_code}", "score": 0.5}
                    
        except Exception as e:
            logger.error(f"AI or Not detection error: {e}")
            return {"error": str(e), "score": 0.5}
    
    def _parse_response(self, data: Dict) -> Dict[str, Any]:
        """Parse AI or Not API response"""
        score = 0.5
        
        if "ai_probability" in data:
            score = data["ai_probability"]
        elif "probability" in data:
            score = data["probability"]
        elif "score" in data:
            score = data["score"]
        
        return {
            "score": score,
            "raw": data,
            "detected": score > 0.3
        }
    
    def get_score(self, result: Dict[str, Any]) -> float:
        """Get detection score"""
        return result.get("score", 0.5)


class ReverseImageSearch(DetectionTester):
    """Reverse image search detection (checks for duplicates)"""
    
    def __init__(self):
        super().__init__("reverse_search")
        # Note: Actual reverse image search APIs require keys
        # This is a placeholder for implementation
    
    def detect(self, image_path: Path) -> Dict[str, Any]:
        """Check if image appears in reverse search"""
        try:
            # Calculate image hash for duplicate detection
            img = Image.open(image_path)
            img_hash = self._calculate_hash(img)
            phash = self._calculate_perceptual_hash(img)
            
            # For now, return hash-based detection
            # In production, integrate with Google Images API, TinEye, etc.
            return {
                "score": 0.0,  # No duplicates found (placeholder)
                "hash": img_hash,
                "perceptual_hash": phash,
                "detected": False,
                "note": "Reverse search not fully implemented"
            }
        except Exception as e:
            logger.error(f"Reverse search error: {e}")
            return {"error": str(e), "score": 0.0}
    
    def _calculate_hash(self, img: Image.Image) -> str:
        """Calculate MD5 hash of image"""
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        return hashlib.md5(img_bytes.getvalue()).hexdigest()
    
    def _calculate_perceptual_hash(self, img: Image.Image) -> str:
        """Calculate perceptual hash of image (for duplicate detection)"""
        # Resize to 8x8 for hash calculation
        img = img.convert("RGB").resize((8, 8), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
        
        # Calculate average
        avg = sum(sum(p) for p in pixels) / len(pixels) / 3
        
        # Create hash
        bits = []
        for pixel in pixels:
            bits.append("1" if sum(pixel) / 3 > avg else "0")
        
        return hashlib.md5("".join(bits).encode()).hexdigest()
    
    def get_score(self, result: Dict[str, Any]) -> float:
        """Get detection score (0.0 = unique, 1.0 = duplicate found)"""
        return result.get("score", 0.0)


class ImageFingerprintingService:
    """Service to avoid image fingerprinting"""
    
    @staticmethod
    def apply_fingerprint_variations(
        img: Image.Image,
        intensity: float = 0.05
    ) -> Image.Image:
        """Apply subtle variations to avoid fingerprinting"""
        try:
            import random
            from PIL import ImageEnhance, ImageFilter
            
            # Slight color adjustments
            if random.random() < intensity:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.98 + random.random() * 0.04)
            
            # Slight brightness adjustments
            if random.random() < intensity:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(0.98 + random.random() * 0.04)
            
            # Slight contrast adjustments
            if random.random() < intensity:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(0.98 + random.random() * 0.04)
            
            # Very subtle noise (to break exact pixel matching)
            if random.random() < intensity * 0.5:
                img_array = np.array(img)
                noise = np.random.normal(0, 1, img_array.shape).astype(np.uint8)
                img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                img = Image.fromarray(img_array)
            
            return img
            
        except Exception as e:
            logger.warning(f"Fingerprint variation error: {e}")
            return img
    
    @staticmethod
    def crop_variation(img: Image.Image, max_crop: int = 5) -> Image.Image:
        """Apply slight crop variation"""
        try:
            import random
            
            width, height = img.size
            crop_x = random.randint(0, min(max_crop, width // 20))
            crop_y = random.randint(0, min(max_crop, height // 20))
            
            # Crop from all sides
            left = crop_x
            top = crop_y
            right = width - crop_x
            bottom = height - crop_y
            
            if right > left and bottom > top:
                img = img.crop((left, top, right, bottom))
                # Resize back to original size
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            logger.warning(f"Crop variation error: {e}")
            return img


class AntiDetectionService:
    """Main anti-detection service"""
    
    def __init__(self):
        self.detection_tools = [
            HiveModeration(),
            SensityAI(),
            AIOrNot(),
            ReverseImageSearch()
        ]
        self.default_threshold = 0.3  # 30% detection threshold
    
    def test_detection(
        self,
        image_path: Path,
        tools: Optional[List[str]] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Test image with multiple detection tools"""
        threshold = threshold or self.default_threshold
        results = {}
        
        # Filter tools if specified
        tools_to_use = self.detection_tools
        if tools:
            tools_to_use = [t for t in self.detection_tools if t.name in tools]
        
        # Test with each tool
        for tool in tools_to_use:
            try:
                result = tool.detect(image_path)
                score = tool.get_score(result)
                results[tool.name] = {
                    "score": score,
                    "detected": score >= threshold,
                    "raw": result.get("raw"),
                    "error": result.get("error")
                }
            except Exception as e:
                logger.error(f"Error testing with {tool.name}: {e}")
                results[tool.name] = {
                    "score": 0.5,
                    "detected": True,
                    "error": str(e)
                }
        
        # Calculate average score
        scores = [r["score"] for r in results.values() if "error" not in r or not r["error"]]
        avg_score = sum(scores) / len(scores) if scores else 0.5
        
        # Determine if passed
        passed = avg_score < threshold and all(
            not r.get("detected", False) or r.get("error")
            for r in results.values()
        )
        
        return {
            "results": results,
            "average_score": avg_score,
            "threshold": threshold,
            "passed": passed,
            "recommendations": self._get_recommendations(results, avg_score)
        }
    
    def _get_recommendations(
        self,
        results: Dict[str, Dict],
        avg_score: float
    ) -> List[str]:
        """Get recommendations based on test results"""
        recommendations = []
        
        if avg_score >= 0.5:
            recommendations.append("High detection risk - apply aggressive humanization")
            recommendations.append("Consider additional post-processing")
            recommendations.append("Review metadata removal")
        
        elif avg_score >= 0.3:
            recommendations.append("Moderate detection risk - apply humanization")
            recommendations.append("Ensure metadata is fully removed")
        
        # Check individual tool results
        for tool_name, result in results.items():
            if result.get("detected") and not result.get("error"):
                recommendations.append(f"{tool_name} detected AI content - review specific patterns")
        
        if not recommendations:
            recommendations.append("Content appears human-like - safe to publish")
        
        return recommendations
    
    def pre_publication_test(
        self,
        image_path: Path,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Comprehensive pre-publication test"""
        threshold = threshold or self.default_threshold
        
        # Run detection tests
        detection_results = self.test_detection(image_path, threshold=threshold)
        
        # Check metadata
        metadata_check = self.check_metadata(image_path)
        
        # Check image quality
        quality_check = self.check_image_quality(image_path)
        
        # Overall assessment
        passed = (
            detection_results["passed"] and
            metadata_check["clean"] and
            quality_check["acceptable"]
        )
        
        return {
            "passed": passed,
            "detection": detection_results,
            "metadata": metadata_check,
            "quality": quality_check,
            "ready_for_publication": passed,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def check_metadata(self, image_path: Path) -> Dict[str, Any]:
        """Check if metadata is clean"""
        try:
            img = Image.open(image_path)
            
            # Check EXIF
            exif_data = img.getexif() if hasattr(img, "getexif") else {}
            has_exif = len(exif_data) > 0
            
            # Check for piexif data
            try:
                exif_dict = piexif.load(str(image_path))
                has_piexif = any(exif_dict.values())
            except:
                has_piexif = False
            
            clean = not has_exif and not has_piexif
            
            return {
                "clean": clean,
                "has_exif": has_exif,
                "has_piexif": has_piexif,
                "exif_count": len(exif_data) if has_exif else 0
            }
        except Exception as e:
            logger.error(f"Metadata check error: {e}")
            return {
                "clean": False,
                "error": str(e)
            }
    
    def check_image_quality(self, image_path: Path) -> Dict[str, Any]:
        """Check image quality indicators"""
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # Basic quality checks
            resolution_ok = width >= 1024 and height >= 1024
            aspect_ratio_ok = 0.5 <= (width / height) <= 2.0
            
            # Check for obvious artifacts (basic check)
            img_array = np.array(img.convert("RGB"))
            variance = np.var(img_array)
            has_content = variance > 100  # Not a blank image
            
            acceptable = resolution_ok and aspect_ratio_ok and has_content
            
            return {
                "acceptable": acceptable,
                "width": width,
                "height": height,
                "resolution_ok": resolution_ok,
                "aspect_ratio_ok": aspect_ratio_ok,
                "has_content": has_content
            }
        except Exception as e:
            logger.error(f"Quality check error: {e}")
            return {
                "acceptable": False,
                "error": str(e)
            }


class MetadataCleaner:
    """Advanced metadata cleaning service"""
    
    @staticmethod
    def clean_all_metadata(image_path: Path, output_path: Path) -> bool:
        """Remove all metadata from image"""
        try:
            img = Image.open(image_path)
            
            # Get raw pixel data
            data = list(img.getdata())
            
            # Create new image without metadata
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(data)
            
            # Remove EXIF if present
            if hasattr(clean_img, "_getexif"):
                try:
                    clean_img._getexif = None
                except:
                    pass
            
            # Save without metadata
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_path.suffix.lower() in [".jpg", ".jpeg"]:
                clean_img = clean_img.convert("RGB")
                clean_img.save(output_path, "JPEG", quality=95, optimize=True)
            elif output_path.suffix.lower() == ".png":
                clean_img.save(output_path, "PNG", optimize=True)
            elif output_path.suffix.lower() == ".webp":
                clean_img.save(output_path, "WEBP", quality=95, method=6)
            else:
                clean_img.save(output_path)
            
            # Verify removal
            verify_img = Image.open(output_path)
            exif = verify_img.getexif() if hasattr(verify_img, "getexif") else {}
            
            # Try piexif check
            try:
                piexif_dict = piexif.load(str(output_path))
                has_piexif = any(piexif_dict.values())
            except:
                has_piexif = False
            
            clean = len(exif) == 0 and not has_piexif
            
            if not clean:
                logger.warning(f"Metadata may not be fully removed from {output_path}")
            
            return clean
            
        except Exception as e:
            logger.error(f"Metadata cleaning error: {e}")
            return False
    
    @staticmethod
    def add_realistic_metadata(
        image_path: Path,
        output_path: Path,
        camera_make: str = "Canon",
        camera_model: str = "Canon EOS R5",
        software: str = "Adobe Lightroom"
    ) -> bool:
        """Add realistic metadata (use with caution)"""
        try:
            img = Image.open(image_path)
            
            # Create realistic EXIF
            exif_dict = {
                "0th": {
                    piexif.ImageIFD.Make: camera_make.encode("utf-8"),
                    piexif.ImageIFD.Model: camera_model.encode("utf-8"),
                    piexif.ImageIFD.Software: software.encode("utf-8")
                },
                "Exif": {
                    piexif.ExifIFD.ExposureTime: (1, 125),
                    piexif.ExifIFD.FNumber: (28, 10),
                    piexif.ExifIFD.ISOSpeedRatings: 400
                }
            }
            
            exif_bytes = piexif.dump(exif_dict)
            
            # Save with metadata
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, exif=exif_bytes)
            
            return True
            
        except Exception as e:
            logger.error(f"Metadata addition error: {e}")
            return False


class ContentHumanizer:
    """Content humanization service"""
    
    def __init__(self):
        self.fingerprinting_service = ImageFingerprintingService()
    
    def add_natural_imperfections(
        self,
        img: Image.Image,
        intensity: float = 0.1
    ) -> Image.Image:
        """Add natural imperfections to image"""
        try:
            import random
            from PIL import ImageFilter, ImageEnhance
            
            # Slight random variations
            if random.random() < intensity:
                # Subtle blur in some areas
                img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            if random.random() < intensity:
                # Slight brightness variation
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(0.98 + random.random() * 0.04)
            
            if random.random() < intensity:
                # Slight color variation
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.98 + random.random() * 0.04)
            
            # Apply fingerprinting variations
            img = self.fingerprinting_service.apply_fingerprint_variations(img, intensity * 0.5)
            
            return img
            
        except Exception as e:
            logger.warning(f"Humanization error: {e}")
            return img
    
    @staticmethod
    def apply_natural_variations(
        img: Image.Image,
        variations: List[str] = None
    ) -> Image.Image:
        """Apply natural content variations"""
        if variations is None:
            variations = ["color", "brightness", "contrast"]
        
        try:
            from PIL import ImageEnhance
            import random
            
            if "color" in variations:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.95 + random.random() * 0.1)
            
            if "brightness" in variations:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(0.95 + random.random() * 0.1)
            
            if "contrast" in variations:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(0.95 + random.random() * 0.1)
            
            return img
            
        except Exception as e:
            logger.warning(f"Variation error: {e}")
            return img

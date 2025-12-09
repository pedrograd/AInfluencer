"""
Quality Assurance Service
Implements realism checklist and AI detection as per docs/18-AI-TOOLS-NVIDIA-SETUP.md
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from PIL import Image
import json

logger = logging.getLogger(__name__)

class QualityAssuranceService:
    """Service for quality assurance and AI detection"""
    
    REALISM_CHECKLIST = [
        {
            "id": "face_quality",
            "name": "Face Quality",
            "description": "No artifacts, natural skin texture",
            "critical": True
        },
        {
            "id": "hands",
            "name": "Hands",
            "description": "Correct number of fingers, natural pose",
            "critical": True
        },
        {
            "id": "lighting",
            "name": "Lighting",
            "description": "Natural, consistent, no harsh shadows",
            "critical": True
        },
        {
            "id": "background",
            "name": "Background",
            "description": "Coherent, realistic, no glitches",
            "critical": False
        },
        {
            "id": "body_proportions",
            "name": "Body Proportions",
            "description": "Natural, realistic",
            "critical": True
        },
        {
            "id": "clothing",
            "name": "Clothing",
            "description": "Realistic fabric, proper fit",
            "critical": False
        },
        {
            "id": "hair",
            "name": "Hair",
            "description": "Natural texture, realistic flow",
            "critical": False
        },
        {
            "id": "eyes",
            "name": "Eyes",
            "description": "Natural color, proper reflection",
            "critical": True
        },
        {
            "id": "skin",
            "name": "Skin",
            "description": "Realistic texture, no AI patterns",
            "critical": True
        },
        {
            "id": "consistency",
            "name": "Consistency",
            "description": "Same face across all images",
            "critical": True
        }
    ]
    
    def __init__(self):
        self.minimum_score = 8.0  # Minimum score for public content (as per guide)
        
    def run_realism_checklist(self, image_path: Path, manual_scores: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Run the realism checklist on an image
        manual_scores: Optional dict of {check_id: score} for manual review
        """
        result = {
            "image_path": str(image_path),
            "checks": {},
            "overall_score": 0.0,
            "meets_standards": False,
            "critical_issues": [],
            "warnings": []
        }
        
        try:
            # Load image for basic checks
            img = Image.open(image_path)
            
            # Initialize check results
            total_score = 0.0
            critical_total = 0.0
            critical_count = 0
            
            for check in self.REALISM_CHECKLIST:
                check_id = check["id"]
                
                # Use manual score if provided
                if manual_scores and check_id in manual_scores:
                    score = manual_scores[check_id]
                else:
                    # Automated scoring (basic implementation)
                    score = self._automated_check(img, check_id)
                
                result["checks"][check_id] = {
                    "name": check["name"],
                    "description": check["description"],
                    "score": score,
                    "critical": check["critical"],
                    "passed": score >= 7.0
                }
                
                total_score += score
                
                if check["critical"]:
                    critical_total += score
                    critical_count += 1
                    
                    if score < 7.0:
                        result["critical_issues"].append({
                            "check": check["name"],
                            "score": score,
                            "issue": check["description"]
                        })
                elif score < 7.0:
                    result["warnings"].append({
                        "check": check["name"],
                        "score": score,
                        "issue": check["description"]
                    })
            
            # Calculate overall score (weighted average)
            if len(self.REALISM_CHECKLIST) > 0:
                result["overall_score"] = round(total_score / len(self.REALISM_CHECKLIST), 1)
            
            # Calculate critical score
            if critical_count > 0:
                critical_score = critical_total / critical_count
                result["critical_score"] = round(critical_score, 1)
            else:
                result["critical_score"] = result["overall_score"]
            
            # Check if meets standards (8+ for public content as per guide)
            result["meets_standards"] = result["overall_score"] >= self.minimum_score
            
        except Exception as e:
            logger.error(f"Realism checklist error: {e}")
            result["error"] = str(e)
        
        return result
    
    def _automated_check(self, img: Image.Image, check_id: str) -> float:
        """
        Automated check scoring (basic implementation)
        Returns score from 0-10
        In production, this would use ML models or advanced image analysis
        """
        # Basic heuristics (placeholder for actual ML-based checks)
        
        # Basic image quality checks
        width, height = img.size
        
        if check_id == "face_quality":
            # Placeholder: In production, use face detection and quality assessment
            return 8.5
        
        elif check_id == "hands":
            # Placeholder: In production, use hand detection and counting
            return 8.0
        
        elif check_id == "lighting":
            # Basic lighting analysis
            import numpy as np
            img_array = np.array(img.convert("L"))  # Grayscale
            mean_brightness = img_array.mean()
            std_brightness = img_array.std()
            
            # Good lighting: moderate brightness, not too high contrast
            if 80 < mean_brightness < 180 and std_brightness < 60:
                return 9.0
            elif 60 < mean_brightness < 200:
                return 7.5
            else:
                return 6.0
        
        elif check_id == "background":
            # Placeholder
            return 8.0
        
        elif check_id == "body_proportions":
            # Placeholder: Would use pose estimation
            return 8.5
        
        elif check_id == "clothing":
            # Placeholder
            return 8.0
        
        elif check_id == "hair":
            # Placeholder
            return 8.0
        
        elif check_id == "eyes":
            # Placeholder: Would use eye detection
            return 8.5
        
        elif check_id == "skin":
            # Placeholder: Would analyze skin texture
            return 8.0
        
        elif check_id == "consistency":
            # This requires comparison with other images
            return 8.5  # Default
        
        return 8.0  # Default score
    
    def test_ai_detection(self, image_path: Path) -> Dict[str, Any]:
        """
        Test image against AI detection tools
        Note: Actual implementation would call external APIs or use local models
        """
        result = {
            "image_path": str(image_path),
            "tests": {
                "hive_moderation": {
                    "available": False,
                    "score": None,
                    "detected_as_ai": None,
                    "url": "https://thehive.ai/"
                },
                "sensity_ai": {
                    "available": False,
                    "score": None,
                    "detected_as_ai": None,
                    "url": "https://sensity.ai/"
                },
                "reverse_image_search": {
                    "available": False,
                    "matches": None,
                    "unique": None,
                    "urls": [
                        "https://www.google.com/imghp",
                        "https://tineye.com/"
                    ]
                }
            },
            "overall_risk": "unknown",
            "recommendation": "Manual review recommended"
        }
        
        # Placeholder implementation
        # In production, this would:
        # 1. Call Hive Moderation API
        # 2. Call Sensity AI API
        # 3. Perform reverse image search
        
        result["recommendation"] = "Use external tools for AI detection testing:\n" \
                                  "- Hive Moderation: https://thehive.ai/\n" \
                                  "- Sensity AI: https://sensity.ai/\n" \
                                  "- Google Reverse Image Search\n" \
                                  "- TinEye"
        
        return result
    
    def quality_score_image(self, image_path: Path, manual_review: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete quality scoring for an image
        Combines realism checklist and AI detection
        """
        result = {
            "image_path": str(image_path),
            "realism_checklist": None,
            "ai_detection": None,
            "overall_score": 0.0,
            "quality_tier": "unknown",
            "approved_for_public": False,
            "recommendations": []
        }
        
        try:
            # Run realism checklist
            manual_scores = manual_review.get("checklist_scores") if manual_review else None
            checklist_result = self.run_realism_checklist(image_path, manual_scores)
            result["realism_checklist"] = checklist_result
            
            # Run AI detection test
            detection_result = self.test_ai_detection(image_path)
            result["ai_detection"] = detection_result
            
            # Calculate overall score
            result["overall_score"] = checklist_result.get("overall_score", 0.0)
            
            # Determine quality tier
            score = result["overall_score"]
            if score >= 9.0:
                result["quality_tier"] = "perfect"
                result["approved_for_public"] = True
            elif score >= 8.0:
                result["quality_tier"] = "good"
                result["approved_for_public"] = True
            elif score >= 7.0:
                result["quality_tier"] = "acceptable"
                result["recommendations"].append("Needs post-processing before public use")
            elif score >= 5.0:
                result["quality_tier"] = "needs_work"
                result["recommendations"].append("Requires significant post-processing or regeneration")
            else:
                result["quality_tier"] = "reject"
                result["recommendations"].append("Should be regenerated")
            
            # Add specific recommendations based on checklist
            for issue in checklist_result.get("critical_issues", []):
                result["recommendations"].append(f"Critical: Fix {issue['check']} (score: {issue['score']})")
            
            for warning in checklist_result.get("warnings", []):
                result["recommendations"].append(f"Warning: Improve {warning['check']} (score: {warning['score']})")
        
        except Exception as e:
            logger.error(f"Quality scoring error: {e}")
            result["error"] = str(e)
        
        return result
    
    def batch_quality_check(self, image_paths: List[Path], manual_reviews: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Run quality checks on multiple images"""
        result = {
            "total": len(image_paths),
            "passed": 0,
            "failed": 0,
            "scores": [],
            "approved_images": [],
            "rejected_images": []
        }
        
        manual_reviews = manual_reviews or {}
        
        for image_path in image_paths:
            image_id = image_path.stem
            manual_review = manual_reviews.get(image_id)
            
            quality_result = self.quality_score_image(image_path, manual_review)
            
            result["scores"].append({
                "image": str(image_path),
                "score": quality_result["overall_score"],
                "tier": quality_result["quality_tier"],
                "approved": quality_result["approved_for_public"]
            })
            
            if quality_result["approved_for_public"]:
                result["passed"] += 1
                result["approved_images"].append(str(image_path))
            else:
                result["failed"] += 1
                result["rejected_images"].append({
                    "image": str(image_path),
                    "score": quality_result["overall_score"],
                    "issues": quality_result["recommendations"]
                })
        
        return result
    
    def get_checklist(self) -> List[Dict[str, Any]]:
        """Get the realism checklist"""
        return self.REALISM_CHECKLIST.copy()
    
    def automated_quality_scoring(self, image_path: str) -> Dict[str, Any]:
        """
        Automated quality scoring (0-10 scale)
        
        Args:
            image_path: Path to image
        
        Returns:
            Quality score and breakdown
        """
        try:
            import numpy as np
            from scipy import ndimage
            
            image = Image.open(image_path)
            image_array = np.array(image)
            
            scores = {
                "overall": 0.0,
                "sharpness": self._score_sharpness(image_array),
                "contrast": self._score_contrast(image_array),
                "color": self._score_color(image_array),
                "artifacts": 10.0 - self._detect_artifacts(image_array),
                "face_quality": 0.0  # Will be set if face detected
            }
            
            # Calculate overall score
            scores["overall"] = (
                scores["sharpness"] * 0.3 +
                scores["contrast"] * 0.2 +
                scores["color"] * 0.2 +
                scores["artifacts"] * 0.3
            )
            
            return scores
        except Exception as e:
            logger.error(f"Quality scoring error: {e}")
            return {"overall": 0.0, "error": str(e)}
    
    def _score_sharpness(self, image_array) -> float:
        """Score image sharpness"""
        try:
            import numpy as np
            from scipy import ndimage
            
            gray = np.mean(image_array, axis=2) if len(image_array.shape) == 3 else image_array
            laplacian = ndimage.laplacian(gray)
            sharpness = np.var(laplacian)
            # Normalize to 0-10 scale
            return min(10.0, sharpness / 100.0)
        except:
            return 7.0  # Default score
    
    def _score_contrast(self, image_array) -> float:
        """Score image contrast"""
        try:
            import numpy as np
            
            gray = np.mean(image_array, axis=2) if len(image_array.shape) == 3 else image_array
            contrast = np.std(gray)
            # Normalize to 0-10 scale
            return min(10.0, contrast / 20.0)
        except:
            return 7.0
    
    def _score_color(self, image_array) -> float:
        """Score color quality"""
        try:
            import numpy as np
            
            if len(image_array.shape) != 3:
                return 7.0
            
            # Check color saturation
            hsv = Image.fromarray(image_array).convert('HSV')
            hsv_array = np.array(hsv)
            saturation = np.mean(hsv_array[:, :, 1])
            
            # Normalize to 0-10 scale
            return min(10.0, saturation / 25.0)
        except:
            return 7.0
    
    def _detect_artifacts(self, image_array) -> float:
        """Detect artifacts in image (returns artifact score, lower is better)"""
        try:
            import numpy as np
            
            gray = np.mean(image_array, axis=2) if len(image_array.shape) == 3 else image_array
            
            # Check for repeating patterns (common AI artifact)
            artifact_score = 0.0
            
            # Check for noise
            noise = np.std(gray)
            if noise > 50:
                artifact_score += 2.0
            
            return min(10.0, artifact_score)
        except:
            return 0.0
    
    def artifact_detection(self, image_path: str) -> Dict[str, Any]:
        """
        Automatic artifact detection and flagging
        
        Args:
            image_path: Path to image
        
        Returns:
            Artifact detection results
        """
        try:
            import numpy as np
            
            image = Image.open(image_path)
            image_array = np.array(image)
            
            artifacts = {
                "detected": False,
                "types": [],
                "severity": 0.0,
                "locations": []
            }
            
            artifact_score = self._detect_artifacts(image_array)
            
            if artifact_score > 2.0:
                artifacts["detected"] = True
                artifacts["severity"] = artifact_score
                artifacts["types"].append("noise")
            
            return artifacts
        except Exception as e:
            logger.error(f"Artifact detection error: {e}")
            return {"detected": False, "error": str(e)}
    
    def realism_scoring(self, image_path: str) -> Dict[str, Any]:
        """
        AI detection bypass scoring (realism assessment)
        
        Args:
            image_path: Path to image
        
        Returns:
            Realism score and metrics
        """
        try:
            # Combine multiple quality metrics
            quality_scores = self.automated_quality_scoring(image_path)
            artifacts = self.artifact_detection(image_path)
            
            realism_score = quality_scores["overall"]
            
            # Penalize for artifacts
            if artifacts["detected"]:
                realism_score -= artifacts["severity"] * 0.5
            
            # Normalize to 0-10
            realism_score = max(0.0, min(10.0, realism_score))
            
            return {
                "realism_score": realism_score,
                "quality_breakdown": quality_scores,
                "artifacts": artifacts,
                "ai_detection_risk": "low" if realism_score > 8.0 else "medium" if realism_score > 6.0 else "high"
            }
        except Exception as e:
            logger.error(f"Realism scoring error: {e}")
            return {"realism_score": 0.0, "error": str(e)}
    
    def batch_quality_filtering(self, image_paths: List[str], min_score: float = 7.0) -> Dict[str, Any]:
        """
        Batch quality filtering - auto-reject low quality
        
        Args:
            image_paths: List of image paths
            min_score: Minimum quality score to accept
        
        Returns:
            Filtering results
        """
        results = {
            "total": len(image_paths),
            "accepted": [],
            "rejected": [],
            "scores": {}
        }
        
        for image_path in image_paths:
            scores = self.automated_quality_scoring(image_path)
            results["scores"][image_path] = scores["overall"]
            
            if scores["overall"] >= min_score:
                results["accepted"].append(image_path)
            else:
                results["rejected"].append(image_path)
        
        return results
    
    def compare_quality(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Compare quality of multiple images side-by-side
        
        Args:
            image_paths: List of image paths to compare
        
        Returns:
            Comparison results with scores and rankings
        """
        try:
            scores = []
            for image_path in image_paths:
                score_data = self.automated_quality_scoring(image_path)
                scores.append({
                    "image_path": image_path,
                    "overall_score": score_data.get("overall_score", 0),
                    "sharpness": score_data.get("sharpness", 0),
                    "contrast": score_data.get("contrast", 0),
                    "color": score_data.get("color", 0),
                    "artifacts": score_data.get("artifacts", 0)
                })
            
            # Sort by overall score
            scores.sort(key=lambda x: x["overall_score"], reverse=True)
            
            return {
                "comparison": scores,
                "best": scores[0] if scores else None,
                "worst": scores[-1] if scores else None,
                "average_score": sum(s["overall_score"] for s in scores) / len(scores) if scores else 0
            }
        except Exception as e:
            logger.error(f"Quality comparison error: {e}")
            return {
                "error": str(e),
                "comparison": []
            }
    
    def get_quality_improvement_suggestions(self, image_path: str) -> Dict[str, Any]:
        """
        Get AI-powered suggestions for improving image quality
        
        Args:
            image_path: Path to image
        
        Returns:
            Suggestions for improvement
        """
        try:
            scores = self.automated_quality_scoring(image_path)
            artifacts = self.artifact_detection(image_path)
            
            suggestions = []
            
            # Check sharpness
            if scores.get("sharpness", 0) < 7.0:
                suggestions.append({
                    "category": "sharpness",
                    "issue": "Image is not sharp enough",
                    "suggestion": "Apply sharpening filter or upscale with sharpening model",
                    "priority": "high"
                })
            
            # Check contrast
            if scores.get("contrast", 0) < 7.0:
                suggestions.append({
                    "category": "contrast",
                    "issue": "Low contrast",
                    "suggestion": "Increase contrast using color grading",
                    "priority": "medium"
                })
            
            # Check color
            if scores.get("color", 0) < 7.0:
                suggestions.append({
                    "category": "color",
                    "issue": "Color quality could be improved",
                    "suggestion": "Apply color grading preset or adjust saturation",
                    "priority": "medium"
                })
            
            # Check artifacts
            if artifacts.get("has_artifacts", False):
                artifact_types = artifacts.get("artifact_types", [])
                for artifact_type in artifact_types:
                    suggestions.append({
                        "category": "artifacts",
                        "issue": f"{artifact_type} detected",
                        "suggestion": f"Apply artifact removal for {artifact_type}",
                        "priority": "high"
                    })
            
            # Check overall score
            overall = scores.get("overall_score", 0)
            if overall < 7.0:
                suggestions.append({
                    "category": "overall",
                    "issue": "Overall quality below threshold",
                    "suggestion": "Consider applying multi-stage upscaling and face restoration",
                    "priority": "high"
                })
            
            return {
                "image_path": image_path,
                "current_score": overall,
                "suggestions": suggestions,
                "estimated_improvement": min(10.0, overall + len(suggestions) * 0.5) if suggestions else overall
            }
        except Exception as e:
            logger.error(f"Quality improvement suggestions error: {e}")
            return {
                "image_path": image_path,
                "error": str(e),
                "suggestions": []
            }

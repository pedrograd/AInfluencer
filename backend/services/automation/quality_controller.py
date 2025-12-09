"""
Quality Controller
Automated quality scoring, artifact detection, and filtering
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List

from services.quality_service import QualityService

logger = logging.getLogger(__name__)

class QualityController:
    """Service for automated quality control"""
    
    def __init__(self):
        self.quality_service = QualityService()
    
    def check_quality(
        self,
        content_path: Path,
        content_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Check content quality with detailed scoring
        
        Args:
            content_path: Path to content file
            content_type: 'image' or 'video'
        
        Returns:
            Quality check results with scores and recommendations
        """
        scores = self.quality_service.score_content(content_path, content_type)
        
        # Get recommendations
        recommendations = self.get_recommendations(scores)
        
        # Determine if passed
        overall_score = scores.get("overall", 0.0)
        artifact_severity = scores.get("artifacts", {}).get("severity", 1.0)
        passed = overall_score >= 8.0 and artifact_severity < 0.2
        
        return {
            "scores": scores,
            "passed": passed,
            "recommendations": recommendations,
            "auto_approved": overall_score >= 9.0 and artifact_severity < 0.1
        }
    
    def check_face_quality(self, content_path: Path) -> Dict[str, Any]:
        """Check face quality specifically"""
        scores = self.quality_service.score_content(content_path, "image")
        face_scores = scores.get("face", {})
        
        return {
            "detected": face_scores.get("detected", False),
            "overall": face_scores.get("overall", 0.0),
            "sharpness": face_scores.get("sharpness", 0.0),
            "symmetry": face_scores.get("symmetry", 0.0),
            "lighting": face_scores.get("lighting", 0.0),
            "expression": face_scores.get("expression", 0.0)
        }
    
    def check_artifacts(self, content_path: Path) -> Dict[str, Any]:
        """Check for artifacts"""
        scores = self.quality_service.score_content(content_path, "image")
        artifact_info = scores.get("artifacts", {})
        
        return {
            "detected": artifact_info.get("detected", False),
            "artifacts": artifact_info.get("artifacts", []),
            "severity": artifact_info.get("severity", 0.0),
            "count": artifact_info.get("count", 0)
        }
    
    def get_recommendations(self, scores: Dict[str, Any]) -> List[str]:
        """Get recommendations based on scores"""
        recommendations = []
        
        overall = scores.get("overall", 0.0)
        face = scores.get("face", {}).get("overall", 0.0)
        technical = scores.get("technical", {}).get("overall", 0.0)
        realism = scores.get("realism", 0.0)
        artifacts = scores.get("artifacts", {}).get("severity", 0.0)
        
        if overall < 7.0:
            recommendations.append("Overall quality is low. Consider regenerating.")
        
        if face < 7.0:
            recommendations.append("Face quality is low. Check face consistency settings.")
        
        if technical < 7.0:
            recommendations.append("Technical quality is low. Check resolution and sharpness.")
        
        if realism < 7.0:
            recommendations.append("Realism score is low. Check lighting and colors.")
        
        if artifacts > 0.2:
            recommendations.append("Artifacts detected. Consider post-processing.")
        
        if not recommendations:
            recommendations.append("Quality is acceptable.")
        
        return recommendations
    
    def filter_content(
        self,
        content_list: List[Dict[str, Any]],
        min_score: float = 8.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filter content based on quality scores
        
        Args:
            content_list: List of content items with paths
            min_score: Minimum quality score threshold
        
        Returns:
            Dictionary with 'passed' and 'rejected' lists
        """
        passed = []
        rejected = []
        
        for content in content_list:
            content_path = Path(content.get("path", content.get("file_path")))
            if not content_path.exists():
                rejected.append({
                    **content,
                    "reason": "File not found"
                })
                continue
            
            result = self.check_quality(content_path, content.get("type", "image"))
            
            if result["passed"] and result["scores"]["overall"] >= min_score:
                passed.append({
                    **content,
                    "quality_scores": result["scores"],
                    "quality_passed": True
                })
            else:
                rejected.append({
                    **content,
                    "quality_scores": result["scores"],
                    "reason": f"Quality score {result['scores']['overall']} below threshold {min_score}",
                    "recommendations": result["recommendations"]
                })
        
        return {
            "passed": passed,
            "rejected": rejected,
            "total": len(content_list),
            "passed_count": len(passed),
            "rejected_count": len(rejected)
        }

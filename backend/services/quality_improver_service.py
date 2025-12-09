"""
Quality Improver Service
Continuous improvement analysis as per docs/28-QUALITY-ASSURANCE-SYSTEM.md
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import QualityScore, MediaItem, GenerationJob

logger = logging.getLogger(__name__)


class QualityImprover:
    """Quality improvement analysis service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_rejections(self, period_days: int = 7) -> Dict[str, Any]:
        """Analyze rejection patterns"""
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        
        # Get rejected content (score < 7.0)
        rejected_scores = self.db.query(QualityScore).join(MediaItem).filter(
            and_(
                MediaItem.created_at >= cutoff,
                QualityScore.overall_score < 0.7  # 7.0/10 scale
            )
        ).all()
        
        # Analyze patterns
        quality_issues = 0
        detection_issues = 0
        technical_issues = 0
        
        for score in rejected_scores:
            # Quality issues (low overall score)
            if score.overall_score < 0.7:
                quality_issues += 1
            
            # Technical issues (low face quality or high artifacts)
            if score.face_quality_score and score.face_quality_score < 0.7:
                technical_issues += 1
            if score.artifact_score and score.artifact_score > 0.3:
                technical_issues += 1
        
        patterns = {
            "quality_issues": quality_issues,
            "detection_issues": detection_issues,
            "technical_issues": technical_issues,
            "total_rejections": len(rejected_scores),
            "period_days": period_days
        }
        
        # Generate recommendations
        recommendations = self.generate_recommendations(patterns)
        
        return {
            "patterns": patterns,
            "recommendations": recommendations,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def generate_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        total = patterns.get("total_rejections", 0)
        if total == 0:
            return ["No rejections to analyze"]
        
        # Quality issues
        quality_issues = patterns.get("quality_issues", 0)
        if quality_issues > total * 0.5:
            recommendations.append("High rate of quality issues - review generation parameters")
            recommendations.append("Consider improving prompt engineering")
            recommendations.append("Review post-processing pipeline")
        
        # Technical issues
        technical_issues = patterns.get("technical_issues", 0)
        if technical_issues > total * 0.3:
            recommendations.append("High rate of technical issues - improve face consistency")
            recommendations.append("Review artifact detection and removal")
            recommendations.append("Consider upscaling and face restoration")
        
        # Detection issues
        detection_issues = patterns.get("detection_issues", 0)
        if detection_issues > total * 0.2:
            recommendations.append("High rate of detection issues - enhance anti-detection")
            recommendations.append("Review metadata removal process")
            recommendations.append("Consider additional humanization techniques")
        
        if not recommendations:
            recommendations.append("Rejection patterns are within acceptable range")
        
        return recommendations
    
    def get_improvement_suggestions(self, media_id: str) -> List[str]:
        """Get improvement suggestions for specific media"""
        # Get quality score
        from models import QualityScore
        quality_score = self.db.query(QualityScore).filter(
            QualityScore.media_id == media_id
        ).first()
        
        if not quality_score:
            return ["No quality score available"]
        
        suggestions = []
        
        # Check face quality
        if quality_score.face_quality_score and quality_score.face_quality_score < 0.8:
            suggestions.append("Face quality below target - consider face restoration")
            suggestions.append("Review face consistency settings")
        
        # Check artifacts
        if quality_score.artifact_score and quality_score.artifact_score > 0.2:
            suggestions.append("Artifacts detected - apply artifact removal")
            suggestions.append("Consider upscaling with artifact reduction")
        
        # Check realism
        if quality_score.realism_score and quality_score.realism_score < 0.8:
            suggestions.append("Realism score below target - enhance post-processing")
            suggestions.append("Review color grading and lighting")
        
        # Check overall
        if quality_score.overall_score < 0.8:
            suggestions.append("Overall quality below target - comprehensive review needed")
        
        if not suggestions:
            suggestions.append("Quality meets standards - no improvements needed")
        
        return suggestions

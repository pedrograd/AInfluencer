"""
Quality Metrics Service
Tracks KPIs and quality statistics as per docs/28-QUALITY-ASSURANCE-SYSTEM.md
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from models import MediaItem, QualityScore, DetectionTest, GenerationJob

logger = logging.getLogger(__name__)


class QualityMetrics:
    """Quality metrics and KPI tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_generation_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get generation metrics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Content generated per day
        total_generations = self.db.query(GenerationJob).filter(
            GenerationJob.created_at >= cutoff
        ).count()
        
        # Quality score average
        quality_scores = self.db.query(QualityScore).join(MediaItem).filter(
            MediaItem.created_at >= cutoff
        ).all()
        
        avg_quality = 0.0
        if quality_scores:
            avg_quality = sum(qs.overall_score for qs in quality_scores) / len(quality_scores)
        
        # Approval rate
        approved = sum(1 for qs in quality_scores if qs.overall_score >= 8.0)
        approval_rate = (approved / len(quality_scores) * 100) if quality_scores else 0.0
        
        # Rejection rate
        rejected = sum(1 for qs in quality_scores if qs.overall_score < 7.0)
        rejection_rate = (rejected / len(quality_scores) * 100) if quality_scores else 0.0
        
        return {
            "content_generated_per_day": total_generations / days if days > 0 else 0,
            "quality_score_average": avg_quality * 10,  # Convert to 0-10 scale
            "approval_rate": approval_rate,
            "rejection_rate": rejection_rate,
            "total_generations": total_generations,
            "period_days": days
        }
    
    def get_quality_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get quality metrics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        quality_scores = self.db.query(QualityScore).join(MediaItem).filter(
            MediaItem.created_at >= cutoff
        ).all()
        
        if not quality_scores:
            return {
                "average_quality_score": 0.0,
                "face_quality_average": 0.0,
                "technical_quality_average": 0.0,
                "realism_score_average": 0.0,
                "total_scored": 0
            }
        
        # Calculate averages
        avg_overall = sum(qs.overall_score for qs in quality_scores) / len(quality_scores)
        avg_face = sum(qs.face_quality_score for qs in quality_scores if qs.face_quality_score) / len([qs for qs in quality_scores if qs.face_quality_score])
        avg_technical = 0.0  # Would need technical score in database
        avg_realism = sum(qs.realism_score for qs in quality_scores if qs.realism_score) / len([qs for qs in quality_scores if qs.realism_score])
        
        return {
            "average_quality_score": avg_overall * 10,  # Convert to 0-10
            "face_quality_average": avg_face * 10 if avg_face else 0.0,
            "technical_quality_average": avg_technical * 10,
            "realism_score_average": avg_realism * 10 if avg_realism else 0.0,
            "total_scored": len(quality_scores)
        }
    
    def get_detection_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get detection metrics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        tests = self.db.query(DetectionTest).filter(
            DetectionTest.created_at >= cutoff
        ).all()
        
        if not tests:
            return {
                "average_detection_score": 0.0,
                "detection_pass_rate": 0.0,
                "tool_specific_scores": {},
                "total_tests": 0
            }
        
        # Average detection score
        avg_score = sum(t.average_score for t in tests) / len(tests)
        
        # Pass rate
        passed = sum(1 for t in tests if t.passed)
        pass_rate = (passed / len(tests) * 100) if tests else 0.0
        
        # Tool-specific scores (from results JSON)
        tool_scores = {}
        for test in tests:
            if test.results:
                for tool_name, result in test.results.items():
                    if isinstance(result, dict) and "score" in result:
                        if tool_name not in tool_scores:
                            tool_scores[tool_name] = []
                        tool_scores[tool_name].append(result["score"])
        
        # Calculate averages per tool
        tool_averages = {}
        for tool_name, scores in tool_scores.items():
            tool_averages[tool_name] = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "average_detection_score": avg_score,
            "detection_pass_rate": pass_rate,
            "tool_specific_scores": tool_averages,
            "total_tests": len(tests),
            "passed_tests": passed,
            "failed_tests": len(tests) - passed
        }
    
    def get_efficiency_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get efficiency metrics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        jobs = self.db.query(GenerationJob).filter(
            GenerationJob.created_at >= cutoff
        ).all()
        
        if not jobs:
            return {
                "time_to_generate": 0.0,
                "time_to_approve": 0.0,
                "automation_rate": 0.0,
                "manual_review_rate": 0.0
            }
        
        # Time to generate
        generation_times = []
        for job in jobs:
            if job.started_at and job.completed_at:
                delta = (job.completed_at - job.started_at).total_seconds()
                generation_times.append(delta)
        
        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0.0
        
        # Time to approve (would need approval tracking)
        # For now, use time from completion to now as placeholder
        approval_times = []
        for job in jobs:
            if job.completed_at and job.status == "completed":
                # Placeholder - would track actual approval time
                delta = (datetime.utcnow() - job.completed_at).total_seconds()
                approval_times.append(delta)
        
        avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0.0
        
        # Automation rate (auto-approved vs manual review)
        # Would need to track this in database
        auto_approved = 0  # Placeholder
        manual_reviewed = 0  # Placeholder
        
        total = len(jobs)
        automation_rate = (auto_approved / total * 100) if total > 0 else 0.0
        manual_review_rate = (manual_reviewed / total * 100) if total > 0 else 0.0
        
        return {
            "time_to_generate": avg_generation_time,
            "time_to_approve": avg_approval_time,
            "automation_rate": automation_rate,
            "manual_review_rate": manual_review_rate,
            "total_jobs": total
        }
    
    def get_all_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            "generation": self.get_generation_metrics(days),
            "quality": self.get_quality_metrics(days),
            "detection": self.get_detection_metrics(days),
            "efficiency": self.get_efficiency_metrics(days),
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat()
        }

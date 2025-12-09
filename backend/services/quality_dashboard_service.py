"""
Quality Dashboard Service
Dashboard for quality metrics and trends as per docs/28-QUALITY-ASSURANCE-SYSTEM.md
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from services.quality_metrics_service import QualityMetrics

logger = logging.getLogger(__name__)


class QualityDashboard:
    """Quality dashboard service"""
    
    def __init__(self, db: Session):
        self.metrics = QualityMetrics(db)
        self.db = db
    
    def get_summary(self) -> Dict[str, Any]:
        """Get dashboard summary"""
        all_metrics = self.metrics.get_all_metrics(days=7)
        
        return {
            "quality_avg": all_metrics["quality"]["average_quality_score"],
            "approval_rate": all_metrics["generation"]["approval_rate"],
            "detection_avg": all_metrics["detection"]["average_detection_score"],
            "generation_count": all_metrics["generation"]["total_generations"],
            "pass_rate": all_metrics["detection"]["detection_pass_rate"],
            "automation_rate": all_metrics["efficiency"]["automation_rate"]
        }
    
    def get_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get quality trends over time"""
        # Get metrics for each day
        daily_metrics = []
        
        for i in range(days):
            day_start = datetime.utcnow() - timedelta(days=days - i)
            day_end = day_start + timedelta(days=1)
            
            # Get metrics for this day
            day_metrics = self.metrics.get_all_metrics(days=1)
            daily_metrics.append({
                "date": day_start.date().isoformat(),
                "quality_avg": day_metrics["quality"]["average_quality_score"],
                "approval_rate": day_metrics["generation"]["approval_rate"],
                "detection_avg": day_metrics["detection"]["average_detection_score"],
                "generation_count": day_metrics["generation"]["total_generations"]
            })
        
        return {
            "daily_metrics": daily_metrics,
            "period_days": days,
            "trend": self._calculate_trend(daily_metrics)
        }
    
    def _calculate_trend(self, daily_metrics: List[Dict]) -> Dict[str, str]:
        """Calculate trend direction"""
        if len(daily_metrics) < 2:
            return {
                "quality": "stable",
                "approval": "stable",
                "detection": "stable"
            }
        
        # Calculate trends
        quality_scores = [m["quality_avg"] for m in daily_metrics]
        approval_rates = [m["approval_rate"] for m in daily_metrics]
        detection_scores = [m["detection_avg"] for m in daily_metrics]
        
        quality_trend = "improving" if quality_scores[-1] > quality_scores[0] else "declining" if quality_scores[-1] < quality_scores[0] else "stable"
        approval_trend = "improving" if approval_rates[-1] > approval_rates[0] else "declining" if approval_rates[-1] < approval_rates[0] else "stable"
        detection_trend = "improving" if detection_scores[-1] < detection_scores[0] else "declining" if detection_scores[-1] > detection_scores[0] else "stable"
        
        return {
            "quality": quality_trend,
            "approval": approval_trend,
            "detection": detection_trend
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get quality alerts"""
        alerts = []
        summary = self.get_summary()
        
        # Quality drops
        if summary["quality_avg"] < 8.0:
            alerts.append({
                "type": "warning",
                "category": "quality",
                "message": f"Average quality score is below target: {summary['quality_avg']:.1f}/10",
                "severity": "high" if summary["quality_avg"] < 7.0 else "medium"
            })
        
        # High rejection rates
        if summary["approval_rate"] < 80:
            alerts.append({
                "type": "warning",
                "category": "approval",
                "message": f"Approval rate is below target: {summary['approval_rate']:.1f}%",
                "severity": "high" if summary["approval_rate"] < 70 else "medium"
            })
        
        # Detection issues
        if summary["detection_avg"] > 0.3:
            alerts.append({
                "type": "warning",
                "category": "detection",
                "message": f"Average detection score is above threshold: {summary['detection_avg']:.2f}",
                "severity": "high" if summary["detection_avg"] > 0.5 else "medium"
            })
        
        # Low pass rate
        if summary["pass_rate"] < 95:
            alerts.append({
                "type": "warning",
                "category": "detection",
                "message": f"Detection pass rate is below target: {summary['pass_rate']:.1f}%",
                "severity": "high" if summary["pass_rate"] < 90 else "medium"
            })
        
        return alerts

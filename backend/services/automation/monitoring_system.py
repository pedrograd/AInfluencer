"""
Monitoring System
Tracks metrics, generates alerts, and monitors system health
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import GenerationJob, BatchJob, MediaItem

logger = logging.getLogger(__name__)

class MonitoringSystem:
    """Service for monitoring and alerting"""
    
    def __init__(self, db: Session):
        self.db = db
        self.metrics = {
            "generated": 0,
            "posted": 0,
            "failed": 0,
            "quality_avg": 0.0,
            "processing_time_avg": 0.0,
            "last_updated": datetime.utcnow()
        }
        self.alert_thresholds = {
            "failure_rate": 0.2,  # 20% failure rate triggers alert
            "low_quality": 7.0,    # Average quality below 7.0 triggers alert
            "no_posts": 10,        # Generated 10+ items but posted 0 triggers alert
        }
    
    def track_generation(self, success: bool = True, quality_score: Optional[float] = None):
        """Track a generation event"""
        if success:
            self.metrics["generated"] += 1
            if quality_score:
                # Update average quality
                current_avg = self.metrics["quality_avg"]
                total = self.metrics["generated"]
                self.metrics["quality_avg"] = (
                    (current_avg * (total - 1) + quality_score) / total
                )
        else:
            self.metrics["failed"] += 1
        
        self.metrics["last_updated"] = datetime.utcnow()
    
    def track_posting(self, success: bool = True):
        """Track a posting event"""
        if success:
            self.metrics["posted"] += 1
        else:
            self.metrics["failed"] += 1
        
        self.metrics["last_updated"] = datetime.utcnow()
    
    def track_processing_time(self, time_seconds: float):
        """Track processing time"""
        current_avg = self.metrics["processing_time_avg"]
        total = self.metrics["generated"]
        if total > 0:
            self.metrics["processing_time_avg"] = (
                (current_avg * (total - 1) + time_seconds) / total
            )
        else:
            self.metrics["processing_time_avg"] = time_seconds
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        # Calculate additional metrics
        total_operations = self.metrics["generated"] + self.metrics["failed"]
        failure_rate = (
            self.metrics["failed"] / total_operations
            if total_operations > 0
            else 0.0
        )
        
        return {
            **self.metrics,
            "failure_rate": failure_rate,
            "success_rate": 1.0 - failure_rate if total_operations > 0 else 0.0
        }
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for alert conditions
        
        Returns:
            List of alerts
        """
        alerts = []
        metrics = self.get_metrics()
        
        # High failure rate
        if metrics["failure_rate"] > self.alert_thresholds["failure_rate"]:
            alerts.append({
                "type": "high_failure_rate",
                "severity": "warning",
                "message": f"High failure rate detected: {metrics['failure_rate']:.1%}",
                "threshold": self.alert_thresholds["failure_rate"],
                "current": metrics["failure_rate"]
            })
        
        # Low quality
        if metrics["quality_avg"] < self.alert_thresholds["low_quality"]:
            alerts.append({
                "type": "low_quality",
                "severity": "warning",
                "message": f"Low quality scores detected: {metrics['quality_avg']:.1f}",
                "threshold": self.alert_thresholds["low_quality"],
                "current": metrics["quality_avg"]
            })
        
        # No posts
        if (metrics["generated"] >= self.alert_thresholds["no_posts"] and
            metrics["posted"] == 0):
            alerts.append({
                "type": "no_posts",
                "severity": "info",
                "message": f"Content generated ({metrics['generated']}) but not posted",
                "generated": metrics["generated"],
                "posted": metrics["posted"]
            })
        
        return alerts
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Get job statistics
        total_jobs = self.db.query(GenerationJob).count()
        pending_jobs = self.db.query(GenerationJob).filter(
            GenerationJob.status == "pending"
        ).count()
        processing_jobs = self.db.query(GenerationJob).filter(
            GenerationJob.status == "processing"
        ).count()
        completed_jobs = self.db.query(GenerationJob).filter(
            GenerationJob.status == "completed"
        ).count()
        failed_jobs = self.db.query(GenerationJob).filter(
            GenerationJob.status == "failed"
        ).count()
        
        # Recent jobs (last 24h)
        recent_jobs = self.db.query(GenerationJob).filter(
            GenerationJob.created_at >= last_24h
        ).count()
        
        # Media statistics
        total_media = self.db.query(MediaItem).count()
        recent_media = self.db.query(MediaItem).filter(
            MediaItem.created_at >= last_24h
        ).count()
        
        # Batch job statistics
        total_batch_jobs = self.db.query(BatchJob).count()
        active_batch_jobs = self.db.query(BatchJob).filter(
            BatchJob.status.in_(["pending", "processing"])
        ).count()
        
        return {
            "jobs": {
                "total": total_jobs,
                "pending": pending_jobs,
                "processing": processing_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs,
                "recent_24h": recent_jobs
            },
            "media": {
                "total": total_media,
                "recent_24h": recent_media
            },
            "batch_jobs": {
                "total": total_batch_jobs,
                "active": active_batch_jobs
            },
            "metrics": self.get_metrics(),
            "alerts": self.check_alerts(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_metrics(self):
        """Reset metrics (useful for testing or periodic resets)"""
        self.metrics = {
            "generated": 0,
            "posted": 0,
            "failed": 0,
            "quality_avg": 0.0,
            "processing_time_avg": 0.0,
            "last_updated": datetime.utcnow()
        }
        logger.info("Metrics reset")

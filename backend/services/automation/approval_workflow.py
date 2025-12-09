"""
Approval Workflow
Automated and manual content approval system
"""
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from models import MediaItem
from services.automation.quality_controller import QualityController

logger = logging.getLogger(__name__)

class ApprovalWorkflow:
    """Service for content approval workflows"""
    
    def __init__(
        self,
        db: Session,
        auto_approve_threshold: float = 9.0
    ):
        self.db = db
        self.threshold = auto_approve_threshold
        self.quality_controller = QualityController()
    
    def approve_content(
        self,
        content_path: Path,
        content_type: str = "image",
        manual_override: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Approve content based on quality scores
        
        Args:
            content_path: Path to content file
            content_type: 'image' or 'video'
            manual_override: Manual approval override (True/False)
        
        Returns:
            Approval result
        """
        # Manual override takes precedence
        if manual_override is not None:
            return {
                "approved": manual_override,
                "method": "manual",
                "score": None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Check quality
        quality_result = self.quality_controller.check_quality(content_path, content_type)
        overall_score = quality_result["scores"].get("overall", 0.0)
        
        # Auto-approve if above threshold
        if overall_score >= self.threshold and quality_result.get("auto_approved", False):
            return {
                "approved": True,
                "method": "auto",
                "score": overall_score,
                "threshold": self.threshold,
                "quality_scores": quality_result["scores"],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "approved": False,
                "method": "manual_review_required",
                "score": overall_score,
                "threshold": self.threshold,
                "issues": quality_result.get("recommendations", []),
                "quality_scores": quality_result["scores"],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def create_review_queue(
        self,
        content_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create review queue from content list
        
        Args:
            content_list: List of content items with paths
        
        Returns:
            Dictionary with 'approved' and 'review_queue' lists
        """
        approved = []
        review_queue = []
        
        for content in content_list:
            content_path = Path(content.get("path", content.get("file_path")))
            if not content_path.exists():
                review_queue.append({
                    **content,
                    "result": {
                        "approved": False,
                        "method": "error",
                        "error": "File not found"
                    }
                })
                continue
            
            result = self.approve_content(
                content_path,
                content.get("type", "image")
            )
            
            if result["approved"]:
                approved.append({
                    **content,
                    "approval": result
                })
            else:
                review_queue.append({
                    **content,
                    "approval": result
                })
        
        return {
            "approved": approved,
            "review_queue": review_queue,
            "approved_count": len(approved),
            "review_count": len(review_queue),
            "total": len(content_list)
        }
    
    def batch_approve(
        self,
        media_ids: List[str],
        auto_approve: bool = True
    ) -> Dict[str, Any]:
        """
        Batch approve media items
        
        Args:
            media_ids: List of media item IDs
            auto_approve: Whether to auto-approve based on quality
        
        Returns:
            Approval results
        """
        approved = []
        rejected = []
        
        for media_id in media_ids:
            media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
            if not media:
                rejected.append({
                    "media_id": media_id,
                    "reason": "Media not found"
                })
                continue
            
            media_path = Path(media.file_path)
            if not media_path.exists():
                rejected.append({
                    "media_id": media_id,
                    "reason": "File not found"
                })
                continue
            
            if auto_approve:
                result = self.approve_content(media_path, media.type)
                if result["approved"]:
                    approved.append({
                        "media_id": media_id,
                        "approval": result
                    })
                else:
                    rejected.append({
                        "media_id": media_id,
                        "approval": result
                    })
            else:
                # Manual approval required
                rejected.append({
                    "media_id": media_id,
                    "reason": "Manual approval required"
                })
        
        return {
            "approved": approved,
            "rejected": rejected,
            "approved_count": len(approved),
            "rejected_count": len(rejected),
            "total": len(media_ids)
        }

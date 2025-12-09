"""
Content Scheduler
Scheduling and automated posting system
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import MediaItem

logger = logging.getLogger(__name__)

class ScheduledPost:
    """Represents a scheduled post"""
    def __init__(
        self,
        content_id: str,
        platform: str,
        scheduled_time: datetime,
        status: str = "scheduled"
    ):
        self.content_id = content_id
        self.platform = platform
        self.scheduled_time = scheduled_time
        self.status = status
        self.created_at = datetime.utcnow()

class ContentScheduler:
    """Service for scheduling content posts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.schedule: List[ScheduledPost] = []
    
    def schedule_content(
        self,
        content_id: str,
        platform: str,
        scheduled_time: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScheduledPost:
        """
        Schedule content for posting
        
        Args:
            content_id: Media item ID
            platform: Platform name (instagram, twitter, onlyfans, etc.)
            scheduled_time: When to post
            metadata: Additional metadata
        
        Returns:
            Scheduled post object
        """
        scheduled_post = ScheduledPost(
            content_id=content_id,
            platform=platform,
            scheduled_time=scheduled_time,
            status="scheduled"
        )
        
        # Store in database (would need ScheduledPost model)
        # For now, store in memory
        self.schedule.append(scheduled_post)
        
        logger.info(
            f"Scheduled {content_id} for {platform} at {scheduled_time}"
        )
        
        return scheduled_post
    
    def get_upcoming_posts(
        self,
        hours: int = 24,
        platform: Optional[str] = None
    ) -> List[ScheduledPost]:
        """
        Get upcoming scheduled posts
        
        Args:
            hours: How many hours ahead to look
            platform: Filter by platform (optional)
        
        Returns:
            List of scheduled posts
        """
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours)
        
        upcoming = [
            post for post in self.schedule
            if post.status == "scheduled"
            and post.scheduled_time <= cutoff
            and (platform is None or post.platform == platform)
        ]
        
        return sorted(upcoming, key=lambda x: x.scheduled_time)
    
    def get_posts_due_now(self) -> List[ScheduledPost]:
        """Get posts that are due to be posted now"""
        now = datetime.utcnow()
        return [
            post for post in self.schedule
            if post.status == "scheduled"
            and post.scheduled_time <= now
        ]
    
    def mark_posted(self, content_id: str, platform: str):
        """Mark a post as posted"""
        for post in self.schedule:
            if post.content_id == content_id and post.platform == platform:
                post.status = "posted"
                logger.info(f"Marked {content_id} as posted on {platform}")
                break
    
    def mark_failed(self, content_id: str, platform: str, error: str):
        """Mark a post as failed"""
        for post in self.schedule:
            if post.content_id == content_id and post.platform == platform:
                post.status = "failed"
                post.error = error
                logger.error(f"Marked {content_id} as failed on {platform}: {error}")
                break
    
    def cancel_scheduled_post(self, content_id: str, platform: str):
        """Cancel a scheduled post"""
        for post in self.schedule:
            if post.content_id == content_id and post.platform == platform:
                post.status = "cancelled"
                logger.info(f"Cancelled {content_id} on {platform}")
                break

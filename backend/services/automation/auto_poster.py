"""
Auto Poster
Automated posting to social media platforms
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from models import MediaItem
from services.automation.content_scheduler import ContentScheduler, ScheduledPost

logger = logging.getLogger(__name__)

class PlatformPoster:
    """Base class for platform posters"""
    
    def post(self, media_path: Path, caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Post content to platform"""
        raise NotImplementedError

class InstagramPoster(PlatformPoster):
    """Instagram poster (placeholder)"""
    
    def post(self, media_path: Path, caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Post to Instagram"""
        logger.info(f"Posting to Instagram: {media_path}")
        # TODO: Implement Instagram API integration
        return {
            "success": True,
            "platform": "instagram",
            "post_id": "placeholder",
            "url": "https://instagram.com/p/placeholder"
        }

class TwitterPoster(PlatformPoster):
    """Twitter poster (placeholder)"""
    
    def post(self, media_path: Path, caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Post to Twitter"""
        logger.info(f"Posting to Twitter: {media_path}")
        # TODO: Implement Twitter API integration
        return {
            "success": True,
            "platform": "twitter",
            "post_id": "placeholder",
            "url": "https://twitter.com/placeholder/status/placeholder"
        }

class OnlyFansPoster(PlatformPoster):
    """OnlyFans poster (placeholder)"""
    
    def post(self, media_path: Path, caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Post to OnlyFans"""
        logger.info(f"Posting to OnlyFans: {media_path}")
        # TODO: Implement OnlyFans API integration
        return {
            "success": True,
            "platform": "onlyfans",
            "post_id": "placeholder"
        }

class AutoPoster:
    """Service for automated posting"""
    
    def __init__(self, db: Session, scheduler: ContentScheduler):
        self.db = db
        self.scheduler = scheduler
        self.platforms = {
            "instagram": InstagramPoster(),
            "twitter": TwitterPoster(),
            "onlyfans": OnlyFansPoster()
        }
    
    def process_scheduled_posts(self) -> Dict[str, Any]:
        """
        Process all scheduled posts that are due
        
        Returns:
            Processing results
        """
        due_posts = self.scheduler.get_posts_due_now()
        
        results = {
            "processed": 0,
            "posted": 0,
            "failed": 0,
            "errors": []
        }
        
        for post in due_posts:
            try:
                # Get media item
                media = self.db.query(MediaItem).filter(
                    MediaItem.id == post.content_id
                ).first()
                
                if not media:
                    error = f"Media {post.content_id} not found"
                    self.scheduler.mark_failed(post.content_id, post.platform, error)
                    results["failed"] += 1
                    results["errors"].append({
                        "content_id": post.content_id,
                        "platform": post.platform,
                        "error": error
                    })
                    continue
                
                # Get platform poster
                poster = self.platforms.get(post.platform)
                if not poster:
                    error = f"Platform {post.platform} not supported"
                    self.scheduler.mark_failed(post.content_id, post.platform, error)
                    results["failed"] += 1
                    results["errors"].append({
                        "content_id": post.content_id,
                        "platform": post.platform,
                        "error": error
                    })
                    continue
                
                # Post content
                media_path = Path(media.file_path)
                if not media_path.exists():
                    error = f"Media file not found: {media_path}"
                    self.scheduler.mark_failed(post.content_id, post.platform, error)
                    results["failed"] += 1
                    results["errors"].append({
                        "content_id": post.content_id,
                        "platform": post.platform,
                        "error": error
                    })
                    continue
                
                # Get caption from metadata
                caption = media.meta_data.get("caption") if media.meta_data else None
                
                # Post
                post_result = poster.post(media_path, caption=caption)
                
                if post_result.get("success"):
                    self.scheduler.mark_posted(post.content_id, post.platform)
                    results["posted"] += 1
                    logger.info(
                        f"Successfully posted {post.content_id} to {post.platform}"
                    )
                else:
                    error = post_result.get("error", "Unknown error")
                    self.scheduler.mark_failed(post.content_id, post.platform, error)
                    results["failed"] += 1
                    results["errors"].append({
                        "content_id": post.content_id,
                        "platform": post.platform,
                        "error": error
                    })
                
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"Error posting {post.content_id} to {post.platform}: {e}")
                self.scheduler.mark_failed(post.content_id, post.platform, str(e))
                results["failed"] += 1
                results["errors"].append({
                    "content_id": post.content_id,
                    "platform": post.platform,
                    "error": str(e)
                })
        
        return results
    
    def post_immediately(
        self,
        media_id: str,
        platform: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post content immediately
        
        Args:
            media_id: Media item ID
            platform: Platform name
            caption: Post caption
        
        Returns:
            Post result
        """
        media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
        if not media:
            return {
                "success": False,
                "error": "Media not found"
            }
        
        poster = self.platforms.get(platform)
        if not poster:
            return {
                "success": False,
                "error": f"Platform {platform} not supported"
            }
        
        media_path = Path(media.file_path)
        if not media_path.exists():
            return {
                "success": False,
                "error": "Media file not found"
            }
        
        try:
            result = poster.post(media_path, caption=caption)
            return result
        except Exception as e:
            logger.error(f"Error posting immediately: {e}")
            return {
                "success": False,
                "error": str(e)
            }

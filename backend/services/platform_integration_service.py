"""
Platform Integration Service
Handles posting to Instagram, OnlyFans, Twitter/X, Facebook, Telegram, YouTube, TikTok, Pinterest
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from database import SessionLocal
from models import PlatformAccount, PlatformPost

logger = logging.getLogger(__name__)


class PlatformIntegrationService:
    """Service for platform integrations and persistence."""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize platform integration service.

        Args:
            db: Optional SQLAlchemy session. If not provided, a new session is created.
        """
        self._external_session = db is not None
        self.db: Session = db or SessionLocal()
        self.platforms = {
            "instagram": InstagramPlatform(),
            "onlyfans": OnlyFansPlatform(),
            "twitter": TwitterPlatform(),
            "facebook": FacebookPlatform(),
            "telegram": TelegramPlatform(),
            "youtube": YouTubePlatform(),
            "tiktok": TikTokPlatform(),
            "pinterest": PinterestPlatform(),
        }

    # -------------------- Account management -------------------- #
    def create_account(
        self,
        platform: str,
        username: str,
        auth_type: str,
        credentials: Dict[str, Any],
        display_name: Optional[str] = None,
    ) -> PlatformAccount:
        if not platform:
            raise ValueError("platform is required")
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")
        if not username:
            raise ValueError("username is required")

        account = PlatformAccount(
            platform=platform,
            username=username,
            auth_type=auth_type or "browser",
            credentials=credentials or {},
            display_name=display_name or username,
            is_active=True,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def list_accounts(
        self,
        platform: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[PlatformAccount]:
        query = self.db.query(PlatformAccount).filter(PlatformAccount.deleted_at.is_(None))
        if platform:
            query = query.filter(PlatformAccount.platform == platform)
        if is_active is not None:
            query = query.filter(PlatformAccount.is_active == is_active)
        return query.order_by(PlatformAccount.created_at.desc()).all()

    def get_account(self, account_id: str) -> Optional[PlatformAccount]:
        if not account_id:
            return None
        return (
            self.db.query(PlatformAccount)
            .filter(PlatformAccount.id == account_id, PlatformAccount.deleted_at.is_(None))
            .first()
        )

    def update_account(
        self,
        account_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[PlatformAccount]:
        account = self.get_account(account_id)
        if not account:
            return None

        if credentials is not None:
            account.credentials = credentials
        if is_active is not None:
            account.is_active = is_active
            account.last_used_at = datetime.utcnow() if is_active else account.last_used_at

        self.db.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, account_id: str) -> bool:
        account = self.get_account(account_id)
        if not account:
            return False

        account.deleted_at = datetime.utcnow()
        account.is_active = False
        self.db.commit()
        return True

    # -------------------- Post management -------------------- #
    def _resolve_account(self, account_id: str) -> Tuple[PlatformAccount, BasePlatform]:
        account = self.get_account(account_id)
        if not account:
            raise ValueError("Account not found or inactive")
        if account.platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {account.platform}")
        return account, self.platforms[account.platform]

    def create_post(
        self,
        account_id: str,
        media_id: Optional[str],
        caption: str,
        post_type: str,
        scheduled_at: Optional[datetime] = None,
    ) -> PlatformPost:
        account = self.get_account(account_id)
        if not account:
            raise ValueError("Account not found")

        status = "scheduled" if scheduled_at else "pending"
        post = PlatformPost(
            account_id=account_id,
            platform=account.platform,
            media_id=media_id,
            caption=caption or "",
            post_type=post_type or "photo",
            status=status,
            scheduled_at=scheduled_at,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def list_posts(
        self,
        account_id: Optional[str] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Dict[str, Any]:
        query = self.db.query(PlatformPost).join(PlatformAccount).filter(PlatformAccount.deleted_at.is_(None))
        if account_id:
            query = query.filter(PlatformPost.account_id == account_id)
        if platform:
            query = query.filter(PlatformPost.platform == platform)
        if status:
            query = query.filter(PlatformPost.status == status)

        total = query.count()
        page = max(page, 1)
        limit = max(1, min(limit, 100))
        posts = (
            query.order_by(PlatformPost.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        total_pages = (total + limit - 1) // limit
        return {"posts": posts, "total": total, "page": page, "limit": limit, "total_pages": total_pages}

    def get_post(self, post_id: str) -> Optional[PlatformPost]:
        if not post_id:
            return None
        return self.db.query(PlatformPost).filter(PlatformPost.id == post_id).first()

    def publish_post(self, post_id: str) -> Dict[str, Any]:
        post = self.get_post(post_id)
        if not post:
            raise ValueError("Post not found")

        account, platform_handler = self._resolve_account(post.account_id)
        account.last_used_at = datetime.utcnow()

        try:
            result = platform_handler.post(
                media_path=post.media_item.file_path if post.media_item else "",
                caption=post.caption,
                hashtags=None,
                schedule_time=post.scheduled_at,
                account_id=account.account_id or account.username,
            )
            post.status = "published"
            post.platform_post_id = result.get("post_id") or result.get("video_id") or result.get("pin_id")
            post.published_at = datetime.utcnow()
            post.error_message = None
        except Exception as exc:  # pragma: no cover - safeguard
            logger.error(f"Publish platform post failed: {exc}")
            post.status = "failed"
            post.failed_at = datetime.utcnow()
            post.retry_count = (post.retry_count or 0) + 1
            post.error_message = str(exc)
            self.db.commit()
            raise

        self.db.commit()
        self.db.refresh(post)
        self.db.refresh(account)
        return {
            "success": post.status == "published",
            "platform_post_id": post.platform_post_id,
            "platform": post.platform,
        }

    # -------------------- Direct platform helpers -------------------- #
    def post_to_platform(
        self,
        platform: str,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Direct posting helper (does not persist posts)."""
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")

        platform_handler = self.platforms[platform]
        return platform_handler.post(
            media_path=media_path,
            caption=caption,
            hashtags=hashtags,
            schedule_time=schedule_time,
            account_id=account_id,
        )

    def get_platform_status(self, platform: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get platform connection status."""
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")

        platform_handler = self.platforms[platform]
        return platform_handler.get_status(account_id)

    def schedule_post(
        self,
        platform: str,
        media_path: str,
        schedule_time: datetime,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Schedule a post for later (direct helper)."""
        return self.post_to_platform(
            platform=platform,
            media_path=media_path,
            caption=caption,
            hashtags=hashtags,
            schedule_time=schedule_time,
            account_id=account_id,
        )

    def get_analytics(
        self,
        platform: str,
        post_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get platform analytics (placeholder stub)."""
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")

        platform_handler = self.platforms[platform]
        return platform_handler.get_analytics(post_id, start_date, end_date)

    def __del__(self):
        if not self._external_session:
            try:
                self.db.close()
            except Exception:
                pass

class BasePlatform:
    """Base class for platform integrations"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post to platform (to be implemented by subclasses)"""
        raise NotImplementedError
    
    def get_status(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get connection status"""
        return {
            "connected": False,
            "message": "Not implemented"
        }
    
    def get_analytics(
        self,
        post_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics"""
        return {
            "platform": self.__class__.__name__,
            "analytics": {}
        }


class InstagramPlatform(BasePlatform):
    """Instagram integration"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post to Instagram"""
        # TODO: Implement Instagram API integration
        # This would use Instagram Graph API or similar
        logger.info(f"Posting to Instagram: {media_path}")
        return {
            "platform": "instagram",
            "post_id": f"ig_{datetime.now().timestamp()}",
            "url": f"https://instagram.com/p/...",
            "scheduled": schedule_time is not None,
            "scheduled_at": schedule_time.isoformat() if schedule_time else None
        }
    
    def get_status(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Instagram connection status"""
        # TODO: Check Instagram API connection
        return {
            "connected": False,
            "platform": "instagram",
            "message": "Instagram integration not configured"
        }


class OnlyFansPlatform(BasePlatform):
    """OnlyFans integration"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post to OnlyFans"""
        # TODO: Implement OnlyFans API integration
        logger.info(f"Posting to OnlyFans: {media_path}")
        return {
            "platform": "onlyfans",
            "post_id": f"of_{datetime.now().timestamp()}",
            "url": f"https://onlyfans.com/...",
            "scheduled": schedule_time is not None,
            "scheduled_at": schedule_time.isoformat() if schedule_time else None
        }


class TwitterPlatform(BasePlatform):
    """Twitter/X integration"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post to Twitter/X"""
        # TODO: Implement Twitter API integration
        logger.info(f"Posting to Twitter: {media_path}")
        return {
            "platform": "twitter",
            "post_id": f"tw_{datetime.now().timestamp()}",
            "url": f"https://twitter.com/...",
            "scheduled": schedule_time is not None,
            "scheduled_at": schedule_time.isoformat() if schedule_time else None
        }


class FacebookPlatform(BasePlatform):
    """Facebook integration"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post to Facebook"""
        # TODO: Implement Facebook Graph API integration
        logger.info(f"Posting to Facebook: {media_path}")
        return {
            "platform": "facebook",
            "post_id": f"fb_{datetime.now().timestamp()}",
            "url": f"https://facebook.com/...",
            "scheduled": schedule_time is not None,
            "scheduled_at": schedule_time.isoformat() if schedule_time else None
        }


class TelegramPlatform(BasePlatform):
    """Telegram bot integration"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post to Telegram"""
        # TODO: Implement Telegram Bot API integration
        logger.info(f"Posting to Telegram: {media_path}")
        return {
            "platform": "telegram",
            "post_id": f"tg_{datetime.now().timestamp()}",
            "scheduled": schedule_time is not None,
            "scheduled_at": schedule_time.isoformat() if schedule_time else None
        }


class YouTubePlatform(BasePlatform):
    """YouTube integration"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload to YouTube"""
        # TODO: Implement YouTube Data API integration
        logger.info(f"Uploading to YouTube: {media_path}")
        return {
            "platform": "youtube",
            "video_id": f"yt_{datetime.now().timestamp()}",
            "url": f"https://youtube.com/watch?v=...",
            "scheduled": schedule_time is not None,
            "scheduled_at": schedule_time.isoformat() if schedule_time else None
        }


class TikTokPlatform(BasePlatform):
    """TikTok integration"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post to TikTok"""
        # TODO: Implement TikTok API integration
        logger.info(f"Posting to TikTok: {media_path}")
        return {
            "platform": "tiktok",
            "post_id": f"tt_{datetime.now().timestamp()}",
            "url": f"https://tiktok.com/@...",
            "scheduled": schedule_time is not None,
            "scheduled_at": schedule_time.isoformat() if schedule_time else None
        }


class PinterestPlatform(BasePlatform):
    """Pinterest integration"""
    
    def post(
        self,
        media_path: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post to Pinterest"""
        # TODO: Implement Pinterest API integration
        logger.info(f"Posting to Pinterest: {media_path}")
        return {
            "platform": "pinterest",
            "pin_id": f"pin_{datetime.now().timestamp()}",
            "url": f"https://pinterest.com/pin/...",
            "scheduled": schedule_time is not None,
            "scheduled_at": schedule_time.isoformat() if schedule_time else None
        }

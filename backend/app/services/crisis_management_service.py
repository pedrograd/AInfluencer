"""Crisis management service for handling content takedowns and compliance issues."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.post import Post
from app.models.content import Content

logger = get_logger(__name__)


class CrisisManagementService:
    """Service for crisis management operations including content takedowns."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize crisis management service with database session."""
        self.db = db

    async def report_takedown(
        self,
        post_id: UUID,
        platform: str,
        reason: str,
        takedown_type: str = "platform",
        notified_at: Optional[datetime] = None,
    ) -> Post:
        """Report a content takedown from a platform.
        
        Args:
            post_id: UUID of the post that was taken down
            platform: Platform name (instagram, twitter, facebook, etc.)
            reason: Reason for takedown (copyright, community_guidelines, etc.)
            takedown_type: Type of takedown (platform, dmca, user_report, etc.)
            notified_at: Timestamp when takedown was notified (defaults to now)
            
        Returns:
            Updated Post object
            
        Raises:
            ValueError: If post not found or platform mismatch
        """
        # Get post
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            raise ValueError(f"Post {post_id} not found")

        # Verify platform matches
        if post.platform != platform:
            logger.warning(
                f"Platform mismatch for post {post_id}: "
                f"expected {platform}, got {post.platform}"
            )

        # Update post status
        post.status = "deleted"
        post.error_message = (
            f"Takedown [{takedown_type}]: {reason}"
            + (f" (notified at {notified_at})" if notified_at else "")
        )
        post.updated_at = datetime.utcnow()

        # Log takedown event
        logger.warning(
            f"Content takedown reported: post_id={post_id}, "
            f"platform={platform}, reason={reason}, type={takedown_type}",
            extra={
                "post_id": str(post_id),
                "platform": platform,
                "reason": reason,
                "takedown_type": takedown_type,
                "character_id": str(post.character_id),
            }
        )

        await self.db.flush()
        await self.db.refresh(post)
        return post

    async def batch_report_takedowns(
        self,
        post_ids: list[UUID],
        platform: str,
        reason: str,
        takedown_type: str = "platform",
    ) -> tuple[int, int]:
        """Batch report multiple content takedowns.
        
        Args:
            post_ids: List of post UUIDs that were taken down
            platform: Platform name
            reason: Reason for takedown
            takedown_type: Type of takedown
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        for post_id in post_ids:
            try:
                await self.report_takedown(
                    post_id=post_id,
                    platform=platform,
                    reason=reason,
                    takedown_type=takedown_type,
                )
                successful += 1
            except ValueError as e:
                logger.error(f"Failed to report takedown for post {post_id}: {e}")
                failed += 1

        return successful, failed

    async def get_takedown_statistics(
        self,
        character_id: Optional[UUID] = None,
        platform: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get takedown statistics.
        
        Args:
            character_id: Optional character ID to filter by
            platform: Optional platform to filter by
            start_date: Optional start date for date range
            end_date: Optional end date for date range
            
        Returns:
            Dictionary with takedown statistics
        """
        # Build query for deleted posts with takedown reasons
        query = select(Post).where(
            and_(
                Post.status == "deleted",
                Post.error_message.like("Takedown%")
            )
        )

        if character_id:
            query = query.where(Post.character_id == character_id)
        if platform:
            query = query.where(Post.platform == platform)
        if start_date:
            query = query.where(Post.updated_at >= start_date)
        if end_date:
            query = query.where(Post.updated_at <= end_date)

        result = await self.db.execute(query)
        takedown_posts = result.scalars().all()

        # Calculate statistics
        total_takedowns = len(takedown_posts)
        by_platform = {}
        by_reason = {}

        for post in takedown_posts:
            # Count by platform
            platform_name = post.platform
            by_platform[platform_name] = by_platform.get(platform_name, 0) + 1

            # Extract reason from error_message
            if post.error_message:
                # Parse "Takedown [type]: reason"
                parts = post.error_message.split(": ", 1)
                if len(parts) > 1:
                    reason = parts[1].split(" (")[0]  # Remove timestamp if present
                    by_reason[reason] = by_reason.get(reason, 0) + 1

        return {
            "total_takedowns": total_takedowns,
            "by_platform": by_platform,
            "by_reason": by_reason,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }
        }

    async def mark_content_for_review(
        self,
        content_id: UUID,
        review_reason: str,
    ) -> Content:
        """Mark content for manual review due to potential issues.
        
        Args:
            content_id: UUID of the content to mark
            review_reason: Reason for review
            
        Returns:
            Updated Content object
            
        Raises:
            ValueError: If content not found
        """
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Mark as rejected with review reason
        content.approval_status = "rejected"
        content.rejection_reason = f"Review required: {review_reason}"
        content.is_approved = False

        logger.info(
            f"Content marked for review: content_id={content_id}, reason={review_reason}",
            extra={
                "content_id": str(content_id),
                "review_reason": review_reason,
            }
        )

        await self.db.flush()
        await self.db.refresh(content)
        return content


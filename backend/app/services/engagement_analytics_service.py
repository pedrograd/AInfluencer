"""Engagement analytics service for calculating engagement metrics and statistics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.post import Post

logger = get_logger(__name__)


class EngagementAnalyticsService:
    """Service for calculating engagement analytics and metrics."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize engagement analytics service.

        Args:
            db: Database session.
        """
        self.db = db

    async def get_overview(
        self,
        character_id: UUID | None = None,
        platform: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get analytics overview with aggregated metrics.

        Args:
            character_id: Optional character ID to filter by.
            platform: Optional platform name to filter by.
            from_date: Optional start date for date range filter.
            to_date: Optional end date for date range filter.

        Returns:
            Dictionary containing analytics overview data.
        """
        # Build base query
        query = select(Post).where(Post.status == "published")

        if character_id:
            query = query.where(Post.character_id == character_id)
        if platform:
            query = query.where(Post.platform == platform)
        if from_date:
            query = query.where(Post.published_at >= from_date)
        if to_date:
            query = query.where(Post.published_at <= to_date)

        # Execute query to get posts
        result = await self.db.execute(query)
        posts = result.scalars().all()

        # Calculate metrics
        total_posts = len(posts)
        total_engagement = sum(
            post.likes_count + post.comments_count + post.shares_count for post in posts
        )
        total_followers = 0  # TODO: Get from platform accounts when available
        total_reach = sum(post.views_count for post in posts)

        # Calculate engagement rate (engagement / reach, or default to 0.05 if no reach)
        engagement_rate = (
            total_engagement / total_reach if total_reach > 0 else 0.05
        )

        # Calculate follower growth (placeholder - would need historical data)
        follower_growth = 0  # TODO: Calculate from historical platform account data

        # Get top performing posts (by total engagement)
        top_posts = sorted(
            posts,
            key=lambda p: p.likes_count + p.comments_count + p.shares_count,
            reverse=True,
        )[:10]

        top_performing_posts = [
            {
                "id": str(post.id),
                "platform": post.platform,
                "post_type": post.post_type,
                "likes": post.likes_count,
                "comments": post.comments_count,
                "shares": post.shares_count,
                "views": post.views_count,
                "published_at": post.published_at.isoformat() if post.published_at else None,
            }
            for post in top_posts
        ]

        # Platform breakdown
        platform_breakdown: dict[str, dict[str, int]] = {}
        for post in posts:
            if post.platform not in platform_breakdown:
                platform_breakdown[post.platform] = {
                    "posts": 0,
                    "engagement": 0,
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                    "views": 0,
                }
            platform_breakdown[post.platform]["posts"] += 1
            platform_breakdown[post.platform]["engagement"] += (
                post.likes_count + post.comments_count + post.shares_count
            )
            platform_breakdown[post.platform]["likes"] += post.likes_count
            platform_breakdown[post.platform]["comments"] += post.comments_count
            platform_breakdown[post.platform]["shares"] += post.shares_count
            platform_breakdown[post.platform]["views"] += post.views_count

        # Calculate trends (last 30 days by default)
        end_date = to_date or datetime.now()
        start_date = from_date or (end_date - timedelta(days=30))

        # Get daily engagement data
        daily_query = (
            select(
                func.date(Post.published_at).label("date"),
                func.sum(Post.likes_count + Post.comments_count + Post.shares_count).label(
                    "engagement"
                ),
            )
            .where(Post.status == "published")
            .where(Post.published_at >= start_date)
            .where(Post.published_at <= end_date)
        )

        if character_id:
            daily_query = daily_query.where(Post.character_id == character_id)
        if platform:
            daily_query = daily_query.where(Post.platform == platform)

        daily_query = daily_query.group_by(func.date(Post.published_at)).order_by(
            func.date(Post.published_at)
        )

        daily_result = await self.db.execute(daily_query)
        daily_data = daily_result.all()

        engagement_trend = [int(row.engagement or 0) for row in daily_data]

        # Follower growth trend (placeholder - would need historical data)
        follower_growth_trend = [0] * len(engagement_trend)

        return {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "total_followers": total_followers,
            "total_reach": total_reach,
            "engagement_rate": round(engagement_rate, 4),
            "follower_growth": follower_growth,
            "top_performing_posts": top_performing_posts,
            "platform_breakdown": platform_breakdown,
            "trends": {
                "follower_growth": follower_growth_trend,
                "engagement": engagement_trend,
            },
        }

    async def get_character_analytics(
        self,
        character_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get character-specific analytics.

        Args:
            character_id: Character ID.
            from_date: Optional start date for date range filter.
            to_date: Optional end date for date range filter.

        Returns:
            Dictionary containing character-specific analytics.
        """
        overview = await self.get_overview(
            character_id=character_id,
            from_date=from_date,
            to_date=to_date,
        )

        # Get platform-specific breakdown for this character
        query = select(Post).where(Post.character_id == character_id).where(
            Post.status == "published"
        )

        if from_date:
            query = query.where(Post.published_at >= from_date)
        if to_date:
            query = query.where(Post.published_at <= to_date)

        result = await self.db.execute(query)
        posts = result.scalars().all()

        # Calculate average engagement per post
        avg_engagement_per_post = (
            overview["total_engagement"] / overview["total_posts"]
            if overview["total_posts"] > 0
            else 0
        )

        # Get best performing platform
        best_platform = max(
            overview["platform_breakdown"].items(),
            key=lambda x: x[1]["engagement"],
        )[0] if overview["platform_breakdown"] else None

        return {
            **overview,
            "character_id": str(character_id),
            "average_engagement_per_post": round(avg_engagement_per_post, 2),
            "best_platform": best_platform,
            "total_posts_by_platform": {
                platform: data["posts"]
                for platform, data in overview["platform_breakdown"].items()
            },
        }

    async def get_post_analytics(self, post_id: UUID) -> dict[str, Any]:
        """
        Get post-specific analytics.

        Args:
            post_id: Post ID.

        Returns:
            Dictionary containing post-specific analytics.
        """
        query = select(Post).where(Post.id == post_id)
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise ValueError(f"Post with ID {post_id} not found")

        total_engagement = post.likes_count + post.comments_count + post.shares_count

        # Calculate engagement rate for this post
        engagement_rate = (
            total_engagement / post.views_count if post.views_count > 0 else 0
        )

        return {
            "post_id": str(post.id),
            "character_id": str(post.character_id),
            "platform": post.platform,
            "post_type": post.post_type,
            "platform_post_id": post.platform_post_id,
            "platform_post_url": post.platform_post_url,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "likes": post.likes_count,
            "comments": post.comments_count,
            "shares": post.shares_count,
            "views": post.views_count,
            "total_engagement": total_engagement,
            "engagement_rate": round(engagement_rate, 4),
            "hashtags": post.hashtags or [],
            "mentions": post.mentions or [],
            "last_engagement_sync_at": (
                post.last_engagement_sync_at.isoformat()
                if post.last_engagement_sync_at
                else None
            ),
        }

"""Character performance tracking service for recording and retrieving historical metrics."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analytics import Analytics
from app.models.post import Post

logger = get_logger(__name__)


class CharacterPerformanceTrackingService:
    """Service for recording and retrieving character performance metrics over time."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize character performance tracking service.

        Args:
            db: Database session.
        """
        self.db = db

    async def record_metrics(
        self,
        character_id: UUID,
        metric_date: date,
        metrics: dict[str, float | int],
        platform: str | None = None,
        platform_account_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record performance metrics for a character on a specific date.

        Args:
            character_id: Character ID.
            metric_date: Date for which metrics are recorded.
            metrics: Dictionary mapping metric_type to metric_value.
            platform: Optional platform name (instagram, twitter, etc.).
            platform_account_id: Optional platform account ID.
            metadata: Optional additional metadata to store.
        """
        valid_metric_types = {
            "follower_count",
            "following_count",
            "post_count",
            "engagement_rate",
            "likes_count",
            "comments_count",
            "shares_count",
            "views_count",
            "reach",
            "impressions",
        }

        for metric_type, metric_value in metrics.items():
            if metric_type not in valid_metric_types:
                logger.warning(f"Invalid metric_type: {metric_type}, skipping")
                continue

            # Check if record already exists
            query = select(Analytics).where(
                and_(
                    Analytics.character_id == character_id,
                    Analytics.metric_date == metric_date,
                    Analytics.metric_type == metric_type,
                    Analytics.platform == platform,
                    Analytics.platform_account_id == platform_account_id,
                )
            )
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing record
                existing.metric_value = Decimal(str(metric_value))
                if metadata:
                    existing.extra_data = metadata
            else:
                # Create new record
                analytics_record = Analytics(
                    character_id=character_id,
                    platform_account_id=platform_account_id,
                    metric_date=metric_date,
                    platform=platform,
                    metric_type=metric_type,
                    metric_value=Decimal(str(metric_value)),
                    extra_data=metadata,
                )
                self.db.add(analytics_record)

        await self.db.commit()
        logger.info(
            f"Recorded {len(metrics)} metrics for character {character_id} on {metric_date}"
        )

    async def get_character_performance(
        self,
        character_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        platform: str | None = None,
        metric_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get historical performance metrics for a character.

        Args:
            character_id: Character ID.
            from_date: Optional start date for date range filter.
            to_date: Optional end date for date range filter.
            platform: Optional platform name to filter by.
            metric_types: Optional list of metric types to filter by.

        Returns:
            Dictionary containing performance metrics organized by date and metric type.
        """
        query = select(Analytics).where(Analytics.character_id == character_id)

        if from_date:
            query = query.where(Analytics.metric_date >= from_date)
        if to_date:
            query = query.where(Analytics.metric_date <= to_date)
        if platform:
            query = query.where(Analytics.platform == platform)
        if metric_types:
            query = query.where(Analytics.metric_type.in_(metric_types))

        query = query.order_by(Analytics.metric_date.desc(), Analytics.metric_type)

        result = await self.db.execute(query)
        records = result.scalars().all()

        # Organize by date and metric type
        performance_data: dict[str, dict[str, Any]] = {}
        for record in records:
            date_str = record.metric_date.isoformat()
            if date_str not in performance_data:
                performance_data[date_str] = {
                    "date": date_str,
                    "platform": record.platform,
                    "metrics": {},
                }

            performance_data[date_str]["metrics"][record.metric_type] = {
                "value": float(record.metric_value),
                "metadata": record.extra_data,
            }

        return {
            "character_id": str(character_id),
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "platform": platform,
            "performance_data": list(performance_data.values()),
        }

    async def get_performance_trends(
        self,
        character_id: UUID,
        metric_type: str,
        days: int = 30,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """
        Get performance trends for a specific metric over time.

        Args:
            character_id: Character ID.
            metric_type: Type of metric to track (follower_count, engagement_rate, etc.).
            days: Number of days to look back (default: 30).
            platform: Optional platform name to filter by.

        Returns:
            Dictionary containing trend data with dates and values.
        """
        to_date = date.today()
        from_date = to_date - timedelta(days=days)

        query = (
            select(Analytics.metric_date, Analytics.metric_value)
            .where(Analytics.character_id == character_id)
            .where(Analytics.metric_type == metric_type)
            .where(Analytics.metric_date >= from_date)
            .where(Analytics.metric_date <= to_date)
        )

        if platform:
            query = query.where(Analytics.platform == platform)

        query = query.order_by(Analytics.metric_date)

        result = await self.db.execute(query)
        records = result.all()

        trend_data = [
            {
                "date": record.metric_date.isoformat(),
                "value": float(record.metric_value),
            }
            for record in records
        ]

        return {
            "character_id": str(character_id),
            "metric_type": metric_type,
            "platform": platform,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "trend": trend_data,
        }

    async def snapshot_character_performance(
        self,
        character_id: UUID,
        snapshot_date: date | None = None,
    ) -> None:
        """
        Create a snapshot of current character performance by calculating metrics from posts.

        Args:
            character_id: Character ID.
            snapshot_date: Date for snapshot (defaults to today).
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        # Calculate metrics from posts
        query = select(Post).where(Post.character_id == character_id).where(
            Post.status == "published"
        )

        result = await self.db.execute(query)
        posts = result.scalars().all()

        # Aggregate metrics by platform
        platform_metrics: dict[str, dict[str, Any]] = {}

        for post in posts:
            platform = post.platform
            if platform not in platform_metrics:
                platform_metrics[platform] = {
                    "post_count": 0,
                    "likes_count": 0,
                    "comments_count": 0,
                    "shares_count": 0,
                    "views_count": 0,
                }

            platform_metrics[platform]["post_count"] += 1
            platform_metrics[platform]["likes_count"] += post.likes_count or 0
            platform_metrics[platform]["comments_count"] += post.comments_count or 0
            platform_metrics[platform]["shares_count"] += post.shares_count or 0
            platform_metrics[platform]["views_count"] += post.views_count or 0

        # Record metrics for each platform
        for platform, metrics in platform_metrics.items():
            total_engagement = (
                metrics["likes_count"]
                + metrics["comments_count"]
                + metrics["shares_count"]
            )
            engagement_rate = (
                total_engagement / metrics["views_count"]
                if metrics["views_count"] > 0
                else 0.0
            )

            await self.record_metrics(
                character_id=character_id,
                metric_date=snapshot_date,
                metrics={
                    "post_count": metrics["post_count"],
                    "likes_count": metrics["likes_count"],
                    "comments_count": metrics["comments_count"],
                    "shares_count": metrics["shares_count"],
                    "views_count": metrics["views_count"],
                    "engagement_rate": engagement_rate,
                },
                platform=platform,
            )

        # Also record aggregate metrics (no platform)
        total_posts = sum(m["post_count"] for m in platform_metrics.values())
        total_likes = sum(m["likes_count"] for m in platform_metrics.values())
        total_comments = sum(m["comments_count"] for m in platform_metrics.values())
        total_shares = sum(m["shares_count"] for m in platform_metrics.values())
        total_views = sum(m["views_count"] for m in platform_metrics.values())
        overall_engagement_rate = (
            (total_likes + total_comments + total_shares) / total_views
            if total_views > 0
            else 0.0
        )

        await self.record_metrics(
            character_id=character_id,
            metric_date=snapshot_date,
            metrics={
                "post_count": total_posts,
                "likes_count": total_likes,
                "comments_count": total_comments,
                "shares_count": total_shares,
                "views_count": total_views,
                "engagement_rate": overall_engagement_rate,
            },
            platform=None,
        )

        logger.info(
            f"Created performance snapshot for character {character_id} on {snapshot_date}"
        )

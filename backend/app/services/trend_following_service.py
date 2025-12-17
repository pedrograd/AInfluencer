"""Trend following service for analyzing and tracking trends in content and hashtags."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.post import Post

logger = get_logger(__name__)


class TrendFollowingService:
    """Service for analyzing and following trends in content, hashtags, and topics."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize trend following service.

        Args:
            db: Database session.
        """
        self.db = db

    async def analyze_hashtag_trends(
        self,
        days: int = 30,
        platform: str | None = None,
        character_id: UUID | None = None,
        min_usage_count: int = 2,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Analyze trending hashtags based on usage and engagement over time.

        Args:
            days: Number of days to look back for trend analysis.
            platform: Optional platform name to filter by.
            character_id: Optional character ID to filter by.
            min_usage_count: Minimum number of times a hashtag must appear.
            limit: Maximum number of trending hashtags to return.

        Returns:
            List of trending hashtags with trend scores and metrics.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        mid_date = start_date + timedelta(days=days / 2)

        # Build base query for recent period
        recent_query = select(Post).where(Post.status == "published").where(
            Post.published_at >= mid_date
        ).where(Post.published_at <= end_date)

        # Build base query for earlier period
        earlier_query = select(Post).where(Post.status == "published").where(
            Post.published_at >= start_date
        ).where(Post.published_at < mid_date)

        if platform:
            recent_query = recent_query.where(Post.platform == platform)
            earlier_query = earlier_query.where(Post.platform == platform)

        if character_id:
            recent_query = recent_query.where(Post.character_id == character_id)
            earlier_query = earlier_query.where(Post.character_id == character_id)

        # Get posts from both periods
        recent_result = await self.db.execute(recent_query)
        recent_posts = recent_result.scalars().all()

        earlier_result = await self.db.execute(earlier_query)
        earlier_posts = earlier_result.scalars().all()

        # Analyze hashtags
        recent_hashtag_stats: dict[str, dict[str, Any]] = {}
        earlier_hashtag_stats: dict[str, dict[str, Any]] = {}

        # Process recent period
        for post in recent_posts:
            if post.hashtags:
                for hashtag in post.hashtags:
                    hashtag_lower = hashtag.lower()
                    if hashtag_lower not in recent_hashtag_stats:
                        recent_hashtag_stats[hashtag_lower] = {
                            "hashtag": hashtag,
                            "count": 0,
                            "total_engagement": 0,
                            "total_views": 0,
                            "posts": [],
                        }
                    recent_hashtag_stats[hashtag_lower]["count"] += 1
                    engagement = post.likes_count + post.comments_count + post.shares_count
                    recent_hashtag_stats[hashtag_lower]["total_engagement"] += engagement
                    recent_hashtag_stats[hashtag_lower]["total_views"] += post.views_count or 0
                    recent_hashtag_stats[hashtag_lower]["posts"].append(post.id)

        # Process earlier period
        for post in earlier_posts:
            if post.hashtags:
                for hashtag in post.hashtags:
                    hashtag_lower = hashtag.lower()
                    if hashtag_lower not in earlier_hashtag_stats:
                        earlier_hashtag_stats[hashtag_lower] = {
                            "hashtag": hashtag,
                            "count": 0,
                            "total_engagement": 0,
                            "total_views": 0,
                        }
                    earlier_hashtag_stats[hashtag_lower]["count"] += 1
                    engagement = post.likes_count + post.comments_count + post.shares_count
                    earlier_hashtag_stats[hashtag_lower]["total_engagement"] += engagement
                    earlier_hashtag_stats[hashtag_lower]["total_views"] += post.views_count or 0

        # Calculate trend scores
        trending_hashtags = []
        for hashtag_lower, recent_stats in recent_hashtag_stats.items():
            if recent_stats["count"] < min_usage_count:
                continue

            earlier_stats = earlier_hashtag_stats.get(hashtag_lower, {
                "count": 0,
                "total_engagement": 0,
                "total_views": 0,
            })

            # Calculate growth rate
            recent_count = recent_stats["count"]
            earlier_count = earlier_stats["count"]
            if earlier_count > 0:
                growth_rate = ((recent_count - earlier_count) / earlier_count) * 100
            else:
                growth_rate = 100.0 if recent_count > 0 else 0.0

            # Calculate engagement metrics
            recent_avg_engagement = (
                recent_stats["total_engagement"] / recent_count if recent_count > 0 else 0
            )
            recent_avg_views = (
                recent_stats["total_views"] / recent_count if recent_count > 0 else 0
            )
            recent_engagement_rate = (
                recent_stats["total_engagement"] / recent_stats["total_views"]
                if recent_stats["total_views"] > 0
                else 0
            )

            # Calculate trend score (combination of growth rate, engagement, and usage)
            # Normalize growth rate (0-1 scale, cap at 500% growth)
            growth_score = min(growth_rate / 500.0, 1.0) if growth_rate > 0 else 0.0

            # Normalize engagement (0-1 scale, assuming max 1000 avg engagement)
            engagement_score = min(recent_avg_engagement / 1000.0, 1.0)

            # Normalize usage count (0-1 scale, assuming max 50 uses)
            usage_score = min(recent_count / 50.0, 1.0)

            # Weighted trend score
            trend_score = (growth_score * 0.4) + (engagement_score * 0.4) + (usage_score * 0.2)

            trending_hashtags.append({
                "hashtag": recent_stats["hashtag"],
                "trend_score": round(trend_score, 4),
                "growth_rate": round(growth_rate, 2),
                "recent_usage_count": recent_count,
                "earlier_usage_count": earlier_count,
                "avg_engagement": round(recent_avg_engagement, 2),
                "avg_views": round(recent_avg_views, 2),
                "engagement_rate": round(recent_engagement_rate, 4),
                "trend_direction": "up" if growth_rate > 10 else "stable" if growth_rate > -10 else "down",
            })

        # Sort by trend score descending
        trending_hashtags.sort(key=lambda x: x["trend_score"], reverse=True)

        return trending_hashtags[:limit]

    async def get_trend_recommendations(
        self,
        character_id: UUID,
        platform: str | None = None,
        days: int = 30,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Get trend recommendations for a character based on trending hashtags and content patterns.

        Args:
            character_id: Character ID to get recommendations for.
            platform: Optional platform name to filter by.
            days: Number of days to look back for trend analysis.
            limit: Maximum number of recommendations to return.

        Returns:
            Dictionary containing trend recommendations and analysis.
        """
        # Get trending hashtags
        trending_hashtags = await self.analyze_hashtag_trends(
            days=days,
            platform=platform,
            character_id=None,  # Look at all characters for trends
            limit=limit * 2,
        )

        # Get character's recent hashtags
        character_query = select(Post).where(
            Post.character_id == character_id
        ).where(Post.status == "published").where(
            Post.published_at >= datetime.now() - timedelta(days=days)
        )

        if platform:
            character_query = character_query.where(Post.platform == platform)

        character_result = await self.db.execute(character_query)
        character_posts = character_result.scalars().all()

        character_hashtags: set[str] = set()
        for post in character_posts:
            if post.hashtags:
                character_hashtags.update(h.lower() for h in post.hashtags)

        # Filter trending hashtags to those not already heavily used by character
        recommendations = []
        for trend in trending_hashtags:
            hashtag_lower = trend["hashtag"].lower()
            if hashtag_lower not in character_hashtags or trend["trend_score"] > 0.5:
                recommendations.append({
                    "type": "hashtag",
                    "hashtag": trend["hashtag"],
                    "trend_score": trend["trend_score"],
                    "growth_rate": trend["growth_rate"],
                    "reason": f"Hashtag is trending with {trend['growth_rate']:.1f}% growth and high engagement",
                    "recommendation": f"Consider using #{trend['hashtag']} in upcoming posts",
                })

        # Get best performing content types for trending hashtags
        content_type_recommendations = []
        if trending_hashtags:
            top_trending = trending_hashtags[:5]
            for trend in top_trending:
                # Find posts using this hashtag
                hashtag_query = select(Post).where(
                    Post.status == "published"
                ).where(
                    Post.published_at >= datetime.now() - timedelta(days=days)
                )

                if platform:
                    hashtag_query = hashtag_query.where(Post.platform == platform)

                hashtag_result = await self.db.execute(hashtag_query)
                hashtag_posts = hashtag_result.scalars().all()

                # Find posts with this hashtag
                posts_with_hashtag = [
                    p for p in hashtag_posts
                    if p.hashtags and trend["hashtag"].lower() in [h.lower() for h in p.hashtags]
                ]

                if posts_with_hashtag:
                    # Analyze content types
                    content_type_stats: dict[str, dict[str, Any]] = {}
                    for post in posts_with_hashtag:
                        post_type = post.post_type or "unknown"
                        if post_type not in content_type_stats:
                            content_type_stats[post_type] = {
                                "count": 0,
                                "total_engagement": 0,
                            }
                        engagement = post.likes_count + post.comments_count + post.shares_count
                        content_type_stats[post_type]["count"] += 1
                        content_type_stats[post_type]["total_engagement"] += engagement

                    # Find best content type
                    if content_type_stats:
                        best_type = max(
                            content_type_stats.items(),
                            key=lambda x: x[1]["total_engagement"] / x[1]["count"],
                        )
                        content_type_recommendations.append({
                            "type": "content_type",
                            "hashtag": trend["hashtag"],
                            "content_type": best_type[0],
                            "avg_engagement": round(
                                best_type[1]["total_engagement"] / best_type[1]["count"], 2
                            ),
                            "reason": f"Posts using #{trend['hashtag']} perform best as {best_type[0]}",
                            "recommendation": f"Create {best_type[0]} content with #{trend['hashtag']}",
                        })

        return {
            "character_id": str(character_id),
            "platform": platform,
            "analysis_period_days": days,
            "trending_hashtags": trending_hashtags[:limit],
            "hashtag_recommendations": recommendations[:limit],
            "content_type_recommendations": content_type_recommendations[:limit],
            "total_trends_analyzed": len(trending_hashtags),
        }

    async def get_trend_velocity(
        self,
        hashtag: str,
        days: int = 7,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """
        Get trend velocity for a specific hashtag (how fast it's growing).

        Args:
            hashtag: Hashtag to analyze.
            platform: Optional platform name to filter by.
            days: Number of days to analyze.

        Returns:
            Dictionary containing trend velocity metrics.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get daily usage counts
        daily_usage: dict[str, int] = {}
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            query = select(Post).where(Post.status == "published").where(
                Post.published_at >= day_start
            ).where(Post.published_at < day_end)

            if platform:
                query = query.where(Post.platform == platform)

            result = await self.db.execute(query)
            posts = result.scalars().all()

            day_key = day_start.strftime("%Y-%m-%d")
            daily_usage[day_key] = 0

            for post in posts:
                if post.hashtags and hashtag.lower() in [h.lower() for h in post.hashtags]:
                    daily_usage[day_key] += 1

        # Calculate velocity (rate of change)
        usage_values = list(daily_usage.values())
        if len(usage_values) < 2:
            velocity = 0.0
        else:
            # Simple linear regression slope as velocity
            n = len(usage_values)
            x = list(range(n))
            x_mean = sum(x) / n
            y_mean = sum(usage_values) / n

            numerator = sum((x[i] - x_mean) * (usage_values[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

            velocity = numerator / denominator if denominator > 0 else 0.0

        return {
            "hashtag": hashtag,
            "platform": platform,
            "days_analyzed": days,
            "daily_usage": daily_usage,
            "total_usage": sum(daily_usage.values()),
            "velocity": round(velocity, 4),
            "trend": "accelerating" if velocity > 0.5 else "stable" if velocity > -0.5 else "declining",
        }

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

    async def get_best_performing_content_analysis(
        self,
        character_id: UUID | None = None,
        platform: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Analyze best-performing content to identify patterns and recommendations.

        Args:
            character_id: Optional character ID to filter by.
            platform: Optional platform name to filter by.
            from_date: Optional start date for date range filter.
            to_date: Optional end date for date range filter.
            limit: Maximum number of items to return in top lists.

        Returns:
            Dictionary containing best-performing content analysis with patterns,
            top performers, and recommendations.
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

        if not posts:
            return {
                "total_posts_analyzed": 0,
                "content_type_analysis": {},
                "hashtag_analysis": [],
                "posting_time_analysis": {},
                "caption_analysis": {},
                "platform_analysis": {},
                "top_performing_posts": [],
                "recommendations": [],
            }

        # Calculate engagement for each post
        post_engagements = [
            {
                "post": post,
                "engagement": post.likes_count + post.comments_count + post.shares_count,
                "engagement_rate": (
                    (post.likes_count + post.comments_count + post.shares_count) / post.views_count
                    if post.views_count > 0
                    else 0
                ),
            }
            for post in posts
        ]

        # Sort by engagement
        post_engagements.sort(key=lambda x: x["engagement"], reverse=True)

        # === Content Type Analysis ===
        content_type_stats: dict[str, dict[str, Any]] = {}
        for item in post_engagements:
            post = item["post"]
            post_type = post.post_type or "unknown"
            if post_type not in content_type_stats:
                content_type_stats[post_type] = {
                    "count": 0,
                    "total_engagement": 0,
                    "total_views": 0,
                    "avg_engagement": 0.0,
                    "avg_engagement_rate": 0.0,
                }
            content_type_stats[post_type]["count"] += 1
            content_type_stats[post_type]["total_engagement"] += item["engagement"]
            content_type_stats[post_type]["total_views"] += post.views_count or 0

        # Calculate averages
        for post_type, stats in content_type_stats.items():
            if stats["count"] > 0:
                stats["avg_engagement"] = round(stats["total_engagement"] / stats["count"], 2)
                stats["avg_engagement_rate"] = round(
                    stats["total_engagement"] / stats["total_views"]
                    if stats["total_views"] > 0
                    else 0,
                    4,
                )

        # === Hashtag Analysis ===
        hashtag_stats: dict[str, dict[str, Any]] = {}
        for item in post_engagements:
            post = item["post"]
            hashtags = post.hashtags or []
            for hashtag in hashtags:
                if hashtag not in hashtag_stats:
                    hashtag_stats[hashtag] = {
                        "count": 0,
                        "total_engagement": 0,
                        "total_views": 0,
                        "avg_engagement": 0.0,
                    }
                hashtag_stats[hashtag]["count"] += 1
                hashtag_stats[hashtag]["total_engagement"] += item["engagement"]
                hashtag_stats[hashtag]["total_views"] += post.views_count or 0

        # Calculate averages and sort
        for hashtag, stats in hashtag_stats.items():
            if stats["count"] > 0:
                stats["avg_engagement"] = round(stats["total_engagement"] / stats["count"], 2)

        top_hashtags = sorted(
            hashtag_stats.items(),
            key=lambda x: x[1]["avg_engagement"],
            reverse=True,
        )[:limit]

        # === Posting Time Analysis ===
        hour_stats: dict[int, dict[str, Any]] = {}
        day_stats: dict[int, dict[str, Any]] = {}
        for item in post_engagements:
            post = item["post"]
            if post.published_at:
                hour = post.published_at.hour
                day = post.published_at.weekday()  # 0=Monday, 6=Sunday

                if hour not in hour_stats:
                    hour_stats[hour] = {"count": 0, "total_engagement": 0}
                hour_stats[hour]["count"] += 1
                hour_stats[hour]["total_engagement"] += item["engagement"]

                if day not in day_stats:
                    day_stats[day] = {"count": 0, "total_engagement": 0}
                day_stats[day]["count"] += 1
                day_stats[day]["total_engagement"] += item["engagement"]

        # Calculate averages
        for hour, stats in hour_stats.items():
            if stats["count"] > 0:
                stats["avg_engagement"] = round(stats["total_engagement"] / stats["count"], 2)

        for day, stats in day_stats.items():
            if stats["count"] > 0:
                stats["avg_engagement"] = round(stats["total_engagement"] / stats["count"], 2)

        # Find best hours and days
        best_hours = sorted(
            hour_stats.items(),
            key=lambda x: x[1]["avg_engagement"],
            reverse=True,
        )[:limit]
        best_days = sorted(
            day_stats.items(),
            key=lambda x: x[1]["avg_engagement"],
            reverse=True,
        )

        # === Caption Analysis ===
        caption_lengths = []
        for item in post_engagements:
            post = item["post"]
            if post.caption:
                caption_lengths.append(
                    {
                        "length": len(post.caption),
                        "engagement": item["engagement"],
                        "engagement_rate": item["engagement_rate"],
                    }
                )

        avg_caption_length = (
            sum(c["length"] for c in caption_lengths) / len(caption_lengths)
            if caption_lengths
            else 0
        )

        # Find optimal caption length range (top 20% performers)
        if caption_lengths:
            top_20_percent = sorted(
                caption_lengths, key=lambda x: x["engagement"], reverse=True
            )[: max(1, len(caption_lengths) // 5)]
            optimal_lengths = [c["length"] for c in top_20_percent]
            optimal_min = min(optimal_lengths) if optimal_lengths else 0
            optimal_max = max(optimal_lengths) if optimal_lengths else 0
        else:
            optimal_min = 0
            optimal_max = 0

        # === Platform Analysis ===
        platform_stats: dict[str, dict[str, Any]] = {}
        for item in post_engagements:
            post = item["post"]
            platform = post.platform
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "count": 0,
                    "total_engagement": 0,
                    "total_views": 0,
                    "avg_engagement": 0.0,
                    "avg_engagement_rate": 0.0,
                }
            platform_stats[platform]["count"] += 1
            platform_stats[platform]["total_engagement"] += item["engagement"]
            platform_stats[platform]["total_views"] += post.views_count or 0

        # Calculate averages
        for platform, stats in platform_stats.items():
            if stats["count"] > 0:
                stats["avg_engagement"] = round(stats["total_engagement"] / stats["count"], 2)
                stats["avg_engagement_rate"] = round(
                    stats["total_engagement"] / stats["total_views"]
                    if stats["total_views"] > 0
                    else 0,
                    4,
                )

        # === Top Performing Posts ===
        top_posts = [
            {
                "id": str(item["post"].id),
                "platform": item["post"].platform,
                "post_type": item["post"].post_type,
                "engagement": item["engagement"],
                "engagement_rate": round(item["engagement_rate"], 4),
                "likes": item["post"].likes_count,
                "comments": item["post"].comments_count,
                "shares": item["post"].shares_count,
                "views": item["post"].views_count,
                "hashtags": item["post"].hashtags or [],
                "published_at": item["post"].published_at.isoformat()
                if item["post"].published_at
                else None,
            }
            for item in post_engagements[:limit]
        ]

        # === Generate Recommendations ===
        recommendations = []

        # Best content type
        if content_type_stats:
            best_content_type = max(
                content_type_stats.items(),
                key=lambda x: x[1]["avg_engagement"],
            )
            recommendations.append(
                {
                    "type": "content_type",
                    "message": f"Best performing content type: {best_content_type[0]} "
                    f"(avg engagement: {best_content_type[1]['avg_engagement']:.0f})",
                    "recommendation": f"Focus on creating more {best_content_type[0]} content",
                }
            )

        # Best hashtags
        if top_hashtags:
            top_3_hashtags = [h[0] for h in top_hashtags[:3]]
            recommendations.append(
                {
                    "type": "hashtags",
                    "message": f"Top performing hashtags: {', '.join(top_3_hashtags)}",
                    "recommendation": f"Include these hashtags in future posts: {', '.join(top_3_hashtags)}",
                }
            )

        # Best posting times
        if best_hours:
            best_hour = best_hours[0][0]
            recommendations.append(
                {
                    "type": "posting_time",
                    "message": f"Best posting hour: {best_hour}:00 (avg engagement: {best_hours[0][1]['avg_engagement']:.0f})",
                    "recommendation": f"Schedule posts around {best_hour}:00 for maximum engagement",
                }
            )

        if best_days:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            best_day = best_days[0][0]
            recommendations.append(
                {
                    "type": "posting_time",
                    "message": f"Best posting day: {day_names[best_day]} (avg engagement: {best_days[0][1]['avg_engagement']:.0f})",
                    "recommendation": f"Post more content on {day_names[best_day]}s for better performance",
                }
            )

        # Caption length
        if optimal_min > 0 and optimal_max > 0:
            recommendations.append(
                {
                    "type": "caption",
                    "message": f"Optimal caption length: {optimal_min}-{optimal_max} characters",
                    "recommendation": f"Keep captions between {optimal_min} and {optimal_max} characters for best engagement",
                }
            )

        # Best platform
        if platform_stats:
            best_platform = max(
                platform_stats.items(),
                key=lambda x: x[1]["avg_engagement"],
            )
            recommendations.append(
                {
                    "type": "platform",
                    "message": f"Best performing platform: {best_platform[0]} "
                    f"(avg engagement: {best_platform[1]['avg_engagement']:.0f})",
                    "recommendation": f"Focus content distribution on {best_platform[0]}",
                }
            )

        return {
            "total_posts_analyzed": len(posts),
            "content_type_analysis": {
                post_type: {
                    "count": stats["count"],
                    "avg_engagement": stats["avg_engagement"],
                    "avg_engagement_rate": stats["avg_engagement_rate"],
                }
                for post_type, stats in content_type_stats.items()
            },
            "hashtag_analysis": [
                {
                    "hashtag": hashtag,
                    "count": stats["count"],
                    "avg_engagement": stats["avg_engagement"],
                }
                for hashtag, stats in top_hashtags
            ],
            "posting_time_analysis": {
                "best_hours": [
                    {"hour": hour, "avg_engagement": stats["avg_engagement"], "count": stats["count"]}
                    for hour, stats in best_hours
                ],
                "best_days": [
                    {
                        "day": day,
                        "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day],
                        "avg_engagement": stats["avg_engagement"],
                        "count": stats["count"],
                    }
                    for day, stats in best_days
                ],
            },
            "caption_analysis": {
                "avg_length": round(avg_caption_length, 0),
                "optimal_range": {"min": optimal_min, "max": optimal_max},
            },
            "platform_analysis": {
                platform: {
                    "count": stats["count"],
                    "avg_engagement": stats["avg_engagement"],
                    "avg_engagement_rate": stats["avg_engagement_rate"],
                }
                for platform, stats in platform_stats.items()
            },
            "top_performing_posts": top_posts,
            "recommendations": recommendations,
        }

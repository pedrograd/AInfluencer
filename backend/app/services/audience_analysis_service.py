"""Audience analysis service for analyzing audience demographics and behavior patterns."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.post import Post

logger = get_logger(__name__)


class AudienceAnalysisService:
    """Service for analyzing audience demographics and behavior patterns."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize audience analysis service.

        Args:
            db: Database session.
        """
        self.db = db

    async def analyze_audience(
        self,
        character_id: UUID | None = None,
        platform: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Analyze audience demographics and behavior patterns.

        Args:
            character_id: Optional character ID to filter by.
            platform: Optional platform name to filter by.
            from_date: Optional start date for date range filter.
            to_date: Optional end date for date range filter.

        Returns:
            Dictionary containing audience analysis data including:
            - Platform distribution
            - Engagement patterns
            - Content preferences
            - Activity patterns
            - Audience growth trends
            - Engagement quality metrics
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
                "total_posts": 0,
                "total_audience_reach": 0,
                "platform_distribution": {},
                "engagement_patterns": {},
                "content_preferences": {},
                "activity_patterns": {},
                "audience_growth": {},
                "engagement_quality": {},
                "audience_insights": [],
            }

        # Calculate total audience reach (sum of views)
        total_audience_reach = sum(post.views_count for post in posts)

        # === Platform Distribution ===
        platform_distribution: dict[str, dict[str, Any]] = {}
        for post in posts:
            if post.platform not in platform_distribution:
                platform_distribution[post.platform] = {
                    "posts_count": 0,
                    "total_reach": 0,
                    "total_engagement": 0,
                    "avg_engagement_rate": 0.0,
                    "audience_share": 0.0,
                }
            platform_distribution[post.platform]["posts_count"] += 1
            platform_distribution[post.platform]["total_reach"] += post.views_count
            platform_distribution[post.platform]["total_engagement"] += (
                post.likes_count + post.comments_count + post.shares_count
            )

        # Calculate averages and audience share
        for platform, stats in platform_distribution.items():
            if stats["posts_count"] > 0:
                stats["avg_engagement_rate"] = round(
                    stats["total_engagement"] / stats["total_reach"]
                    if stats["total_reach"] > 0
                    else 0,
                    4,
                )
            if total_audience_reach > 0:
                stats["audience_share"] = round(
                    stats["total_reach"] / total_audience_reach, 4
                )

        # === Engagement Patterns ===
        # Analyze engagement by post type
        engagement_by_type: dict[str, dict[str, Any]] = {}
        for post in posts:
            post_type = post.post_type or "unknown"
            if post_type not in engagement_by_type:
                engagement_by_type[post_type] = {
                    "count": 0,
                    "total_engagement": 0,
                    "total_reach": 0,
                    "avg_engagement": 0.0,
                    "avg_engagement_rate": 0.0,
                }
            engagement_by_type[post_type]["count"] += 1
            engagement_by_type[post_type]["total_engagement"] += (
                post.likes_count + post.comments_count + post.shares_count
            )
            engagement_by_type[post_type]["total_reach"] += post.views_count

        # Calculate averages
        for post_type, stats in engagement_by_type.items():
            if stats["count"] > 0:
                stats["avg_engagement"] = round(
                    stats["total_engagement"] / stats["count"], 2
                )
                stats["avg_engagement_rate"] = round(
                    stats["total_engagement"] / stats["total_reach"]
                    if stats["total_reach"] > 0
                    else 0,
                    4,
                )

        # === Content Preferences ===
        # Analyze which content types get most engagement
        content_preferences: dict[str, dict[str, Any]] = {}
        for post in posts:
            post_type = post.post_type or "unknown"
            if post_type not in content_preferences:
                content_preferences[post_type] = {
                    "posts": 0,
                    "total_engagement": 0,
                    "total_reach": 0,
                    "engagement_per_post": 0.0,
                    "preference_score": 0.0,
                }
            content_preferences[post_type]["posts"] += 1
            content_preferences[post_type]["total_engagement"] += (
                post.likes_count + post.comments_count + post.shares_count
            )
            content_preferences[post_type]["total_reach"] += post.views_count

        # Calculate preference scores (engagement per post normalized)
        total_engagement = sum(
            p.likes_count + p.comments_count + p.shares_count for p in posts
        )
        for post_type, stats in content_preferences.items():
            if stats["posts"] > 0:
                stats["engagement_per_post"] = round(
                    stats["total_engagement"] / stats["posts"], 2
                )
                # Preference score: engagement per post / average engagement per post
                avg_engagement_per_post = (
                    total_engagement / len(posts) if posts else 0
                )
                stats["preference_score"] = round(
                    stats["engagement_per_post"] / avg_engagement_per_post
                    if avg_engagement_per_post > 0
                    else 0,
                    2,
                )

        # === Activity Patterns ===
        # Analyze posting times and days
        hour_distribution: dict[int, dict[str, Any]] = {}
        day_distribution: dict[int, dict[str, Any]] = {}
        for post in posts:
            if post.published_at:
                hour = post.published_at.hour
                day = post.published_at.weekday()  # 0=Monday, 6=Sunday

                if hour not in hour_distribution:
                    hour_distribution[hour] = {
                        "posts": 0,
                        "total_engagement": 0,
                        "total_reach": 0,
                        "avg_engagement": 0.0,
                    }
                hour_distribution[hour]["posts"] += 1
                hour_distribution[hour]["total_engagement"] += (
                    post.likes_count + post.comments_count + post.shares_count
                )
                hour_distribution[hour]["total_reach"] += post.views_count

                if day not in day_distribution:
                    day_distribution[day] = {
                        "posts": 0,
                        "total_engagement": 0,
                        "total_reach": 0,
                        "avg_engagement": 0.0,
                    }
                day_distribution[day]["posts"] += 1
                day_distribution[day]["total_engagement"] += (
                    post.likes_count + post.comments_count + post.shares_count
                )
                day_distribution[day]["total_reach"] += post.views_count

        # Calculate averages
        for hour, stats in hour_distribution.items():
            if stats["posts"] > 0:
                stats["avg_engagement"] = round(
                    stats["total_engagement"] / stats["posts"], 2
                )

        for day, stats in day_distribution.items():
            if stats["posts"] > 0:
                stats["avg_engagement"] = round(
                    stats["total_engagement"] / stats["posts"], 2
                )

        # Find peak hours and days
        peak_hours = sorted(
            hour_distribution.items(),
            key=lambda x: x[1]["avg_engagement"],
            reverse=True,
        )[:5]

        peak_days = sorted(
            day_distribution.items(),
            key=lambda x: x[1]["avg_engagement"],
            reverse=True,
        )

        # === Audience Growth ===
        # Calculate growth trends over time
        end_date = to_date or datetime.now()
        start_date = from_date or (end_date - timedelta(days=30))

        # Get daily reach data
        daily_query = (
            select(
                func.date(Post.published_at).label("date"),
                func.sum(Post.views_count).label("reach"),
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

        reach_trend = [int(row.reach or 0) for row in daily_data]
        engagement_trend = [int(row.engagement or 0) for row in daily_data]

        # Calculate growth rate (comparing first half to second half of period)
        growth_rate = 0.0
        if len(reach_trend) > 1:
            midpoint = len(reach_trend) // 2
            first_half_avg = sum(reach_trend[:midpoint]) / midpoint if midpoint > 0 else 0
            second_half_avg = (
                sum(reach_trend[midpoint:]) / (len(reach_trend) - midpoint)
                if len(reach_trend) > midpoint
                else 0
            )
            if first_half_avg > 0:
                growth_rate = round(
                    ((second_half_avg - first_half_avg) / first_half_avg) * 100, 2
                )

        # === Engagement Quality ===
        # Analyze engagement quality metrics
        total_likes = sum(post.likes_count for post in posts)
        total_comments = sum(post.comments_count for post in posts)
        total_shares = sum(post.shares_count for post in posts)

        engagement_quality = {
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "likes_to_comments_ratio": round(
                total_likes / total_comments if total_comments > 0 else 0, 2
            ),
            "comments_to_shares_ratio": round(
                total_comments / total_shares if total_shares > 0 else 0, 2
            ),
            "avg_engagement_per_post": round(
                (total_likes + total_comments + total_shares) / len(posts)
                if posts
                else 0,
                2,
            ),
            "avg_engagement_rate": round(
                (total_likes + total_comments + total_shares) / total_audience_reach
                if total_audience_reach > 0
                else 0,
                4,
            ),
        }

        # === Audience Insights ===
        insights = []

        # Platform insight
        if platform_distribution:
            top_platform = max(
                platform_distribution.items(),
                key=lambda x: x[1]["audience_share"],
            )
            insights.append(
                {
                    "type": "platform",
                    "message": f"Primary audience platform: {top_platform[0]} "
                    f"({top_platform[1]['audience_share']*100:.1f}% of reach)",
                    "recommendation": f"Focus content strategy on {top_platform[0]} for maximum reach",
                }
            )

        # Content preference insight
        if content_preferences:
            top_content_type = max(
                content_preferences.items(),
                key=lambda x: x[1]["preference_score"],
            )
            if top_content_type[1]["preference_score"] > 1.0:
                insights.append(
                    {
                        "type": "content",
                        "message": f"Audience prefers {top_content_type[0]} content "
                        f"(preference score: {top_content_type[1]['preference_score']:.2f}x average)",
                        "recommendation": f"Increase {top_content_type[0]} content production",
                    }
                )

        # Activity pattern insight
        if peak_hours:
            best_hour = peak_hours[0][0]
            insights.append(
                {
                    "type": "timing",
                    "message": f"Peak audience activity at {best_hour}:00 "
                    f"(avg engagement: {peak_hours[0][1]['avg_engagement']:.0f})",
                    "recommendation": f"Schedule posts around {best_hour}:00 for maximum engagement",
                }
            )

        # Growth insight
        if growth_rate > 0:
            insights.append(
                {
                    "type": "growth",
                    "message": f"Audience reach growing at {growth_rate:.1f}% rate",
                    "recommendation": "Continue current content strategy to maintain growth",
                }
            )
        elif growth_rate < 0:
            insights.append(
                {
                    "type": "growth",
                    "message": f"Audience reach declining at {abs(growth_rate):.1f}% rate",
                    "recommendation": "Review content strategy and posting frequency",
                }
            )

        # Engagement quality insight
        if engagement_quality["comments_to_shares_ratio"] > 2.0:
            insights.append(
                {
                    "type": "engagement",
                    "message": "High comment-to-share ratio indicates engaged audience",
                    "recommendation": "Encourage more sharing to expand reach",
                }
            )

        return {
            "total_posts": len(posts),
            "total_audience_reach": total_audience_reach,
            "platform_distribution": platform_distribution,
            "engagement_patterns": {
                "by_post_type": engagement_by_type,
            },
            "content_preferences": content_preferences,
            "activity_patterns": {
                "peak_hours": [
                    {
                        "hour": hour,
                        "posts": stats["posts"],
                        "avg_engagement": stats["avg_engagement"],
                        "total_reach": stats["total_reach"],
                    }
                    for hour, stats in peak_hours
                ],
                "peak_days": [
                    {
                        "day": day,
                        "day_name": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ][day],
                        "posts": stats["posts"],
                        "avg_engagement": stats["avg_engagement"],
                        "total_reach": stats["total_reach"],
                    }
                    for day, stats in peak_days
                ],
            },
            "audience_growth": {
                "reach_trend": reach_trend,
                "engagement_trend": engagement_trend,
                "growth_rate": growth_rate,
            },
            "engagement_quality": engagement_quality,
            "audience_insights": insights,
        }

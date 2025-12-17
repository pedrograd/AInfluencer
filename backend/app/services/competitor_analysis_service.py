"""Competitor analysis service for analyzing competitor accounts and comparing metrics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.character import Character
from app.models.post import Post
from app.models.analytics import Analytics

logger = get_logger(__name__)


class CompetitorAnalysisService:
    """Service for analyzing competitor accounts and comparing metrics."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize competitor analysis service.

        Args:
            db: Database session.
        """
        self.db = db

    async def analyze_competitor(
        self,
        competitor_name: str,
        competitor_platform: str,
        competitor_metrics: dict[str, Any],
        character_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a competitor account and compare with our characters.

        Args:
            competitor_name: Name or identifier of the competitor.
            competitor_platform: Platform name (instagram, twitter, facebook, etc.).
            competitor_metrics: Dictionary containing competitor metrics:
                - follower_count: Number of followers
                - following_count: Number of following (optional)
                - post_count: Number of posts (optional)
                - engagement_rate: Average engagement rate (optional)
                - avg_likes: Average likes per post (optional)
                - avg_comments: Average comments per post (optional)
                - avg_shares: Average shares per post (optional)
            character_id: Optional character ID to compare against specific character.

        Returns:
            Dictionary containing competitor analysis including:
            - Competitor information
            - Metric comparison
            - Performance gaps
            - Recommendations
        """
        # Get our character metrics for comparison
        our_metrics = await self._get_our_metrics(
            character_id=character_id,
            platform=competitor_platform,
        )

        # Calculate performance gaps
        gaps = self._calculate_gaps(competitor_metrics, our_metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, competitor_metrics, our_metrics)

        return {
            "competitor": {
                "name": competitor_name,
                "platform": competitor_platform,
                "metrics": competitor_metrics,
            },
            "our_metrics": our_metrics,
            "comparison": {
                "gaps": gaps,
                "strengths": self._identify_strengths(our_metrics, competitor_metrics),
                "weaknesses": self._identify_weaknesses(our_metrics, competitor_metrics),
            },
            "recommendations": recommendations,
            "analysis_date": datetime.utcnow().isoformat(),
        }

    async def _get_our_metrics(
        self,
        character_id: UUID | None = None,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """
        Get our character metrics for comparison.

        Args:
            character_id: Optional character ID to filter by.
            platform: Optional platform name to filter by.

        Returns:
            Dictionary containing our metrics.
        """
        # Build query for posts
        query = select(Post).where(Post.status == "published")

        if character_id:
            query = query.where(Post.character_id == character_id)
        if platform:
            query = query.where(Post.platform == platform)

        result = await self.db.execute(query)
        posts = result.scalars().all()

        if not posts:
            return {
                "follower_count": 0,
                "post_count": 0,
                "engagement_rate": 0.0,
                "avg_likes": 0.0,
                "avg_comments": 0.0,
                "avg_shares": 0.0,
                "total_engagement": 0,
                "total_views": 0,
            }

        # Calculate metrics from posts
        total_posts = len(posts)
        total_likes = sum(post.likes_count for post in posts)
        total_comments = sum(post.comments_count for post in posts)
        total_shares = sum(post.shares_count for post in posts)
        total_views = sum(post.views_count for post in posts)
        total_engagement = total_likes + total_comments + total_shares

        avg_likes = total_likes / total_posts if total_posts > 0 else 0.0
        avg_comments = total_comments / total_posts if total_posts > 0 else 0.0
        avg_shares = total_shares / total_posts if total_posts > 0 else 0.0
        engagement_rate = (
            (total_engagement / total_views) if total_views > 0 else 0.0
        )

        # Try to get follower count from analytics
        follower_count = 0
        if character_id:
            analytics_query = (
                select(Analytics)
                .where(Analytics.character_id == character_id)
                .where(Analytics.metric_type == "follower_count")
                .where(Analytics.platform == platform if platform else True)
                .order_by(Analytics.metric_date.desc())
                .limit(1)
            )
            analytics_result = await self.db.execute(analytics_query)
            latest_analytics = analytics_result.scalar_one_or_none()
            if latest_analytics:
                follower_count = float(latest_analytics.metric_value)

        return {
            "follower_count": int(follower_count),
            "post_count": total_posts,
            "engagement_rate": round(engagement_rate, 4),
            "avg_likes": round(avg_likes, 2),
            "avg_comments": round(avg_comments, 2),
            "avg_shares": round(avg_shares, 2),
            "total_engagement": total_engagement,
            "total_views": total_views,
        }

    def _calculate_gaps(
        self,
        competitor_metrics: dict[str, Any],
        our_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate performance gaps between competitor and our metrics.

        Args:
            competitor_metrics: Competitor metrics dictionary.
            our_metrics: Our metrics dictionary.

        Returns:
            Dictionary containing gap analysis.
        """
        gaps: dict[str, Any] = {}

        # Follower count gap
        comp_followers = competitor_metrics.get("follower_count", 0)
        our_followers = our_metrics.get("follower_count", 0)
        if comp_followers > 0:
            gaps["follower_count"] = {
                "competitor": comp_followers,
                "ours": our_followers,
                "difference": comp_followers - our_followers,
                "percentage_gap": round(
                    ((comp_followers - our_followers) / comp_followers) * 100, 2
                ) if comp_followers > 0 else 0.0,
            }

        # Engagement rate gap
        comp_engagement_rate = competitor_metrics.get("engagement_rate", 0.0)
        our_engagement_rate = our_metrics.get("engagement_rate", 0.0)
        gaps["engagement_rate"] = {
            "competitor": comp_engagement_rate,
            "ours": our_engagement_rate,
            "difference": round(comp_engagement_rate - our_engagement_rate, 4),
            "percentage_gap": round(
                ((comp_engagement_rate - our_engagement_rate) / comp_engagement_rate) * 100, 2
            ) if comp_engagement_rate > 0 else 0.0,
        }

        # Average likes gap
        comp_avg_likes = competitor_metrics.get("avg_likes", 0.0)
        our_avg_likes = our_metrics.get("avg_likes", 0.0)
        gaps["avg_likes"] = {
            "competitor": comp_avg_likes,
            "ours": our_avg_likes,
            "difference": round(comp_avg_likes - our_avg_likes, 2),
            "percentage_gap": round(
                ((comp_avg_likes - our_avg_likes) / comp_avg_likes) * 100, 2
            ) if comp_avg_likes > 0 else 0.0,
        }

        # Average comments gap
        comp_avg_comments = competitor_metrics.get("avg_comments", 0.0)
        our_avg_comments = our_metrics.get("avg_comments", 0.0)
        gaps["avg_comments"] = {
            "competitor": comp_avg_comments,
            "ours": our_avg_comments,
            "difference": round(comp_avg_comments - our_avg_comments, 2),
            "percentage_gap": round(
                ((comp_avg_comments - our_avg_comments) / comp_avg_comments) * 100, 2
            ) if comp_avg_comments > 0 else 0.0,
        }

        return gaps

    def _identify_strengths(
        self,
        our_metrics: dict[str, Any],
        competitor_metrics: dict[str, Any],
    ) -> list[str]:
        """
        Identify areas where we outperform the competitor.

        Args:
            our_metrics: Our metrics dictionary.
            competitor_metrics: Competitor metrics dictionary.

        Returns:
            List of strength descriptions.
        """
        strengths: list[str] = []

        our_engagement_rate = our_metrics.get("engagement_rate", 0.0)
        comp_engagement_rate = competitor_metrics.get("engagement_rate", 0.0)
        if our_engagement_rate > comp_engagement_rate:
            strengths.append(
                f"Higher engagement rate ({our_engagement_rate:.2%} vs {comp_engagement_rate:.2%})"
            )

        our_avg_likes = our_metrics.get("avg_likes", 0.0)
        comp_avg_likes = competitor_metrics.get("avg_likes", 0.0)
        if our_avg_likes > comp_avg_likes:
            strengths.append(
                f"Higher average likes per post ({our_avg_likes:.0f} vs {comp_avg_likes:.0f})"
            )

        our_avg_comments = our_metrics.get("avg_comments", 0.0)
        comp_avg_comments = competitor_metrics.get("avg_comments", 0.0)
        if our_avg_comments > comp_avg_comments:
            strengths.append(
                f"Higher average comments per post ({our_avg_comments:.0f} vs {comp_avg_comments:.0f})"
            )

        return strengths

    def _identify_weaknesses(
        self,
        our_metrics: dict[str, Any],
        competitor_metrics: dict[str, Any],
    ) -> list[str]:
        """
        Identify areas where we underperform compared to the competitor.

        Args:
            our_metrics: Our metrics dictionary.
            competitor_metrics: Competitor metrics dictionary.

        Returns:
            List of weakness descriptions.
        """
        weaknesses: list[str] = []

        our_followers = our_metrics.get("follower_count", 0)
        comp_followers = competitor_metrics.get("follower_count", 0)
        if comp_followers > our_followers:
            gap = comp_followers - our_followers
            percentage = (gap / comp_followers) * 100 if comp_followers > 0 else 0
            weaknesses.append(
                f"Lower follower count ({our_followers:,} vs {comp_followers:,}, {percentage:.1f}% gap)"
            )

        our_engagement_rate = our_metrics.get("engagement_rate", 0.0)
        comp_engagement_rate = competitor_metrics.get("engagement_rate", 0.0)
        if comp_engagement_rate > our_engagement_rate:
            weaknesses.append(
                f"Lower engagement rate ({our_engagement_rate:.2%} vs {comp_engagement_rate:.2%})"
            )

        our_avg_likes = our_metrics.get("avg_likes", 0.0)
        comp_avg_likes = competitor_metrics.get("avg_likes", 0.0)
        if comp_avg_likes > our_avg_likes:
            weaknesses.append(
                f"Lower average likes per post ({our_avg_likes:.0f} vs {comp_avg_likes:.0f})"
            )

        our_avg_comments = our_metrics.get("avg_comments", 0.0)
        comp_avg_comments = competitor_metrics.get("avg_comments", 0.0)
        if comp_avg_comments > our_avg_comments:
            weaknesses.append(
                f"Lower average comments per post ({our_avg_comments:.0f} vs {comp_avg_comments:.0f})"
            )

        return weaknesses

    def _generate_recommendations(
        self,
        gaps: dict[str, Any],
        competitor_metrics: dict[str, Any],
        our_metrics: dict[str, Any],
    ) -> list[str]:
        """
        Generate actionable recommendations based on gap analysis.

        Args:
            gaps: Gap analysis dictionary.
            competitor_metrics: Competitor metrics dictionary.
            our_metrics: Our metrics dictionary.

        Returns:
            List of recommendation strings.
        """
        recommendations: list[str] = []

        # Follower count recommendations
        follower_gap = gaps.get("follower_count", {})
        if follower_gap.get("difference", 0) > 0:
            percentage_gap = abs(follower_gap.get("percentage_gap", 0))
            if percentage_gap > 50:
                recommendations.append(
                    "Focus on follower growth: Consider increasing posting frequency and engagement activities"
                )
            elif percentage_gap > 20:
                recommendations.append(
                    "Improve follower acquisition: Optimize content strategy and hashtag usage"
                )

        # Engagement rate recommendations
        engagement_gap = gaps.get("engagement_rate", {})
        if engagement_gap.get("difference", 0) > 0:
            recommendations.append(
                "Improve engagement rate: Analyze competitor content types and posting times"
            )
            recommendations.append(
                "Enhance content quality: Focus on creating more engaging and interactive content"
            )

        # Average likes recommendations
        likes_gap = gaps.get("avg_likes", {})
        if likes_gap.get("difference", 0) > 0:
            recommendations.append(
                "Increase post engagement: Study competitor content formats and visual styles"
            )

        # Average comments recommendations
        comments_gap = gaps.get("avg_comments", {})
        if comments_gap.get("difference", 0) > 0:
            recommendations.append(
                "Encourage more comments: Use call-to-action questions and interactive content"
            )

        # If we're performing well, provide positive reinforcement
        if not recommendations:
            recommendations.append(
                "Maintain current strategy: Performance is competitive or better"
            )

        return recommendations

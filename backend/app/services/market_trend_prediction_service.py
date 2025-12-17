"""Market trend prediction service for forecasting future trends in content, hashtags, and topics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.post import Post

logger = get_logger(__name__)


class MarketTrendPredictionService:
    """Service for predicting future market trends based on historical data."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize market trend prediction service.

        Args:
            db: Database session.
        """
        self.db = db

    async def predict_hashtag_trends(
        self,
        days_ahead: int = 7,
        historical_days: int = 60,
        platform: str | None = None,
        character_id: UUID | None = None,
        min_usage_count: int = 3,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Predict future trending hashtags based on historical patterns.

        Uses historical data to forecast which hashtags are likely to trend
        in the future based on growth patterns, engagement trends, and velocity.

        Args:
            days_ahead: Number of days into the future to predict (default: 7).
            historical_days: Number of days of historical data to analyze (default: 60).
            platform: Optional platform name to filter by.
            character_id: Optional character ID to filter by.
            min_usage_count: Minimum number of times a hashtag must appear in history.
            limit: Maximum number of predictions to return.

        Returns:
            List of predicted trending hashtags with confidence scores and forecasts.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=historical_days)

        # Divide historical period into 3 segments for trend analysis
        segment_size = historical_days / 3
        segment1_start = start_date
        segment1_end = start_date + timedelta(days=segment_size)
        segment2_start = segment1_end
        segment2_end = segment2_start + timedelta(days=segment_size)
        segment3_start = segment2_end
        segment3_end = end_date

        # Build queries for each segment
        segments = [
            (segment1_start, segment1_end),
            (segment2_start, segment2_end),
            (segment3_start, segment3_end),
        ]

        segment_data: list[dict[str, dict[str, Any]]] = []

        for seg_start, seg_end in segments:
            query = select(Post).where(Post.status == "published").where(
                Post.published_at >= seg_start
            ).where(Post.published_at < seg_end)

            if platform:
                query = query.where(Post.platform == platform)
            if character_id:
                query = query.where(Post.character_id == character_id)

            result = await self.db.execute(query)
            posts = result.scalars().all()

            hashtag_stats: dict[str, dict[str, Any]] = {}
            for post in posts:
                if post.hashtags:
                    for hashtag in post.hashtags:
                        hashtag_lower = hashtag.lower()
                        if hashtag_lower not in hashtag_stats:
                            hashtag_stats[hashtag_lower] = {
                                "hashtag": hashtag,
                                "count": 0,
                                "total_engagement": 0,
                                "total_views": 0,
                            }
                        hashtag_stats[hashtag_lower]["count"] += 1
                        engagement = post.likes_count + post.comments_count + post.shares_count
                        hashtag_stats[hashtag_lower]["total_engagement"] += engagement
                        hashtag_stats[hashtag_lower]["total_views"] += post.views_count or 0

            segment_data.append(hashtag_stats)

        # Analyze trends across segments and predict future
        predictions = []
        all_hashtags = set()
        for segment in segment_data:
            all_hashtags.update(segment.keys())

        for hashtag_lower in all_hashtags:
            # Get data for each segment
            seg1_data = segment_data[0].get(hashtag_lower, {"count": 0, "total_engagement": 0, "total_views": 0})
            seg2_data = segment_data[1].get(hashtag_lower, {"count": 0, "total_engagement": 0, "total_views": 0})
            seg3_data = segment_data[2].get(hashtag_lower, {"count": 0, "total_engagement": 0, "total_views": 0})

            total_count = seg1_data["count"] + seg2_data["count"] + seg3_data["count"]
            if total_count < min_usage_count:
                continue

            # Calculate growth rates between segments
            growth_1_to_2 = 0.0
            if seg1_data["count"] > 0:
                growth_1_to_2 = ((seg2_data["count"] - seg1_data["count"]) / seg1_data["count"]) * 100
            else:
                growth_1_to_2 = 100.0 if seg2_data["count"] > 0 else 0.0

            growth_2_to_3 = 0.0
            if seg2_data["count"] > 0:
                growth_2_to_3 = ((seg3_data["count"] - seg2_data["count"]) / seg2_data["count"]) * 100
            else:
                growth_2_to_3 = 100.0 if seg3_data["count"] > 0 else 0.0

            # Calculate average engagement trends
            avg_engagement_1 = seg1_data["total_engagement"] / seg1_data["count"] if seg1_data["count"] > 0 else 0
            avg_engagement_2 = seg2_data["total_engagement"] / seg2_data["count"] if seg2_data["count"] > 0 else 0
            avg_engagement_3 = seg3_data["total_engagement"] / seg3_data["count"] if seg3_data["count"] > 0 else 0

            engagement_growth = 0.0
            if avg_engagement_2 > 0:
                engagement_growth = ((avg_engagement_3 - avg_engagement_2) / avg_engagement_2) * 100

            # Predict future growth using linear extrapolation
            # If growth is accelerating, predict continued growth
            # If growth is decelerating, predict slower growth or plateau
            acceleration = growth_2_to_3 - growth_1_to_2

            # Predict future count (simple linear extrapolation with momentum)
            if seg3_data["count"] > 0:
                # Base prediction on recent trend
                predicted_growth_rate = growth_2_to_3
                if acceleration > 0:
                    # Accelerating trend - predict higher growth
                    predicted_growth_rate = min(growth_2_to_3 + (acceleration * 0.5), 200.0)
                elif acceleration < -10:
                    # Decelerating trend - predict slower growth or decline
                    predicted_growth_rate = max(growth_2_to_3 + (acceleration * 0.3), -50.0)

                predicted_count = seg3_data["count"] * (1 + (predicted_growth_rate / 100) * (days_ahead / segment_size))
                predicted_count = max(0, int(predicted_count))
            else:
                predicted_count = 0
                predicted_growth_rate = 0.0

            # Calculate confidence score (0.0 to 1.0)
            # Higher confidence for:
            # - Consistent growth across segments
            # - High recent usage
            # - Positive engagement trends
            confidence = 0.0

            # Consistency score (how consistent is the trend)
            if growth_1_to_2 > 0 and growth_2_to_3 > 0:
                consistency = 0.4  # Both periods show growth
            elif growth_1_to_2 < 0 and growth_2_to_3 < 0:
                consistency = 0.1  # Both periods show decline
            else:
                consistency = 0.2  # Mixed signals

            # Recent usage score
            usage_score = min(seg3_data["count"] / 20.0, 0.3)  # Cap at 0.3

            # Engagement trend score
            engagement_score = 0.0
            if engagement_growth > 0:
                engagement_score = min(engagement_growth / 100.0, 0.2)  # Cap at 0.2
            elif engagement_growth < -20:
                engagement_score = -0.1  # Penalty for declining engagement

            # Growth momentum score
            momentum_score = 0.0
            if acceleration > 0:
                momentum_score = min(acceleration / 50.0, 0.1)  # Cap at 0.1

            confidence = consistency + usage_score + engagement_score + momentum_score
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1

            # Only include predictions with positive predicted growth and reasonable confidence
            if predicted_growth_rate > 0 and confidence > 0.2:
                predictions.append({
                    "hashtag": seg3_data.get("hashtag", segment_data[2].get(hashtag_lower, {}).get("hashtag", hashtag_lower)),
                    "predicted_growth_rate": round(predicted_growth_rate, 2),
                    "predicted_usage_count": predicted_count,
                    "current_usage_count": seg3_data["count"],
                    "historical_growth_rate": round(growth_2_to_3, 2),
                    "acceleration": round(acceleration, 2),
                    "confidence": round(confidence, 4),
                    "predicted_days_ahead": days_ahead,
                    "avg_engagement": round(avg_engagement_3, 2),
                    "engagement_trend": "up" if engagement_growth > 5 else "stable" if engagement_growth > -5 else "down",
                })

        # Sort by confidence and predicted growth
        predictions.sort(key=lambda x: (x["confidence"] * 0.6 + min(x["predicted_growth_rate"] / 100.0, 1.0) * 0.4), reverse=True)

        return predictions[:limit]

    async def predict_content_type_trends(
        self,
        days_ahead: int = 7,
        historical_days: int = 60,
        platform: str | None = None,
        character_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Predict future trending content types based on historical performance.

        Args:
            days_ahead: Number of days into the future to predict.
            historical_days: Number of days of historical data to analyze.
            platform: Optional platform name to filter by.
            character_id: Optional character ID to filter by.
            limit: Maximum number of predictions to return.

        Returns:
            List of predicted trending content types with confidence scores.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=historical_days)

        # Divide into segments
        segment_size = historical_days / 3
        segment1_start = start_date
        segment1_end = start_date + timedelta(days=segment_size)
        segment2_start = segment1_end
        segment2_end = segment2_start + timedelta(days=segment_size)
        segment3_start = segment2_end
        segment3_end = end_date

        segments = [
            (segment1_start, segment1_end),
            (segment2_start, segment2_end),
            (segment3_start, segment3_end),
        ]

        segment_data: list[dict[str, dict[str, Any]]] = []

        for seg_start, seg_end in segments:
            query = select(Post).where(Post.status == "published").where(
                Post.published_at >= seg_start
            ).where(Post.published_at < seg_end)

            if platform:
                query = query.where(Post.platform == platform)
            if character_id:
                query = query.where(Post.character_id == character_id)

            result = await self.db.execute(query)
            posts = result.scalars().all()

            content_type_stats: dict[str, dict[str, Any]] = {}
            for post in posts:
                post_type = post.post_type or "unknown"
                if post_type not in content_type_stats:
                    content_type_stats[post_type] = {
                        "count": 0,
                        "total_engagement": 0,
                        "total_views": 0,
                    }
                content_type_stats[post_type]["count"] += 1
                engagement = post.likes_count + post.comments_count + post.shares_count
                content_type_stats[post_type]["total_engagement"] += engagement
                content_type_stats[post_type]["total_views"] += post.views_count or 0

            segment_data.append(content_type_stats)

        # Analyze and predict
        predictions = []
        all_types = set()
        for segment in segment_data:
            all_types.update(segment.keys())

        for content_type in all_types:
            seg1_data = segment_data[0].get(content_type, {"count": 0, "total_engagement": 0, "total_views": 0})
            seg2_data = segment_data[1].get(content_type, {"count": 0, "total_engagement": 0, "total_views": 0})
            seg3_data = segment_data[2].get(content_type, {"count": 0, "total_engagement": 0, "total_views": 0})

            if seg3_data["count"] == 0:
                continue

            # Calculate growth and engagement trends
            growth_2_to_3 = 0.0
            if seg2_data["count"] > 0:
                growth_2_to_3 = ((seg3_data["count"] - seg2_data["count"]) / seg2_data["count"]) * 100

            avg_engagement_3 = seg3_data["total_engagement"] / seg3_data["count"] if seg3_data["count"] > 0 else 0
            avg_engagement_2 = seg2_data["total_engagement"] / seg2_data["count"] if seg2_data["count"] > 0 else 0

            engagement_growth = 0.0
            if avg_engagement_2 > 0:
                engagement_growth = ((avg_engagement_3 - avg_engagement_2) / avg_engagement_2) * 100

            # Predict future performance
            predicted_growth = growth_2_to_3 if growth_2_to_3 > 0 else 0.0
            confidence = min(0.5 + (growth_2_to_3 / 100.0) * 0.3 + (engagement_growth / 100.0) * 0.2, 1.0)
            confidence = max(0.0, confidence)

            if confidence > 0.3:
                predictions.append({
                    "content_type": content_type,
                    "predicted_growth_rate": round(predicted_growth, 2),
                    "current_usage_count": seg3_data["count"],
                    "avg_engagement": round(avg_engagement_3, 2),
                    "engagement_trend": "up" if engagement_growth > 5 else "stable" if engagement_growth > -5 else "down",
                    "confidence": round(confidence, 4),
                    "predicted_days_ahead": days_ahead,
                })

        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        return predictions[:limit]

    async def get_market_trend_predictions(
        self,
        days_ahead: int = 7,
        historical_days: int = 60,
        platform: str | None = None,
        character_id: UUID | None = None,
        hashtag_limit: int = 20,
        content_type_limit: int = 10,
    ) -> dict[str, Any]:
        """
        Get comprehensive market trend predictions including hashtags and content types.

        Args:
            days_ahead: Number of days into the future to predict.
            historical_days: Number of days of historical data to analyze.
            platform: Optional platform name to filter by.
            character_id: Optional character ID to filter by.
            hashtag_limit: Maximum number of hashtag predictions.
            content_type_limit: Maximum number of content type predictions.

        Returns:
            Dictionary containing predicted trends for hashtags and content types.
        """
        hashtag_predictions = await self.predict_hashtag_trends(
            days_ahead=days_ahead,
            historical_days=historical_days,
            platform=platform,
            character_id=character_id,
            limit=hashtag_limit,
        )

        content_type_predictions = await self.predict_content_type_trends(
            days_ahead=days_ahead,
            historical_days=historical_days,
            platform=platform,
            character_id=character_id,
            limit=content_type_limit,
        )

        return {
            "prediction_date": datetime.now().isoformat(),
            "days_ahead": days_ahead,
            "historical_days": historical_days,
            "platform": platform,
            "character_id": str(character_id) if character_id else None,
            "hashtag_predictions": hashtag_predictions,
            "content_type_predictions": content_type_predictions,
            "total_hashtag_predictions": len(hashtag_predictions),
            "total_content_type_predictions": len(content_type_predictions),
        }

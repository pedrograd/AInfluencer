"""Content intelligence service for trending topics, content calendar, posting times, variations, and engagement prediction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TrendingTopic:
    """A trending topic with metadata."""

    keyword: str
    category: str  # e.g., "technology", "fashion", "lifestyle"
    trend_score: float  # 0.0 to 1.0
    growth_rate: float  # Percentage change
    related_keywords: list[str]
    estimated_reach: int | None = None
    source: str = "manual"  # "manual", "api", "scraped"


@dataclass
class ContentCalendarEntry:
    """A content calendar entry."""

    date: datetime
    character_id: UUID | None
    content_type: str  # "image", "video", "text", "audio"
    platform: str  # "instagram", "twitter", "facebook", etc.
    topic: str | None = None
    caption_template: str | None = None
    scheduled_time: datetime | None = None
    status: str = "planned"  # "planned", "generated", "scheduled", "posted"
    notes: str | None = None


@dataclass
class OptimalPostingTime:
    """Optimal posting time recommendation."""

    platform: str
    character_id: UUID | None
    day_of_week: int  # 0=Monday, 6=Sunday
    hour: int  # 0-23
    engagement_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    reasoning: str | None = None


@dataclass
class ContentVariation:
    """A variation of content."""

    base_content_id: UUID | str
    variation_type: str  # "caption", "image_style", "video_edit", "text_tone"
    variation_data: dict[str, Any]
    platform: str | None = None


@dataclass
class EngagementPrediction:
    """Engagement prediction for content."""

    content_id: UUID | str | None
    platform: str
    predicted_likes: int
    predicted_comments: int
    predicted_shares: int
    predicted_reach: int
    confidence: float  # 0.0 to 1.0
    factors: dict[str, Any]  # Factors influencing prediction


class ContentIntelligenceService:
    """Service for content intelligence features."""

    def __init__(self) -> None:
        """Initialize content intelligence service."""
        # In-memory storage for trending topics (could be moved to database)
        self._trending_topics: list[TrendingTopic] = []
        # In-memory storage for content calendar (could be moved to database)
        self._content_calendar: list[ContentCalendarEntry] = []
        # In-memory storage for posting time data (could be moved to database)
        self._posting_time_data: dict[str, list[dict[str, Any]]] = {}

    # ===== Trending Topic Analysis =====

    def analyze_trending_topics(
        self,
        category: str | None = None,
        limit: int = 10,
    ) -> list[TrendingTopic]:
        """
        Analyze trending topics.

        Args:
            category: Optional category filter
            limit: Maximum number of topics to return

        Returns:
            List of trending topics sorted by trend_score
        """
        topics = self._trending_topics.copy()

        if category:
            topics = [t for t in topics if t.category.lower() == category.lower()]

        # Sort by trend_score descending
        topics.sort(key=lambda x: x.trend_score, reverse=True)

        return topics[:limit]

    def add_trending_topic(self, topic: TrendingTopic) -> None:
        """Add a trending topic to the analysis."""
        # Remove existing topic with same keyword if exists
        self._trending_topics = [t for t in self._trending_topics if t.keyword != topic.keyword]
        self._trending_topics.append(topic)
        logger.info(f"Added trending topic: {topic.keyword} (score: {topic.trend_score})")

    def get_trending_topics_for_character(
        self,
        character_id: UUID,
        character_interests: list[str] | None = None,
        limit: int = 5,
    ) -> list[TrendingTopic]:
        """
        Get trending topics relevant to a character's interests.

        Args:
            character_id: Character UUID
            character_interests: List of character interest keywords
            limit: Maximum number of topics to return

        Returns:
            List of relevant trending topics
        """
        all_topics = self.analyze_trending_topics(limit=limit * 2)

        if not character_interests:
            return all_topics[:limit]

        # Filter topics by character interests
        relevant_topics = []
        for topic in all_topics:
            # Check if topic keyword or category matches any interest
            topic_lower = topic.keyword.lower()
            category_lower = topic.category.lower()
            for interest in character_interests:
                interest_lower = interest.lower()
                if interest_lower in topic_lower or interest_lower in category_lower:
                    relevant_topics.append(topic)
                    break

        # If not enough relevant topics, add top trending
        if len(relevant_topics) < limit:
            for topic in all_topics:
                if topic not in relevant_topics:
                    relevant_topics.append(topic)
                if len(relevant_topics) >= limit:
                    break

        return relevant_topics[:limit]

    # ===== Content Calendar Generation =====

    def generate_content_calendar(
        self,
        start_date: datetime,
        end_date: datetime,
        character_id: UUID | None = None,
        posts_per_day: int = 2,
        platforms: list[str] | None = None,
    ) -> list[ContentCalendarEntry]:
        """
        Generate a content calendar for a date range.

        Args:
            start_date: Start date for calendar
            end_date: End date for calendar
            character_id: Optional character ID
            posts_per_day: Number of posts per day
            platforms: List of platforms (default: ["instagram", "twitter"])

        Returns:
            List of content calendar entries
        """
        if platforms is None:
            platforms = ["instagram", "twitter"]

        calendar: list[ContentCalendarEntry] = []
        current_date = start_date

        content_types = ["image", "video", "text", "audio"]
        content_type_index = 0

        while current_date <= end_date:
            for platform in platforms:
                for _ in range(posts_per_day):
                    # Rotate content types
                    content_type = content_types[content_type_index % len(content_types)]
                    content_type_index += 1

                    # Default posting time: 9 AM, 2 PM, 6 PM
                    hour = 9 if len(calendar) % 3 == 0 else (14 if len(calendar) % 3 == 1 else 18)
                    scheduled_time = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)

                    entry = ContentCalendarEntry(
                        date=current_date,
                        character_id=character_id,
                        content_type=content_type,
                        platform=platform,
                        scheduled_time=scheduled_time,
                        status="planned",
                    )
                    calendar.append(entry)

            current_date += timedelta(days=1)

        # Store in service
        self._content_calendar.extend(calendar)
        logger.info(f"Generated content calendar: {len(calendar)} entries from {start_date} to {end_date}")

        return calendar

    def get_content_calendar(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        character_id: UUID | None = None,
        platform: str | None = None,
    ) -> list[ContentCalendarEntry]:
        """
        Get content calendar entries with optional filters.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            character_id: Optional character ID filter
            platform: Optional platform filter

        Returns:
            List of filtered content calendar entries
        """
        entries = self._content_calendar.copy()

        if character_id:
            entries = [e for e in entries if e.character_id == character_id]

        if platform:
            entries = [e for e in entries if e.platform.lower() == platform.lower()]

        if start_date:
            entries = [e for e in entries if e.date >= start_date]

        if end_date:
            entries = [e for e in entries if e.date <= end_date]

        # Sort by date
        entries.sort(key=lambda x: x.date)

        return entries

    def update_calendar_entry(
        self,
        entry_index: int,
        **updates: Any,
    ) -> ContentCalendarEntry | None:
        """Update a calendar entry by index."""
        if 0 <= entry_index < len(self._content_calendar):
            entry = self._content_calendar[entry_index]
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            logger.info(f"Updated calendar entry at index {entry_index}")
            return entry
        return None

    # ===== Optimal Posting Time Calculation =====

    def calculate_optimal_posting_time(
        self,
        platform: str,
        character_id: UUID | None = None,
        day_of_week: int | None = None,
    ) -> OptimalPostingTime:
        """
        Calculate optimal posting time for a platform.

        Args:
            platform: Platform name
            character_id: Optional character ID for personalized recommendations
            day_of_week: Optional specific day (0=Monday, 6=Sunday)

        Returns:
            Optimal posting time recommendation
        """
        # Default optimal times by platform (based on general social media research)
        platform_defaults: dict[str, dict[str, Any]] = {
            "instagram": {"hour": 11, "day": 1},  # Tuesday 11 AM
            "twitter": {"hour": 9, "day": 2},  # Wednesday 9 AM
            "facebook": {"hour": 13, "day": 3},  # Thursday 1 PM
            "tiktok": {"hour": 19, "day": 4},  # Friday 7 PM
            "youtube": {"hour": 14, "day": 1},  # Tuesday 2 PM
        }

        # Get platform defaults
        defaults = platform_defaults.get(platform.lower(), {"hour": 12, "day": 1})

        # If we have historical data for this character/platform, use it
        if character_id and platform in self._posting_time_data:
            historical = self._posting_time_data[platform]
            if historical:
                # Calculate average best time from historical data
                best_hour = int(sum(h.get("hour", defaults["hour"]) for h in historical) / len(historical))
                best_day = int(sum(h.get("day", defaults["day"]) for h in historical) / len(historical))
                confidence = 0.7  # Higher confidence with historical data
            else:
                best_hour = defaults["hour"]
                best_day = defaults["day"]
                confidence = 0.5  # Lower confidence without data
        else:
            best_hour = defaults["hour"]
            best_day = defaults["day"]
            confidence = 0.5

        # Override day if specified
        if day_of_week is not None:
            best_day = day_of_week

        # Calculate engagement score (simplified - would use ML in production)
        engagement_score = 0.6 + (confidence * 0.3)  # Base 0.6, up to 0.9 with confidence

        reasoning = f"Based on {'historical data' if character_id and platform in self._posting_time_data else 'platform defaults'} for {platform}"

        return OptimalPostingTime(
            platform=platform,
            character_id=character_id,
            day_of_week=best_day,
            hour=best_hour,
            engagement_score=engagement_score,
            confidence=confidence,
            reasoning=reasoning,
        )

    def record_posting_time_performance(
        self,
        platform: str,
        posting_time: datetime,
        engagement_metrics: dict[str, int],
        character_id: UUID | None = None,
    ) -> None:
        """
        Record posting time performance for learning.

        Args:
            platform: Platform name
            posting_time: When the post was made
            engagement_metrics: Dict with likes, comments, shares, reach
            character_id: Optional character ID
        """
        if platform not in self._posting_time_data:
            self._posting_time_data[platform] = []

        total_engagement = sum(engagement_metrics.values())
        self._posting_time_data[platform].append(
            {
                "hour": posting_time.hour,
                "day": posting_time.weekday(),
                "engagement": total_engagement,
                "character_id": str(character_id) if character_id else None,
            }
        )

        # Keep only last 100 entries per platform
        if len(self._posting_time_data[platform]) > 100:
            self._posting_time_data[platform] = self._posting_time_data[platform][-100:]

        logger.info(f"Recorded posting time performance for {platform} at {posting_time}")

    # ===== Content Variation System =====

    def generate_content_variations(
        self,
        base_content_id: UUID | str,
        variation_types: list[str] | None = None,
        count: int = 3,
    ) -> list[ContentVariation]:
        """
        Generate variations of content.

        Args:
            base_content_id: ID of base content
            variation_types: Types of variations (caption, image_style, video_edit, text_tone)
            count: Number of variations to generate

        Returns:
            List of content variations
        """
        if variation_types is None:
            variation_types = ["caption", "text_tone"]

        variations: list[ContentVariation] = []

        for i in range(count):
            variation_type = variation_types[i % len(variation_types)]

            if variation_type == "caption":
                variation_data = {
                    "style": ["casual", "professional", "humorous", "inspirational"][i % 4],
                    "hashtag_count": 5 + (i * 2),
                    "emoji_usage": i % 2 == 0,
                }
            elif variation_type == "text_tone":
                variation_data = {
                    "tone": ["friendly", "professional", "casual", "enthusiastic"][i % 4],
                    "length": ["short", "medium", "long"][i % 3],
                }
            elif variation_type == "image_style":
                variation_data = {
                    "style": ["natural", "vibrant", "minimalist", "dramatic"][i % 4],
                    "filter": ["none", "warm", "cool", "vintage"][i % 4],
                }
            elif variation_type == "video_edit":
                variation_data = {
                    "edit_style": ["fast_cuts", "slow_motion", "time_lapse", "normal"][i % 4],
                    "music": ["upbeat", "calm", "energetic", "none"][i % 4],
                }
            else:
                variation_data = {"variation_index": i}

            variation = ContentVariation(
                base_content_id=base_content_id,
                variation_type=variation_type,
                variation_data=variation_data,
            )
            variations.append(variation)

        logger.info(f"Generated {len(variations)} variations for content {base_content_id}")
        return variations

    def get_variation_for_platform(
        self,
        base_content_id: UUID | str,
        platform: str,
    ) -> ContentVariation | None:
        """
        Get platform-optimized variation of content.

        Args:
            base_content_id: ID of base content
            platform: Target platform

        Returns:
            Platform-optimized variation or None
        """
        # Platform-specific variation preferences
        platform_preferences: dict[str, dict[str, Any]] = {
            "instagram": {"variation_type": "caption", "hashtag_count": 10, "emoji": True},
            "twitter": {"variation_type": "text_tone", "length": "short", "hashtag_count": 2},
            "facebook": {"variation_type": "text_tone", "length": "medium"},
            "tiktok": {"variation_type": "video_edit", "edit_style": "fast_cuts"},
        }

        prefs = platform_preferences.get(platform.lower(), {})
        variation_type = prefs.get("variation_type", "caption")

        variation_data = prefs.copy()
        variation_data.pop("variation_type", None)

        return ContentVariation(
            base_content_id=base_content_id,
            variation_type=variation_type,
            variation_data=variation_data,
            platform=platform,
        )

    # ===== Engagement Prediction =====

    def predict_engagement(
        self,
        platform: str,
        content_type: str,
        character_id: UUID | None = None,
        content_metadata: dict[str, Any] | None = None,
    ) -> EngagementPrediction:
        """
        Predict engagement for content.

        Args:
            platform: Platform name
            content_type: Type of content (image, video, text, audio)
            character_id: Optional character ID
            content_metadata: Optional content metadata (hashtags, caption_length, etc.)

        Returns:
            Engagement prediction
        """
        # Base predictions by platform and content type (simplified model)
        base_predictions: dict[str, dict[str, dict[str, int]]] = {
            "instagram": {
                "image": {"likes": 500, "comments": 50, "shares": 20, "reach": 2000},
                "video": {"likes": 800, "comments": 80, "shares": 40, "reach": 3000},
                "text": {"likes": 300, "comments": 30, "shares": 10, "reach": 1500},
            },
            "twitter": {
                "text": {"likes": 200, "comments": 40, "shares": 100, "reach": 5000},
                "image": {"likes": 300, "comments": 50, "shares": 150, "reach": 6000},
                "video": {"likes": 400, "comments": 60, "shares": 200, "reach": 8000},
            },
            "facebook": {
                "text": {"likes": 100, "comments": 20, "shares": 30, "reach": 2000},
                "image": {"likes": 150, "comments": 25, "shares": 40, "reach": 2500},
                "video": {"likes": 200, "comments": 30, "shares": 50, "reach": 3000},
            },
        }

        # Get base prediction
        platform_data = base_predictions.get(platform.lower(), {})
        content_data = platform_data.get(content_type, {"likes": 100, "comments": 10, "shares": 5, "reach": 500})

        predicted_likes = content_data["likes"]
        predicted_comments = content_data["comments"]
        predicted_shares = content_data["shares"]
        predicted_reach = content_data["reach"]

        # Adjust based on metadata if provided
        factors: dict[str, Any] = {}
        if content_metadata:
            # Hashtags boost
            hashtag_count = content_metadata.get("hashtag_count", 0)
            if hashtag_count > 0:
                boost = min(hashtag_count * 0.05, 0.3)  # Up to 30% boost
                predicted_likes = int(predicted_likes * (1 + boost))
                predicted_reach = int(predicted_reach * (1 + boost))
                factors["hashtag_boost"] = boost

            # Caption length boost (medium length is best)
            caption_length = content_metadata.get("caption_length", 0)
            if 50 <= caption_length <= 200:
                boost = 0.15
                predicted_likes = int(predicted_likes * (1 + boost))
                factors["caption_length_boost"] = boost

            # Trending topic boost
            if content_metadata.get("trending_topic", False):
                boost = 0.25
                predicted_likes = int(predicted_likes * (1 + boost))
                predicted_reach = int(predicted_reach * (1 + boost))
                factors["trending_topic_boost"] = boost

        # Calculate confidence (simplified - would use ML model in production)
        confidence = 0.6  # Base confidence
        if character_id:
            confidence += 0.1  # Higher confidence with character context
        if content_metadata:
            confidence += 0.1  # Higher confidence with metadata

        confidence = min(confidence, 0.9)  # Cap at 0.9

        factors["base_prediction"] = content_data
        factors["platform"] = platform
        factors["content_type"] = content_type

        return EngagementPrediction(
            content_id=None,
            platform=platform,
            predicted_likes=predicted_likes,
            predicted_comments=predicted_comments,
            predicted_shares=predicted_shares,
            predicted_reach=predicted_reach,
            confidence=confidence,
            factors=factors,
        )

    def update_engagement_prediction_with_actual(
        self,
        prediction: EngagementPrediction,
        actual_metrics: dict[str, int],
    ) -> None:
        """
        Update engagement prediction model with actual results (for learning).

        Args:
            prediction: Original prediction
            actual_metrics: Actual engagement metrics
        """
        # In a production system, this would update an ML model
        # For now, just log the comparison
        logger.info(
            f"Engagement prediction vs actual for {prediction.platform}: "
            f"predicted={prediction.predicted_likes} likes, "
            f"actual={actual_metrics.get('likes', 0)} likes"
        )


# Global service instance
content_intelligence_service = ContentIntelligenceService()


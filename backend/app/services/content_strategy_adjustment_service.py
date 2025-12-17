"""Content strategy adjustment service for automated strategy optimization based on analytics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.automation_rule import AutomationRule
from app.services.engagement_analytics_service import EngagementAnalyticsService

logger = get_logger(__name__)


class ContentStrategyAdjustmentError(RuntimeError):
    """Error raised when content strategy adjustment operations fail."""

    pass


class ContentStrategyAdjustmentService:
    """Service for automatically adjusting content strategy based on analytics."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize content strategy adjustment service.

        Args:
            db: Database session.
        """
        self.db = db
        self.analytics_service = EngagementAnalyticsService(db)

    async def adjust_strategy_for_character(
        self,
        character_id: UUID,
        platform: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        min_posts_required: int = 10,
    ) -> dict[str, Any]:
        """
        Automatically adjust content strategy for a character based on analytics.

        Args:
            character_id: Character ID to adjust strategy for.
            platform: Optional platform to filter analysis by.
            from_date: Optional start date for analysis period.
            to_date: Optional end date for analysis period.
            min_posts_required: Minimum number of posts required for adjustment (default: 10).

        Returns:
            Dictionary containing adjustment results and recommendations.

        Raises:
            ContentStrategyAdjustmentError: If adjustment fails.
        """
        try:
            # Get best-performing content analysis
            analysis = await self.analytics_service.get_best_performing_content_analysis(
                character_id=character_id,
                platform=platform,
                from_date=from_date,
                to_date=to_date,
                limit=50,
            )

            # Check if we have enough data
            if analysis["total_posts_analyzed"] < min_posts_required:
                return {
                    "adjusted": False,
                    "reason": f"Insufficient data: {analysis['total_posts_analyzed']} posts (minimum: {min_posts_required})",
                    "analysis": analysis,
                }

            adjustments: dict[str, Any] = {
                "character_id": str(character_id),
                "platform": platform,
                "adjusted_at": datetime.now().isoformat(),
                "adjustments": {},
                "recommendations": analysis.get("recommendations", []),
            }

            # Adjust automation rules based on best posting times
            posting_time_adjustments = await self._adjust_posting_times(
                character_id, analysis.get("posting_time_analysis", {})
            )
            if posting_time_adjustments:
                adjustments["adjustments"]["posting_times"] = posting_time_adjustments

            # Adjust content type preferences
            content_type_adjustments = self._adjust_content_type_preferences(
                analysis.get("content_type_analysis", {})
            )
            if content_type_adjustments:
                adjustments["adjustments"]["content_types"] = content_type_adjustments

            # Adjust hashtag strategy
            hashtag_adjustments = self._adjust_hashtag_strategy(
                analysis.get("hashtag_analysis", [])
            )
            if hashtag_adjustments:
                adjustments["adjustments"]["hashtags"] = hashtag_adjustments

            # Adjust caption length preferences
            caption_adjustments = self._adjust_caption_preferences(
                analysis.get("caption_analysis", {})
            )
            if caption_adjustments:
                adjustments["adjustments"]["caption"] = caption_adjustments

            # Adjust platform focus
            platform_adjustments = self._adjust_platform_focus(
                analysis.get("platform_analysis", {})
            )
            if platform_adjustments:
                adjustments["adjustments"]["platforms"] = platform_adjustments

            adjustments["adjusted"] = len(adjustments["adjustments"]) > 0

            logger.info(
                f"Adjusted content strategy for character {character_id}: "
                f"{len(adjustments['adjustments'])} adjustment categories"
            )

            return adjustments

        except Exception as exc:
            logger.error(f"Failed to adjust content strategy for character {character_id}: {exc}")
            raise ContentStrategyAdjustmentError(
                f"Failed to adjust content strategy: {exc}"
            ) from exc

    async def _adjust_posting_times(
        self, character_id: UUID, posting_time_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Adjust automation rule posting times based on best-performing hours/days.

        Args:
            character_id: Character ID.
            posting_time_analysis: Analysis data with best hours and days.

        Returns:
            Dictionary with adjustment results.
        """
        adjustments: dict[str, Any] = {
            "rules_updated": 0,
            "best_hours": [],
            "best_days": [],
        }

        best_hours = posting_time_analysis.get("best_hours", [])
        best_days = posting_time_analysis.get("best_days", [])

        if not best_hours and not best_days:
            return adjustments

        # Extract best hours and days
        if best_hours:
            top_hours = [h["hour"] for h in best_hours[:3]]  # Top 3 hours
            adjustments["best_hours"] = top_hours

        if best_days:
            top_days = [d["day"] for d in best_days[:3]]  # Top 3 days
            adjustments["best_days"] = top_days

        # Find automation rules for this character that use schedule triggers
        query = select(AutomationRule).where(
            AutomationRule.character_id == character_id,
            AutomationRule.trigger_type == "schedule",
            AutomationRule.is_enabled == True,
        )
        result = await self.db.execute(query)
        rules = result.scalars().all()

        updated_count = 0
        for rule in rules:
            trigger_config = rule.trigger_config or {}

            # Update cron schedule if best hours are available
            if best_hours and "cron" in trigger_config:
                # Update cron to use best hours (simplified - would need proper cron parsing)
                # For now, store best hours in trigger_config for reference
                trigger_config["optimal_hours"] = top_hours
                trigger_config["last_adjusted_at"] = datetime.now().isoformat()

            # Update schedule days if best days are available
            if best_days and "days" in trigger_config:
                trigger_config["optimal_days"] = top_days
                trigger_config["last_adjusted_at"] = datetime.now().isoformat()

            # Only update if we made changes
            if "optimal_hours" in trigger_config or "optimal_days" in trigger_config:
                rule.trigger_config = trigger_config
                updated_count += 1

        if updated_count > 0:
            await self.db.commit()
            adjustments["rules_updated"] = updated_count
            logger.info(
                f"Updated {updated_count} automation rules with optimal posting times "
                f"for character {character_id}"
            )

        return adjustments

    def _adjust_content_type_preferences(
        self, content_type_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Determine optimal content type preferences based on performance.

        Args:
            content_type_analysis: Analysis data with content type performance.

        Returns:
            Dictionary with content type preferences.
        """
        if not content_type_analysis:
            return {}

        # Find best performing content type
        best_type = max(
            content_type_analysis.items(),
            key=lambda x: x[1].get("avg_engagement", 0),
        )

        # Calculate distribution percentages based on performance
        total_engagement = sum(
            stats.get("avg_engagement", 0) for stats in content_type_analysis.values()
        )

        preferences: dict[str, Any] = {
            "recommended_types": [],
            "distribution": {},
        }

        # Recommend top 3 content types
        sorted_types = sorted(
            content_type_analysis.items(),
            key=lambda x: x[1].get("avg_engagement", 0),
            reverse=True,
        )[:3]

        for content_type, stats in sorted_types:
            engagement = stats.get("avg_engagement", 0)
            percentage = (
                round((engagement / total_engagement * 100), 1) if total_engagement > 0 else 0
            )
            preferences["recommended_types"].append(
                {
                    "type": content_type,
                    "avg_engagement": stats.get("avg_engagement", 0),
                    "recommended_percentage": percentage,
                }
            )
            preferences["distribution"][content_type] = percentage

        preferences["primary_type"] = best_type[0]
        preferences["primary_avg_engagement"] = best_type[1].get("avg_engagement", 0)

        return preferences

    def _adjust_hashtag_strategy(
        self, hashtag_analysis: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Determine optimal hashtag strategy based on performance.

        Args:
            hashtag_analysis: Analysis data with hashtag performance.

        Returns:
            Dictionary with hashtag strategy recommendations.
        """
        if not hashtag_analysis:
            return {}

        # Get top performing hashtags
        top_hashtags = [
            {
                "hashtag": h["hashtag"],
                "avg_engagement": h["avg_engagement"],
                "count": h["count"],
            }
            for h in hashtag_analysis[:10]  # Top 10
        ]

        return {
            "recommended_hashtags": top_hashtags,
            "primary_hashtags": [h["hashtag"] for h in top_hashtags[:5]],  # Top 5
            "hashtag_count_recommendation": min(len(top_hashtags), 10),  # Use up to 10
        }

    def _adjust_caption_preferences(
        self, caption_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Determine optimal caption length preferences based on performance.

        Args:
            caption_analysis: Analysis data with caption performance.

        Returns:
            Dictionary with caption preferences.
        """
        if not caption_analysis:
            return {}

        optimal_range = caption_analysis.get("optimal_range", {})
        avg_length = caption_analysis.get("avg_length", 0)

        if not optimal_range or optimal_range.get("min", 0) == 0:
            return {}

        return {
            "optimal_length_min": optimal_range.get("min", 0),
            "optimal_length_max": optimal_range.get("max", 0),
            "target_length": round((optimal_range.get("min", 0) + optimal_range.get("max", 0)) / 2),
            "current_avg_length": round(avg_length, 0),
        }

    def _adjust_platform_focus(
        self, platform_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Determine optimal platform focus based on performance.

        Args:
            platform_analysis: Analysis data with platform performance.

        Returns:
            Dictionary with platform focus recommendations.
        """
        if not platform_analysis:
            return {}

        # Find best performing platform
        best_platform = max(
            platform_analysis.items(),
            key=lambda x: x[1].get("avg_engagement", 0),
        )

        # Calculate platform priorities
        sorted_platforms = sorted(
            platform_analysis.items(),
            key=lambda x: x[1].get("avg_engagement", 0),
            reverse=True,
        )

        platform_priorities = [
            {
                "platform": platform,
                "avg_engagement": stats.get("avg_engagement", 0),
                "avg_engagement_rate": stats.get("avg_engagement_rate", 0),
                "post_count": stats.get("count", 0),
                "priority": idx + 1,
            }
            for idx, (platform, stats) in enumerate(sorted_platforms)
        ]

        return {
            "primary_platform": best_platform[0],
            "primary_avg_engagement": best_platform[1].get("avg_engagement", 0),
            "platform_priorities": platform_priorities,
            "recommendation": f"Focus content distribution on {best_platform[0]} for maximum engagement",
        }

    async def get_strategy_recommendations(
        self,
        character_id: UUID,
        platform: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get strategy recommendations without applying adjustments.

        Args:
            character_id: Character ID.
            platform: Optional platform to filter by.
            from_date: Optional start date for analysis period.
            to_date: Optional end date for analysis period.

        Returns:
            Dictionary with recommendations.
        """
        analysis = await self.analytics_service.get_best_performing_content_analysis(
            character_id=character_id,
            platform=platform,
            from_date=from_date,
            to_date=to_date,
            limit=50,
        )

        recommendations: dict[str, Any] = {
            "character_id": str(character_id),
            "platform": platform,
            "analysis_period": {
                "from": from_date.isoformat() if from_date else None,
                "to": to_date.isoformat() if to_date else None,
            },
            "total_posts_analyzed": analysis["total_posts_analyzed"],
            "recommendations": analysis.get("recommendations", []),
            "content_type_preferences": self._adjust_content_type_preferences(
                analysis.get("content_type_analysis", {})
            ),
            "hashtag_strategy": self._adjust_hashtag_strategy(
                analysis.get("hashtag_analysis", [])
            ),
            "caption_preferences": self._adjust_caption_preferences(
                analysis.get("caption_analysis", {})
            ),
            "platform_focus": self._adjust_platform_focus(
                analysis.get("platform_analysis", {})
            ),
        }

        return recommendations

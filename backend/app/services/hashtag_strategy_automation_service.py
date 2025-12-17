"""Hashtag strategy automation service for automatically selecting and applying hashtag strategies."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.automation_rule import AutomationRule
from app.services.content_strategy_adjustment_service import ContentStrategyAdjustmentService

logger = get_logger(__name__)


class HashtagStrategyAutomationError(RuntimeError):
    """Error raised when hashtag strategy automation operations fail."""

    pass


class HashtagStrategyAutomationService:
    """Service for automatically selecting and applying hashtag strategies based on performance."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize hashtag strategy automation service.

        Args:
            db: Database session.
        """
        self.db = db
        self.strategy_service = ContentStrategyAdjustmentService(db)

    async def apply_hashtag_strategy_to_character(
        self,
        character_id: UUID,
        platform: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        min_posts_required: int = 10,
    ) -> dict[str, Any]:
        """
        Automatically apply hashtag strategy to a character's automation rules and content generation.

        Retrieves hashtag strategy recommendations from analytics and applies them to:
        - Automation rules (stores recommended hashtags in action_config)
        - Content generation preferences (for future use)

        Args:
            character_id: Character ID to apply strategy for.
            platform: Optional platform to filter analysis by.
            from_date: Optional start date for analysis period.
            to_date: Optional end date for analysis period.
            min_posts_required: Minimum number of posts required for strategy (default: 10).

        Returns:
            Dictionary containing application results.

        Raises:
            HashtagStrategyAutomationError: If application fails.
        """
        try:
            # Get hashtag strategy recommendations
            recommendations = await self.strategy_service.get_strategy_recommendations(
                character_id=character_id,
                platform=platform,
                from_date=from_date,
                to_date=to_date,
            )

            hashtag_strategy = recommendations.get("hashtag_strategy", {})
            if not hashtag_strategy:
                return {
                    "applied": False,
                    "reason": "No hashtag strategy recommendations available",
                    "recommendations": recommendations,
                }

            # Check if we have enough data
            total_posts = recommendations.get("total_posts_analyzed", 0)
            if total_posts < min_posts_required:
                return {
                    "applied": False,
                    "reason": f"Insufficient data: {total_posts} posts (minimum: {min_posts_required})",
                    "recommendations": recommendations,
                }

            # Apply to automation rules
            automation_results = await self._apply_to_automation_rules(
                character_id, hashtag_strategy, platform
            )

            # Prepare result
            result: dict[str, Any] = {
                "character_id": str(character_id),
                "platform": platform,
                "applied_at": datetime.now().isoformat(),
                "applied": True,
                "hashtag_strategy": hashtag_strategy,
                "automation_rules_updated": automation_results.get("rules_updated", 0),
                "recommended_hashtags": hashtag_strategy.get("recommended_hashtags", []),
                "primary_hashtags": hashtag_strategy.get("primary_hashtags", []),
                "hashtag_count_recommendation": hashtag_strategy.get(
                    "hashtag_count_recommendation", 10
                ),
            }

            logger.info(
                f"Applied hashtag strategy to character {character_id}: "
                f"{automation_results.get('rules_updated', 0)} rules updated"
            )

            return result

        except Exception as exc:
            logger.error(
                f"Failed to apply hashtag strategy for character {character_id}: {exc}"
            )
            raise HashtagStrategyAutomationError(
                f"Failed to apply hashtag strategy: {exc}"
            ) from exc

    async def _apply_to_automation_rules(
        self,
        character_id: UUID,
        hashtag_strategy: dict[str, Any],
        platform: str | None = None,
    ) -> dict[str, Any]:
        """
        Apply hashtag strategy to automation rules.

        Stores recommended hashtags in automation rule action_config for use in
        engagement automation (likes, comments on posts with specific hashtags).

        Args:
            character_id: Character ID.
            hashtag_strategy: Hashtag strategy recommendations.
            platform: Optional platform filter.

        Returns:
            Dictionary with update results.
        """
        # Find automation rules for this character
        query = select(AutomationRule).where(
            AutomationRule.character_id == character_id,
            AutomationRule.is_enabled == True,
        )

        if platform:
            query = query.where(AutomationRule.platforms.contains([platform]))

        result = await self.db.execute(query)
        rules = result.scalars().all()

        updated_count = 0
        primary_hashtags = hashtag_strategy.get("primary_hashtags", [])
        recommended_hashtags = hashtag_strategy.get("recommended_hashtags", [])

        for rule in rules:
            action_config = rule.action_config or {}

            # Store hashtag strategy in action_config
            if "hashtag_strategy" not in action_config:
                action_config["hashtag_strategy"] = {}

            action_config["hashtag_strategy"].update(
                {
                    "primary_hashtags": primary_hashtags,
                    "recommended_hashtags": [
                        h.get("hashtag", h) if isinstance(h, dict) else h
                        for h in recommended_hashtags[:10]
                    ],
                    "hashtag_count": hashtag_strategy.get("hashtag_count_recommendation", 10),
                    "last_updated": datetime.now().isoformat(),
                }
            )

            rule.action_config = action_config
            updated_count += 1

        if updated_count > 0:
            await self.db.commit()
            logger.info(
                f"Updated {updated_count} automation rules with hashtag strategy "
                f"for character {character_id}"
            )

        return {"rules_updated": updated_count}

    async def get_recommended_hashtags_for_character(
        self,
        character_id: UUID,
        platform: str | None = None,
        count: int | None = None,
        use_primary_only: bool = False,
    ) -> list[str]:
        """
        Get recommended hashtags for a character based on performance analytics.

        Args:
            character_id: Character ID.
            platform: Optional platform to filter by.
            count: Number of hashtags to return (default: use recommendation from strategy).
            use_primary_only: If True, return only primary hashtags (top 5).

        Returns:
            List of recommended hashtag strings (without # prefix).
        """
        try:
            # Get strategy recommendations (use last 30 days by default)
            to_date = datetime.now()
            from_date = to_date - timedelta(days=30)

            recommendations = await self.strategy_service.get_strategy_recommendations(
                character_id=character_id,
                platform=platform,
                from_date=from_date,
                to_date=to_date,
            )

            hashtag_strategy = recommendations.get("hashtag_strategy", {})
            if not hashtag_strategy:
                logger.warning(
                    f"No hashtag strategy available for character {character_id}, "
                    "returning empty list"
                )
                return []

            if use_primary_only:
                hashtags = hashtag_strategy.get("primary_hashtags", [])
            else:
                recommended = hashtag_strategy.get("recommended_hashtags", [])
                hashtags = [
                    h.get("hashtag", h) if isinstance(h, dict) else h for h in recommended
                ]

            # Apply count limit if specified
            if count is not None:
                hashtags = hashtags[:count]
            else:
                # Use recommendation from strategy
                recommended_count = hashtag_strategy.get("hashtag_count_recommendation", 10)
                hashtags = hashtags[:recommended_count]

            return hashtags

        except Exception as exc:
            logger.error(
                f"Failed to get recommended hashtags for character {character_id}: {exc}"
            )
            return []

    async def get_hashtag_strategy_from_rule(
        self, automation_rule_id: UUID
    ) -> dict[str, Any] | None:
        """
        Get hashtag strategy stored in an automation rule.

        Args:
            automation_rule_id: Automation rule ID.

        Returns:
            Dictionary with hashtag strategy or None if not found.
        """
        query = select(AutomationRule).where(AutomationRule.id == automation_rule_id)
        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            return None

        action_config = rule.action_config or {}
        return action_config.get("hashtag_strategy")

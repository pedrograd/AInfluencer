"""Automation rule service for managing engagement automation rules."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.automation_rule import AutomationRule

logger = get_logger(__name__)


class AutomationRuleServiceError(RuntimeError):
    """Error raised when automation rule operations fail."""

    pass


class AutomationRuleService:
    """Service for managing automation rules."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize automation rule service.

        Args:
            db: Database session for accessing automation rules.
        """
        self.db = db

    async def create_rule(
        self,
        character_id: UUID,
        name: str,
        trigger_type: str,
        trigger_config: dict,
        action_type: str,
        action_config: dict,
        platforms: list[str],
        platform_account_id: UUID | None = None,
        description: str | None = None,
        is_enabled: bool = True,
        max_executions_per_day: int | None = None,
        max_executions_per_week: int | None = None,
        cooldown_minutes: int = 60,
    ) -> AutomationRule:
        """
        Create a new automation rule.

        Args:
            character_id: Character ID this rule belongs to.
            name: Rule name.
            trigger_type: Trigger type (schedule, event, manual).
            trigger_config: Trigger configuration (JSONB).
            action_type: Action type (comment, like, follow).
            action_config: Action configuration (JSONB).
            platforms: List of platform names.
            platform_account_id: Optional platform account ID.
            description: Optional rule description.
            is_enabled: Whether rule is enabled (default: True).
            max_executions_per_day: Maximum executions per day (optional).
            max_executions_per_week: Maximum executions per week (optional).
            cooldown_minutes: Cooldown between executions in minutes (default: 60).

        Returns:
            Created AutomationRule object.

        Raises:
            AutomationRuleServiceError: If creation fails.
        """
        try:
            rule = AutomationRule(
                character_id=character_id,
                platform_account_id=platform_account_id,
                name=name,
                description=description,
                is_enabled=is_enabled,
                trigger_type=trigger_type,
                trigger_config=trigger_config,
                action_type=action_type,
                action_config=action_config,
                platforms=platforms,
                max_executions_per_day=max_executions_per_day,
                max_executions_per_week=max_executions_per_week,
                cooldown_minutes=cooldown_minutes,
            )

            self.db.add(rule)
            await self.db.commit()
            await self.db.refresh(rule)

            logger.info(f"Created automation rule {rule.id} for character {character_id}")
            return rule
        except Exception as exc:
            await self.db.rollback()
            logger.error(f"Failed to create automation rule: {exc}")
            raise AutomationRuleServiceError(f"Failed to create automation rule: {exc}") from exc

    async def get_rule(self, rule_id: UUID) -> AutomationRule | None:
        """
        Get automation rule by ID.

        Args:
            rule_id: Automation rule UUID.

        Returns:
            AutomationRule object or None if not found.
        """
        result = await self.db.execute(
            select(AutomationRule).where(AutomationRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def list_rules(
        self,
        character_id: UUID | None = None,
        platform_account_id: UUID | None = None,
        is_enabled: bool | None = None,
        action_type: str | None = None,
    ) -> list[AutomationRule]:
        """
        List automation rules with optional filters.

        Args:
            character_id: Filter by character ID (optional).
            platform_account_id: Filter by platform account ID (optional).
            is_enabled: Filter by enabled status (optional).
            action_type: Filter by action type (optional).

        Returns:
            List of AutomationRule objects.
        """
        query = select(AutomationRule)

        if character_id:
            query = query.where(AutomationRule.character_id == character_id)
        if platform_account_id:
            query = query.where(AutomationRule.platform_account_id == platform_account_id)
        if is_enabled is not None:
            query = query.where(AutomationRule.is_enabled == is_enabled)
        if action_type:
            query = query.where(AutomationRule.action_type == action_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_rule(
        self,
        rule_id: UUID,
        name: str | None = None,
        description: str | None = None,
        is_enabled: bool | None = None,
        trigger_type: str | None = None,
        trigger_config: dict | None = None,
        action_type: str | None = None,
        action_config: dict | None = None,
        platforms: list[str] | None = None,
        max_executions_per_day: int | None = None,
        max_executions_per_week: int | None = None,
        cooldown_minutes: int | None = None,
    ) -> AutomationRule:
        """
        Update an automation rule.

        Args:
            rule_id: Automation rule UUID.
            name: New rule name (optional).
            description: New rule description (optional).
            is_enabled: New enabled status (optional).
            trigger_type: New trigger type (optional).
            trigger_config: New trigger configuration (optional).
            action_type: New action type (optional).
            action_config: New action configuration (optional).
            platforms: New platforms list (optional).
            max_executions_per_day: New max executions per day (optional).
            max_executions_per_week: New max executions per week (optional).
            cooldown_minutes: New cooldown minutes (optional).

        Returns:
            Updated AutomationRule object.

        Raises:
            AutomationRuleServiceError: If rule not found or update fails.
        """
        rule = await self.get_rule(rule_id)
        if not rule:
            raise AutomationRuleServiceError(f"Automation rule {rule_id} not found")

        try:
            if name is not None:
                rule.name = name
            if description is not None:
                rule.description = description
            if is_enabled is not None:
                rule.is_enabled = is_enabled
            if trigger_type is not None:
                rule.trigger_type = trigger_type
            if trigger_config is not None:
                rule.trigger_config = trigger_config
            if action_type is not None:
                rule.action_type = action_type
            if action_config is not None:
                rule.action_config = action_config
            if platforms is not None:
                rule.platforms = platforms
            if max_executions_per_day is not None:
                rule.max_executions_per_day = max_executions_per_day
            if max_executions_per_week is not None:
                rule.max_executions_per_week = max_executions_per_week
            if cooldown_minutes is not None:
                rule.cooldown_minutes = cooldown_minutes

            await self.db.commit()
            await self.db.refresh(rule)

            logger.info(f"Updated automation rule {rule_id}")
            return rule
        except Exception as exc:
            await self.db.rollback()
            logger.error(f"Failed to update automation rule {rule_id}: {exc}")
            raise AutomationRuleServiceError(f"Failed to update automation rule: {exc}") from exc

    async def delete_rule(self, rule_id: UUID) -> None:
        """
        Delete an automation rule.

        Args:
            rule_id: Automation rule UUID.

        Raises:
            AutomationRuleServiceError: If rule not found or deletion fails.
        """
        rule = await self.get_rule(rule_id)
        if not rule:
            raise AutomationRuleServiceError(f"Automation rule {rule_id} not found")

        try:
            await self.db.delete(rule)
            await self.db.commit()
            logger.info(f"Deleted automation rule {rule_id}")
        except Exception as exc:
            await self.db.rollback()
            logger.error(f"Failed to delete automation rule {rule_id}: {exc}")
            raise AutomationRuleServiceError(f"Failed to delete automation rule: {exc}") from exc

    async def get_enabled_rules_for_scheduling(self) -> list[AutomationRule]:
        """
        Get all enabled automation rules that are scheduled (for scheduler).

        Returns:
            List of enabled AutomationRule objects with trigger_type='schedule'.
        """
        result = await self.db.execute(
            select(AutomationRule).where(
                AutomationRule.is_enabled == True,  # noqa: E712
                AutomationRule.trigger_type == "schedule",
            )
        )
        return list(result.scalars().all())


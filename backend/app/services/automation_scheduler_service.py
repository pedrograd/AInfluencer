"""Automation scheduler service for executing automation rules."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.automation_rule_service import AutomationRuleService
from app.services.human_timing_service import HumanTimingService
from app.services.integrated_engagement_service import IntegratedEngagementService

logger = get_logger(__name__)


class AutomationSchedulerError(RuntimeError):
    """Error raised when automation scheduler operations fail."""

    pass


class AutomationSchedulerService:
    """Service for executing automation rules."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize automation scheduler service.

        Args:
            db: Database session for accessing automation rules and platform accounts.
        """
        self.db = db
        self.rule_service = AutomationRuleService(db)
        self.engagement_service = IntegratedEngagementService(db)
        self.timing_service = HumanTimingService()

    async def can_execute_rule(self, rule_id: UUID) -> tuple[bool, str]:
        """
        Check if an automation rule can be executed (cooldown, limits, etc.).

        Args:
            rule_id: Automation rule UUID.

        Returns:
            Tuple of (can_execute: bool, reason: str).
        """
        rule = await self.rule_service.get_rule(rule_id)
        if not rule:
            return False, "Rule not found"

        if not rule.is_enabled:
            return False, "Rule is disabled"

        # Check cooldown
        if rule.last_executed_at:
            cooldown_end = rule.last_executed_at + timedelta(minutes=rule.cooldown_minutes)
            if datetime.now(rule.last_executed_at.tzinfo) < cooldown_end:
                return False, f"Cooldown active until {cooldown_end}"

        # Check daily limit
        if rule.max_executions_per_day:
            # This is simplified - in production, you'd track executions per day
            # For now, we'll allow if last execution was more than 24 hours ago
            if rule.last_executed_at:
                day_ago = datetime.now(rule.last_executed_at.tzinfo) - timedelta(days=1)
                if rule.last_executed_at > day_ago and rule.times_executed >= rule.max_executions_per_day:
                    return False, "Daily execution limit reached"

        # Check weekly limit
        if rule.max_executions_per_week:
            # This is simplified - in production, you'd track executions per week
            # For now, we'll allow if last execution was more than 7 days ago
            if rule.last_executed_at:
                week_ago = datetime.now(rule.last_executed_at.tzinfo) - timedelta(days=7)
                if rule.last_executed_at > week_ago and rule.times_executed >= rule.max_executions_per_week:
                    return False, "Weekly execution limit reached"

        return True, "OK"

    async def execute_rule(self, rule_id: UUID, platform_account_id: UUID | None = None) -> dict:
        """
        Execute an automation rule.

        Args:
            rule_id: Automation rule UUID.
            platform_account_id: Optional platform account ID (if not specified, uses rule's platform_account_id).

        Returns:
            Dictionary with execution result.

        Raises:
            AutomationSchedulerError: If execution fails.
        """
        rule = await self.rule_service.get_rule(rule_id)
        if not rule:
            raise AutomationSchedulerError(f"Automation rule {rule_id} not found")

        # Check if rule can be executed
        can_execute, reason = await self.can_execute_rule(rule_id)
        if not can_execute:
            raise AutomationSchedulerError(f"Cannot execute rule: {reason}")

        # Determine platform account ID
        target_account_id = platform_account_id or rule.platform_account_id
        if not target_account_id:
            raise AutomationSchedulerError("No platform account specified for rule execution")

        # Check if action should be skipped based on human-like activity patterns
        if self.timing_service.should_skip_action():
            logger.info(
                f"Skipping rule {rule_id} execution due to low activity probability (human-like pattern)"
            )
            raise AutomationSchedulerError("Action skipped due to human-like activity pattern")

        try:
            # Wait for human-like delay before executing action
            await self.timing_service.wait_engagement_delay(action_type=rule.action_type)

            # Execute action based on action_type
            result = None
            if rule.action_type == "comment":
                result = await self._execute_comment_action(rule, target_account_id)
            elif rule.action_type == "like":
                result = await self._execute_like_action(rule, target_account_id)
            elif rule.action_type == "follow":
                result = await self._execute_follow_action(rule, target_account_id)
            else:
                raise AutomationSchedulerError(f"Unknown action type: {rule.action_type}")

            # Update rule statistics
            rule.times_executed += 1
            rule.last_executed_at = datetime.now()
            rule.success_count += 1
            await self.db.commit()
            await self.db.refresh(rule)

            logger.info(f"Successfully executed automation rule {rule_id}")
            return {
                "success": True,
                "rule_id": str(rule_id),
                "action_type": rule.action_type,
                "result": result,
            }
        except Exception as exc:
            # Update failure count
            rule.times_executed += 1
            rule.last_executed_at = datetime.now()
            rule.failure_count += 1
            await self.db.commit()

            logger.error(f"Failed to execute automation rule {rule_id}: {exc}")
            raise AutomationSchedulerError(f"Failed to execute rule: {exc}") from exc

    async def _execute_comment_action(
        self, rule: "AutomationRule", platform_account_id: UUID
    ) -> dict:
        """
        Execute a comment action.

        Args:
            rule: Automation rule.
            platform_account_id: Platform account UUID.

        Returns:
            Dictionary with comment result.

        Raises:
            AutomationSchedulerError: If comment action fails.
        """
        action_config = rule.action_config or {}
        media_id = action_config.get("media_id")
        comment_text = action_config.get("comment_text") or action_config.get("template")

        if not media_id:
            raise AutomationSchedulerError("Comment action requires media_id in action_config")
        if not comment_text:
            raise AutomationSchedulerError("Comment action requires comment_text or template in action_config")

        result = await self.engagement_service.comment_on_post(
            platform_account_id=platform_account_id,
            media_id=media_id,
            comment_text=comment_text,
        )

        return result

    async def _execute_like_action(self, rule: "AutomationRule", platform_account_id: UUID) -> dict:
        """
        Execute a like action.

        Args:
            rule: Automation rule.
            platform_account_id: Platform account UUID.

        Returns:
            Dictionary with like result.

        Raises:
            AutomationSchedulerError: If like action fails.
        """
        action_config = rule.action_config or {}
        media_id = action_config.get("media_id")

        if not media_id:
            raise AutomationSchedulerError("Like action requires media_id in action_config")

        result = await self.engagement_service.like_post(
            platform_account_id=platform_account_id,
            media_id=media_id,
        )

        return result

    async def _execute_follow_action(self, rule: "AutomationRule", platform_account_id: UUID) -> dict:
        """
        Execute a follow action.

        Args:
            rule: Automation rule.
            platform_account_id: Platform account UUID.

        Returns:
            Dictionary with follow result.

        Raises:
            AutomationSchedulerError: If follow action fails (not yet implemented).
        """
        # Follow action is not yet implemented in IntegratedEngagementService
        raise AutomationSchedulerError("Follow action is not yet implemented")


"""Automation scheduler service for executing automation rules."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.automation_rule_service import AutomationRuleService
from app.services.behavior_randomization_service import BehaviorRandomizationService
from app.services.comment_generation_service import (
    CommentGenerationRequest,
    comment_generation_service,
)
from app.services.human_timing_service import HumanTimingService
from app.services.integrated_engagement_service import IntegratedEngagementService
from app.services.integrated_posting_service import IntegratedPostingService

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
        self.posting_service = IntegratedPostingService(db)
        self.timing_service = HumanTimingService()
        self.behavior_service = BehaviorRandomizationService()

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

        # Check if we should take a random break (behavior randomization)
        if self.behavior_service.should_take_break():
            break_duration = self.behavior_service.get_break_duration()
            logger.info(
                f"Taking random break for {break_duration:.1f} minutes (behavior randomization)"
            )
            raise AutomationSchedulerError(f"Random break: {break_duration:.1f} minutes")

        # Check selective engagement (behavior randomization)
        # For like/comment actions, decide if we should engage with this post
        if rule.action_type in ("like", "comment"):
            post_quality = (rule.action_config or {}).get("post_quality_score")
            if not self.behavior_service.should_engage_with_post(
                engagement_rate=0.7, post_quality_score=post_quality
            ):
                logger.info(
                    f"Skipping engagement with post (selective engagement - behavior randomization)"
                )
                raise AutomationSchedulerError("Skipped engagement (selective engagement pattern)")

        try:
            # Wait for human-like delay before executing action
            base_delay = self.timing_service.get_engagement_delay(action_type=rule.action_type)
            # Add random variation to delay (behavior randomization)
            varied_delay = self.behavior_service.get_engagement_delay_variation(
                base_delay, variation_percent=0.3
            )
            logger.debug(f"Waiting engagement delay: {varied_delay:.1f}s (base: {base_delay:.1f}s)")
            await asyncio.sleep(varied_delay)

            # Execute action based on action_type
            result = None
            if rule.action_type == "comment":
                result = await self._execute_comment_action(rule, target_account_id)
            elif rule.action_type == "like":
                result = await self._execute_like_action(rule, target_account_id)
            elif rule.action_type == "follow":
                result = await self._execute_follow_action(rule, target_account_id)
            elif rule.action_type == "unfollow":
                result = await self._execute_unfollow_action(rule, target_account_id)
            elif rule.action_type == "story":
                result = await self._execute_story_action(rule, target_account_id)
            elif rule.action_type == "dm_response":
                result = await self._execute_dm_response_action(rule, target_account_id)
            elif rule.action_type == "dm_send":
                result = await self._execute_dm_send_action(rule, target_account_id)
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
        Execute a comment action with natural, varied comment generation.

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
        post_description = action_config.get("post_description")
        post_media_type = action_config.get("post_media_type", "image")
        comment_style = action_config.get("comment_style")
        use_generated_comment = action_config.get("use_generated_comment", True)

        if not media_id:
            raise AutomationSchedulerError("Comment action requires media_id in action_config")

        # Generate natural, varied comment if enabled
        comment_text = None
        if use_generated_comment and rule.character_id:
            try:
                # Get character persona for comment generation
                from app.models.character import Character, CharacterPersonality
                from sqlalchemy import select

                char_result = await self.db.execute(
                    select(Character).where(Character.id == rule.character_id)
                )
                character = char_result.scalar_one_or_none()

                character_persona = None
                if character and character.personality:
                    personality = character.personality
                    character_persona = {
                        "personality_traits": [
                            trait
                            for trait in [
                                "openness",
                                "conscientiousness",
                                "extraversion",
                                "agreeableness",
                                "neuroticism",
                            ]
                            if getattr(personality, trait, None) is not None
                        ],
                        "communication_style": personality.communication_style or "",
                    }

                # Generate comment
                comment_request = CommentGenerationRequest(
                    character_id=str(rule.character_id),
                    post_description=post_description,
                    post_media_type=post_media_type,
                    comment_style=comment_style,
                    max_length=150,
                )
                comment_result = comment_generation_service.generate_comment(
                    comment_request, character_persona
                )
                comment_text = comment_result.comment_text
                logger.info(
                    f"Generated natural comment for rule {rule.id}: {comment_text[:50]}..."
                )
            except Exception as exc:
                logger.warning(f"Failed to generate comment, falling back to template: {exc}")
                comment_text = action_config.get("comment_text") or action_config.get("template")
        else:
            comment_text = action_config.get("comment_text") or action_config.get("template")

        if not comment_text:
            raise AutomationSchedulerError(
                "Comment action requires comment_text, template, or use_generated_comment=True"
            )

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
        Execute a follow action for growth strategy automation.

        Args:
            rule: Automation rule.
            platform_account_id: Platform account UUID.

        Returns:
            Dictionary with follow result.

        Raises:
            AutomationSchedulerError: If follow action fails.
        """
        action_config = rule.action_config or {}
        target_user_id = action_config.get("target_user_id") or action_config.get("username")

        if not target_user_id:
            raise AutomationSchedulerError("Follow action requires target_user_id or username in action_config")

        result = await self.engagement_service.follow_user(
            platform_account_id=platform_account_id,
            target_user_id=target_user_id,
        )

        return result

    async def _execute_unfollow_action(self, rule: "AutomationRule", platform_account_id: UUID) -> dict:
        """
        Execute an unfollow action for growth strategy automation.

        Args:
            rule: Automation rule.
            platform_account_id: Platform account UUID.

        Returns:
            Dictionary with unfollow result.

        Raises:
            AutomationSchedulerError: If unfollow action fails.
        """
        action_config = rule.action_config or {}
        target_user_id = action_config.get("target_user_id") or action_config.get("username")

        if not target_user_id:
            raise AutomationSchedulerError("Unfollow action requires target_user_id or username in action_config")

        result = await self.engagement_service.unfollow_user(
            platform_account_id=platform_account_id,
            target_user_id=target_user_id,
        )

        return result

    async def _execute_story_action(self, rule: "AutomationRule", platform_account_id: UUID) -> dict:
        """
        Execute a daily story update action.

        Args:
            rule: Automation rule.
            platform_account_id: Platform account UUID.

        Returns:
            Dictionary with story posting result.

        Raises:
            AutomationSchedulerError: If story action fails.
        """
        action_config = rule.action_config or {}
        content_id = action_config.get("content_id")
        caption = action_config.get("caption", "")

        if not content_id and not rule.character_id:
            raise AutomationSchedulerError(
                "Story action requires content_id in action_config or character_id in rule"
            )

        # If no content_id, try to find recent content for character
        if not content_id and rule.character_id:
            from app.models.content import Content
            from sqlalchemy import select

            result = await self.db.execute(
                select(Content)
                .where(Content.character_id == rule.character_id)
                .where(Content.content_type.in_(["image", "video"]))
                .order_by(Content.created_at.desc())
                .limit(1)
            )
            content = result.scalar_one_or_none()
            if content:
                content_id = str(content.id)
            else:
                raise AutomationSchedulerError(
                    f"No content found for character {rule.character_id} to post as story"
                )

        if not content_id:
            raise AutomationSchedulerError("Story action requires content_id")

        result = await self.posting_service.post_story_to_instagram(
            platform_account_id=platform_account_id,
            content_id=UUID(content_id),
            caption=caption,
        )

        return result

    async def _execute_dm_response_action(self, rule: "AutomationRule", platform_account_id: UUID) -> dict:
        """
        Execute an automated DM response action.

        Args:
            rule: Automation rule.
            platform_account_id: Platform account UUID.

        Returns:
            Dictionary with DM response result.

        Raises:
            AutomationSchedulerError: If DM response action fails.
        """
        action_config = rule.action_config or {}
        thread_id = action_config.get("thread_id")
        message_text = action_config.get("message_text")
        use_generated_response = action_config.get("use_generated_response", True)

        if not thread_id:
            raise AutomationSchedulerError("DM response action requires thread_id in action_config")

        # Generate response if enabled
        if use_generated_response and rule.character_id and not message_text:
            try:
                # Get character persona for response generation
                from app.models.character import Character, CharacterPersonality
                from sqlalchemy import select

                char_result = await self.db.execute(
                    select(Character).where(Character.id == rule.character_id)
                )
                character = char_result.scalar_one_or_none()

                character_persona = None
                if character and character.personality:
                    personality = character.personality
                    character_persona = {
                        "personality_traits": [
                            trait
                            for trait in [
                                "openness",
                                "conscientiousness",
                                "extraversion",
                                "agreeableness",
                                "neuroticism",
                            ]
                            if getattr(personality, trait, None) is not None
                        ],
                        "communication_style": personality.communication_style or "",
                    }

                # Generate DM response using text generation
                from app.services.text_generation_service import TextGenerationRequest, text_generation_service

                incoming_message = action_config.get("incoming_message", "")
                prompt = f"Generate a natural, friendly DM response to this message: {incoming_message}\nKeep it brief (under 100 words) and match the character's personality."

                text_request = TextGenerationRequest(
                    prompt=prompt,
                    model="llama3:8b",
                    character_id=str(rule.character_id),
                    character_persona=character_persona,
                    temperature=0.8,
                    max_tokens=100,
                )
                text_result = text_generation_service.generate_text(text_request)
                message_text = text_result.text.strip()
                logger.info(f"Generated DM response for rule {rule.id}: {message_text[:50]}...")
            except Exception as exc:
                logger.warning(f"Failed to generate DM response, using template: {exc}")
                message_text = action_config.get("message_text") or "Thanks for reaching out!"

        if not message_text:
            raise AutomationSchedulerError(
                "DM response action requires message_text or use_generated_response=True"
            )

        result = await self.engagement_service.send_dm(
            platform_account_id=platform_account_id,
            thread_id=thread_id,
            message_text=message_text,
        )

        return result

    async def _execute_dm_send_action(self, rule: "AutomationRule", platform_account_id: UUID) -> dict:
        """
        Execute a proactive DM send action (not a response to incoming message).

        Args:
            rule: Automation rule.
            platform_account_id: Platform account UUID.

        Returns:
            Dictionary with DM send result.

        Raises:
            AutomationSchedulerError: If DM send action fails.
        """
        action_config = rule.action_config or {}
        thread_id = action_config.get("thread_id")
        user_id = action_config.get("user_id")  # Alternative: user_id or username
        message_text = action_config.get("message_text")
        use_generated_message = action_config.get("use_generated_message", False)

        # Use thread_id or user_id (user_id can be username or user ID)
        target_id = thread_id or user_id
        if not target_id:
            raise AutomationSchedulerError(
                "DM send action requires thread_id or user_id in action_config"
            )

        # Generate message if enabled
        if use_generated_message and rule.character_id and not message_text:
            try:
                # Get character persona for message generation
                from app.models.character import Character, CharacterPersonality
                from sqlalchemy import select

                char_result = await self.db.execute(
                    select(Character).where(Character.id == rule.character_id)
                )
                character = char_result.scalar_one_or_none()

                character_persona = None
                if character and character.personality:
                    personality = character.personality
                    character_persona = {
                        "personality_traits": [
                            trait
                            for trait in [
                                "openness",
                                "conscientiousness",
                                "extraversion",
                                "agreeableness",
                                "neuroticism",
                            ]
                            if getattr(personality, trait, None) is not None
                        ],
                        "communication_style": personality.communication_style or "",
                    }

                # Generate DM message using text generation
                from app.services.text_generation_service import TextGenerationRequest, text_generation_service

                context = action_config.get("context", "")
                prompt = f"Generate a natural, friendly DM message to start a conversation."
                if context:
                    prompt += f" Context: {context}"
                prompt += "\nKeep it brief (under 100 words) and match the character's personality."

                text_request = TextGenerationRequest(
                    prompt=prompt,
                    model="llama3:8b",
                    character_id=str(rule.character_id),
                    character_persona=character_persona,
                    temperature=0.8,
                    max_tokens=100,
                )
                text_result = text_generation_service.generate_text(text_request)
                message_text = text_result.text.strip()
                logger.info(f"Generated DM message for rule {rule.id}: {message_text[:50]}...")
            except Exception as exc:
                logger.warning(f"Failed to generate DM message, using template: {exc}")
                message_text = action_config.get("message_text") or "Hey! How are you doing?"

        if not message_text:
            raise AutomationSchedulerError(
                "DM send action requires message_text or use_generated_message=True"
            )

        result = await self.engagement_service.send_dm(
            platform_account_id=platform_account_id,
            thread_id=target_id,
            message_text=message_text,
        )

        return result


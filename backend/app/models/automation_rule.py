"""Automation rule database models for engagement automation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AutomationRule(Base):
    """Automation rule model for storing engagement automation configurations.
    
    Stores automation rules for automated comments, likes, and follows
    on social media platforms based on schedules or triggers.
    
    Attributes:
        id: Unique identifier (UUID) for the automation rule.
        character_id: Foreign key to the Character this rule belongs to.
        platform_account_id: Foreign key to the PlatformAccount this rule applies to.
        name: Rule name (required).
        description: Rule description (optional).
        is_enabled: Whether the rule is enabled (default: True).
        trigger_type: Trigger type (schedule, event, manual, required).
        trigger_config: JSONB object with trigger configuration (cron, event conditions, etc., required).
        action_type: Action type (comment, like, follow, required).
        action_config: JSONB object with action configuration (comment templates, filters, etc., required).
        platforms: Array of platform names this rule applies to (required, at least one).
        max_executions_per_day: Maximum executions per day (optional).
        max_executions_per_week: Maximum executions per week (optional).
        cooldown_minutes: Cooldown between executions in minutes (default: 60).
        times_executed: Number of times rule has been executed (default: 0).
        last_executed_at: Timestamp of last execution (optional).
        success_count: Number of successful executions (default: 0).
        failure_count: Number of failed executions (default: 0).
        created_at: Timestamp when rule was created.
        updated_at: Timestamp when rule was last updated.
        character: Relationship back to Character (many-to-one).
        platform_account: Relationship to PlatformAccount (many-to-one).
    """

    __tablename__ = "automation_rules"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("platform_accounts.id", ondelete="CASCADE"),
        nullable=True,  # Optional - can apply to all accounts for character
        index=True,
    )

    # Rule Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Trigger
    trigger_type = Column(String(50), nullable=False)  # schedule, event, manual
    trigger_config = Column(JSONB, nullable=False)  # Schedule cron, event conditions, etc.

    # Action
    action_type = Column(String(50), nullable=False)  # comment, like, follow
    action_config = Column(JSONB, nullable=False)  # Comment templates, filters, etc.

    # Platforms
    platforms = Column(ARRAY(String(50)), nullable=False)  # At least one platform required

    # Limits
    max_executions_per_day = Column(Integer, nullable=True)
    max_executions_per_week = Column(Integer, nullable=True)
    cooldown_minutes = Column(Integer, default=60, nullable=False)

    # Statistics
    times_executed = Column(Integer, default=0, nullable=False)
    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    character = relationship("Character", back_populates="automation_rules")
    platform_account = relationship("PlatformAccount", back_populates="automation_rules")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "trigger_type IN ('schedule', 'event', 'manual')",
            name="automation_rule_trigger_type_check",
        ),
        CheckConstraint(
            "action_type IN ('comment', 'like', 'follow')",
            name="automation_rule_action_type_check",
        ),
        CheckConstraint(
            "array_length(platforms, 1) > 0",
            name="automation_rule_platforms_check",
        ),
        CheckConstraint(
            "max_executions_per_day IS NULL OR max_executions_per_day > 0",
            name="automation_rule_max_executions_per_day_check",
        ),
        CheckConstraint(
            "max_executions_per_week IS NULL OR max_executions_per_week > 0",
            name="automation_rule_max_executions_per_week_check",
        ),
        CheckConstraint(
            "cooldown_minutes >= 0",
            name="automation_rule_cooldown_minutes_check",
        ),
        CheckConstraint(
            "times_executed >= 0",
            name="automation_rule_times_executed_check",
        ),
        CheckConstraint(
            "success_count >= 0",
            name="automation_rule_success_count_check",
        ),
        CheckConstraint(
            "failure_count >= 0",
            name="automation_rule_failure_count_check",
        ),
        Index("idx_automation_rules_character", "character_id"),
        Index("idx_automation_rules_platform_account", "platform_account_id"),
        Index("idx_automation_rules_enabled", "is_enabled"),
        Index("idx_automation_rules_trigger_type", "trigger_type"),
    )

    def __repr__(self) -> str:
        return f"<AutomationRule(id={self.id}, character_id={self.character_id}, name={self.name}, action_type={self.action_type})>"


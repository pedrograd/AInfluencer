"""Analytics database model for storing historical performance metrics."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID

from app.core.database import Base


class Analytics(Base):
    """Analytics model for storing historical performance metrics.
    
    Stores daily snapshots of character performance metrics including
    follower counts, engagement rates, post counts, and other metrics
    tracked over time.
    
    Attributes:
        id: Unique identifier (UUID) for the analytics record.
        character_id: Foreign key to the Character these metrics belong to.
        platform_account_id: Optional foreign key to the PlatformAccount.
        metric_date: Date for which this metric was recorded.
        platform: Platform name (instagram, twitter, facebook, etc.) or None for aggregate.
        metric_type: Type of metric (follower_count, engagement_rate, post_count, etc.).
        metric_value: Numeric value of the metric.
        extra_data: Additional context data stored as JSON (renamed from 'metadata' to avoid SQLAlchemy conflict).
        created_at: Timestamp when this record was created.
    """

    __tablename__ = "analytics"

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
        nullable=True,
        index=True,
    )

    # Metrics
    metric_date = Column(Date, nullable=False, index=True)
    platform = Column(String(50), nullable=True, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    metric_value = Column(Numeric(12, 2), nullable=False)

    # Additional Data (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_data = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "platform IS NULL OR platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')",
            name="analytics_platform_check",
        ),
        CheckConstraint(
            "metric_type IN ('follower_count', 'following_count', 'post_count', "
            "'engagement_rate', 'likes_count', 'comments_count', 'shares_count', "
            "'views_count', 'reach', 'impressions', 'revenue', 'cost')",
            name="analytics_metric_type_check",
        ),
        Index("idx_analytics_character_date", "character_id", "metric_date"),
        Index(
            "idx_analytics_character_platform_date",
            "character_id",
            "platform",
            "metric_date",
        ),
        Index(
            "idx_analytics_unique",
            "character_id",
            "platform_account_id",
            "metric_date",
            "metric_type",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Analytics(id={self.id}, character_id={self.character_id}, "
            f"metric_date={self.metric_date}, metric_type={self.metric_type}, "
            f"metric_value={self.metric_value})>"
        )

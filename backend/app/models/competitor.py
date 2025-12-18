"""Competitor database models for tracking and monitoring competitors."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Competitor(Base):
    """Competitor model for storing tracked competitor accounts.
    
    Stores information about competitors to monitor, including their
    platform, name, and which character to compare against.
    
    Attributes:
        id: Unique identifier (UUID) for the competitor.
        character_id: Foreign key to the Character to compare against.
        competitor_name: Name or identifier of the competitor account.
        competitor_platform: Platform name (instagram, twitter, facebook, etc.).
        competitor_username: Optional username/handle for the competitor.
        monitoring_enabled: Whether monitoring is enabled for this competitor (default: True).
        monitoring_frequency_hours: How often to monitor (in hours, default: 24).
        last_monitored_at: Timestamp of last monitoring check.
        extra_data: Additional data stored as JSON (renamed from 'metadata' to avoid SQLAlchemy conflict).
        created_at: Timestamp when competitor was added.
        updated_at: Timestamp when competitor was last updated.
        character: Relationship back to Character (many-to-one).
        snapshots: Relationship to CompetitorMonitoringSnapshot (one-to-many).
    """

    __tablename__ = "competitors"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Competitor Information
    competitor_name = Column(String(255), nullable=False)
    competitor_platform = Column(String(50), nullable=False, index=True)
    competitor_username = Column(String(255), nullable=True)

    # Monitoring Settings
    monitoring_enabled = Column(String(10), default="true", nullable=False)
    monitoring_frequency_hours = Column(Integer, default=24, nullable=False)

    # Status
    last_monitored_at = Column(DateTime(timezone=True), nullable=True)

    # Additional Data (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_data = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    character = relationship("Character", back_populates="competitors")
    snapshots = relationship(
        "CompetitorMonitoringSnapshot",
        back_populates="competitor",
        cascade="all, delete-orphan",
        order_by="desc(CompetitorMonitoringSnapshot.monitored_at)",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "competitor_platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube', 'tiktok', 'snapchat', 'linkedin', 'discord', 'twitch')",
            name="competitor_platform_check",
        ),
        CheckConstraint(
            "monitoring_enabled IN ('true', 'false')",
            name="competitor_monitoring_enabled_check",
        ),
        CheckConstraint(
            "monitoring_frequency_hours > 0",
            name="competitor_frequency_check",
        ),
        Index("idx_competitor_character", "character_id"),
        Index("idx_competitor_platform", "competitor_platform"),
        Index("idx_competitor_enabled", "monitoring_enabled"),
    )

    def __repr__(self) -> str:
        return f"<Competitor(id={self.id}, name={self.competitor_name}, platform={self.competitor_platform})>"


class CompetitorMonitoringSnapshot(Base):
    """Competitor monitoring snapshot model for storing historical monitoring data.
    
    Stores snapshots of competitor metrics captured during periodic monitoring,
    allowing tracking of competitor performance over time.
    
    Attributes:
        id: Unique identifier (UUID) for the snapshot.
        competitor_id: Foreign key to the Competitor this snapshot belongs to.
        monitored_at: Timestamp when this snapshot was captured.
        follower_count: Competitor follower count at snapshot time.
        following_count: Competitor following count (optional).
        post_count: Competitor post count (optional).
        engagement_rate: Average engagement rate (optional).
        avg_likes: Average likes per post (optional).
        avg_comments: Average comments per post (optional).
        avg_shares: Average shares per post (optional).
        metrics: Full metrics dictionary stored as JSON.
        analysis_result: Full analysis result from CompetitorAnalysisService (optional).
        created_at: Timestamp when snapshot was created.
        competitor: Relationship back to Competitor (many-to-one).
    """

    __tablename__ = "competitor_monitoring_snapshots"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    competitor_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Snapshot Timestamp
    monitored_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Metrics (stored both as individual columns and in metrics JSON)
    follower_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    post_count = Column(Integer, nullable=True)
    engagement_rate = Column(Numeric(6, 4), nullable=True)
    avg_likes = Column(Numeric(10, 2), nullable=True)
    avg_comments = Column(Numeric(10, 2), nullable=True)
    avg_shares = Column(Numeric(10, 2), nullable=True)

    # Full Data
    metrics = Column(JSONB, nullable=True)  # Full competitor metrics dict
    analysis_result = Column(JSONB, nullable=True)  # Full analysis result

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    competitor = relationship("Competitor", back_populates="snapshots")

    # Constraints
    __table_args__ = (
        Index("idx_snapshot_competitor_date", "competitor_id", "monitored_at"),
        Index("idx_snapshot_date", "monitored_at"),
    )

    def __repr__(self) -> str:
        return f"<CompetitorMonitoringSnapshot(id={self.id}, competitor_id={self.competitor_id}, monitored_at={self.monitored_at})>"

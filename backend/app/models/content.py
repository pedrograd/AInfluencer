"""Content database models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Content(Base):
    """Content model for storing generated images, videos, text, and audio."""

    __tablename__ = "content"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content Type
    content_type = Column(String(20), nullable=False)  # image, video, text, audio
    content_category = Column(String(50), nullable=True)  # post, story, reel, short, message, etc.
    is_nsfw = Column(Boolean, default=False, nullable=False)

    # Storage
    file_url = Column(Text, nullable=True)  # URL if stored remotely
    file_path = Column(Text, nullable=False)  # Local storage path
    thumbnail_url = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)

    # Metadata
    file_size = Column(BigInteger, nullable=True)  # Bytes
    width = Column(Integer, nullable=True)  # For images/videos
    height = Column(Integer, nullable=True)  # For images/videos
    duration = Column(Integer, nullable=True)  # Seconds, for videos/audio
    mime_type = Column(String(100), nullable=True)

    # Generation Info
    prompt = Column(Text, nullable=True)  # Generation prompt used
    negative_prompt = Column(Text, nullable=True)
    generation_settings = Column(JSONB, nullable=True)  # Model, steps, CFG, etc.
    generation_time_seconds = Column(Integer, nullable=True)

    # Quality & Status
    quality_score = Column(Numeric(3, 2), nullable=True)  # 0.0 to 1.0, if automated QA
    is_approved = Column(Boolean, default=False, nullable=False)
    approval_status = Column(
        String(20), default="pending", nullable=False
    )  # pending, approved, rejected
    rejection_reason = Column(Text, nullable=True)

    # Usage
    times_used = Column(Integer, default=0, nullable=False)  # How many times posted
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    character = relationship("Character", back_populates="content")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('image', 'video', 'text', 'audio')", name="content_type_check"
        ),
        CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected')",
            name="approval_status_check",
        ),
        Index("idx_content_character", "character_id"),
        Index("idx_content_type", "content_type"),
        Index("idx_content_category", "content_category"),
        Index("idx_content_approved", "is_approved"),
        Index("idx_content_nsfw", "is_nsfw"),
        Index("idx_content_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, character_id={self.character_id}, type={self.content_type})>"


class ScheduledPost(Base):
    """Scheduled post model for scheduling content to be posted at a future time."""

    __tablename__ = "scheduled_posts"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=True,  # Can schedule without content (for future generation)
        index=True,
    )

    # Scheduling
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(50), nullable=True)  # e.g., "America/New_York"
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, posted, cancelled, failed

    # Posting Details
    platform = Column(String(50), nullable=True)  # instagram, twitter, facebook, etc.
    caption = Column(Text, nullable=True)  # Post caption/text
    post_settings = Column(JSONB, nullable=True)  # Platform-specific settings

    # Execution
    posted_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    character = relationship("Character", back_populates="scheduled_posts")
    content = relationship("Content", foreign_keys=[content_id])

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'posted', 'cancelled', 'failed')", name="scheduled_post_status_check"
        ),
        Index("idx_scheduled_post_character", "character_id"),
        Index("idx_scheduled_post_content", "content_id"),
        Index("idx_scheduled_post_time", "scheduled_time"),
        Index("idx_scheduled_post_status", "status"),
        Index("idx_scheduled_post_platform", "platform"),
    )

    def __repr__(self) -> str:
        return f"<ScheduledPost(id={self.id}, character_id={self.character_id}, scheduled_time={self.scheduled_time}, status={self.status})>"


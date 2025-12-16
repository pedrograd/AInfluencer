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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Content(Base):
    """Content model for storing generated images, videos, text, and audio.
    
    Stores metadata and file information for all generated content items,
    including images, videos, text, and audio files.
    
    Attributes:
        id: Unique identifier (UUID) for the content item.
        character_id: Foreign key to the Character this content belongs to.
        content_type: Type of content (image, video, text, audio, required).
        content_category: Content category (post, story, reel, short, message, etc., optional).
        is_nsfw: Whether content is NSFW (default: False).
        file_url: URL if content is stored remotely (optional).
        file_path: Local storage path to content file (required).
        thumbnail_url: URL to thumbnail image if stored remotely (optional).
        thumbnail_path: Local file path to thumbnail image (optional).
        file_size: File size in bytes (optional).
        width: Image/video width in pixels (optional).
        height: Image/video height in pixels (optional).
        duration: Video/audio duration in seconds (optional).
        mime_type: MIME type of the content file (optional).
        prompt: Generation prompt used to create this content (optional).
        negative_prompt: Negative prompt used during generation (optional).
        generation_settings: JSON object with generation settings (model, steps, CFG, etc., optional).
        generation_time_seconds: Time taken to generate content in seconds (optional).
        quality_score: Automated quality score (0.0-1.0, optional).
        is_approved: Whether content is approved (default: False).
        approval_status: Approval status (pending, approved, rejected, default: "pending").
        rejection_reason: Reason for rejection if rejected (optional).
        times_used: Number of times this content has been posted (default: 0).
        last_used_at: Timestamp when content was last used (optional).
        description: Auto-generated or user-defined description of the content (optional).
        tags: User-defined tags for categorization (optional).
        folder_path: Organization folder path (optional).
        created_at: Timestamp when content was created.
        updated_at: Timestamp when content was last updated.
        character: Relationship back to Character (many-to-one).
    """

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

    # Description & Tags
    description = Column(Text, nullable=True)  # Auto-generated or user-defined description
    tags = Column(ARRAY(String), nullable=True)  # User-defined tags for categorization
    folder_path = Column(Text, nullable=True)  # Organization folder path

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
        Index("idx_content_tags", "tags", postgresql_using="gin"),  # GIN index for array search
    )

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, character_id={self.character_id}, type={self.content_type})>"


class ScheduledPost(Base):
    """Scheduled post model for scheduling content to be posted at a future time.
    
    Stores scheduled posts with timing, platform, caption, and execution status
    information for automated content posting.
    
    Attributes:
        id: Unique identifier (UUID) for the scheduled post.
        character_id: Foreign key to the Character this post belongs to.
        content_id: Foreign key to the Content item to post (optional, can schedule without content).
        scheduled_time: Scheduled posting time with timezone (required, indexed).
        timezone: Timezone string (e.g., "America/New_York", optional).
        status: Post status (pending, posted, cancelled, failed, default: "pending").
        platform: Target platform (instagram, twitter, facebook, etc., optional).
        caption: Post caption/text content (optional).
        post_settings: JSON object with platform-specific posting settings (optional).
        posted_at: Timestamp when post was actually posted (optional).
        error_message: Error message if posting failed (optional).
        retry_count: Number of retry attempts (default: 0).
        created_at: Timestamp when scheduled post was created.
        updated_at: Timestamp when scheduled post was last updated.
        character: Relationship back to Character (many-to-one).
        content: Relationship to Content item (many-to-one).
    """

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


"""Post database models for storing published posts across platforms."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY,
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
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Post(Base):
    """Post model for storing published posts across all platforms.
    
    Stores metadata and status for posts published to Instagram, Twitter,
    Facebook, Telegram, OnlyFans, and YouTube.
    
    Attributes:
        id: Unique identifier (UUID) for the post.
        character_id: Foreign key to the Character this post belongs to.
        platform_account_id: Foreign key to the PlatformAccount used for posting.
        platform: Platform name (instagram, twitter, facebook, etc.).
        post_type: Type of post (post, story, reel, short, tweet, message, etc.).
        platform_post_id: ID returned by the platform after posting.
        platform_post_url: URL to the published post on the platform.
        content_id: Foreign key to the primary Content item (image/video).
        additional_content_ids: Array of additional content IDs for carousels.
        caption: Post caption/text content.
        hashtags: Array of hashtags used in the post.
        mentions: Array of mentioned usernames.
        likes_count: Number of likes (cached from platform).
        comments_count: Number of comments (cached from platform).
        shares_count: Number of shares (cached from platform).
        views_count: Number of views (cached from platform).
        last_engagement_sync_at: Timestamp of last engagement sync.
        status: Post status (draft, scheduled, published, failed, deleted).
        published_at: Timestamp when post was actually published.
        error_message: Error message if posting failed.
        retry_count: Number of retry attempts.
        created_at: Timestamp when post was created.
        updated_at: Timestamp when post was last updated.
    """

    __tablename__ = "posts"

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
        nullable=False,
        index=True,
    )

    # Post Info
    platform = Column(String(50), nullable=False)  # instagram, twitter, facebook, etc.
    post_type = Column(String(50), nullable=True)  # post, story, reel, short, tweet, message, etc.
    platform_post_id = Column(String(255), nullable=True)  # ID returned by platform
    platform_post_url = Column(Text, nullable=True)

    # Content
    content_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("content.id", ondelete="SET NULL"),
        nullable=True,
    )  # Primary content (image/video)
    additional_content_ids = Column(ARRAY(PostgresUUID(as_uuid=True)), nullable=True)  # Carousel items

    # Text Content
    caption = Column(Text, nullable=True)
    hashtags = Column(ARRAY(String), nullable=True)
    mentions = Column(ARRAY(String), nullable=True)

    # Engagement (cached from platform)
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    shares_count = Column(Integer, default=0, nullable=False)
    views_count = Column(Integer, default=0, nullable=False)
    last_engagement_sync_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(
        String(20), default="draft", nullable=False
    )  # draft, scheduled, published, failed, deleted
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Error Handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    # Note: platform_accounts and content relationships would be defined if those models exist

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')",
            name="post_platform_check",
        ),
        CheckConstraint(
            "status IN ('draft', 'scheduled', 'published', 'failed', 'deleted')",
            name="post_status_check",
        ),
        Index("idx_posts_character", "character_id"),
        Index("idx_posts_platform_account", "platform_account_id"),
        Index("idx_posts_platform", "platform"),
        Index("idx_posts_status", "status"),
        Index("idx_posts_published", "published_at"),
        Index("idx_posts_platform_post_id", "platform", "platform_post_id"),
    )

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, character_id={self.character_id}, platform={self.platform}, status={self.status})>"


"""Platform account database models for storing social media platform connections."""

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
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlatformAccount(Base):
    """Platform account model for storing social media platform connections and credentials.
    
    Stores authentication data, connection status, account statistics, and settings
    for each character's platform accounts (Instagram, Twitter, Facebook, etc.).
    
    Attributes:
        id: Unique identifier (UUID) for the platform account.
        character_id: Foreign key to the Character this account belongs to.
        platform: Platform name (instagram, twitter, facebook, telegram, onlyfans, youtube).
        account_username: Username on the platform (optional).
        account_id: Platform's user ID (optional).
        account_url: URL to the account profile (optional).
        auth_type: Authentication type (api_key, oauth, browser_session, cookie, optional).
        auth_data: JSONB object with encrypted credentials (API keys, tokens, etc., optional).
        is_connected: Whether the account is currently connected (default: False).
        connection_status: Connection status (connected, disconnected, error, rate_limited, suspended, default: "disconnected").
        follower_count: Cached follower count (default: 0).
        following_count: Cached following count (default: 0).
        post_count: Cached post count (default: 0).
        last_synced_at: Timestamp of last account sync (optional).
        auto_posting_enabled: Whether auto-posting is enabled (default: True).
        auto_engagement_enabled: Whether auto-engagement is enabled (default: True).
        posting_frequency: Posting frequency setting (daily, weekly, custom, optional).
        engagement_frequency: Engagement frequency setting (optional).
        rate_limit_remaining: Remaining rate limit (optional).
        rate_limit_reset_at: Timestamp when rate limit resets (optional).
        last_rate_limit_hit_at: Timestamp of last rate limit hit (optional).
        created_at: Timestamp when account was created.
        updated_at: Timestamp when account was last updated.
        last_activity_at: Timestamp of last activity (optional).
        character: Relationship back to Character (many-to-one).
    """

    __tablename__ = "platform_accounts"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Platform Info
    platform = Column(String(50), nullable=False)  # instagram, twitter, facebook, etc.
    account_username = Column(String(255), nullable=True)
    account_id = Column(String(255), nullable=True)  # Platform's user ID
    account_url = Column(Text, nullable=True)

    # Authentication
    auth_type = Column(String(50), nullable=True)  # api_key, oauth, browser_session, cookie
    auth_data = Column(JSONB, nullable=True)  # Encrypted credentials (API keys, tokens, etc.)
    is_connected = Column(Boolean, default=False, nullable=False)
    connection_status = Column(
        String(20), default="disconnected", nullable=False
    )  # connected, disconnected, error, rate_limited, suspended

    # Account Stats (cached)
    follower_count = Column(Integer, default=0, nullable=False)
    following_count = Column(Integer, default=0, nullable=False)
    post_count = Column(Integer, default=0, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # Settings
    auto_posting_enabled = Column(Boolean, default=True, nullable=False)
    auto_engagement_enabled = Column(Boolean, default=True, nullable=False)
    posting_frequency = Column(String(50), nullable=True)  # daily, weekly, custom
    engagement_frequency = Column(String(50), nullable=True)

    # Rate Limiting
    rate_limit_remaining = Column(Integer, nullable=True)
    rate_limit_reset_at = Column(DateTime(timezone=True), nullable=True)
    last_rate_limit_hit_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_activity_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    character = relationship("Character", back_populates="platform_accounts")
    automation_rules = relationship("AutomationRule", back_populates="platform_account", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')",
            name="platform_account_platform_check",
        ),
        CheckConstraint(
            "connection_status IN ('connected', 'disconnected', 'error', 'rate_limited', 'suspended')",
            name="platform_account_connection_status_check",
        ),
        Index("idx_platform_accounts_character", "character_id"),
        Index("idx_platform_accounts_platform", "platform"),
        Index("idx_platform_accounts_connected", "is_connected"),
        Index("idx_platform_accounts_unique", "character_id", "platform", unique=True),
    )

    def __repr__(self) -> str:
        return f"<PlatformAccount(id={self.id}, character_id={self.character_id}, platform={self.platform}, username={self.account_username})>"


"""API Key database model for third-party integrations."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class APIKey(Base):
    """API Key model for third-party integrations.
    
    Represents an API key that can be used by third-party applications to access
    the AInfluencer API. Keys are hashed before storage and can have scoped permissions.
    
    Attributes:
        id: Unique identifier (UUID) for the API key.
        key_hash: Hashed API key value (stored securely, never returned).
        name: Human-readable name for the API key (for management).
        user_id: Foreign key to the user who owns this API key.
        scopes: JSON array of permission scopes (e.g., ["read:characters", "write:content"]).
        rate_limit: Maximum requests per hour for this key (default: 1000).
        is_active: Whether the API key is active (default: True).
        expires_at: Optional expiration date for the key (None if no expiration).
        last_used_at: Timestamp of last successful API call using this key.
        created_at: Timestamp when key was created.
        updated_at: Timestamp when key was last updated.
        deleted_at: Timestamp when key was soft-deleted (None if not deleted).
    """

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scopes = Column(JSONB, nullable=False, default=list)  # List of permission scopes
    rate_limit = Column(Integer, default=1000, nullable=False)  # Requests per hour
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, user_id={self.user_id}, is_active={self.is_active})>"

    def is_expired(self) -> bool:
        """Check if the API key has expired.
        
        Returns:
            True if the key has an expiration date and it has passed, False otherwise.
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)

    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired).
        
        Returns:
            True if the key is active and not expired, False otherwise.
        """
        return self.is_active and not self.is_expired() and self.deleted_at is None

    def has_scope(self, scope: str) -> bool:
        """Check if the API key has a specific permission scope.
        
        Args:
            scope: The permission scope to check (e.g., "read:characters").
            
        Returns:
            True if the key has the scope, False otherwise.
        """
        if not isinstance(self.scopes, list):
            return False
        return scope in self.scopes or "*" in self.scopes  # "*" means all scopes

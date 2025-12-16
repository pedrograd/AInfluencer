"""User database model for authentication."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    """User model for authentication and user management.
    
    Represents a platform user with authentication credentials, profile information,
    and account status.
    
    Attributes:
        id: Unique identifier (UUID) for the user.
        email: User email address (unique, required, used for login).
        password_hash: Hashed password (bcrypt hash, required).
        is_verified: Whether the user's email has been verified (default: False).
        is_active: Whether the user account is active (default: True).
        full_name: User's full name (optional).
        created_at: Timestamp when user was created.
        updated_at: Timestamp when user was last updated.
        last_login_at: Timestamp of last successful login.
        deleted_at: Timestamp when user was soft-deleted (None if not deleted).
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"


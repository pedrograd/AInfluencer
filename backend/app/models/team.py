"""Team and team member database models for collaboration features."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TeamRole(str, Enum):
    """Team member role enumeration."""
    
    OWNER = "owner"  # Full control, can delete team
    ADMIN = "admin"  # Can manage members and team settings
    MEMBER = "member"  # Can create/edit team resources
    VIEWER = "viewer"  # Read-only access


class Team(Base):
    """Team/Organization model for multi-user collaboration.
    
    Represents a team/organization that can have multiple members with different roles.
    Teams can own shared resources like characters, allowing collaboration.
    
    Attributes:
        id: Unique identifier (UUID) for the team.
        name: Team name (1-255 characters, required).
        description: Team description text (optional).
        owner_id: Foreign key to the User who owns/created this team (required).
        is_active: Whether the team is currently active (default: True).
        created_at: Timestamp when team was created.
        updated_at: Timestamp when team was last updated.
        deleted_at: Timestamp when team was soft-deleted (None if not deleted).
        members: Relationship to TeamMember objects (team members).
    """

    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name}, owner_id={self.owner_id})>"


class TeamMember(Base):
    """Team member model for managing user-team relationships and roles.
    
    Represents a user's membership in a team with a specific role that determines
    their permissions and access level.
    
    Attributes:
        id: Unique identifier (UUID) for the team membership.
        team_id: Foreign key to the Team (required).
        user_id: Foreign key to the User (required).
        role: Team member role (owner, admin, member, viewer, default: "member").
        is_active: Whether the membership is active (default: True).
        invited_by_id: Foreign key to the User who invited this member (optional).
        joined_at: Timestamp when user joined the team.
        created_at: Timestamp when membership was created.
        updated_at: Timestamp when membership was last updated.
        deleted_at: Timestamp when membership was soft-deleted (None if not deleted).
        team: Relationship to Team object.
    """

    __tablename__ = "team_members"
    __table_args__ = (
        # Ensure a user can only have one active membership per team
        {"comment": "Team memberships with roles for collaboration"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default=TeamRole.MEMBER.value)
    is_active = Column(Boolean, default=True, nullable=False)
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    team = relationship("Team", back_populates="members")

    def __repr__(self) -> str:
        return f"<TeamMember(id={self.id}, team_id={self.team_id}, user_id={self.user_id}, role={self.role})>"

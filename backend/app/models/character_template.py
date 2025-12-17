"""Character template marketplace models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from typing import Any


class CharacterTemplate(Base):
    """Character template model for marketplace.
    
    Stores published character templates that users can browse and use to create new characters.
    Templates include character data (name, bio, personality, appearance) in JSON format.
    
    Attributes:
        id: Unique identifier (UUID) for the template.
        creator_id: Foreign key to the User who created/published this template.
        name: Template name (1-255 characters, required).
        description: Template description text.
        category: Template category (e.g., "influencer", "professional", "creative", "entertainer").
        tags: Array of tag strings for search/filtering.
        template_data: JSONB field containing full character data (character, personality, appearance).
        preview_image_url: URL to preview image for the template.
        is_featured: Whether this template is featured/promoted.
        is_public: Whether this template is publicly visible (default: True).
        download_count: Number of times this template has been used/downloaded.
        rating: Average rating (0.0-5.0, optional).
        rating_count: Number of ratings.
        created_at: Timestamp when template was created.
        updated_at: Timestamp when template was last updated.
        deleted_at: Timestamp when template was soft-deleted (None if not deleted).
        creator: Relationship to User who created this template.
    """

    __tablename__ = "character_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Basic Info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), index=True)  # influencer, professional, creative, entertainer, etc.
    tags = Column(ARRAY(String))  # Array of tags for search

    # Template Data (JSONB for flexible storage)
    template_data = Column(JSONB, nullable=False)  # Contains character, personality, appearance data

    # Preview
    preview_image_url = Column(Text)

    # Marketplace Metadata
    is_featured = Column(Boolean, default=False, index=True)
    is_public = Column(Boolean, default=True, index=True)
    download_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2))  # 0.0-5.0
    rating_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])

    __table_args__ = (
        CheckConstraint("LENGTH(name) >= 1 AND LENGTH(name) <= 255", name="template_name_length_check"),
        CheckConstraint("rating IS NULL OR (rating >= 0.0 AND rating <= 5.0)", name="rating_range_check"),
        CheckConstraint("download_count >= 0", name="download_count_check"),
        CheckConstraint("rating_count >= 0", name="rating_count_check"),
    )

    def __repr__(self) -> str:
        return f"<CharacterTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"

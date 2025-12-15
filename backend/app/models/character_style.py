"""Character image style database models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CharacterImageStyle(Base):
    """Character image style model for multiple styles per character."""

    __tablename__ = "character_image_styles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)

    # Style Definition
    name = Column(String(255), nullable=False)  # e.g., "Casual", "Formal", "Sporty", "Glamour"
    description = Column(Text)  # Optional description of the style

    # Style-Specific Prompt Modifications
    prompt_suffix = Column(Text)  # Additional prompt text appended for this style
    prompt_prefix = Column(Text)  # Additional prompt text prepended for this style
    negative_prompt_addition = Column(Text)  # Additional negative prompt text for this style

    # Style-Specific Generation Settings
    checkpoint = Column(String(255))  # Override checkpoint for this style (optional)
    sampler_name = Column(String(64))  # Override sampler for this style (optional)
    scheduler = Column(String(64))  # Override scheduler for this style (optional)
    steps = Column(Integer)  # Override steps for this style (optional)
    cfg = Column(Numeric(5, 2))  # Override CFG scale for this style (optional)
    width = Column(Integer)  # Override width for this style (optional)
    height = Column(Integer)  # Override height for this style (optional)

    # Style Keywords (for filtering/searching)
    style_keywords = Column(ARRAY(String))  # Array of style descriptors

    # Ordering and Status
    display_order = Column(Integer, default=0)  # Order for display in UI
    is_active = Column(Boolean, default=True)  # Whether this style is active
    is_default = Column(Boolean, default=False)  # Whether this is the default style for the character

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    character = relationship("Character", back_populates="image_styles")

    __table_args__ = (
        CheckConstraint("LENGTH(name) >= 1 AND LENGTH(name) <= 255", name="name_length_check"),
        CheckConstraint("steps IS NULL OR (steps >= 1 AND steps <= 200)", name="steps_range_check"),
        CheckConstraint("cfg IS NULL OR (cfg >= 0.0 AND cfg <= 30.0)", name="cfg_range_check"),
        CheckConstraint("width IS NULL OR (width >= 256 AND width <= 4096)", name="width_range_check"),
        CheckConstraint("height IS NULL OR (height >= 256 AND height <= 4096)", name="height_range_check"),
    )

    def __repr__(self) -> str:
        return f"<CharacterImageStyle(id={self.id}, character_id={self.character_id}, name='{self.name}')>"


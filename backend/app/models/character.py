"""Character database models."""

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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from typing import Any


class Character(Base):
    """Character profile model."""

    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    bio = Column(Text)
    age = Column(Integer)
    location = Column(String(255))
    timezone = Column(String(50), default="UTC")
    interests = Column(ARRAY(String))
    profile_image_url = Column(Text)
    profile_image_path = Column(Text)

    # Status
    status = Column(String(20), default="active")
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    personality = relationship(
        "CharacterPersonality",
        back_populates="character",
        uselist=False,
        cascade="all, delete-orphan",
    )
    appearance = relationship(
        "CharacterAppearance",
        back_populates="character",
        uselist=False,
        cascade="all, delete-orphan",
    )
    content = relationship("Content", back_populates="character", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'error', 'deleted')", name="status_check"),
        CheckConstraint("LENGTH(name) >= 1 AND LENGTH(name) <= 255", name="name_length_check"),
        CheckConstraint("age IS NULL OR (age >= 0 AND age <= 150)", name="age_range_check"),
    )

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, name='{self.name}', status='{self.status}')>"


class CharacterPersonality(Base):
    """Character personality traits and behavior patterns."""

    __tablename__ = "character_personalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)

    # Personality Traits (0.0 to 1.0 scale)
    extroversion = Column(Numeric(3, 2), default=0.5)  # 0.0 = introverted, 1.0 = extroverted
    creativity = Column(Numeric(3, 2), default=0.5)
    humor = Column(Numeric(3, 2), default=0.5)
    professionalism = Column(Numeric(3, 2), default=0.5)
    authenticity = Column(Numeric(3, 2), default=0.5)

    # Communication Style
    communication_style = Column(String(50))  # casual, professional, friendly, sassy, etc.
    preferred_topics = Column(ARRAY(String))  # Array of topics
    content_tone = Column(String(50))  # positive, neutral, edgy, etc.

    # LLM Settings
    llm_personality_prompt = Column(Text)  # Custom prompt for LLM
    temperature = Column(Numeric(3, 2), default=0.7)  # LLM temperature

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    character = relationship("Character", back_populates="personality")

    __table_args__ = (
        UniqueConstraint("character_id", name="unique_character_personality"),
    )

    def __repr__(self) -> str:
        return f"<CharacterPersonality(id={self.id}, character_id={self.character_id})>"


class CharacterAppearance(Base):
    """Character physical attributes and appearance settings."""

    __tablename__ = "character_appearances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)

    # Face Consistency
    face_reference_image_url = Column(Text)
    face_reference_image_path = Column(Text)
    face_consistency_method = Column(String(50), default="ip-adapter")  # ip-adapter, instantid, faceid, lora
    lora_model_path = Column(Text)  # If using LoRA

    # Physical Attributes
    hair_color = Column(String(50))
    hair_style = Column(String(50))
    eye_color = Column(String(50))
    skin_tone = Column(String(50))
    body_type = Column(String(50))
    height = Column(String(20))
    age_range = Column(String(20))  # e.g., "25-30"

    # Style Preferences
    clothing_style = Column(String(100))  # casual, formal, sporty, etc.
    preferred_colors = Column(ARRAY(String))  # Array of colors
    style_keywords = Column(ARRAY(String))  # Array of style descriptors

    # Generation Settings
    base_model = Column(String(100), default="realistic-vision-v6")  # SD model name
    negative_prompt = Column(Text)  # Default negative prompt
    default_prompt_prefix = Column(Text)  # Prefix added to all prompts

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    character = relationship("Character", back_populates="appearance")

    __table_args__ = (
        UniqueConstraint("character_id", name="unique_character_appearance"),
    )

    def __repr__(self) -> str:
        return f"<CharacterAppearance(id={self.id}, character_id={self.character_id})>"


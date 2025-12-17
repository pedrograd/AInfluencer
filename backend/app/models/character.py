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
    """Character profile model.
    
    Represents a character/influencer profile with basic information, status,
    and relationships to personality, appearance, content, and scheduling data.
    
    Attributes:
        id: Unique identifier (UUID) for the character.
        user_id: Foreign key to the User who owns this character (required).
        team_id: Foreign key to the Team (optional, for team-shared characters).
        name: Character name (1-255 characters, required).
        bio: Character biography/description text.
        age: Character age (0-150, optional).
        location: Character location string.
        timezone: Character timezone (default: "UTC").
        interests: Array of interest strings.
        profile_image_url: URL to character profile image.
        profile_image_path: Local file path to character profile image.
        status: Character status (active, paused, error, deleted, default: "active").
        is_active: Whether the character is currently active (default: True).
        created_at: Timestamp when character was created.
        updated_at: Timestamp when character was last updated.
        deleted_at: Timestamp when character was soft-deleted (None if not deleted).
        personality: Relationship to CharacterPersonality (one-to-one).
        appearance: Relationship to CharacterAppearance (one-to-one).
        content: Relationship to Content items (one-to-many).
        scheduled_posts: Relationship to ScheduledPost items (one-to-many).
        image_styles: Relationship to CharacterImageStyle items (one-to-many).
    """

    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
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
    scheduled_posts = relationship("ScheduledPost", back_populates="character", cascade="all, delete-orphan")
    image_styles = relationship("CharacterImageStyle", back_populates="character", cascade="all, delete-orphan")
    platform_accounts = relationship("PlatformAccount", back_populates="character", cascade="all, delete-orphan")
    automation_rules = relationship("AutomationRule", back_populates="character", cascade="all, delete-orphan")
    competitors = relationship("Competitor", back_populates="character", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'error', 'deleted')", name="status_check"),
        CheckConstraint("LENGTH(name) >= 1 AND LENGTH(name) <= 255", name="name_length_check"),
        CheckConstraint("age IS NULL OR (age >= 0 AND age <= 150)", name="age_range_check"),
    )

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, name='{self.name}', status='{self.status}')>"


class CharacterPersonality(Base):
    """Character personality traits and behavior patterns.
    
    Stores personality traits, communication style, and LLM settings that
    influence how the character generates content and interacts.
    
    Attributes:
        id: Unique identifier (UUID) for the personality record.
        character_id: Foreign key to the Character this personality belongs to.
        extroversion: Extroversion level (0.0=introverted, 1.0=extroverted, default: 0.5).
        creativity: Creativity level (0.0-1.0 scale, default: 0.5).
        humor: Humor level (0.0-1.0 scale, default: 0.5).
        professionalism: Professionalism level (0.0-1.0 scale, default: 0.5).
        authenticity: Authenticity level (0.0-1.0 scale, default: 0.5).
        communication_style: Communication style (casual, professional, friendly, sassy, etc.).
        preferred_topics: Array of preferred topic strings.
        content_tone: Content tone (positive, neutral, edgy, etc.).
        llm_personality_prompt: Custom prompt text for LLM personality injection.
        temperature: LLM temperature setting (0.0-1.0, default: 0.7).
        created_at: Timestamp when personality was created.
        updated_at: Timestamp when personality was last updated.
        character: Relationship back to Character (many-to-one).
    """

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
    """Character physical attributes and appearance settings.
    
    Stores physical attributes, face consistency settings, style preferences,
    and generation settings used for image generation.
    
    Attributes:
        id: Unique identifier (UUID) for the appearance record.
        character_id: Foreign key to the Character this appearance belongs to.
        face_reference_image_url: URL to face reference image for consistency.
        face_reference_image_path: Local file path to face reference image.
        face_consistency_method: Method used for face consistency (ip-adapter, instantid, faceid, lora, default: "ip-adapter").
        lora_model_path: Path to LoRA model if using LoRA for face consistency.
        hair_color: Character hair color.
        hair_style: Character hair style.
        eye_color: Character eye color.
        skin_tone: Character skin tone.
        body_type: Character body type.
        height: Character height string.
        age_range: Character age range (e.g., "25-30").
        clothing_style: Preferred clothing style (casual, formal, sporty, etc.).
        preferred_colors: Array of preferred color strings.
        style_keywords: Array of style descriptor strings.
        base_model: Base Stable Diffusion model name (default: "realistic-vision-v6").
        negative_prompt: Default negative prompt text for image generation.
        default_prompt_prefix: Prefix text added to all generation prompts.
        created_at: Timestamp when appearance was created.
        updated_at: Timestamp when appearance was last updated.
        character: Relationship back to Character (many-to-one).
    """

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


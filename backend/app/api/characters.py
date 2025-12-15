"""Character management API endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.character import Character, CharacterAppearance, CharacterPersonality

router = APIRouter()


# Request/Response Models
class PersonalityCreate(BaseModel):
    """Personality traits for character creation."""

    extroversion: float = Field(default=0.5, ge=0.0, le=1.0)
    creativity: float = Field(default=0.5, ge=0.0, le=1.0)
    humor: float = Field(default=0.5, ge=0.0, le=1.0)
    professionalism: float = Field(default=0.5, ge=0.0, le=1.0)
    authenticity: float = Field(default=0.5, ge=0.0, le=1.0)
    communication_style: str | None = None
    preferred_topics: list[str] | None = None
    content_tone: str | None = None
    llm_personality_prompt: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class AppearanceCreate(BaseModel):
    """Appearance settings for character creation."""

    face_reference_image_url: str | None = None
    face_reference_image_path: str | None = None
    face_consistency_method: str = Field(default="ip-adapter")
    lora_model_path: str | None = None
    hair_color: str | None = None
    hair_style: str | None = None
    eye_color: str | None = None
    skin_tone: str | None = None
    body_type: str | None = None
    height: str | None = None
    age_range: str | None = None
    clothing_style: str | None = None
    preferred_colors: list[str] | None = None
    style_keywords: list[str] | None = None
    base_model: str = Field(default="realistic-vision-v6")
    negative_prompt: str | None = None
    default_prompt_prefix: str | None = None


class CharacterCreate(BaseModel):
    """Request model for creating a character."""

    name: str = Field(..., min_length=1, max_length=255)
    bio: str | None = None
    age: int | None = Field(None, ge=0, le=150)
    location: str | None = None
    timezone: str = Field(default="UTC")
    interests: list[str] | None = None
    profile_image_url: str | None = None
    profile_image_path: str | None = None
    personality: PersonalityCreate | None = None
    appearance: AppearanceCreate | None = None


class CharacterResponse(BaseModel):
    """Response model for character data."""

    id: UUID
    name: str
    bio: str | None
    age: int | None
    location: str | None
    timezone: str
    interests: list[str] | None
    profile_image_url: str | None
    profile_image_path: str | None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=dict)
async def create_character(
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new character with optional personality and appearance."""
    # Create character
    character = Character(
        name=character_data.name,
        bio=character_data.bio,
        age=character_data.age,
        location=character_data.location,
        timezone=character_data.timezone,
        interests=character_data.interests,
        profile_image_url=character_data.profile_image_url,
        profile_image_path=character_data.profile_image_path,
        status="active",
        is_active=True,
    )
    db.add(character)
    await db.flush()  # Get the character ID

    # Create personality if provided
    if character_data.personality:
        personality = CharacterPersonality(
            character_id=character.id,
            extroversion=character_data.personality.extroversion,
            creativity=character_data.personality.creativity,
            humor=character_data.personality.humor,
            professionalism=character_data.personality.professionalism,
            authenticity=character_data.personality.authenticity,
            communication_style=character_data.personality.communication_style,
            preferred_topics=character_data.personality.preferred_topics,
            content_tone=character_data.personality.content_tone,
            llm_personality_prompt=character_data.personality.llm_personality_prompt,
            temperature=character_data.personality.temperature,
        )
        db.add(personality)

    # Create appearance if provided
    if character_data.appearance:
        appearance = CharacterAppearance(
            character_id=character.id,
            face_reference_image_url=character_data.appearance.face_reference_image_url,
            face_reference_image_path=character_data.appearance.face_reference_image_path,
            face_consistency_method=character_data.appearance.face_consistency_method,
            lora_model_path=character_data.appearance.lora_model_path,
            hair_color=character_data.appearance.hair_color,
            hair_style=character_data.appearance.hair_style,
            eye_color=character_data.appearance.eye_color,
            skin_tone=character_data.appearance.skin_tone,
            body_type=character_data.appearance.body_type,
            height=character_data.appearance.height,
            age_range=character_data.appearance.age_range,
            clothing_style=character_data.appearance.clothing_style,
            preferred_colors=character_data.appearance.preferred_colors,
            style_keywords=character_data.appearance.style_keywords,
            base_model=character_data.appearance.base_model,
            negative_prompt=character_data.appearance.negative_prompt,
            default_prompt_prefix=character_data.appearance.default_prompt_prefix,
        )
        db.add(appearance)

    await db.commit()
    await db.refresh(character)

    return {
        "success": True,
        "data": {
            "id": character.id,
            "name": character.name,
            "status": character.status,
            "created_at": character.created_at.isoformat(),
        },
        "message": "Character created successfully",
    }


"""Character management API endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


class PersonalityUpdate(BaseModel):
    """Personality traits for character update (all optional)."""

    extroversion: float | None = Field(None, ge=0.0, le=1.0)
    creativity: float | None = Field(None, ge=0.0, le=1.0)
    humor: float | None = Field(None, ge=0.0, le=1.0)
    professionalism: float | None = Field(None, ge=0.0, le=1.0)
    authenticity: float | None = Field(None, ge=0.0, le=1.0)
    communication_style: str | None = None
    preferred_topics: list[str] | None = None
    content_tone: str | None = None
    llm_personality_prompt: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)


class AppearanceUpdate(BaseModel):
    """Appearance settings for character update (all optional)."""

    face_reference_image_url: str | None = None
    face_reference_image_path: str | None = None
    face_consistency_method: str | None = None
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
    base_model: str | None = None
    negative_prompt: str | None = None
    default_prompt_prefix: str | None = None


class CharacterUpdate(BaseModel):
    """Request model for updating a character (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    bio: str | None = None
    age: int | None = Field(None, ge=0, le=150)
    location: str | None = None
    timezone: str | None = None
    interests: list[str] | None = None
    profile_image_url: str | None = None
    profile_image_path: str | None = None
    personality: PersonalityUpdate | None = None
    appearance: AppearanceUpdate | None = None


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


@router.get("", response_model=dict)
async def list_characters(
    status: str | None = Query(None, description="Filter by status (active, paused, error)"),
    search: str | None = Query(None, description="Search by name"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get list of all characters with pagination and filtering."""
    # Build query
    query = select(Character).where(Character.deleted_at.is_(None))

    # Apply filters
    if status:
        query = query.where(Character.status == status)
    if search:
        query = query.where(Character.name.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Character.created_at.desc()).limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    characters = result.scalars().all()

    return {
        "success": True,
        "data": {
            "characters": [
                {
                    "id": char.id,
                    "name": char.name,
                    "bio": char.bio,
                    "status": char.status,
                    "profile_image_url": char.profile_image_url,
                    "created_at": char.created_at.isoformat(),
                }
                for char in characters
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/{character_id}", response_model=dict)
async def get_character(
    character_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get detailed character information."""
    # Query character with relationships
    query = (
        select(Character)
        .options(
            selectinload(Character.personality),
            selectinload(Character.appearance),
        )
        .where(Character.id == character_id)
        .where(Character.deleted_at.is_(None))
    )

    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Build response
    response_data = {
        "id": character.id,
        "name": character.name,
        "bio": character.bio,
        "age": character.age,
        "location": character.location,
        "timezone": character.timezone,
        "interests": character.interests,
        "profile_image_url": character.profile_image_url,
        "profile_image_path": character.profile_image_path,
        "status": character.status,
        "is_active": character.is_active,
        "created_at": character.created_at.isoformat(),
        "updated_at": character.updated_at.isoformat(),
    }

    # Add personality if exists
    if character.personality:
        response_data["personality"] = {
            "extroversion": float(character.personality.extroversion) if character.personality.extroversion else None,
            "creativity": float(character.personality.creativity) if character.personality.creativity else None,
            "humor": float(character.personality.humor) if character.personality.humor else None,
            "professionalism": float(character.personality.professionalism) if character.personality.professionalism else None,
            "authenticity": float(character.personality.authenticity) if character.personality.authenticity else None,
            "communication_style": character.personality.communication_style,
            "preferred_topics": character.personality.preferred_topics,
            "content_tone": character.personality.content_tone,
            "llm_personality_prompt": character.personality.llm_personality_prompt,
            "temperature": float(character.personality.temperature) if character.personality.temperature else None,
        }

    # Add appearance if exists
    if character.appearance:
        response_data["appearance"] = {
            "face_reference_image_url": character.appearance.face_reference_image_url,
            "face_reference_image_path": character.appearance.face_reference_image_path,
            "face_consistency_method": character.appearance.face_consistency_method,
            "lora_model_path": character.appearance.lora_model_path,
            "hair_color": character.appearance.hair_color,
            "hair_style": character.appearance.hair_style,
            "eye_color": character.appearance.eye_color,
            "skin_tone": character.appearance.skin_tone,
            "body_type": character.appearance.body_type,
            "height": character.appearance.height,
            "age_range": character.appearance.age_range,
            "clothing_style": character.appearance.clothing_style,
            "preferred_colors": character.appearance.preferred_colors,
            "style_keywords": character.appearance.style_keywords,
            "base_model": character.appearance.base_model,
            "negative_prompt": character.appearance.negative_prompt,
            "default_prompt_prefix": character.appearance.default_prompt_prefix,
        }

    return {
        "success": True,
        "data": response_data,
    }


@router.put("/{character_id}", response_model=dict)
async def update_character(
    character_id: UUID,
    character_data: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update character information."""
    # Get character with relationships
    query = (
        select(Character)
        .options(
            selectinload(Character.personality),
            selectinload(Character.appearance),
        )
        .where(Character.id == character_id)
        .where(Character.deleted_at.is_(None))
    )

    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Update character fields
    if character_data.name is not None:
        character.name = character_data.name
    if character_data.bio is not None:
        character.bio = character_data.bio
    if character_data.age is not None:
        character.age = character_data.age
    if character_data.location is not None:
        character.location = character_data.location
    if character_data.timezone is not None:
        character.timezone = character_data.timezone
    if character_data.interests is not None:
        character.interests = character_data.interests
    if character_data.profile_image_url is not None:
        character.profile_image_url = character_data.profile_image_url
    if character_data.profile_image_path is not None:
        character.profile_image_path = character_data.profile_image_path

    # Update or create personality
    if character_data.personality:
        if character.personality:
            # Update existing personality
            personality = character.personality
            if character_data.personality.extroversion is not None:
                personality.extroversion = character_data.personality.extroversion
            if character_data.personality.creativity is not None:
                personality.creativity = character_data.personality.creativity
            if character_data.personality.humor is not None:
                personality.humor = character_data.personality.humor
            if character_data.personality.professionalism is not None:
                personality.professionalism = character_data.personality.professionalism
            if character_data.personality.authenticity is not None:
                personality.authenticity = character_data.personality.authenticity
            if character_data.personality.communication_style is not None:
                personality.communication_style = character_data.personality.communication_style
            if character_data.personality.preferred_topics is not None:
                personality.preferred_topics = character_data.personality.preferred_topics
            if character_data.personality.content_tone is not None:
                personality.content_tone = character_data.personality.content_tone
            if character_data.personality.llm_personality_prompt is not None:
                personality.llm_personality_prompt = character_data.personality.llm_personality_prompt
            if character_data.personality.temperature is not None:
                personality.temperature = character_data.personality.temperature
        else:
            # Create new personality
            personality = CharacterPersonality(
                character_id=character.id,
                extroversion=character_data.personality.extroversion or 0.5,
                creativity=character_data.personality.creativity or 0.5,
                humor=character_data.personality.humor or 0.5,
                professionalism=character_data.personality.professionalism or 0.5,
                authenticity=character_data.personality.authenticity or 0.5,
                communication_style=character_data.personality.communication_style,
                preferred_topics=character_data.personality.preferred_topics,
                content_tone=character_data.personality.content_tone,
                llm_personality_prompt=character_data.personality.llm_personality_prompt,
                temperature=character_data.personality.temperature or 0.7,
            )
            db.add(personality)

    # Update or create appearance
    if character_data.appearance:
        if character.appearance:
            # Update existing appearance
            appearance = character.appearance
            if character_data.appearance.face_reference_image_url is not None:
                appearance.face_reference_image_url = character_data.appearance.face_reference_image_url
            if character_data.appearance.face_reference_image_path is not None:
                appearance.face_reference_image_path = character_data.appearance.face_reference_image_path
            if character_data.appearance.face_consistency_method is not None:
                appearance.face_consistency_method = character_data.appearance.face_consistency_method
            if character_data.appearance.lora_model_path is not None:
                appearance.lora_model_path = character_data.appearance.lora_model_path
            if character_data.appearance.hair_color is not None:
                appearance.hair_color = character_data.appearance.hair_color
            if character_data.appearance.hair_style is not None:
                appearance.hair_style = character_data.appearance.hair_style
            if character_data.appearance.eye_color is not None:
                appearance.eye_color = character_data.appearance.eye_color
            if character_data.appearance.skin_tone is not None:
                appearance.skin_tone = character_data.appearance.skin_tone
            if character_data.appearance.body_type is not None:
                appearance.body_type = character_data.appearance.body_type
            if character_data.appearance.height is not None:
                appearance.height = character_data.appearance.height
            if character_data.appearance.age_range is not None:
                appearance.age_range = character_data.appearance.age_range
            if character_data.appearance.clothing_style is not None:
                appearance.clothing_style = character_data.appearance.clothing_style
            if character_data.appearance.preferred_colors is not None:
                appearance.preferred_colors = character_data.appearance.preferred_colors
            if character_data.appearance.style_keywords is not None:
                appearance.style_keywords = character_data.appearance.style_keywords
            if character_data.appearance.base_model is not None:
                appearance.base_model = character_data.appearance.base_model
            if character_data.appearance.negative_prompt is not None:
                appearance.negative_prompt = character_data.appearance.negative_prompt
            if character_data.appearance.default_prompt_prefix is not None:
                appearance.default_prompt_prefix = character_data.appearance.default_prompt_prefix
        else:
            # Create new appearance
            appearance = CharacterAppearance(
                character_id=character.id,
                face_reference_image_url=character_data.appearance.face_reference_image_url,
                face_reference_image_path=character_data.appearance.face_reference_image_path,
                face_consistency_method=character_data.appearance.face_consistency_method or "ip-adapter",
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
                base_model=character_data.appearance.base_model or "realistic-vision-v6",
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
            "updated_at": character.updated_at.isoformat(),
        },
        "message": "Character updated successfully",
    }


@router.delete("/{character_id}", response_model=dict)
async def delete_character(
    character_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete (soft delete) a character."""
    query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))

    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Soft delete
    character.deleted_at = datetime.utcnow()
    character.status = "deleted"
    character.is_active = False

    await db.commit()

    return {
        "success": True,
        "message": "Character deleted successfully",
    }


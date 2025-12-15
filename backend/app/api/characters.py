"""Character management API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.character import Character, CharacterAppearance, CharacterPersonality
from app.models.character_style import CharacterImageStyle

logger = logging.getLogger(__name__)
from app.services.character_content_service import (
    CharacterContentRequest,
    character_content_service,
)
from app.services.generation_service import generation_service

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


class CharacterImageGenerateRequest(BaseModel):
    """Request model for character-specific image generation."""

    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str | None = Field(None, max_length=2000)
    seed: int | None = None
    width: int = Field(default=1024, ge=256, le=4096)
    height: int = Field(default=1024, ge=256, le=4096)
    steps: int = Field(default=25, ge=1, le=200)
    cfg: float = Field(default=7.0, ge=0.0, le=30.0)
    sampler_name: str = Field(default="euler", max_length=64)
    scheduler: str = Field(default="normal", max_length=64)
    batch_size: int = Field(default=1, ge=1, le=8)


@router.post("/{character_id}/generate/image", response_model=dict)
async def generate_character_image(
    character_id: UUID,
    req: CharacterImageGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate image for a character using their appearance settings."""
    # Get character with appearance
    query = (
        select(Character)
        .options(selectinload(Character.appearance))
        .where(Character.id == character_id)
        .where(Character.deleted_at.is_(None))
    )

    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Build prompt with character's default prompt prefix if available
    final_prompt = req.prompt
    if character.appearance and character.appearance.default_prompt_prefix:
        final_prompt = f"{character.appearance.default_prompt_prefix}, {req.prompt}"

    # Use character's appearance settings
    negative_prompt = req.negative_prompt
    if character.appearance and character.appearance.negative_prompt:
        if negative_prompt:
            negative_prompt = f"{character.appearance.negative_prompt}, {negative_prompt}"
        else:
            negative_prompt = character.appearance.negative_prompt

    checkpoint = None
    if character.appearance and character.appearance.base_model:
        checkpoint = character.appearance.base_model

    # Create image generation job
    job = generation_service.create_image_job(
        prompt=final_prompt,
        negative_prompt=negative_prompt,
        seed=req.seed,
        checkpoint=checkpoint,
        width=req.width,
        height=req.height,
        steps=req.steps,
        cfg=req.cfg,
        sampler_name=req.sampler_name,
        scheduler=req.scheduler,
        batch_size=req.batch_size,
    )

    return {
        "success": True,
        "data": {
            "job_id": job.id,
            "state": job.state,
            "character_id": str(character.id),
            "character_name": character.name,
        },
        "message": "Image generation job created successfully",
    }


class CharacterContentGenerateRequest(BaseModel):
    """Request model for character-specific content generation."""

    content_type: str = Field(..., pattern="^(image|image_with_caption|text|video|audio)$")
    prompt: str | None = Field(None, min_length=1, max_length=2000)
    platform: str = Field(default="instagram", pattern="^(instagram|twitter|facebook|tiktok)$")
    category: str | None = Field(None, max_length=50)  # post, story, reel, short, message
    include_caption: bool = Field(default=False)
    is_nsfw: bool = Field(default=False)


@router.post("/{character_id}/generate/content", response_model=dict)
async def generate_character_content(
    character_id: UUID,
    req: CharacterContentGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate character-specific content (image, text, etc.) with full character context.

    This endpoint orchestrates content generation using the character's personality,
    appearance, and preferences to ensure consistency across all content types.
    """
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

    # Build request
    content_request = CharacterContentRequest(
        character_id=character_id,
        content_type=req.content_type,
        prompt=req.prompt,
        platform=req.platform,
        category=req.category,
        include_caption=req.include_caption,
        is_nsfw=req.is_nsfw,
    )

    # Generate content
    try:
        content_result = await character_content_service.generate_content(
            content_request,
            character,
            character.personality,
            character.appearance,
        )

        return {
            "success": True,
            "data": {
                "character_id": str(content_result.character_id),
                "content_type": content_result.content_type,
                "content_id": content_result.content_id,
                "file_path": content_result.file_path,
                "caption": content_result.caption,
                "hashtags": content_result.hashtags,
                "full_caption": content_result.full_caption,
                "metadata": content_result.metadata,
            },
            "message": f"{content_result.content_type} generation completed successfully",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Error generating content for character {character_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {exc}") from exc


# Character Image Style Models
class ImageStyleCreate(BaseModel):
    """Request model for creating a character image style."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    prompt_suffix: str | None = None
    prompt_prefix: str | None = None
    negative_prompt_addition: str | None = None
    checkpoint: str | None = Field(None, max_length=255)
    sampler_name: str | None = Field(None, max_length=64)
    scheduler: str | None = Field(None, max_length=64)
    steps: int | None = Field(None, ge=1, le=200)
    cfg: float | None = Field(None, ge=0.0, le=30.0)
    width: int | None = Field(None, ge=256, le=4096)
    height: int | None = Field(None, ge=256, le=4096)
    style_keywords: list[str] | None = None
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)


class ImageStyleUpdate(BaseModel):
    """Request model for updating a character image style (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    prompt_suffix: str | None = None
    prompt_prefix: str | None = None
    negative_prompt_addition: str | None = None
    checkpoint: str | None = Field(None, max_length=255)
    sampler_name: str | None = Field(None, max_length=64)
    scheduler: str | None = Field(None, max_length=64)
    steps: int | None = Field(None, ge=1, le=200)
    cfg: float | None = Field(None, ge=0.0, le=30.0)
    width: int | None = Field(None, ge=256, le=4096)
    height: int | None = Field(None, ge=256, le=4096)
    style_keywords: list[str] | None = None
    display_order: int | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class ImageStyleResponse(BaseModel):
    """Response model for character image style data."""

    id: UUID
    character_id: UUID
    name: str
    description: str | None
    prompt_suffix: str | None
    prompt_prefix: str | None
    negative_prompt_addition: str | None
    checkpoint: str | None
    sampler_name: str | None
    scheduler: str | None
    steps: int | None
    cfg: float | None
    width: int | None
    height: int | None
    style_keywords: list[str] | None
    display_order: int
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/{character_id}/styles", response_model=dict)
async def create_character_style(
    character_id: UUID,
    style_data: ImageStyleCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new image style for a character."""
    # Verify character exists
    query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # If this is set as default, unset other defaults for this character
    if style_data.is_default:
        existing_defaults_query = select(CharacterImageStyle).where(
            CharacterImageStyle.character_id == character_id,
            CharacterImageStyle.is_default == True,  # noqa: E712
        )
        existing_defaults_result = await db.execute(existing_defaults_query)
        existing_defaults = existing_defaults_result.scalars().all()
        for existing_style in existing_defaults:
            existing_style.is_default = False

    # Create style
    style = CharacterImageStyle(
        character_id=character_id,
        name=style_data.name,
        description=style_data.description,
        prompt_suffix=style_data.prompt_suffix,
        prompt_prefix=style_data.prompt_prefix,
        negative_prompt_addition=style_data.negative_prompt_addition,
        checkpoint=style_data.checkpoint,
        sampler_name=style_data.sampler_name,
        scheduler=style_data.scheduler,
        steps=style_data.steps,
        cfg=style_data.cfg,
        width=style_data.width,
        height=style_data.height,
        style_keywords=style_data.style_keywords,
        display_order=style_data.display_order,
        is_active=style_data.is_active,
        is_default=style_data.is_default,
    )
    db.add(style)
    await db.commit()
    await db.refresh(style)

    return {
        "success": True,
        "data": {
            "id": style.id,
            "name": style.name,
            "character_id": str(style.character_id),
            "is_default": style.is_default,
            "created_at": style.created_at.isoformat(),
        },
        "message": "Image style created successfully",
    }


@router.get("/{character_id}/styles", response_model=dict)
async def list_character_styles(
    character_id: UUID,
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get list of all image styles for a character."""
    # Verify character exists
    query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Build query
    style_query = select(CharacterImageStyle).where(CharacterImageStyle.character_id == character_id)

    # Apply filters
    if is_active is not None:
        style_query = style_query.where(CharacterImageStyle.is_active == is_active)

    # Order by display_order, then created_at
    style_query = style_query.order_by(CharacterImageStyle.display_order.asc(), CharacterImageStyle.created_at.asc())

    # Execute query
    style_result = await db.execute(style_query)
    styles = style_result.scalars().all()

    return {
        "success": True,
        "data": {
            "character_id": str(character_id),
            "styles": [
                {
                    "id": style.id,
                    "name": style.name,
                    "description": style.description,
                    "is_active": style.is_active,
                    "is_default": style.is_default,
                    "display_order": style.display_order,
                    "created_at": style.created_at.isoformat(),
                }
                for style in styles
            ],
            "total": len(styles),
        },
    }


@router.get("/{character_id}/styles/{style_id}", response_model=dict)
async def get_character_style(
    character_id: UUID,
    style_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get detailed information about a character image style."""
    # Verify character exists
    char_query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    char_result = await db.execute(char_query)
    character = char_result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Get style
    style_query = select(CharacterImageStyle).where(
        CharacterImageStyle.id == style_id,
        CharacterImageStyle.character_id == character_id,
    )
    style_result = await db.execute(style_query)
    style = style_result.scalar_one_or_none()

    if not style:
        raise HTTPException(status_code=404, detail=f"Image style '{style_id}' not found for character '{character_id}'")

    return {
        "success": True,
        "data": {
            "id": style.id,
            "character_id": str(style.character_id),
            "name": style.name,
            "description": style.description,
            "prompt_suffix": style.prompt_suffix,
            "prompt_prefix": style.prompt_prefix,
            "negative_prompt_addition": style.negative_prompt_addition,
            "checkpoint": style.checkpoint,
            "sampler_name": style.sampler_name,
            "scheduler": style.scheduler,
            "steps": int(style.steps) if style.steps else None,
            "cfg": float(style.cfg) if style.cfg else None,
            "width": style.width,
            "height": style.height,
            "style_keywords": style.style_keywords,
            "display_order": style.display_order,
            "is_active": style.is_active,
            "is_default": style.is_default,
            "created_at": style.created_at.isoformat(),
            "updated_at": style.updated_at.isoformat(),
        },
    }


@router.put("/{character_id}/styles/{style_id}", response_model=dict)
async def update_character_style(
    character_id: UUID,
    style_id: UUID,
    style_data: ImageStyleUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a character image style."""
    # Verify character exists
    char_query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    char_result = await db.execute(char_query)
    character = char_result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Get style
    style_query = select(CharacterImageStyle).where(
        CharacterImageStyle.id == style_id,
        CharacterImageStyle.character_id == character_id,
    )
    style_result = await db.execute(style_query)
    style = style_result.scalar_one_or_none()

    if not style:
        raise HTTPException(status_code=404, detail=f"Image style '{style_id}' not found for character '{character_id}'")

    # If setting as default, unset other defaults
    if style_data.is_default is True:
        existing_defaults_query = select(CharacterImageStyle).where(
            CharacterImageStyle.character_id == character_id,
            CharacterImageStyle.id != style_id,
            CharacterImageStyle.is_default == True,  # noqa: E712
        )
        existing_defaults_result = await db.execute(existing_defaults_query)
        existing_defaults = existing_defaults_result.scalars().all()
        for existing_style in existing_defaults:
            existing_style.is_default = False

    # Update fields
    if style_data.name is not None:
        style.name = style_data.name
    if style_data.description is not None:
        style.description = style_data.description
    if style_data.prompt_suffix is not None:
        style.prompt_suffix = style_data.prompt_suffix
    if style_data.prompt_prefix is not None:
        style.prompt_prefix = style_data.prompt_prefix
    if style_data.negative_prompt_addition is not None:
        style.negative_prompt_addition = style_data.negative_prompt_addition
    if style_data.checkpoint is not None:
        style.checkpoint = style_data.checkpoint
    if style_data.sampler_name is not None:
        style.sampler_name = style_data.sampler_name
    if style_data.scheduler is not None:
        style.scheduler = style_data.scheduler
    if style_data.steps is not None:
        style.steps = style_data.steps
    if style_data.cfg is not None:
        style.cfg = style_data.cfg
    if style_data.width is not None:
        style.width = style_data.width
    if style_data.height is not None:
        style.height = style_data.height
    if style_data.style_keywords is not None:
        style.style_keywords = style_data.style_keywords
    if style_data.display_order is not None:
        style.display_order = style_data.display_order
    if style_data.is_active is not None:
        style.is_active = style_data.is_active
    if style_data.is_default is not None:
        style.is_default = style_data.is_default

    await db.commit()
    await db.refresh(style)

    return {
        "success": True,
        "data": {
            "id": style.id,
            "name": style.name,
            "character_id": str(style.character_id),
            "is_default": style.is_default,
            "updated_at": style.updated_at.isoformat(),
        },
        "message": "Image style updated successfully",
    }


@router.delete("/{character_id}/styles/{style_id}", response_model=dict)
async def delete_character_style(
    character_id: UUID,
    style_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a character image style."""
    # Verify character exists
    char_query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    char_result = await db.execute(char_query)
    character = char_result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Get style
    style_query = select(CharacterImageStyle).where(
        CharacterImageStyle.id == style_id,
        CharacterImageStyle.character_id == character_id,
    )
    style_result = await db.execute(style_query)
    style = style_result.scalar_one_or_none()

    if not style:
        raise HTTPException(status_code=404, detail=f"Image style '{style_id}' not found for character '{character_id}'")

    # Delete style (CASCADE will handle it, but explicit delete is cleaner)
    await db.delete(style)
    await db.commit()

    return {
        "success": True,
        "message": "Image style deleted successfully",
    }


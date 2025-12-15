"""Character management API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
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
    style_keywords: list[str] | None = Field(None, description="Array of style descriptor keywords (max 50 items)")
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
    style_keywords: list[str] | None = Field(None, description="Array of style descriptor keywords (max 50 items)")
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
    """
    Create a new character with optional personality and appearance settings.

    This endpoint creates a new character profile in the system. The character can be
    created with basic information only, or with detailed personality traits and
    appearance settings for AI content generation.

    Args:
        character_data: Character creation data including name, bio, age, location,
            timezone, interests, and optional personality/appearance settings.
        db: Database session dependency.

    Returns:
        dict: Success response with created character data including:
            - success: Boolean indicating operation success
            - data: Character information (id, name, status, created_at)
            - message: Success message

    Raises:
        HTTPException: If validation fails or database error occurs.

    Example:
        ```json
        {
            "success": true,
            "data": {
                "id": "uuid-here",
                "name": "Character Name",
                "status": "active",
                "created_at": "2025-12-15T19:16:00Z"
            },
            "message": "Character created successfully"
        }
        ```
    """
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
    """
    Get list of all characters with pagination and filtering.

    Retrieves a paginated list of all active characters in the system. Supports
    filtering by status and searching by name. Results are ordered by creation
    date (newest first).

    Args:
        status: Optional status filter (active, paused, error, deleted).
            Only non-deleted characters are returned.
        search: Optional search term to filter characters by name (case-insensitive).
        limit: Maximum number of results to return (1-100, default: 20).
        offset: Number of results to skip for pagination (default: 0).
        db: Database session dependency.

    Returns:
        dict: Success response with paginated character list:
            - success: Boolean indicating operation success
            - data: Object containing:
                - characters: List of character summaries (id, name, bio, status,
                  profile_image_url, created_at)
                - total: Total number of matching characters
                - limit: Applied limit value
                - offset: Applied offset value

    Example:
        ```json
        {
            "success": true,
            "data": {
                "characters": [...],
                "total": 42,
                "limit": 20,
                "offset": 0
            }
        }
        ```
    """
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
    """
    Get detailed character information including personality and appearance.

    Retrieves complete character profile data including all basic information,
    personality traits, and appearance settings. This is the primary endpoint
    for viewing a character's full configuration.

    Args:
        character_id: UUID of the character to retrieve.
        db: Database session dependency.

    Returns:
        dict: Success response with complete character data:
            - success: Boolean indicating operation success
            - data: Character object with all fields including:
                - Basic info: id, name, bio, age, location, timezone, interests
                - Status: status, is_active
                - Personality: All personality traits and LLM settings (if exists)
                - Appearance: All appearance settings and generation config (if exists)
                - Timestamps: created_at, updated_at

    Raises:
        HTTPException: 404 if character not found or has been deleted.

    Example:
        ```json
        {
            "success": true,
            "data": {
                "id": "uuid-here",
                "name": "Character Name",
                "personality": {...},
                "appearance": {...}
            }
        }
        ```
    """
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
    """
    Update character information including personality and appearance.

    Updates one or more fields of an existing character. All fields in the
    request are optional - only provided fields will be updated. Personality
    and appearance can be updated or created if they don't exist.

    Args:
        character_id: UUID of the character to update.
        character_data: Character update data with optional fields for:
            - Basic info: name, bio, age, location, timezone, interests
            - Profile images: profile_image_url, profile_image_path
            - Personality: All personality traits (creates if missing)
            - Appearance: All appearance settings (creates if missing)
        db: Database session dependency.

    Returns:
        dict: Success response with updated character data:
            - success: Boolean indicating operation success
            - data: Updated character info (id, name, status, updated_at)
            - message: Success message

    Raises:
        HTTPException: 404 if character not found or has been deleted.

    Example:
        ```json
        {
            "success": true,
            "data": {
                "id": "uuid-here",
                "name": "Updated Name",
                "status": "active",
                "updated_at": "2025-12-15T19:16:00Z"
            },
            "message": "Character updated successfully"
        }
        ```
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
    """
    Delete (soft delete) a character.

    Performs a soft delete on the character by setting deleted_at timestamp,
    status to "deleted", and is_active to False. The character and all related
    data (personality, appearance, styles, content) remain in the database
    but are excluded from normal queries.

    Args:
        character_id: UUID of the character to delete.
        db: Database session dependency.

    Returns:
        dict: Success response:
            - success: Boolean indicating operation success
            - message: Success message

    Raises:
        HTTPException: 404 if character not found or already deleted.

    Note:
        This is a soft delete. To permanently remove data, use database
        administration tools. Related content, styles, and scheduled posts
        are preserved but marked as inactive.
    """
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
    style_id: UUID | None = Field(None, description="Optional image style ID to apply")
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
    """
    Generate image for a character using their appearance settings and optional image style.

    Creates an image generation job for a specific character. The generation uses
    the character's appearance settings (base model, negative prompt, prompt prefix)
    and optionally applies a character image style. Style settings override request
    parameters, and appearance settings serve as fallback.

    Args:
        character_id: UUID of the character for image generation.
        req: Image generation request with:
            - prompt: Main generation prompt (required)
            - negative_prompt: Optional negative prompt
            - style_id: Optional image style ID to apply
            - seed: Optional random seed for reproducibility
            - width/height: Image dimensions (default: 1024x1024)
            - steps: Number of generation steps (default: 25)
            - cfg: CFG scale (default: 7.0)
            - sampler_name: Sampler algorithm (default: "euler")
            - scheduler: Scheduler type (default: "normal")
            - batch_size: Number of images to generate (default: 1)
        db: Database session dependency.

    Returns:
        dict: Success response with job information:
            - success: Boolean indicating operation success
            - data: Job details including:
                - job_id: Generation job identifier
                - state: Current job state
                - character_id: Character UUID
                - character_name: Character name
                - style_id: Applied style ID (if any)
                - style_name: Applied style name (if any)
            - message: Success message

    Raises:
        HTTPException: 404 if character not found, deleted, or style not found/inactive.
        HTTPException: 400 if generation parameters are invalid.

    Note:
        The generation job is created asynchronously. Use the job_id to check
        status via the generation service endpoints.
    """
    # Get character with appearance and image styles
    query = (
        select(Character)
        .options(
            selectinload(Character.appearance),
            selectinload(Character.image_styles),
        )
        .where(Character.id == character_id)
        .where(Character.deleted_at.is_(None))
    )

    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Load image style if provided
    style = None
    if req.style_id:
        style_query = select(CharacterImageStyle).where(
            CharacterImageStyle.id == req.style_id,
            CharacterImageStyle.character_id == character_id,
            CharacterImageStyle.is_active == True,  # noqa: E712
        )
        style_result = await db.execute(style_query)
        style = style_result.scalar_one_or_none()
        if not style:
            raise HTTPException(
                status_code=404,
                detail=f"Image style '{req.style_id}' not found or inactive for character '{character_id}'",
            )

    # Build prompt with character's default prompt prefix and style modifications
    final_prompt = req.prompt
    if style and style.prompt_prefix:
        final_prompt = f"{style.prompt_prefix}, {final_prompt}"
    elif character.appearance and character.appearance.default_prompt_prefix:
        final_prompt = f"{character.appearance.default_prompt_prefix}, {final_prompt}"

    if style and style.prompt_suffix:
        final_prompt = f"{final_prompt}, {style.prompt_suffix}"

    # Build negative prompt
    negative_prompt = req.negative_prompt
    if style and style.negative_prompt_addition:
        if negative_prompt:
            negative_prompt = f"{negative_prompt}, {style.negative_prompt_addition}"
        else:
            negative_prompt = style.negative_prompt_addition

    if character.appearance and character.appearance.negative_prompt:
        if negative_prompt:
            negative_prompt = f"{character.appearance.negative_prompt}, {negative_prompt}"
        else:
            negative_prompt = character.appearance.negative_prompt

    # Determine generation settings (style overrides request, appearance is fallback)
    checkpoint = None
    if style and style.checkpoint:
        checkpoint = style.checkpoint
    elif character.appearance and character.appearance.base_model:
        checkpoint = character.appearance.base_model

    width = style.width if style and style.width else req.width
    height = style.height if style and style.height else req.height
    steps = style.steps if style and style.steps else req.steps
    cfg = float(style.cfg) if style and style.cfg else req.cfg
    sampler_name = style.sampler_name if style and style.sampler_name else req.sampler_name
    scheduler = style.scheduler if style and style.scheduler else req.scheduler

    # Create image generation job
    job = generation_service.create_image_job(
        prompt=final_prompt,
        negative_prompt=negative_prompt,
        seed=req.seed,
        checkpoint=checkpoint,
        width=width,
        height=height,
        steps=steps,
        cfg=cfg,
        sampler_name=sampler_name,
        scheduler=scheduler,
        batch_size=req.batch_size,
    )

    return {
        "success": True,
        "data": {
            "job_id": job.id,
            "state": job.state,
            "character_id": str(character.id),
            "character_name": character.name,
            "style_id": str(style.id) if style else None,
            "style_name": style.name if style else None,
        },
        "message": "Image generation job created successfully",
    }


class CharacterContentGenerateRequest(BaseModel):
    """Request model for character-specific content generation."""

    content_type: str = Field(..., pattern="^(image|image_with_caption|text|video|audio)$", description="Type of content to generate: 'image', 'image_with_caption', 'text', 'video', or 'audio'")
    prompt: str | None = Field(None, min_length=1, max_length=2000, description="Optional generation prompt (character context used if omitted, 1-2000 characters)")
    style_id: UUID | None = Field(None, description="Optional image style ID to apply (for image content types)")
    platform: str = Field(default="instagram", pattern="^(instagram|twitter|facebook|tiktok)$", description="Target platform: 'instagram', 'twitter', 'facebook', or 'tiktok' (default: 'instagram')")
    category: str | None = Field(None, max_length=50, description="Content category: 'post', 'story', 'reel', 'short', 'message' (optional, max 50 characters)")
    include_caption: bool = Field(default=False, description="Whether to generate caption for image content (default: False)")
    is_nsfw: bool = Field(default=False, description="Whether content is NSFW (default: False)")


@router.post("/{character_id}/generate/content", response_model=dict)
async def generate_character_content(
    character_id: UUID,
    req: CharacterContentGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate character-specific content (image, text, video, audio) with full character context.

    Orchestrates comprehensive content generation using the character's personality,
    appearance, and preferences to ensure consistency across all content types. This
    endpoint handles the full content generation pipeline including image generation,
    caption creation, and platform-specific formatting.

    Args:
        character_id: UUID of the character for content generation.
        req: Content generation request with:
            - content_type: Type of content to generate (image, image_with_caption,
              text, video, audio)
            - prompt: Optional generation prompt (character context used if omitted)
            - style_id: Optional image style ID (for image content types)
            - platform: Target platform (instagram, twitter, facebook, tiktok)
            - category: Content category (post, story, reel, short, message)
            - include_caption: Whether to generate caption for image content
            - is_nsfw: Whether content is NSFW
        db: Database session dependency.

    Returns:
        dict: Success response with generated content information:
            - success: Boolean indicating operation success
            - data: Content details including:
                - character_id: Character UUID
                - content_type: Generated content type
                - content_id: Created content record ID
                - file_path: Local file path to generated content
                - caption: Generated caption (if applicable)
                - hashtags: Generated hashtags (if applicable)
                - full_caption: Complete caption with hashtags (if applicable)
                - metadata: Additional generation metadata
            - message: Success message

    Raises:
        HTTPException: 404 if character not found, deleted, or style not found/inactive.
        HTTPException: 400 if content type is invalid or generation fails.
        HTTPException: 500 if content generation service error occurs.

    Note:
        This endpoint uses the character content service which applies personality
        traits, appearance settings, and style modifications automatically.
    """
    # Get character with relationships
    query = (
        select(Character)
        .options(
            selectinload(Character.personality),
            selectinload(Character.appearance),
            selectinload(Character.image_styles),
        )
        .where(Character.id == character_id)
        .where(Character.deleted_at.is_(None))
    )

    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Load image style if provided
    style = None
    if req.style_id:
        style_query = select(CharacterImageStyle).where(
            CharacterImageStyle.id == req.style_id,
            CharacterImageStyle.character_id == character_id,
            CharacterImageStyle.is_active == True,  # noqa: E712
        )
        style_result = await db.execute(style_query)
        style = style_result.scalar_one_or_none()
        if not style:
            raise HTTPException(
                status_code=404,
                detail=f"Image style '{req.style_id}' not found or inactive for character '{character_id}'",
            )

    # Build request
    content_request = CharacterContentRequest(
        character_id=character_id,
        content_type=req.content_type,
        prompt=req.prompt,
        style_id=req.style_id,
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
            style,
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

    name: str = Field(..., min_length=1, max_length=255, description="Style name (1-255 characters)")
    description: str | None = Field(None, description="Optional style description")
    prompt_suffix: str | None = Field(None, description="Additional prompt text appended for this style")
    prompt_prefix: str | None = Field(None, description="Additional prompt text prepended for this style")
    negative_prompt_addition: str | None = Field(None, description="Additional negative prompt text for this style")
    checkpoint: str | None = Field(None, max_length=255, description="Override checkpoint model name (optional)")
    sampler_name: str | None = Field(None, max_length=64, description="Override sampler name (optional)")
    scheduler: str | None = Field(None, max_length=64, description="Override scheduler name (optional)")
    steps: int | None = Field(None, ge=1, le=200, description="Override number of steps (1-200, optional)")
    cfg: float | None = Field(None, ge=0.0, le=30.0, description="Override CFG scale (0.0-30.0, optional)")
    width: int | None = Field(None, ge=256, le=4096, description="Override image width (256-4096, optional)")
    height: int | None = Field(None, ge=256, le=4096, description="Override image height (256-4096, optional)")
    style_keywords: list[str] | None = Field(None, description="Array of style descriptor keywords (max 50 items)")
    display_order: int = Field(default=0, description="Order for UI display (default: 0)")
    is_active: bool = Field(default=True, description="Whether style is active (default: True)")
    is_default: bool = Field(default=False, description="Whether this is the default style (default: False)")

    @field_validator("style_keywords")
    @classmethod
    def validate_style_keywords(cls, v: list[str] | None) -> list[str] | None:
        """Validate style_keywords array length."""
        if v is not None and len(v) > 50:
            raise ValueError("style_keywords array cannot exceed 50 items")
        return v


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
    style_keywords: list[str] | None = Field(None, description="Array of style descriptor keywords (max 50 items)")
    display_order: int | None = None
    is_active: bool | None = None
    is_default: bool | None = None

    @field_validator("style_keywords")
    @classmethod
    def validate_style_keywords(cls, v: list[str] | None) -> list[str] | None:
        """Validate style_keywords array length."""
        if v is not None and len(v) > 50:
            raise ValueError("style_keywords array cannot exceed 50 items")
        return v


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
    """
    Create a new image style for a character.

    Creates a new image style configuration for a character. Image styles allow
    different visual styles (e.g., "Casual", "Formal", "Sporty") to be applied
    during image generation. If the style is marked as default, any existing
    default style for the character will be unset.

    Args:
        character_id: UUID of the character to create style for.
        style_data: Style creation data including:
            - name: Style name (required, 1-255 characters)
            - description: Optional style description
            - prompt_suffix/prefix: Prompt modifications for this style
            - negative_prompt_addition: Additional negative prompt text
            - checkpoint: Override checkpoint model (optional)
            - sampler_name/scheduler: Override sampler/scheduler (optional)
            - steps/cfg: Override generation steps and CFG scale (optional)
            - width/height: Override image dimensions (optional)
            - style_keywords: Array of style descriptor keywords
            - display_order: Order for UI display (default: 0)
            - is_active: Whether style is active (default: True)
            - is_default: Whether this is the default style (default: False)
        db: Database session dependency.

    Returns:
        dict: Success response with created style data:
            - success: Boolean indicating operation success
            - data: Style information (id, name, character_id, is_default, created_at)
            - message: Success message

    Raises:
        HTTPException: 404 if character not found or has been deleted.

    Note:
        Only one style per character can be marked as default. Setting is_default=True
        will automatically unset any existing default style for the character.
    """
    # Verify character exists
    query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        logger.warning(f"Attempted to create style for non-existent character: {character_id}")
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    logger.info(f"Creating image style '{style_data.name}' for character '{character_id}'")

    # Check for duplicate style name for this character
    existing_style_query = select(CharacterImageStyle).where(
        CharacterImageStyle.character_id == character_id,
        CharacterImageStyle.name == style_data.name,
    )
    existing_style_result = await db.execute(existing_style_query)
    existing_style = existing_style_result.scalar_one_or_none()
    if existing_style:
        logger.warning(f"Duplicate style name '{style_data.name}' for character '{character_id}'")
        raise HTTPException(
            status_code=400,
            detail=f"An image style with name '{style_data.name}' already exists for this character",
        )

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
    try:
        db.add(style)
        await db.commit()
        await db.refresh(style)
    except Exception as e:
        logger.error(f"Failed to create image style for character '{character_id}': {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create image style. Please try again.")

    logger.info(f"Successfully created image style '{style.id}' ({style.name}) for character '{character_id}'")

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
    """
    Get list of all image styles for a character.

    Retrieves all image styles configured for a character, optionally filtered
    by active status. Results are ordered by display_order (ascending), then by
    creation date (ascending).

    Args:
        character_id: UUID of the character to get styles for.
        is_active: Optional filter to show only active/inactive styles.
            If None, returns all styles regardless of status.
        db: Database session dependency.

    Returns:
        dict: Success response with style list:
            - success: Boolean indicating operation success
            - data: Object containing:
                - character_id: Character UUID
                - styles: List of style summaries (id, name, description,
                  is_active, is_default, display_order, created_at)
                - total: Total number of styles (after filtering)

    Raises:
        HTTPException: 404 if character not found or has been deleted.

    Example:
        ```json
        {
            "success": true,
            "data": {
                "character_id": "uuid-here",
                "styles": [...],
                "total": 3
            }
        }
        ```
    """
    # Verify character exists
    query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    result = await db.execute(query)
    character = result.scalar_one_or_none()

    if not character:
        logger.warning(f"Attempted to list styles for non-existent character: {character_id}")
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    logger.debug(f"Listing image styles for character '{character_id}' (is_active={is_active})")

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
    """
    Get detailed information about a character image style.

    Retrieves complete configuration for a specific image style, including all
    prompt modifications, generation settings, and metadata.

    Args:
        character_id: UUID of the character that owns the style.
        style_id: UUID of the style to retrieve.
        db: Database session dependency.

    Returns:
        dict: Success response with complete style data:
            - success: Boolean indicating operation success
            - data: Style object with all fields including:
                - Basic info: id, character_id, name, description
                - Prompt modifications: prompt_suffix, prompt_prefix,
                  negative_prompt_addition
                - Generation settings: checkpoint, sampler_name, scheduler,
                  steps, cfg, width, height
                - Metadata: style_keywords, display_order, is_active,
                  is_default, created_at, updated_at

    Raises:
        HTTPException: 404 if character not found, deleted, or style not found.

    Example:
        ```json
        {
            "success": true,
            "data": {
                "id": "style-uuid",
                "name": "Casual",
                "prompt_prefix": "casual outfit, relaxed",
                "steps": 30,
                "is_default": true
            }
        }
        ```
    """
    # Verify character exists
    char_query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    char_result = await db.execute(char_query)
    character = char_result.scalar_one_or_none()

    if not character:
        logger.warning(f"Attempted to get style for non-existent character: {character_id}")
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Get style
    style_query = select(CharacterImageStyle).where(
        CharacterImageStyle.id == style_id,
        CharacterImageStyle.character_id == character_id,
    )
    style_result = await db.execute(style_query)
    style = style_result.scalar_one_or_none()

    if not style:
        logger.warning(f"Image style '{style_id}' not found for character '{character_id}'")
        raise HTTPException(status_code=404, detail=f"Image style '{style_id}' not found for character '{character_id}'")

    logger.debug(f"Retrieved image style '{style_id}' ({style.name}) for character '{character_id}'")

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
    """
    Update a character image style.

    Updates one or more fields of an existing image style. All fields in the
    request are optional - only provided fields will be updated. If setting
    is_default to True, any existing default style for the character will be
    automatically unset.

    Args:
        character_id: UUID of the character that owns the style.
        style_id: UUID of the style to update.
        style_data: Style update data with optional fields (same as ImageStyleCreate
            but all fields optional). Can update any style configuration including
            name, description, prompt modifications, generation settings, and metadata.
        db: Database session dependency.

    Returns:
        dict: Success response with updated style data:
            - success: Boolean indicating operation success
            - data: Updated style information (id, name, character_id, is_default, updated_at)
            - message: Success message

    Raises:
        HTTPException: 404 if character not found, deleted, or style not found.

    Note:
        Setting is_default=True will automatically unset any other default style
        for the character. Only one style per character can be default.
    """
    # Verify character exists
    char_query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    char_result = await db.execute(char_query)
    character = char_result.scalar_one_or_none()

    if not character:
        logger.warning(f"Attempted to update style for non-existent character: {character_id}")
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Get style
    style_query = select(CharacterImageStyle).where(
        CharacterImageStyle.id == style_id,
        CharacterImageStyle.character_id == character_id,
    )
    style_result = await db.execute(style_query)
    style = style_result.scalar_one_or_none()

    if not style:
        logger.warning(f"Image style '{style_id}' not found for character '{character_id}'")
        raise HTTPException(status_code=404, detail=f"Image style '{style_id}' not found for character '{character_id}'")

    logger.info(f"Updating image style '{style_id}' ({style.name}) for character '{character_id}'")

    # Check for duplicate style name if name is being updated
    if style_data.name is not None and style_data.name != style.name:
        existing_style_query = select(CharacterImageStyle).where(
            CharacterImageStyle.character_id == character_id,
            CharacterImageStyle.name == style_data.name,
            CharacterImageStyle.id != style_id,
        )
        existing_style_result = await db.execute(existing_style_query)
        existing_style = existing_style_result.scalar_one_or_none()
        if existing_style:
            logger.warning(f"Duplicate style name '{style_data.name}' for character '{character_id}'")
            raise HTTPException(
                status_code=400,
                detail=f"An image style with name '{style_data.name}' already exists for this character",
            )

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

    try:
        await db.commit()
        await db.refresh(style)
    except Exception as e:
        logger.error(f"Failed to update image style '{style_id}' for character '{character_id}': {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update image style. Please try again.")

    logger.info(f"Successfully updated image style '{style_id}' ({style.name}) for character '{character_id}'")

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
    """
    Delete a character image style.

    Permanently deletes an image style from the character. This operation cannot
    be undone. The style will be removed from the database and will no longer
    be available for image generation.

    Args:
        character_id: UUID of the character that owns the style.
        style_id: UUID of the style to delete.
        db: Database session dependency.

    Returns:
        dict: Success response:
            - success: Boolean indicating operation success
            - message: Success message

    Raises:
        HTTPException: 404 if character not found, deleted, or style not found.

    Warning:
        This is a permanent deletion. The style and all its configuration will
        be removed from the database. Any ongoing or future image generation
        jobs that reference this style will fail or fall back to default settings.
    """
    # Verify character exists
    char_query = select(Character).where(Character.id == character_id).where(Character.deleted_at.is_(None))
    char_result = await db.execute(char_query)
    character = char_result.scalar_one_or_none()

    if not character:
        logger.warning(f"Attempted to delete style for non-existent character: {character_id}")
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")

    # Get style
    style_query = select(CharacterImageStyle).where(
        CharacterImageStyle.id == style_id,
        CharacterImageStyle.character_id == character_id,
    )
    style_result = await db.execute(style_query)
    style = style_result.scalar_one_or_none()

    if not style:
        logger.warning(f"Image style '{style_id}' not found for character '{character_id}'")
        raise HTTPException(status_code=404, detail=f"Image style '{style_id}' not found for character '{character_id}'")

    style_name = style.name
    logger.info(f"Deleting image style '{style_id}' ({style_name}) for character '{character_id}'")

    # Delete style (CASCADE will handle it, but explicit delete is cleaner)
    try:
        await db.delete(style)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to delete image style '{style_id}' for character '{character_id}': {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete image style. Please try again.")

    logger.info(f"Successfully deleted image style '{style_id}' ({style_name}) for character '{character_id}'")

    return {
        "success": True,
        "message": "Image style deleted successfully",
    }


"""Character template marketplace API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.character import Character, CharacterPersonality, CharacterAppearance
from app.models.character_template import CharacterTemplate
from app.models.user import User
from app.api.auth import get_current_user_from_token
from app.api.characters import CharacterCreate, PersonalityCreate, AppearanceCreate

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class TemplatePublishRequest(BaseModel):
    """Request model for publishing a character as a template."""
    
    character_id: UUID = Field(..., description="ID of the character to publish as template")
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: str | None = Field(None, description="Template description")
    category: str | None = Field(None, description="Template category (e.g., influencer, professional)")
    tags: list[str] | None = Field(None, description="Tags for search/filtering")
    preview_image_url: str | None = Field(None, description="Preview image URL")
    is_public: bool = Field(default=True, description="Whether template is publicly visible")


class TemplateUseRequest(BaseModel):
    """Request model for using a template to create a character."""
    
    template_id: UUID = Field(..., description="ID of the template to use")
    name: str | None = Field(None, min_length=1, max_length=255, description="Optional new character name (uses template name if not provided)")
    team_id: str | None = Field(None, description="Optional team ID for team-shared characters")


class TemplateResponse(BaseModel):
    """Response model for template data."""
    
    id: UUID
    creator_id: UUID | None
    name: str
    description: str | None
    category: str | None
    tags: list[str] | None
    preview_image_url: str | None
    is_featured: bool
    is_public: bool
    download_count: int
    rating: float | None
    rating_count: int
    created_at: datetime
    updated_at: datetime
    creator_name: str | None = None  # Creator username/email
    
    class Config:
        from_attributes = True


class TemplateDetailResponse(TemplateResponse):
    """Response model for template details including template_data."""
    
    template_data: dict  # Full character data (character, personality, appearance)


@router.get("", response_model=dict)
async def list_templates(
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search in name, description, tags"),
    featured_only: bool = Query(False, description="Show only featured templates"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List available character templates in the marketplace.
    
    Returns a paginated list of public templates that users can browse and use.
    Supports filtering by category, search query, and featured status.
    
    Args:
        category: Optional category filter.
        search: Optional search query (searches name, description, tags).
        featured_only: If True, only return featured templates.
        limit: Maximum number of results (1-100, default: 20).
        offset: Number of results to skip for pagination.
        db: Database session dependency.
        
    Returns:
        dict: Success response with list of templates and pagination info.
    """
    # Build query
    query = select(CharacterTemplate).where(
        and_(
            CharacterTemplate.deleted_at.is_(None),
            CharacterTemplate.is_public == True,
        )
    )
    
    # Apply filters
    if category:
        query = query.where(CharacterTemplate.category == category)
    
    if featured_only:
        query = query.where(CharacterTemplate.is_featured == True)
    
    if search:
        search_filter = or_(
            CharacterTemplate.name.ilike(f"%{search}%"),
            CharacterTemplate.description.ilike(f"%{search}%"),
            CharacterTemplate.tags.contains([search]),
        )
        query = query.where(search_filter)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply pagination and ordering
    query = query.order_by(
        CharacterTemplate.is_featured.desc(),
        CharacterTemplate.download_count.desc(),
        CharacterTemplate.created_at.desc()
    ).limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    templates = result.scalars().all()
    
    # Load creator info
    template_list = []
    for template in templates:
        template_dict = {
            "id": template.id,
            "creator_id": template.creator_id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "tags": template.tags,
            "preview_image_url": template.preview_image_url,
            "is_featured": template.is_featured,
            "is_public": template.is_public,
            "download_count": template.download_count,
            "rating": float(template.rating) if template.rating else None,
            "rating_count": template.rating_count,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
            "creator_name": None,
        }
        
        # Load creator name if available
        if template.creator_id:
            creator_query = select(User).where(User.id == template.creator_id)
            creator_result = await db.execute(creator_query)
            creator = creator_result.scalar_one_or_none()
            if creator:
                template_dict["creator_name"] = creator.email or creator.username
        
        template_list.append(template_dict)
    
    return {
        "success": True,
        "data": template_list,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
        },
    }


@router.get("/{template_id}", response_model=dict)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get detailed information about a specific template.
    
    Returns full template data including the template_data JSON which contains
    all character, personality, and appearance information.
    
    Args:
        template_id: UUID of the template to retrieve.
        db: Database session dependency.
        
    Returns:
        dict: Success response with template details.
        
    Raises:
        HTTPException: 404 if template not found or not public.
    """
    query = select(CharacterTemplate).where(
        and_(
            CharacterTemplate.id == template_id,
            CharacterTemplate.deleted_at.is_(None),
            CharacterTemplate.is_public == True,
        )
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    
    # Load creator info
    creator_name = None
    if template.creator_id:
        creator_query = select(User).where(User.id == template.creator_id)
        creator_result = await db.execute(creator_query)
        creator = creator_result.scalar_one_or_none()
        if creator:
            creator_name = creator.email or creator.username
    
    template_dict = {
        "id": template.id,
        "creator_id": template.creator_id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "tags": template.tags,
        "preview_image_url": template.preview_image_url,
        "is_featured": template.is_featured,
        "is_public": template.is_public,
        "download_count": template.download_count,
        "rating": float(template.rating) if template.rating else None,
        "rating_count": template.rating_count,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
        "creator_name": creator_name,
        "template_data": template.template_data,  # Full character data
    }
    
    return {
        "success": True,
        "data": template_dict,
    }


@router.post("/publish", response_model=dict)
async def publish_template(
    request: TemplatePublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
) -> dict:
    """
    Publish a character as a template in the marketplace.
    
    Creates a new template from an existing character, including all personality
    and appearance data. The character must be owned by the current user.
    
    Args:
        request: Template publish request with character_id and template metadata.
        db: Database session dependency.
        current_user: Current authenticated user.
        
    Returns:
        dict: Success response with created template data.
        
    Raises:
        HTTPException: 404 if character not found, 403 if user doesn't own character.
    """
    # Get character with personality and appearance
    query = (
        select(Character)
        .where(
            and_(
                Character.id == request.character_id,
                Character.deleted_at.is_(None),
            )
        )
        .options(
            selectinload(Character.personality),
            selectinload(Character.appearance),
        )
    )
    result = await db.execute(query)
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{request.character_id}' not found")
    
    # Verify ownership
    if character.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only publish templates from your own characters",
        )
    
    # Build template data JSON
    template_data = {
        "character": {
            "name": character.name,
            "bio": character.bio,
            "age": character.age,
            "location": character.location,
            "timezone": character.timezone,
            "interests": character.interests,
            "profile_image_url": character.profile_image_url,
        },
    }
    
    # Add personality data if exists
    if character.personality:
        template_data["personality"] = {
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
    
    # Add appearance data if exists
    if character.appearance:
        template_data["appearance"] = {
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
    
    # Create template
    template = CharacterTemplate(
        creator_id=current_user.id,
        name=request.name,
        description=request.description,
        category=request.category,
        tags=request.tags,
        template_data=template_data,
        preview_image_url=request.preview_image_url or character.profile_image_url,
        is_public=request.is_public,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return {
        "success": True,
        "data": {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "created_at": template.created_at,
        },
        "message": "Template published successfully",
    }


@router.post("/{template_id}/use", response_model=dict)
async def use_template(
    template_id: UUID,
    request: TemplateUseRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
) -> dict:
    """
    Use a template to create a new character.
    
    Creates a new character from a template, copying all personality and appearance
    settings. Increments the template's download_count.
    
    Args:
        template_id: UUID of the template to use.
        request: Optional request with custom character name and team_id.
        db: Database session dependency.
        current_user: Current authenticated user.
        
    Returns:
        dict: Success response with created character data.
        
    Raises:
        HTTPException: 404 if template not found or not public.
    """
    # Get template
    query = select(CharacterTemplate).where(
        and_(
            CharacterTemplate.id == template_id,
            CharacterTemplate.deleted_at.is_(None),
            CharacterTemplate.is_public == True,
        )
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    
    # Get template data
    template_data = template.template_data
    char_data = template_data.get("character", {})
    personality_data = template_data.get("personality")
    appearance_data = template_data.get("appearance")
    
    # Determine character name
    character_name = request.name if request and request.name else char_data.get("name", "New Character")
    
    # Verify team access if team_id is provided
    team_id = None
    if request and request.team_id:
        from app.models.team import Team, TeamMember
        try:
            team_uuid = UUID(request.team_id)
            team_query = select(Team).where(
                and_(
                    Team.id == team_uuid,
                    Team.deleted_at.is_(None),
                    Team.is_active == True,
                )
            )
            team_result = await db.execute(team_query)
            team = team_result.scalar_one_or_none()
            
            if not team:
                raise HTTPException(status_code=404, detail=f"Team '{request.team_id}' not found")
            
            if team.owner_id != current_user.id:
                membership_query = select(TeamMember).where(
                    and_(
                        TeamMember.team_id == team_uuid,
                        TeamMember.user_id == current_user.id,
                        TeamMember.deleted_at.is_(None),
                        TeamMember.is_active == True,
                    )
                )
                membership_result = await db.execute(membership_query)
                membership = membership_result.scalar_one_or_none()
                if not membership:
                    raise HTTPException(
                        status_code=403,
                        detail="You must be a team member or owner to create team characters",
                    )
            team_id = team_uuid
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid team_id format: '{request.team_id}'")
    
    # Create character from template
    character = Character(
        user_id=current_user.id,
        team_id=team_id,
        name=character_name,
        bio=char_data.get("bio"),
        age=char_data.get("age"),
        location=char_data.get("location"),
        timezone=char_data.get("timezone", "UTC"),
        interests=char_data.get("interests"),
        profile_image_url=char_data.get("profile_image_url"),
        status="active",
        is_active=True,
    )
    db.add(character)
    await db.flush()
    
    # Create personality if template has it
    if personality_data:
        personality = CharacterPersonality(
            character_id=character.id,
            extroversion=personality_data.get("extroversion"),
            creativity=personality_data.get("creativity"),
            humor=personality_data.get("humor"),
            professionalism=personality_data.get("professionalism"),
            authenticity=personality_data.get("authenticity"),
            communication_style=personality_data.get("communication_style"),
            preferred_topics=personality_data.get("preferred_topics"),
            content_tone=personality_data.get("content_tone"),
            llm_personality_prompt=personality_data.get("llm_personality_prompt"),
            temperature=personality_data.get("temperature", 0.7),
        )
        db.add(personality)
    
    # Create appearance if template has it
    if appearance_data:
        appearance = CharacterAppearance(
            character_id=character.id,
            face_reference_image_url=appearance_data.get("face_reference_image_url"),
            face_reference_image_path=appearance_data.get("face_reference_image_path"),
            face_consistency_method=appearance_data.get("face_consistency_method", "ip-adapter"),
            lora_model_path=appearance_data.get("lora_model_path"),
            hair_color=appearance_data.get("hair_color"),
            hair_style=appearance_data.get("hair_style"),
            eye_color=appearance_data.get("eye_color"),
            skin_tone=appearance_data.get("skin_tone"),
            body_type=appearance_data.get("body_type"),
            height=appearance_data.get("height"),
            age_range=appearance_data.get("age_range"),
            clothing_style=appearance_data.get("clothing_style"),
            preferred_colors=appearance_data.get("preferred_colors"),
            style_keywords=appearance_data.get("style_keywords"),
            base_model=appearance_data.get("base_model", "realistic-vision-v6"),
            negative_prompt=appearance_data.get("negative_prompt"),
            default_prompt_prefix=appearance_data.get("default_prompt_prefix"),
        )
        db.add(appearance)
    
    # Increment template download count
    template.download_count = (template.download_count or 0) + 1
    
    await db.commit()
    await db.refresh(character)
    
    return {
        "success": True,
        "data": {
            "id": character.id,
            "name": character.name,
            "status": character.status,
            "created_at": character.created_at,
        },
        "message": "Character created from template successfully",
    }

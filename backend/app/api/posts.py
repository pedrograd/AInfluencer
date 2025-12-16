"""Posts API endpoints for creating and managing posts (images, reels, stories)."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.post_service import PostService

logger = get_logger(__name__)

router = APIRouter()


class PostCreateRequest(BaseModel):
    """Request model for creating a post."""

    character_id: str = Field(..., description="Character ID")
    platform_account_id: str = Field(..., description="Platform account ID")
    platform: str = Field(..., description="Platform (instagram, twitter, facebook, etc.)")
    post_type: str = Field(..., description="Post type (post, story, reel, short, tweet, message)")
    content_id: Optional[str] = Field(default=None, description="Primary content ID (image/video)")
    additional_content_ids: Optional[list[str]] = Field(
        default=None, description="Additional content IDs for carousels"
    )
    caption: Optional[str] = Field(default=None, description="Post caption/text")
    hashtags: Optional[list[str]] = Field(default=None, description="List of hashtags")
    mentions: Optional[list[str]] = Field(default=None, description="List of mentioned usernames")
    status: str = Field(default="draft", description="Post status (draft, scheduled, published, failed, deleted)")


class PostResponse(BaseModel):
    """Response model for post."""

    id: str
    character_id: str
    platform_account_id: str
    platform: str
    post_type: Optional[str]
    platform_post_id: Optional[str]
    platform_post_url: Optional[str]
    content_id: Optional[str]
    additional_content_ids: Optional[list[str]]
    caption: Optional[str]
    hashtags: Optional[list[str]]
    mentions: Optional[list[str]]
    likes_count: int
    comments_count: int
    shares_count: int
    views_count: int
    status: str
    published_at: Optional[str]
    error_message: Optional[str]
    retry_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=PostResponse)
async def create_post(
    req: PostCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Create a new post (image, reel, story, etc.).
    
    Creates a post record for a character. The post can be a draft, scheduled,
    or immediately published depending on the status field. Supports single images,
    carousels (multiple images), reels, stories, and other post types.
    
    Args:
        req: Post creation request with character, platform, content, and metadata
        db: Database session dependency
        
    Returns:
        PostResponse with created post information
        
    Raises:
        HTTPException: 400 if validation fails, 404 if character or content not found
    """
    try:
        post_service = PostService(db)
        
        # Convert string IDs to UUIDs
        character_uuid = UUID(req.character_id)
        platform_account_uuid = UUID(req.platform_account_id)
        content_uuid = UUID(req.content_id) if req.content_id else None
        additional_content_uuids = (
            [UUID(cid) for cid in req.additional_content_ids] if req.additional_content_ids else None
        )
        
        # Create post
        post = await post_service.create_post(
            character_id=character_uuid,
            platform_account_id=platform_account_uuid,
            platform=req.platform,
            post_type=req.post_type,
            content_id=content_uuid,
            additional_content_ids=additional_content_uuids,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
            status=req.status,
        )
        
        await db.commit()
        await db.refresh(post)
        
        return PostResponse.model_validate(post)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Get a post by ID.
    
    Args:
        post_id: Post UUID
        db: Database session dependency
        
    Returns:
        PostResponse with post information
        
    Raises:
        HTTPException: 404 if post not found
    """
    try:
        post_uuid = UUID(post_id)
        post_service = PostService(db)
        post = await post_service.get_post(post_uuid)
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return PostResponse.model_validate(post)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID format")


@router.get("", response_model=dict)
async def list_posts(
    character_id: Optional[str] = Query(default=None, description="Filter by character ID"),
    platform: Optional[str] = Query(default=None, description="Filter by platform"),
    post_type: Optional[str] = Query(default=None, description="Filter by post type (post, story, reel, etc.)"),
    status: Optional[str] = Query(default=None, description="Filter by status (draft, scheduled, published, etc.)"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of posts to return"),
    offset: int = Query(default=0, ge=0, description="Number of posts to skip"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List posts with optional filters.
    
    Args:
        character_id: Optional character ID filter
        platform: Optional platform filter
        post_type: Optional post type filter
        status: Optional status filter
        limit: Maximum number of posts to return (1-100)
        offset: Number of posts to skip
        db: Database session dependency
        
    Returns:
        Dictionary with posts list and total count
    """
    try:
        post_service = PostService(db)
        
        character_uuid = UUID(character_id) if character_id else None
        
        posts, total_count = await post_service.list_posts(
            character_id=character_uuid,
            platform=platform,
            post_type=post_type,
            status=status,
            limit=limit,
            offset=offset,
        )
        
        return {
            "ok": True,
            "posts": [PostResponse.model_validate(post).model_dump() for post in posts],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid character ID format")
    except Exception as e:
        logger.error(f"Error listing posts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list posts: {str(e)}")


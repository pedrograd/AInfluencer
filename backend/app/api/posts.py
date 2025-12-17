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
from app.services.integrated_posting_service import IntegratedPostingService, IntegratedPostingError
from app.services.follower_interaction_simulation_service import FollowerInteractionSimulationService

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


class CrossPostImageRequest(BaseModel):
    """Request model for cross-posting an image to multiple platforms."""

    content_id: str = Field(..., description="Content ID (must be image type and approved)")
    platform_account_ids: list[str] = Field(..., description="List of platform account IDs to post to")
    caption: Optional[str] = Field(default="", description="Post caption/text content")
    hashtags: Optional[list[str]] = Field(default=None, description="List of hashtags (without #)")
    mentions: Optional[list[str]] = Field(default=None, description="List of usernames to mention (without @)")


class CrossPostImageResponse(BaseModel):
    """Response model for cross-posting result."""

    ok: bool
    successful: dict[str, PostResponse] = Field(..., description="Successfully posted platforms and their posts")
    failed: dict[str, str] = Field(default_factory=dict, description="Failed platforms and error messages")
    total_platforms: int
    successful_count: int
    failed_count: int


@router.post("/cross-post", response_model=CrossPostImageResponse, tags=["posts"])
async def cross_post_image(
    req: CrossPostImageRequest,
    db: AsyncSession = Depends(get_db),
) -> CrossPostImageResponse:
    """
    Cross-post an image to multiple platforms simultaneously.
    
    Posts the same content to multiple platforms (Instagram, Twitter, Facebook)
    using their respective platform accounts. Each platform is posted to independently,
    and failures on one platform do not prevent posting to others.
    
    Args:
        req: Cross-post request containing:
            - content_id (str): Content UUID (must be image type and approved)
            - platform_account_ids (list[str]): List of platform account UUIDs to post to
            - caption (str, optional): Post caption/text content
            - hashtags (list[str], optional): List of hashtags (without #)
            - mentions (list[str], optional): List of usernames to mention (without @)
        db: Database session dependency
        
    Returns:
        CrossPostImageResponse with successful and failed posts
        
    Raises:
        HTTPException: 400 if validation fails, 404 if content not found, 500 if all platforms fail
    """
    try:
        # Convert string IDs to UUIDs
        content_uuid = UUID(req.content_id)
        platform_account_uuids = [UUID(pid) for pid in req.platform_account_ids]

        # Create integrated posting service
        posting_service = IntegratedPostingService(db)

        # Cross-post to all platforms
        results = await posting_service.cross_post_image(
            content_id=content_uuid,
            platform_account_ids=platform_account_uuids,
            caption=req.caption or "",
            hashtags=req.hashtags,
            mentions=req.mentions,
        )

        # Convert successful posts to response format
        successful_posts = {
            platform: PostResponse.model_validate(post)
            for platform, post in results.items()
        }

        # Note: Failed platforms are logged but not returned in results
        # We could enhance this to track failures separately if needed
        failed_platforms: dict[str, str] = {}

        return CrossPostImageResponse(
            ok=True,
            successful=successful_posts,
            failed=failed_platforms,
            total_platforms=len(req.platform_account_ids),
            successful_count=len(successful_posts),
            failed_count=len(failed_platforms),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {e}")
    except IntegratedPostingError as e:
        error_msg = str(e)
        logger.error(f"Cross-posting error: {e}", exc_info=True)
        
        # If all platforms failed, return 500
        if "failed for all platforms" in error_msg:
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Otherwise return 400 for validation errors
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Unexpected error during cross-posting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cross-post: {str(e)}")


class SimulateInteractionsRequest(BaseModel):
    """Request model for simulating follower interactions."""

    override_engagement: Optional[dict[str, int]] = Field(
        default=None,
        description="Optional dict with likes/comments/shares/views to set directly (overrides simulation)",
    )


@router.post("/{post_id}/simulate-interactions", response_model=PostResponse)
async def simulate_interactions_for_post(
    post_id: str,
    req: Optional[SimulateInteractionsRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Simulate follower interactions for a specific post.
    
    Simulates realistic follower engagement (likes, comments, shares, views) based on:
    - Follower count from platform account
    - Platform-specific engagement rates
    - Post age (most engagement happens in first 24-48 hours)
    - Post type (reels/videos get more engagement than static posts)
    
    Args:
        post_id: Post UUID
        req: Optional request with override_engagement to set specific values
        db: Database session dependency
        
    Returns:
        PostResponse with updated engagement counts
        
    Raises:
        HTTPException: 404 if post not found, 400 if post not published
    """
    try:
        post_uuid = UUID(post_id)
        simulation_service = FollowerInteractionSimulationService(db)
        
        override = req.override_engagement if req else None
        post = await simulation_service.simulate_interactions_for_post(
            post_id=post_uuid,
            override_engagement=override,
        )
        
        return PostResponse.model_validate(post)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error simulating interactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to simulate interactions: {str(e)}")


@router.post("/character/{character_id}/simulate-interactions", response_model=dict)
async def simulate_interactions_for_character(
    character_id: str,
    platform: Optional[str] = Query(default=None, description="Optional platform filter"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of posts to process"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Simulate follower interactions for all recent posts by a character.
    
    Args:
        character_id: Character UUID
        platform: Optional platform filter
        limit: Maximum number of posts to process
        db: Database session dependency
        
    Returns:
        Dictionary with updated posts count and list of updated posts
    """
    try:
        character_uuid = UUID(character_id)
        simulation_service = FollowerInteractionSimulationService(db)
        
        updated_posts = await simulation_service.simulate_interactions_for_character(
            character_id=character_uuid,
            platform=platform,
            limit=limit,
        )
        
        return {
            "ok": True,
            "updated_count": len(updated_posts),
            "posts": [PostResponse.model_validate(post).model_dump() for post in updated_posts],
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid character ID format")
    except Exception as e:
        logger.error(f"Error simulating interactions for character: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to simulate interactions: {str(e)}")


@router.post("/simulate-interactions/recent", response_model=dict)
async def simulate_interactions_for_recent_posts(
    hours: int = Query(default=48, ge=1, le=168, description="Only process posts published within this many hours"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of posts to process"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Simulate follower interactions for all recent posts across all characters.
    
    Args:
        hours: Only process posts published within this many hours (1-168)
        limit: Maximum number of posts to process (1-500)
        db: Database session dependency
        
    Returns:
        Dictionary with updated posts count and list of updated posts
    """
    try:
        simulation_service = FollowerInteractionSimulationService(db)
        
        updated_posts = await simulation_service.simulate_interactions_for_recent_posts(
            hours=hours,
            limit=limit,
        )
        
        return {
            "ok": True,
            "updated_count": len(updated_posts),
            "posts": [PostResponse.model_validate(post).model_dump() for post in updated_posts],
        }
        
    except Exception as e:
        logger.error(f"Error simulating interactions for recent posts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to simulate interactions: {str(e)}")


"""Instagram API endpoints for Instagram Graph API integration and posting."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.instagram_client import InstagramApiClient, InstagramApiError
from app.services.instagram_posting_service import InstagramPostingService, InstagramPostingError
from app.services.integrated_posting_service import IntegratedPostingService, IntegratedPostingError

logger = get_logger(__name__)

router = APIRouter()


class InstagramConnectionTestResponse(BaseModel):
    """Response model for Instagram connection test."""
    connected: bool
    user_info: dict | None = None
    error: str | None = None


class InstagramUserInfoResponse(BaseModel):
    """Response model for Instagram user information."""
    user_info: dict


@router.get("/status", tags=["instagram"])
def get_instagram_status() -> dict:
    """
    Get Instagram API client status.
    
    Returns:
        Status information about Instagram API configuration.
    """
    client = InstagramApiClient()
    has_token = client.access_token is not None
    
    return {
        "configured": has_token,
        "api_version": client.api_version,
        "base_url": client.base_url,
    }


@router.get("/test-connection", response_model=InstagramConnectionTestResponse, tags=["instagram"])
def test_instagram_connection() -> InstagramConnectionTestResponse:
    """
    Test connection to Instagram API.
    
    Attempts to connect to Instagram Graph API and fetch authenticated user info.
    
    Returns:
        Connection test result with user info if successful.
        
    Raises:
        HTTPException: If connection test fails.
    """
    try:
        client = InstagramApiClient()
        user_info = client.test_connection()
        
        return InstagramConnectionTestResponse(
            connected=True,
            user_info=user_info,
        )
    except InstagramApiError as exc:
        logger.error(f"Instagram connection test failed: {exc}")
        return InstagramConnectionTestResponse(
            connected=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error during Instagram connection test: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/user-info", response_model=InstagramUserInfoResponse, tags=["instagram"])
def get_user_info(user_id: str = "me", fields: str | None = None) -> InstagramUserInfoResponse:
    """
    Get Instagram user information.
    
    Args:
        user_id: Instagram user ID. Defaults to "me" for authenticated user.
        fields: Comma-separated list of fields to retrieve. Defaults to id, username, account_type.
    
    Returns:
        User information dictionary.
        
    Raises:
        HTTPException: If API request fails.
    """
    try:
        client = InstagramApiClient()
        fields_list = fields.split(",") if fields else None
        user_info = client.get_user_info(user_id=user_id, fields=fields_list)
        
        return InstagramUserInfoResponse(user_info=user_info)
    except InstagramApiError as exc:
        logger.error(f"Failed to get Instagram user info: {exc}")
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(f"Unexpected error getting Instagram user info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class PostImageRequest(BaseModel):
    """Request model for posting an image to Instagram."""
    username: str
    password: str
    image_path: str
    caption: str = ""
    hashtags: list[str] | None = None
    mentions: list[str] | None = None
    session_file: str | None = None


class PostCarouselRequest(BaseModel):
    """Request model for posting a carousel to Instagram."""
    username: str
    password: str
    image_paths: list[str]
    caption: str = ""
    hashtags: list[str] | None = None
    mentions: list[str] | None = None
    session_file: str | None = None


class PostReelRequest(BaseModel):
    """Request model for posting a reel to Instagram."""
    username: str
    password: str
    video_path: str
    caption: str = ""
    hashtags: list[str] | None = None
    mentions: list[str] | None = None
    thumbnail_path: str | None = None
    session_file: str | None = None


class PostStoryRequest(BaseModel):
    """Request model for posting a story to Instagram."""
    username: str
    password: str
    image_path: str | None = None
    video_path: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    mentions: list[str] | None = None
    session_file: str | None = None


class PostResponse(BaseModel):
    """Response model for Instagram posting operations."""
    success: bool
    platform_post_id: str | None = None
    platform_post_url: str | None = None
    media_type: str | None = None
    error: str | None = None


@router.post("/post/image", response_model=PostResponse, tags=["instagram"])
def post_image(req: PostImageRequest) -> PostResponse:
    """
    Post a single image to Instagram feed.
    
    Args:
        req: Post image request with credentials and image details.
    
    Returns:
        Post response with platform_post_id and platform_post_url.
        
    Raises:
        HTTPException: If posting fails.
    """
    posting_service = None
    try:
        posting_service = InstagramPostingService(
            username=req.username,
            password=req.password,
            session_file=req.session_file,
        )
        result = posting_service.post_image(
            image_path=req.image_path,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
        )
        
        return PostResponse(
            success=True,
            platform_post_id=result.get("platform_post_id"),
            platform_post_url=result.get("platform_post_url"),
            media_type=result.get("media_type"),
        )
    except InstagramPostingError as exc:
        logger.error(f"Failed to post image to Instagram: {exc}")
        return PostResponse(
            success=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error posting image to Instagram: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc
    finally:
        if posting_service:
            posting_service.close()


@router.post("/post/carousel", response_model=PostResponse, tags=["instagram"])
def post_carousel(req: PostCarouselRequest) -> PostResponse:
    """
    Post multiple images as a carousel to Instagram feed.
    
    Args:
        req: Post carousel request with credentials and image details.
    
    Returns:
        Post response with platform_post_id and platform_post_url.
        
    Raises:
        HTTPException: If posting fails.
    """
    posting_service = None
    try:
        posting_service = InstagramPostingService(
            username=req.username,
            password=req.password,
            session_file=req.session_file,
        )
        result = posting_service.post_carousel(
            image_paths=req.image_paths,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
        )
        
        return PostResponse(
            success=True,
            platform_post_id=result.get("platform_post_id"),
            platform_post_url=result.get("platform_post_url"),
            media_type=result.get("media_type"),
        )
    except InstagramPostingError as exc:
        logger.error(f"Failed to post carousel to Instagram: {exc}")
        return PostResponse(
            success=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error posting carousel to Instagram: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc
    finally:
        if posting_service:
            posting_service.close()


@router.post("/post/reel", response_model=PostResponse, tags=["instagram"])
def post_reel(req: PostReelRequest) -> PostResponse:
    """
    Post a reel (short video) to Instagram.
    
    Args:
        req: Post reel request with credentials and video details.
    
    Returns:
        Post response with platform_post_id and platform_post_url.
        
    Raises:
        HTTPException: If posting fails.
    """
    posting_service = None
    try:
        posting_service = InstagramPostingService(
            username=req.username,
            password=req.password,
            session_file=req.session_file,
        )
        result = posting_service.post_reel(
            video_path=req.video_path,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
            thumbnail_path=req.thumbnail_path,
        )
        
        return PostResponse(
            success=True,
            platform_post_id=result.get("platform_post_id"),
            platform_post_url=result.get("platform_post_url"),
            media_type=result.get("media_type"),
        )
    except InstagramPostingError as exc:
        logger.error(f"Failed to post reel to Instagram: {exc}")
        return PostResponse(
            success=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error posting reel to Instagram: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc
    finally:
        if posting_service:
            posting_service.close()


@router.post("/post/story", response_model=PostResponse, tags=["instagram"])
def post_story(req: PostStoryRequest) -> PostResponse:
    """
    Post a story (image or video) to Instagram.
    
    Args:
        req: Post story request with credentials and media details.
    
    Returns:
        Post response with platform_post_id.
        
    Raises:
        HTTPException: If posting fails.
    """
    posting_service = None
    try:
        posting_service = InstagramPostingService(
            username=req.username,
            password=req.password,
            session_file=req.session_file,
        )
        result = posting_service.post_story(
            image_path=req.image_path,
            video_path=req.video_path,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
        )
        
        return PostResponse(
            success=True,
            platform_post_id=result.get("platform_post_id"),
            platform_post_url=result.get("platform_post_url"),
            media_type=result.get("media_type"),
        )
    except InstagramPostingError as exc:
        logger.error(f"Failed to post story to Instagram: {exc}")
        return PostResponse(
            success=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error posting story to Instagram: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc
    finally:
        if posting_service:
            posting_service.close()



# Integrated Posting Endpoints (using content library and platform accounts)

class IntegratedPostImageRequest(BaseModel):
    """Request model for posting an image using content library."""
    content_id: str
    platform_account_id: str
    caption: str = ""
    hashtags: list[str] | None = None
    mentions: list[str] | None = None


class IntegratedPostCarouselRequest(BaseModel):
    """Request model for posting a carousel using content library."""
    content_ids: list[str]
    platform_account_id: str
    caption: str = ""
    hashtags: list[str] | None = None
    mentions: list[str] | None = None


class IntegratedPostReelRequest(BaseModel):
    """Request model for posting a reel using content library."""
    content_id: str
    platform_account_id: str
    caption: str = ""
    hashtags: list[str] | None = None
    mentions: list[str] | None = None
    thumbnail_content_id: str | None = None


class IntegratedPostStoryRequest(BaseModel):
    """Request model for posting a story using content library."""
    content_id: str
    platform_account_id: str
    caption: str | None = None
    hashtags: list[str] | None = None
    mentions: list[str] | None = None
    is_video: bool = False


@router.post("/post/image/integrated", response_model=PostResponse, tags=["instagram"])
async def post_image_integrated(
    req: IntegratedPostImageRequest,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Post an image to Instagram using content from the library.
    
    Uses content_id to retrieve the image from the content library and
    platform_account_id to get Instagram credentials. Creates a Post record
    in the database after successful posting.
    
    Args:
        req: Integrated post image request with content_id and platform_account_id.
        db: Database session dependency.
    
    Returns:
        PostResponse with created post information.
        
    Raises:
        HTTPException: 400 if validation fails, 404 if content or account not found.
    """
    try:
        service = IntegratedPostingService(db)
        
        content_uuid = UUID(req.content_id)
        platform_account_uuid = UUID(req.platform_account_id)
        
        post = await service.post_image_to_instagram(
            content_id=content_uuid,
            platform_account_id=platform_account_uuid,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
        )
        
        return PostResponse(
            success=True,
            platform_post_id=post.platform_post_id,
            platform_post_url=post.platform_post_url,
            media_type="photo",
        )
    except IntegratedPostingError as exc:
        logger.error(f"Failed to post image (integrated): {exc}")
        return PostResponse(
            success=False,
            error=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error posting image (integrated): {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/post/carousel/integrated", response_model=PostResponse, tags=["instagram"])
async def post_carousel_integrated(
    req: IntegratedPostCarouselRequest,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Post a carousel to Instagram using content from the library.
    
    Uses content_ids to retrieve images from the content library and
    platform_account_id to get Instagram credentials. Creates a Post record
    in the database after successful posting.
    
    Args:
        req: Integrated post carousel request with content_ids and platform_account_id.
        db: Database session dependency.
    
    Returns:
        PostResponse with created post information.
        
    Raises:
        HTTPException: 400 if validation fails, 404 if content or account not found.
    """
    try:
        service = IntegratedPostingService(db)
        
        content_uuids = [UUID(cid) for cid in req.content_ids]
        platform_account_uuid = UUID(req.platform_account_id)
        
        post = await service.post_carousel_to_instagram(
            content_ids=content_uuids,
            platform_account_id=platform_account_uuid,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
        )
        
        return PostResponse(
            success=True,
            platform_post_id=post.platform_post_id,
            platform_post_url=post.platform_post_url,
            media_type="carousel",
        )
    except IntegratedPostingError as exc:
        logger.error(f"Failed to post carousel (integrated): {exc}")
        return PostResponse(
            success=False,
            error=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error posting carousel (integrated): {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/post/reel/integrated", response_model=PostResponse, tags=["instagram"])
async def post_reel_integrated(
    req: IntegratedPostReelRequest,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Post a reel to Instagram using content from the library.
    
    Uses content_id to retrieve the video from the content library and
    platform_account_id to get Instagram credentials. Creates a Post record
    in the database after successful posting.
    
    Args:
        req: Integrated post reel request with content_id and platform_account_id.
        db: Database session dependency.
    
    Returns:
        PostResponse with created post information.
        
    Raises:
        HTTPException: 400 if validation fails, 404 if content or account not found.
    """
    try:
        service = IntegratedPostingService(db)
        
        content_uuid = UUID(req.content_id)
        platform_account_uuid = UUID(req.platform_account_id)
        thumbnail_content_uuid = UUID(req.thumbnail_content_id) if req.thumbnail_content_id else None
        
        post = await service.post_reel_to_instagram(
            content_id=content_uuid,
            platform_account_id=platform_account_uuid,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
            thumbnail_content_id=thumbnail_content_uuid,
        )
        
        return PostResponse(
            success=True,
            platform_post_id=post.platform_post_id,
            platform_post_url=post.platform_post_url,
            media_type="reel",
        )
    except IntegratedPostingError as exc:
        logger.error(f"Failed to post reel (integrated): {exc}")
        return PostResponse(
            success=False,
            error=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error posting reel (integrated): {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/post/story/integrated", response_model=PostResponse, tags=["instagram"])
async def post_story_integrated(
    req: IntegratedPostStoryRequest,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """
    Post a story to Instagram using content from the library.
    
    Uses content_id to retrieve the image/video from the content library and
    platform_account_id to get Instagram credentials. Creates a Post record
    in the database after successful posting.
    
    Args:
        req: Integrated post story request with content_id and platform_account_id.
        db: Database session dependency.
    
    Returns:
        PostResponse with created post information.
        
    Raises:
        HTTPException: 400 if validation fails, 404 if content or account not found.
    """
    try:
        service = IntegratedPostingService(db)
        
        content_uuid = UUID(req.content_id)
        platform_account_uuid = UUID(req.platform_account_id)
        
        post = await service.post_story_to_instagram(
            content_id=content_uuid,
            platform_account_id=platform_account_uuid,
            caption=req.caption,
            hashtags=req.hashtags,
            mentions=req.mentions,
            is_video=req.is_video,
        )
        
        return PostResponse(
            success=True,
            platform_post_id=post.platform_post_id,
            platform_post_url=post.platform_post_url,
            media_type="story_photo" if not req.is_video else "story_video",
        )
    except IntegratedPostingError as exc:
        logger.error(f"Failed to post story (integrated): {exc}")
        return PostResponse(
            success=False,
            error=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error posting story (integrated): {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

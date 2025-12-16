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
from app.services.instagram_engagement_service import InstagramEngagementService, InstagramEngagementError
from app.services.integrated_engagement_service import IntegratedEngagementService, IntegratedEngagementError

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
    
    Returns the current configuration status of the Instagram API client,
    including whether an access token is configured, API version, and base URL.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether access token is configured
            - api_version (str): Instagram Graph API version
            - base_url (str): Base URL for API requests
    
    Example:
        ```json
        {
            "configured": true,
            "api_version": "v18.0",
            "base_url": "https://graph.instagram.com"
        }
        ```
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
    This endpoint verifies that the configured access token is valid and can
    successfully authenticate with Instagram's API.
    
    Returns:
        InstagramConnectionTestResponse: Connection test result containing:
            - connected (bool): Whether connection was successful
            - user_info (dict | None): User information if connected, None otherwise
            - error (str | None): Error message if connection failed, None otherwise
        
    Raises:
        HTTPException: 500 if unexpected error occurs during connection test.
        
    Example:
        ```json
        {
            "connected": true,
            "user_info": {
                "id": "123456789",
                "username": "example_user",
                "account_type": "BUSINESS"
            },
            "error": null
        }
        ```
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
    
    Retrieves user information from Instagram Graph API. By default, returns
    information about the authenticated user. Can optionally retrieve information
    about other users if their user ID is provided and permissions allow.
    
    Args:
        user_id: Instagram user ID. Defaults to "me" for authenticated user.
            Can be a specific user ID if permissions allow.
        fields: Comma-separated list of fields to retrieve. Defaults to
            "id,username,account_type". Available fields include: id, username,
            account_type, followers_count, media_count, etc.
    
    Returns:
        InstagramUserInfoResponse: User information dictionary containing
            requested fields.
        
    Raises:
        HTTPException: 400 if API request fails (invalid user_id or fields),
            500 if unexpected error occurs.
            
    Example:
        Request: GET /user-info?fields=id,username,followers_count
        Response:
        ```json
        {
            "user_info": {
                "id": "123456789",
                "username": "example_user",
                "followers_count": 1000
            }
        }
        ```
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
    
    Posts a single image to the authenticated user's Instagram feed using
    direct credentials (username/password). The image must be accessible at the
    provided image_path. Supports optional caption, hashtags, and mentions.
    
    Args:
        req: PostImageRequest containing:
            - username (str): Instagram username
            - password (str): Instagram password
            - image_path (str): Path to image file to post
            - caption (str): Optional caption text (default: "")
            - hashtags (list[str] | None): Optional list of hashtags
            - mentions (list[str] | None): Optional list of usernames to mention
            - session_file (str | None): Optional path to session file for reuse
    
    Returns:
        PostResponse: Post result containing:
            - success (bool): Whether posting was successful
            - platform_post_id (str | None): Instagram post ID if successful
            - platform_post_url (str | None): URL to the posted content
            - media_type (str | None): Type of media posted (e.g., "photo")
            - error (str | None): Error message if posting failed
        
    Raises:
        HTTPException: 500 if unexpected error occurs during posting.
        
    Note:
        This endpoint uses direct Instagram credentials. For production use,
        consider using the integrated endpoints with platform accounts.
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
    
    Posts multiple images as a carousel (swipeable post) to the authenticated
    user's Instagram feed. Carousels can contain 2-10 images. All images must be
    accessible at the provided image_paths.
    
    Args:
        req: PostCarouselRequest containing:
            - username (str): Instagram username
            - password (str): Instagram password
            - image_paths (list[str]): List of paths to image files (2-10 images)
            - caption (str): Optional caption text (default: "")
            - hashtags (list[str] | None): Optional list of hashtags
            - mentions (list[str] | None): Optional list of usernames to mention
            - session_file (str | None): Optional path to session file for reuse
    
    Returns:
        PostResponse: Post result containing:
            - success (bool): Whether posting was successful
            - platform_post_id (str | None): Instagram post ID if successful
            - platform_post_url (str | None): URL to the posted content
            - media_type (str | None): Type of media posted (e.g., "carousel")
            - error (str | None): Error message if posting failed
        
    Raises:
        HTTPException: 500 if unexpected error occurs during posting.
        
    Note:
        Instagram carousels require 2-10 images. This endpoint uses direct
        credentials. For production use, consider using integrated endpoints.
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
    
    Posts a short video reel to the authenticated user's Instagram account.
    Reels are vertical videos (typically 9:16 aspect ratio) with a maximum
    duration. Supports optional caption, hashtags, mentions, and custom thumbnail.
    
    Args:
        req: PostReelRequest containing:
            - username (str): Instagram username
            - password (str): Instagram password
            - video_path (str): Path to video file to post
            - caption (str): Optional caption text (default: "")
            - hashtags (list[str] | None): Optional list of hashtags
            - mentions (list[str] | None): Optional list of usernames to mention
            - thumbnail_path (str | None): Optional path to custom thumbnail image
            - session_file (str | None): Optional path to session file for reuse
    
    Returns:
        PostResponse: Post result containing:
            - success (bool): Whether posting was successful
            - platform_post_id (str | None): Instagram reel ID if successful
            - platform_post_url (str | None): URL to the posted reel
            - media_type (str | None): Type of media posted (e.g., "reel")
            - error (str | None): Error message if posting failed
        
    Raises:
        HTTPException: 500 if unexpected error occurs during posting.
        
    Note:
        Reels have specific requirements (aspect ratio, duration, file format).
        This endpoint uses direct credentials. For production use, consider
        using integrated endpoints with platform accounts.
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
    
    Posts an image or video story to the authenticated user's Instagram account.
    Stories are temporary content that disappears after 24 hours. Supports
    optional caption, hashtags, and mentions. Either image_path or video_path
    must be provided.
    
    Args:
        req: PostStoryRequest containing:
            - username (str): Instagram username
            - password (str): Instagram password
            - image_path (str | None): Path to image file (for image story)
            - video_path (str | None): Path to video file (for video story)
            - caption (str | None): Optional caption text
            - hashtags (list[str] | None): Optional list of hashtags
            - mentions (list[str] | None): Optional list of usernames to mention
            - session_file (str | None): Optional path to session file for reuse
    
    Returns:
        PostResponse: Post result containing:
            - success (bool): Whether posting was successful
            - platform_post_id (str | None): Instagram story ID if successful
            - platform_post_url (str | None): URL to the posted story (if available)
            - media_type (str | None): Type of media posted (e.g., "story_photo", "story_video")
            - error (str | None): Error message if posting failed
        
    Raises:
        HTTPException: 500 if unexpected error occurs during posting.
        
    Note:
        Stories expire after 24 hours. Either image_path or video_path must be
        provided. This endpoint uses direct credentials. For production use,
        consider using integrated endpoints with platform accounts.
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
    
    Posts an image to Instagram using content from the content library and
    credentials from a platform account. This integrated endpoint:
    1. Retrieves the image content using content_id
    2. Gets Instagram credentials from platform_account_id
    3. Posts the image to Instagram
    4. Creates a Post record in the database
    
    Args:
        req: IntegratedPostImageRequest containing:
            - content_id (str): UUID of content item in library
            - platform_account_id (str): UUID of platform account to use
            - caption (str): Optional caption text (default: "")
            - hashtags (list[str] | None): Optional list of hashtags
            - mentions (list[str] | None): Optional list of usernames to mention
        db: Database session dependency for accessing content and accounts.
    
    Returns:
        PostResponse: Post result containing:
            - success (bool): Whether posting was successful
            - platform_post_id (str | None): Instagram post ID if successful
            - platform_post_url (str | None): URL to the posted content
            - media_type (str): Always "photo" for image posts
            - error (str | None): Error message if posting failed
        
    Raises:
        HTTPException: 
            - 400 if UUID format is invalid or validation fails
            - 404 if content item or platform account not found
            - 500 if unexpected error occurs
            
    Note:
        This is the recommended endpoint for production use as it integrates
        with the content library and platform account management system.
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
    
    Posts multiple images as a carousel (swipeable post) to Instagram using
    content from the content library and credentials from a platform account.
    This integrated endpoint:
    1. Retrieves multiple image content items using content_ids (2-10 images)
    2. Gets Instagram credentials from platform_account_id
    3. Posts the carousel to Instagram
    4. Creates a Post record in the database
    
    Args:
        req: IntegratedPostCarouselRequest containing:
            - content_ids (list[str]): List of UUIDs of content items (2-10 images)
            - platform_account_id (str): UUID of platform account to use
            - caption (str): Optional caption text (default: "")
            - hashtags (list[str] | None): Optional list of hashtags
            - mentions (list[str] | None): Optional list of usernames to mention
        db: Database session dependency for accessing content and accounts.
    
    Returns:
        PostResponse: Post result containing:
            - success (bool): Whether posting was successful
            - platform_post_id (str | None): Instagram post ID if successful
            - platform_post_url (str | None): URL to the posted carousel
            - media_type (str): Always "carousel" for carousel posts
            - error (str | None): Error message if posting failed
        
    Raises:
        HTTPException: 
            - 400 if UUID format is invalid, validation fails, or wrong number of images
            - 404 if any content item or platform account not found
            - 500 if unexpected error occurs
            
    Note:
        Instagram carousels require 2-10 images. This is the recommended
        endpoint for production use as it integrates with the content library.
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
    
    Posts a short video reel to Instagram using content from the content library
    and credentials from a platform account. This integrated endpoint:
    1. Retrieves the video content using content_id
    2. Optionally retrieves thumbnail content using thumbnail_content_id
    3. Gets Instagram credentials from platform_account_id
    4. Posts the reel to Instagram
    5. Creates a Post record in the database
    
    Args:
        req: IntegratedPostReelRequest containing:
            - content_id (str): UUID of video content item in library
            - platform_account_id (str): UUID of platform account to use
            - caption (str): Optional caption text (default: "")
            - hashtags (list[str] | None): Optional list of hashtags
            - mentions (list[str] | None): Optional list of usernames to mention
            - thumbnail_content_id (str | None): Optional UUID of thumbnail content
        db: Database session dependency for accessing content and accounts.
    
    Returns:
        PostResponse: Post result containing:
            - success (bool): Whether posting was successful
            - platform_post_id (str | None): Instagram reel ID if successful
            - platform_post_url (str | None): URL to the posted reel
            - media_type (str): Always "reel" for reel posts
            - error (str | None): Error message if posting failed
        
    Raises:
        HTTPException: 
            - 400 if UUID format is invalid or validation fails
            - 404 if content item, thumbnail, or platform account not found
            - 500 if unexpected error occurs
            
    Note:
        Reels have specific requirements (aspect ratio, duration, file format).
        This is the recommended endpoint for production use as it integrates
        with the content library and platform account management system.
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
    
    Posts an image or video story to Instagram using content from the content
    library and credentials from a platform account. Stories are temporary
    content that disappears after 24 hours. This integrated endpoint:
    1. Retrieves the image/video content using content_id
    2. Gets Instagram credentials from platform_account_id
    3. Posts the story to Instagram
    4. Creates a Post record in the database
    
    Args:
        req: IntegratedPostStoryRequest containing:
            - content_id (str): UUID of content item in library (image or video)
            - platform_account_id (str): UUID of platform account to use
            - caption (str | None): Optional caption text
            - hashtags (list[str] | None): Optional list of hashtags
            - mentions (list[str] | None): Optional list of usernames to mention
            - is_video (bool): Whether content is video (default: False)
        db: Database session dependency for accessing content and accounts.
    
    Returns:
        PostResponse: Post result containing:
            - success (bool): Whether posting was successful
            - platform_post_id (str | None): Instagram story ID if successful
            - platform_post_url (str | None): URL to the posted story (if available)
            - media_type (str): "story_photo" or "story_video" based on is_video
            - error (str | None): Error message if posting failed
        
    Raises:
        HTTPException: 
            - 400 if UUID format is invalid or validation fails
            - 404 if content item or platform account not found
            - 500 if unexpected error occurs
            
    Note:
        Stories expire after 24 hours. This is the recommended endpoint for
        production use as it integrates with the content library and platform
        account management system.
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


# Engagement Endpoints (Comments, Likes)

class CommentRequest(BaseModel):
    """Request model for commenting on a post."""
    username: str
    password: str
    session_file: str | None = None
    media_id: str
    comment_text: str


class CommentResponse(BaseModel):
    """Response model for comment operation."""
    success: bool
    comment_id: str | None = None
    media_id: str | None = None
    error: str | None = None


@router.post("/comment", response_model=CommentResponse, tags=["instagram"])
def comment_on_post(req: CommentRequest) -> CommentResponse:
    """
    Comment on an Instagram post.
    
    Posts a comment on a specific Instagram post using direct credentials
    (username/password). The comment will appear on the post identified by
    media_id. Supports session file reuse for authenticated sessions.
    
    Args:
        req: CommentRequest containing:
            - username (str): Instagram username
            - password (str): Instagram password
            - media_id (str): Instagram media ID of the post to comment on
            - comment_text (str): Text content of the comment
            - session_file (str | None): Optional path to session file for reuse
    
    Returns:
        CommentResponse: Comment result containing:
            - success (bool): Whether commenting was successful
            - comment_id (str | None): Instagram comment ID if successful
            - media_id (str | None): Media ID of the commented post
            - error (str | None): Error message if commenting failed
        
    Raises:
        HTTPException: 500 if unexpected error occurs during commenting.
        
    Note:
        This endpoint uses direct Instagram credentials. For production use,
        consider using the integrated endpoint with platform accounts.
    """
    engagement_service = None
    try:
        engagement_service = InstagramEngagementService(
            username=req.username,
            password=req.password,
            session_file=req.session_file,
        )
        result = engagement_service.comment_on_post(
            media_id=req.media_id,
            comment_text=req.comment_text,
        )
        
        return CommentResponse(
            success=True,
            comment_id=result.get("comment_id"),
            media_id=result.get("media_id"),
        )
    except InstagramEngagementError as exc:
        logger.error(f"Failed to comment on post: {exc}")
        return CommentResponse(
            success=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error commenting on post: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc
    finally:
        if engagement_service:
            engagement_service.close()


# Integrated Engagement Endpoints (using platform accounts)

class IntegratedCommentRequest(BaseModel):
    """Request model for commenting on a post using platform account."""
    platform_account_id: str
    media_id: str
    comment_text: str


class IntegratedLikeRequest(BaseModel):
    """Request model for liking a post using platform account."""
    platform_account_id: str
    media_id: str


class IntegratedUnlikeRequest(BaseModel):
    """Request model for unliking a post using platform account."""
    platform_account_id: str
    media_id: str


@router.post("/comment/integrated", response_model=CommentResponse, tags=["instagram"])
async def comment_on_post_integrated(
    req: IntegratedCommentRequest,
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """
    Comment on an Instagram post using platform account.
    
    Posts a comment on a specific Instagram post using credentials from a
    platform account stored in the database. This integrated endpoint:
    1. Retrieves Instagram credentials from platform_account_id
    2. Posts the comment on the post identified by media_id
    3. Returns the comment result
    
    The platform account must be connected and have valid credentials stored
    in auth_data. This is the recommended approach for production use.
    
    Args:
        req: IntegratedCommentRequest containing:
            - platform_account_id (str): UUID of platform account to use
            - media_id (str): Instagram media ID of the post to comment on
            - comment_text (str): Text content of the comment
        db: Database session dependency for accessing platform account.
    
    Returns:
        CommentResponse: Comment result containing:
            - success (bool): Whether commenting was successful
            - comment_id (str | None): Instagram comment ID if successful
            - media_id (str | None): Media ID of the commented post
            - error (str | None): Error message if commenting failed
        
    Raises:
        HTTPException: 
            - 400 if UUID format is invalid or validation fails
            - 404 if platform account not found or not connected
            - 500 if unexpected error occurs
            
    Note:
        This is the recommended endpoint for production use as it integrates
        with the platform account management system and avoids exposing
        credentials in API requests.
    """
    try:
        service = IntegratedEngagementService(db)
        
        platform_account_uuid = UUID(req.platform_account_id)
        
        result = await service.comment_on_post(
            platform_account_id=platform_account_uuid,
            media_id=req.media_id,
            comment_text=req.comment_text,
        )
        
        return CommentResponse(
            success=True,
            comment_id=result.get("comment_id"),
            media_id=result.get("media_id"),
        )
    except IntegratedEngagementError as exc:
        logger.error(f"Failed to comment on post (integrated): {exc}")
        return CommentResponse(
            success=False,
            error=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error commenting on post (integrated): {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class LikeRequest(BaseModel):
    """Request model for liking a post."""
    username: str
    password: str
    session_file: str | None = None
    media_id: str


class LikeResponse(BaseModel):
    """Response model for like operation."""
    success: bool
    media_id: str | None = None
    error: str | None = None


@router.post("/like", response_model=LikeResponse, tags=["instagram"])
def like_post(req: LikeRequest) -> LikeResponse:
    """
    Like an Instagram post.
    
    Likes a specific Instagram post using direct credentials (username/password).
    The like will be applied to the post identified by media_id. Supports session
    file reuse for authenticated sessions.
    
    Args:
        req: LikeRequest containing:
            - username (str): Instagram username
            - password (str): Instagram password
            - media_id (str): Instagram media ID of the post to like
            - session_file (str | None): Optional path to session file for reuse
    
    Returns:
        LikeResponse: Like result containing:
            - success (bool): Whether liking was successful
            - media_id (str | None): Media ID of the liked post
            - error (str | None): Error message if liking failed
        
    Raises:
        HTTPException: 500 if unexpected error occurs during liking.
        
    Note:
        This endpoint uses direct Instagram credentials. For production use,
        consider using the integrated endpoint with platform accounts.
    """
    engagement_service = None
    try:
        engagement_service = InstagramEngagementService(
            username=req.username,
            password=req.password,
            session_file=req.session_file,
        )
        result = engagement_service.like_post(media_id=req.media_id)
        
        return LikeResponse(
            success=True,
            media_id=result.get("media_id"),
        )
    except InstagramEngagementError as exc:
        logger.error(f"Failed to like post: {exc}")
        return LikeResponse(
            success=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error liking post: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc
    finally:
        if engagement_service:
            engagement_service.close()


@router.post("/unlike", response_model=LikeResponse, tags=["instagram"])
def unlike_post(req: LikeRequest) -> LikeResponse:
    """
    Unlike an Instagram post.
    
    Unlikes (removes like from) a specific Instagram post using direct credentials
    (username/password). The unlike will be applied to the post identified by media_id.
    Supports session file reuse for authenticated sessions.
    
    Args:
        req: LikeRequest containing:
            - username (str): Instagram username
            - password (str): Instagram password
            - media_id (str): Instagram media ID of the post to unlike
            - session_file (str | None): Optional path to session file for reuse
    
    Returns:
        LikeResponse: Unlike result containing:
            - success (bool): Whether unliking was successful
            - media_id (str | None): Media ID of the unliked post
            - error (str | None): Error message if unliking failed
        
    Raises:
        HTTPException: 500 if unexpected error occurs during unliking.
        
    Note:
        This endpoint uses direct Instagram credentials. For production use,
        consider using the integrated endpoint with platform accounts.
    """
    engagement_service = None
    try:
        engagement_service = InstagramEngagementService(
            username=req.username,
            password=req.password,
            session_file=req.session_file,
        )
        result = engagement_service.unlike_post(media_id=req.media_id)
        
        return LikeResponse(
            success=True,
            media_id=result.get("media_id"),
        )
    except InstagramEngagementError as exc:
        logger.error(f"Failed to unlike post: {exc}")
        return LikeResponse(
            success=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error unliking post: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc
    finally:
        if engagement_service:
            engagement_service.close()


@router.post("/like/integrated", response_model=LikeResponse, tags=["instagram"])
async def like_post_integrated(
    req: IntegratedLikeRequest,
    db: AsyncSession = Depends(get_db),
) -> LikeResponse:
    """
    Like an Instagram post using platform account.
    
    Likes a specific Instagram post using credentials from a platform account
    stored in the database. This integrated endpoint:
    1. Retrieves Instagram credentials from platform_account_id
    2. Likes the post identified by media_id
    3. Returns the like result
    
    The platform account must be connected and have valid credentials stored
    in auth_data. This is the recommended approach for production use.
    
    Args:
        req: IntegratedLikeRequest containing:
            - platform_account_id (str): UUID of platform account to use
            - media_id (str): Instagram media ID of the post to like
        db: Database session dependency for accessing platform account.
    
    Returns:
        LikeResponse: Like result containing:
            - success (bool): Whether liking was successful
            - media_id (str | None): Media ID of the liked post
            - error (str | None): Error message if liking failed
        
    Raises:
        HTTPException: 
            - 400 if UUID format is invalid or validation fails
            - 404 if platform account not found or not connected
            - 500 if unexpected error occurs
            
    Note:
        This is the recommended endpoint for production use as it integrates
        with the platform account management system and avoids exposing
        credentials in API requests.
    """
    try:
        service = IntegratedEngagementService(db)
        
        platform_account_uuid = UUID(req.platform_account_id)
        
        result = await service.like_post(
            platform_account_id=platform_account_uuid,
            media_id=req.media_id,
        )
        
        return LikeResponse(
            success=True,
            media_id=result.get("media_id"),
        )
    except IntegratedEngagementError as exc:
        logger.error(f"Failed to like post (integrated): {exc}")
        return LikeResponse(
            success=False,
            error=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error liking post (integrated): {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/unlike/integrated", response_model=LikeResponse, tags=["instagram"])
async def unlike_post_integrated(
    req: IntegratedUnlikeRequest,
    db: AsyncSession = Depends(get_db),
) -> LikeResponse:
    """
    Unlike an Instagram post using platform account.
    
    Unlikes (removes like from) a specific Instagram post using credentials
    from a platform account stored in the database. This integrated endpoint:
    1. Retrieves Instagram credentials from platform_account_id
    2. Unlikes the post identified by media_id
    3. Returns the unlike result
    
    The platform account must be connected and have valid credentials stored
    in auth_data. This is the recommended approach for production use.
    
    Args:
        req: IntegratedUnlikeRequest containing:
            - platform_account_id (str): UUID of platform account to use
            - media_id (str): Instagram media ID of the post to unlike
        db: Database session dependency for accessing platform account.
    
    Returns:
        LikeResponse: Unlike result containing:
            - success (bool): Whether unliking was successful
            - media_id (str | None): Media ID of the unliked post
            - error (str | None): Error message if unliking failed
        
    Raises:
        HTTPException: 
            - 400 if UUID format is invalid or validation fails
            - 404 if platform account not found or not connected
            - 500 if unexpected error occurs
            
    Note:
        This is the recommended endpoint for production use as it integrates
        with the platform account management system and avoids exposing
        credentials in API requests.
    """
    try:
        service = IntegratedEngagementService(db)
        
        platform_account_uuid = UUID(req.platform_account_id)
        
        result = await service.unlike_post(
            platform_account_id=platform_account_uuid,
            media_id=req.media_id,
        )
        
        return LikeResponse(
            success=True,
            media_id=result.get("media_id"),
        )
    except IntegratedEngagementError as exc:
        logger.error(f"Failed to unlike post (integrated): {exc}")
        return LikeResponse(
            success=False,
            error=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error unliking post (integrated): {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

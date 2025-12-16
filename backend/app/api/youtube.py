"""YouTube Data API endpoints for YouTube API integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.core.paths import videos_dir
from app.services.thumbnail_optimization_service import ThumbnailOptimizationService, ThumbnailOptimizationError
from app.services.youtube_client import YouTubeApiClient, YouTubeApiError

logger = get_logger(__name__)

router = APIRouter()


class YouTubeConnectionTestResponse(BaseModel):
    """Response model for YouTube connection test."""
    connected: bool
    channel_info: dict | None = None
    error: str | None = None


class YouTubeChannelInfoResponse(BaseModel):
    """Response model for YouTube channel information."""
    channel_info: dict


class YouTubeUploadVideoRequest(BaseModel):
    """Request model for YouTube video upload."""
    video_path: str
    title: str
    description: str = ""
    tags: list[str] | None = None
    category_id: str = "22"  # Default: People & Blogs
    privacy_status: str = "private"  # private, unlisted, public
    thumbnail_path: str | None = None


class YouTubeUploadVideoResponse(BaseModel):
    """Response model for YouTube video upload."""
    success: bool
    video_id: str | None = None
    video_url: str | None = None
    title: str | None = None
    description: str | None = None
    privacy_status: str | None = None
    error: str | None = None


class YouTubeUploadShortRequest(BaseModel):
    """Request model for YouTube Short upload."""
    video_path: str
    title: str
    description: str = ""
    tags: list[str] | None = None
    privacy_status: str = "private"  # private, unlisted, public
    thumbnail_path: str | None = None
    validate_duration: bool = True
    validate_aspect_ratio: bool = True


class YouTubeUploadShortResponse(BaseModel):
    """Response model for YouTube Short upload."""
    success: bool
    video_id: str | None = None
    video_url: str | None = None
    title: str | None = None
    description: str | None = None
    privacy_status: str | None = None
    is_short: bool = False
    error: str | None = None


@router.get("/status", tags=["youtube"])
def get_youtube_status() -> dict:
    """
    Get YouTube Data API client status.
    
    Returns the current configuration status of the YouTube Data API client,
    including whether credentials are configured.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether YouTube credentials are configured
            - has_client_credentials (bool): Whether client ID and secret are configured
            - has_refresh_token (bool): Whether refresh token is configured
    
    Example:
        ```json
        {
            "configured": true,
            "has_client_credentials": true,
            "has_refresh_token": true
        }
        ```
    """
    client = YouTubeApiClient()
    has_client_credentials = all([client.client_id, client.client_secret])
    has_refresh_token = client.refresh_token is not None
    
    return {
        "configured": has_client_credentials and has_refresh_token,
        "has_client_credentials": has_client_credentials,
        "has_refresh_token": has_refresh_token,
    }


@router.get("/test-connection", response_model=YouTubeConnectionTestResponse, tags=["youtube"])
def test_youtube_connection() -> YouTubeConnectionTestResponse:
    """
    Test connection to YouTube Data API.
    
    Attempts to connect to YouTube Data API and fetch authenticated channel info.
    This endpoint verifies that the configured credentials are valid and can
    successfully authenticate with YouTube's API.
    
    Returns:
        YouTubeConnectionTestResponse: Connection test result containing:
            - connected (bool): Whether connection was successful
            - channel_info (dict | None): Channel information if connected, None otherwise
            - error (str | None): Error message if connection failed, None otherwise
        
    Raises:
        HTTPException: 500 if unexpected error occurs during connection test.
        
    Example:
        ```json
        {
            "connected": true,
            "channel_info": {
                "id": "UCxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "title": "My Channel",
                "description": "Channel description",
                "custom_url": "@mychannel",
                "subscriber_count": 1000
            },
            "error": null
        }
        ```
    """
    try:
        client = YouTubeApiClient()
        channel_info = client.test_connection()
        return YouTubeConnectionTestResponse(
            connected=True,
            channel_info=channel_info,
            error=None,
        )
    except YouTubeApiError as exc:
        logger.error(f"YouTube connection test failed: {exc}")
        return YouTubeConnectionTestResponse(
            connected=False,
            channel_info=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during YouTube connection test")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/me", response_model=YouTubeChannelInfoResponse, tags=["youtube"])
def get_youtube_channel_info() -> YouTubeChannelInfoResponse:
    """
    Get authenticated YouTube channel information.
    
    Fetches information about the authenticated YouTube channel, including
    channel ID, title, description, custom URL, and subscriber count.
    
    Returns:
        YouTubeChannelInfoResponse: Channel information containing:
            - channel_info (dict): Channel information dictionary with:
                - id (str): Channel ID
                - title (str): Channel title
                - description (str): Channel description
                - custom_url (str, optional): Custom URL
                - subscriber_count (int, optional): Subscriber count
        
    Raises:
        HTTPException:
            - 500 if YouTube Data API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
        
    Example:
        ```json
        {
            "channel_info": {
                "id": "UCxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "title": "My Channel",
                "description": "Channel description",
                "custom_url": "@mychannel",
                "subscriber_count": 1000
            }
        }
        ```
    """
    try:
        client = YouTubeApiClient()
        channel_info = client.get_me()
        return YouTubeChannelInfoResponse(channel_info=channel_info)
    except YouTubeApiError as exc:
        logger.error(f"Failed to get YouTube channel info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"YouTube Data API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error getting YouTube channel info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/upload-video", response_model=YouTubeUploadVideoResponse, tags=["youtube"])
def upload_youtube_video(request: YouTubeUploadVideoRequest) -> YouTubeUploadVideoResponse:
    """
    Upload a video to YouTube.
    
    Uploads a video file to YouTube using the YouTube Data API v3.
    Supports resumable uploads for large files and optional thumbnail upload.
    
    Args:
        request: Upload request containing:
            - video_path (str): Path to the video file to upload
            - title (str): Video title (required, max 100 characters)
            - description (str): Video description (optional)
            - tags (list[str] | None): List of tags for the video (optional)
            - category_id (str): YouTube category ID (default: "22" for People & Blogs)
            - privacy_status (str): Privacy status - "private", "unlisted", or "public" (default: "private")
            - thumbnail_path (str | None): Path to thumbnail image file (optional)
    
    Returns:
        YouTubeUploadVideoResponse: Upload result containing:
            - success (bool): Whether upload was successful
            - video_id (str | None): YouTube video ID if successful
            - video_url (str | None): URL to uploaded video if successful
            - title (str | None): Video title if successful
            - description (str | None): Video description if successful
            - privacy_status (str | None): Privacy status if successful
            - error (str | None): Error message if upload failed
    
    Raises:
        HTTPException:
            - 400 if request validation fails
            - 500 if YouTube Data API error occurs
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "success": true,
            "video_id": "dQw4w9WgXcQ",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "My Video",
            "description": "Video description",
            "privacy_status": "private",
            "error": null
        }
        ```
    """
    try:
        client = YouTubeApiClient()
        result = client.upload_video(
            video_path=request.video_path,
            title=request.title,
            description=request.description,
            tags=request.tags,
            category_id=request.category_id,
            privacy_status=request.privacy_status,
            thumbnail_path=request.thumbnail_path,
        )
        return YouTubeUploadVideoResponse(
            success=True,
            video_id=result.get("video_id"),
            video_url=result.get("video_url"),
            title=result.get("title"),
            description=result.get("description"),
            privacy_status=result.get("privacy_status"),
            error=None,
        )
    except YouTubeApiError as exc:
        logger.error(f"YouTube video upload failed: {exc}")
        return YouTubeUploadVideoResponse(
            success=False,
            video_id=None,
            video_url=None,
            title=None,
            description=None,
            privacy_status=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during YouTube video upload")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/upload-short", response_model=YouTubeUploadShortResponse, tags=["youtube"])
def upload_youtube_short(request: YouTubeUploadShortRequest) -> YouTubeUploadShortResponse:
    """
    Upload a YouTube Short (vertical video, 60 seconds or less).
    
    YouTube Shorts are automatically detected by YouTube when videos meet these criteria:
    - Duration: 60 seconds or less
    - Aspect ratio: Vertical (9:16 recommended)
    - Has "#Shorts" in title or description (optional but recommended)
    
    Args:
        request: Upload request containing:
            - video_path (str): Path to the video file to upload
            - title (str): Video title (required, max 100 characters). Should include "#Shorts" for best results
            - description (str): Video description (optional). Can include "#Shorts" tag
            - tags (list[str] | None): List of tags for the video (optional). "#Shorts" will be automatically added if not present
            - privacy_status (str): Privacy status - "private", "unlisted", or "public" (default: "private")
            - thumbnail_path (str | None): Path to thumbnail image file (optional)
            - validate_duration (bool): Whether to validate video duration is 60 seconds or less (default: True)
            - validate_aspect_ratio (bool): Whether to validate aspect ratio is vertical (default: True)
    
    Returns:
        YouTubeUploadShortResponse: Upload result containing:
            - success (bool): Whether upload was successful
            - video_id (str | None): YouTube video ID if successful
            - video_url (str | None): URL to uploaded video if successful
            - title (str | None): Video title if successful
            - description (str | None): Video description if successful
            - privacy_status (str | None): Privacy status if successful
            - is_short (bool): Whether video meets Shorts criteria
            - error (str | None): Error message if upload failed
    
    Raises:
        HTTPException:
            - 400 if request validation fails
            - 500 if YouTube Data API error occurs
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "success": true,
            "video_id": "dQw4w9WgXcQ",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "My Short #Shorts",
            "description": "Short video description #Shorts",
            "privacy_status": "private",
            "is_short": true,
            "error": null
        }
        ```
    """
    try:
        client = YouTubeApiClient()
        result = client.upload_short(
            video_path=request.video_path,
            title=request.title,
            description=request.description,
            tags=request.tags,
            privacy_status=request.privacy_status,
            thumbnail_path=request.thumbnail_path,
            validate_duration=request.validate_duration,
            validate_aspect_ratio=request.validate_aspect_ratio,
        )
        return YouTubeUploadShortResponse(
            success=True,
            video_id=result.get("video_id"),
            video_url=result.get("video_url"),
            title=result.get("title"),
            description=result.get("description"),
            privacy_status=result.get("privacy_status"),
            is_short=result.get("is_short", True),
            error=None,
        )
    except YouTubeApiError as exc:
        logger.error(f"YouTube Short upload failed: {exc}")
        return YouTubeUploadShortResponse(
            success=False,
            video_id=None,
            video_url=None,
            title=None,
            description=None,
            privacy_status=None,
            is_short=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during YouTube Short upload")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class YouTubeThumbnailOptimizeRequest(BaseModel):
    """Request model for YouTube thumbnail optimization."""
    video_path: str | None = None
    video_filename: str | None = None
    thumbnail_path: str | None = None
    timestamp: float | None = None


class YouTubeThumbnailOptimizeResponse(BaseModel):
    """Response model for YouTube thumbnail optimization."""
    success: bool
    thumbnail_path: str | None = None
    width: int | None = None
    height: int | None = None
    file_size_kb: float | None = None
    error: str | None = None


@router.post("/optimize-thumbnail", response_model=YouTubeThumbnailOptimizeResponse, tags=["youtube"])
def optimize_youtube_thumbnail(request: YouTubeThumbnailOptimizeRequest) -> YouTubeThumbnailOptimizeResponse:
    """
    Generate and optimize a thumbnail for YouTube upload.
    
    This endpoint can either:
    1. Generate a thumbnail from a video file and optimize it for YouTube
    2. Optimize an existing thumbnail image for YouTube
    
    YouTube thumbnail requirements:
    - Recommended: 1280x720 pixels
    - Minimum: 640x360 pixels
    - Maximum file size: 2MB
    - Format: JPG, PNG, or GIF (JPG recommended)
    
    Args:
        request: Optimization request containing:
            - video_path (str | None): Full path to video file (optional if video_filename provided)
            - video_filename (str | None): Filename of video in videos directory (optional if video_path provided)
            - thumbnail_path (str | None): Path to existing thumbnail to optimize (optional if video provided)
            - timestamp (float | None): Timestamp in seconds to capture frame from video (default: middle or 1s)
    
    Returns:
        YouTubeThumbnailOptimizeResponse: Optimization result containing:
            - success (bool): Whether optimization was successful
            - thumbnail_path (str | None): Path to optimized thumbnail if successful
            - width (int | None): Thumbnail width in pixels if successful
            - height (int | None): Thumbnail height in pixels if successful
            - file_size_kb (float | None): File size in KB if successful
            - error (str | None): Error message if optimization failed
    
    Raises:
        HTTPException:
            - 400 if request validation fails
            - 500 if optimization fails
    
    Example:
        ```json
        {
            "success": true,
            "thumbnail_path": "/content/thumbnails/video_optimized.jpg",
            "width": 1280,
            "height": 720,
            "file_size_kb": 145.3,
            "error": null
        }
        ```
    """
    try:
        service = ThumbnailOptimizationService()
        
        # Determine video path
        video_path = None
        if request.video_path:
            video_path = request.video_path
        elif request.video_filename:
            video_dir = videos_dir()
            video_path = video_dir / request.video_filename
            if not video_path.exists():
                return YouTubeThumbnailOptimizeResponse(
                    success=False,
                    thumbnail_path=None,
                    width=None,
                    height=None,
                    file_size_kb=None,
                    error=f"Video file not found: {request.video_filename}",
                )
            video_path = str(video_path)
        
        # Generate and optimize thumbnail
        if video_path:
            # Generate from video and optimize
            optimized_path = service.generate_and_optimize_for_youtube(
                video_path=video_path,
                timestamp=request.timestamp,
            )
        elif request.thumbnail_path:
            # Optimize existing thumbnail
            optimized_path = service.optimize_for_youtube(
                thumbnail_path=request.thumbnail_path,
            )
        else:
            return YouTubeThumbnailOptimizeResponse(
                success=False,
                thumbnail_path=None,
                width=None,
                height=None,
                file_size_kb=None,
                error="Either video_path/video_filename or thumbnail_path must be provided",
            )
        
        # Get thumbnail metadata
        try:
            from PIL import Image
            img = Image.open(optimized_path)
            width, height = img.size
            file_size_kb = optimized_path.stat().st_size / 1024
        except Exception:
            width = None
            height = None
            file_size_kb = None
        
        # Return relative path from content directory
        try:
            from app.core.paths import content_dir
            content_path = content_dir()
            if optimized_path.is_relative_to(content_path):
                relative_path = str(optimized_path.relative_to(content_path))
                thumbnail_path = f"/content/{relative_path}"
            else:
                thumbnail_path = str(optimized_path)
        except Exception:
            thumbnail_path = str(optimized_path)
        
        return YouTubeThumbnailOptimizeResponse(
            success=True,
            thumbnail_path=thumbnail_path,
            width=width,
            height=height,
            file_size_kb=file_size_kb,
            error=None,
        )
    except ThumbnailOptimizationError as exc:
        logger.error(f"YouTube thumbnail optimization failed: {exc}")
        return YouTubeThumbnailOptimizeResponse(
            success=False,
            thumbnail_path=None,
            width=None,
            height=None,
            file_size_kb=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during YouTube thumbnail optimization")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


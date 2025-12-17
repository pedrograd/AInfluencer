"""YouTube Data API endpoints for YouTube API integration."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.core.paths import videos_dir
from app.services.thumbnail_optimization_service import ThumbnailOptimizationService, ThumbnailOptimizationError
from app.services.video_generation_service import VideoGenerationService, VideoGenerationMethod
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


class YouTubeCreateAndUploadShortRequest(BaseModel):
    """Request model for creating and uploading a YouTube Short."""
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt describing the video to generate")
    negative_prompt: str | None = Field(default=None, max_length=2000, description="Negative prompt describing what to avoid")
    duration: int | None = Field(default=30, ge=1, le=60, description="Video duration in seconds (1-60, default: 30)")
    fps: int | None = Field(default=30, ge=8, le=60, description="Frames per second (8-60, default: 30)")
    seed: int | None = Field(default=None, description="Random seed for reproducibility")
    method: str = Field(default="animatediff", description="Video generation method: 'animatediff' or 'stable_video_diffusion'")
    title: str = Field(..., min_length=1, max_length=100, description="YouTube video title (required, max 100 characters). Should include '#Shorts' for best results")
    description: str = Field(default="", description="Video description (optional). Can include '#Shorts' tag")
    tags: list[str] | None = Field(default=None, description="List of tags for the video (optional). '#Shorts' will be automatically added if not present")
    privacy_status: str = Field(default="private", description="Privacy status - 'private', 'unlisted', or 'public' (default: 'private')")
    thumbnail_path: str | None = Field(default=None, description="Path to thumbnail image file (optional)")
    max_wait_seconds: int = Field(default=600, ge=60, le=3600, description="Maximum time to wait for video generation before timing out (60-3600 seconds, default: 600)")


class YouTubeCreateAndUploadShortResponse(BaseModel):
    """Response model for creating and uploading a YouTube Short."""
    success: bool
    generation_job_id: str | None = None
    video_id: str | None = None
    video_url: str | None = None
    title: str | None = None
    description: str | None = None
    privacy_status: str | None = None
    is_short: bool = False
    video_path: str | None = None
    generation_status: str | None = None
    upload_status: str | None = None
    error: str | None = None


@router.post("/create-and-upload-short", response_model=YouTubeCreateAndUploadShortResponse, tags=["youtube"])
def create_and_upload_youtube_short(request: YouTubeCreateAndUploadShortRequest) -> YouTubeCreateAndUploadShortResponse:
    """
    Create a YouTube Short video and automatically upload it to YouTube.
    
    This endpoint combines video generation and YouTube upload into a single workflow:
    1. Generates a YouTube Short video using the specified method and parameters
    2. Waits for video generation to complete (with timeout)
    3. Automatically uploads the generated video to YouTube
    4. Returns combined results from both operations
    
    YouTube Shorts are automatically detected by YouTube when videos meet these criteria:
    - Duration: 60 seconds or less
    - Aspect ratio: Vertical (9:16 recommended)
    - Has "#Shorts" in title or description (optional but recommended)
    
    Args:
        request: Request containing:
            - prompt (str): Text prompt describing the video to generate (required)
            - negative_prompt (str | None): Negative prompt (optional)
            - duration (int | None): Video duration in seconds (1-60, default: 30)
            - fps (int | None): Frames per second (8-60, default: 30)
            - seed (int | None): Random seed for reproducibility (optional)
            - method (str): Video generation method - 'animatediff' or 'stable_video_diffusion' (default: 'animatediff')
            - title (str): YouTube video title (required, max 100 characters). Should include "#Shorts"
            - description (str): Video description (optional). Can include "#Shorts" tag
            - tags (list[str] | None): List of tags (optional). "#Shorts" will be automatically added
            - privacy_status (str): Privacy status - "private", "unlisted", or "public" (default: "private")
            - thumbnail_path (str | None): Path to thumbnail image file (optional)
            - max_wait_seconds (int): Maximum time to wait for generation (60-3600 seconds, default: 600)
    
    Returns:
        YouTubeCreateAndUploadShortResponse: Combined result containing:
            - success (bool): Whether both generation and upload were successful
            - generation_job_id (str | None): Video generation job ID
            - video_id (str | None): YouTube video ID if upload successful
            - video_url (str | None): URL to uploaded video if successful
            - title (str | None): Video title if successful
            - description (str | None): Video description if successful
            - privacy_status (str | None): Privacy status if successful
            - is_short (bool): Whether video meets Shorts criteria
            - video_path (str | None): Path to generated video file
            - generation_status (str | None): Final generation job status
            - upload_status (str | None): Upload operation status
            - error (str | None): Error message if any operation failed
    
    Raises:
        HTTPException:
            - 400 if request validation fails
            - 500 if video generation fails
            - 500 if YouTube upload fails
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "success": true,
            "generation_job_id": "abc123",
            "video_id": "dQw4w9WgXcQ",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "My Short #Shorts",
            "description": "Short video description #Shorts",
            "privacy_status": "private",
            "is_short": true,
            "video_path": "/content/videos/generated_short.mp4",
            "generation_status": "succeeded",
            "upload_status": "success",
            "error": null
        }
        ```
    """
    try:
        # Initialize services
        video_service = VideoGenerationService()
        youtube_client = YouTubeApiClient()
        
        # Validate and prepare generation method
        try:
            method = VideoGenerationMethod(request.method.lower())
        except ValueError:
            return YouTubeCreateAndUploadShortResponse(
                success=False,
                error=f"Invalid method '{request.method}'. Must be 'animatediff' or 'stable_video_diffusion'",
            )
        
        # Step 1: Generate video
        logger.info(f"Starting YouTube Short generation: prompt={request.prompt[:50]}..., method={method.value}")
        generation_result = video_service.generate_video(
            method=method,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            duration=request.duration,
            fps=request.fps,
            seed=request.seed,
            is_short_video=True,
            platform="youtube_shorts",
        )
        
        generation_job_id = generation_result.get("job_id")
        if not generation_job_id:
            return YouTubeCreateAndUploadShortResponse(
                success=False,
                error="Failed to create video generation job",
            )
        
        logger.info(f"Video generation job created: job_id={generation_job_id}")
        
        # Step 2: Wait for video generation to complete
        start_time = time.time()
        video_path = None
        generation_status = "queued"
        
        while time.time() - start_time < request.max_wait_seconds:
            status = video_service.get_video_generation_status(generation_job_id)
            generation_status = status.get("status", "unknown")
            video_path = status.get("video_path")
            
            if generation_status == "succeeded" and video_path:
                logger.info(f"Video generation completed: job_id={generation_job_id}, video_path={video_path}")
                break
            elif generation_status == "failed":
                error_msg = status.get("error", "Video generation failed")
                logger.error(f"Video generation failed: job_id={generation_job_id}, error={error_msg}")
                return YouTubeCreateAndUploadShortResponse(
                    success=False,
                    generation_job_id=generation_job_id,
                    generation_status=generation_status,
                    error=f"Video generation failed: {error_msg}",
                )
            elif generation_status == "cancelled":
                return YouTubeCreateAndUploadShortResponse(
                    success=False,
                    generation_job_id=generation_job_id,
                    generation_status=generation_status,
                    error="Video generation was cancelled",
                )
            
            # Wait before next poll
            time.sleep(5)
        
        # Check if generation completed
        if not video_path or generation_status != "succeeded":
            return YouTubeCreateAndUploadShortResponse(
                success=False,
                generation_job_id=generation_job_id,
                generation_status=generation_status,
                error=f"Video generation did not complete within {request.max_wait_seconds} seconds",
            )
        
        # Ensure video_path is a Path object
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            return YouTubeCreateAndUploadShortResponse(
                success=False,
                generation_job_id=generation_job_id,
                generation_status=generation_status,
                video_path=str(video_path),
                error=f"Generated video file not found: {video_path}",
            )
        
        # Step 3: Upload to YouTube
        logger.info(f"Uploading video to YouTube: video_path={video_path}")
        try:
            # Ensure "#Shorts" is in tags if not present
            tags = request.tags or []
            if "#Shorts" not in tags and "#Shorts" not in request.title.lower() and "#Shorts" not in request.description.lower():
                tags.append("#Shorts")
            
            upload_result = youtube_client.upload_short(
                video_path=video_path_obj,
                title=request.title,
                description=request.description,
                tags=tags,
                privacy_status=request.privacy_status,
                thumbnail_path=request.thumbnail_path,
                validate_duration=True,
                validate_aspect_ratio=True,
            )
            
            logger.info(f"YouTube Short uploaded successfully: video_id={upload_result.get('video_id')}")
            
            return YouTubeCreateAndUploadShortResponse(
                success=True,
                generation_job_id=generation_job_id,
                video_id=upload_result.get("video_id"),
                video_url=upload_result.get("video_url"),
                title=upload_result.get("title"),
                description=upload_result.get("description"),
                privacy_status=upload_result.get("privacy_status"),
                is_short=upload_result.get("is_short", True),
                video_path=str(video_path),
                generation_status=generation_status,
                upload_status="success",
                error=None,
            )
        except YouTubeApiError as exc:
            logger.error(f"YouTube Short upload failed: {exc}")
            return YouTubeCreateAndUploadShortResponse(
                success=False,
                generation_job_id=generation_job_id,
                video_path=str(video_path),
                generation_status=generation_status,
                upload_status="failed",
                error=f"YouTube upload failed: {str(exc)}",
            )
    except Exception as exc:
        logger.exception("Unexpected error during YouTube Short creation and upload")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


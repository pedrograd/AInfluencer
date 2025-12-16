"""YouTube Data API endpoints for YouTube API integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
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


"""TikTok API endpoints for TikTok API integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel

from app.core.logging import get_logger
from app.core.middleware import limiter
from app.services.tiktok_client import TikTokApiClient, TikTokApiError

logger = get_logger(__name__)

router = APIRouter()


class TikTokConnectionTestResponse(BaseModel):
    """Response model for TikTok connection test."""
    connected: bool
    user_info: dict | None = None
    error: str | None = None


class TikTokUserInfoResponse(BaseModel):
    """Response model for TikTok user information."""
    user_info: dict


@router.get("/status", tags=["tiktok"])
def get_tiktok_status() -> dict:
    """
    Get TikTok API client status.
    
    Returns the current configuration status of the TikTok API client,
    including whether an access token is configured, API version, and base URL.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether access token is configured
            - api_version (str): TikTok API version
            - base_url (str): Base URL for API requests
    
    Example:
        ```json
        {
            "configured": true,
            "api_version": "v2",
            "base_url": "https://open.tiktokapis.com"
        }
        ```
    """
    client = TikTokApiClient()
    has_token = client.access_token is not None
    
    return {
        "configured": has_token,
        "api_version": client.api_version,
        "base_url": client.base_url,
    }


@router.get("/test-connection", response_model=TikTokConnectionTestResponse, tags=["tiktok"])
def test_tiktok_connection() -> TikTokConnectionTestResponse:
    """
    Test connection to TikTok API.
    
    Attempts to connect to TikTok API and fetch authenticated user info.
    This endpoint verifies that the configured access token is valid and can
    successfully authenticate with TikTok's API.
    
    Returns:
        TikTokConnectionTestResponse: Connection test result containing:
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
                "open_id": "123456789",
                "display_name": "example_user",
                "avatar_url": "https://..."
            },
            "error": null
        }
        ```
    """
    try:
        client = TikTokApiClient()
        user_info = client.test_connection()
        return TikTokConnectionTestResponse(
            connected=True,
            user_info=user_info,
            error=None,
        )
    except TikTokApiError as exc:
        logger.error(f"TikTok connection test failed: {exc}")
        return TikTokConnectionTestResponse(
            connected=False,
            user_info=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during TikTok connection test")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/me", response_model=TikTokUserInfoResponse, tags=["tiktok"])
def get_tiktok_user_info() -> TikTokUserInfoResponse:
    """
    Get authenticated TikTok user information.
    
    Fetches information about the authenticated TikTok user, including
    user Open ID, Union ID, display name, and avatar URL.
    
    Returns:
        TikTokUserInfoResponse: User information containing:
            - user_info (dict): User information dictionary with:
                - open_id (str): User Open ID
                - union_id (str | None): User Union ID (if available)
                - avatar_url (str | None): User avatar URL
                - display_name (str | None): User display name
        
    Raises:
        HTTPException:
            - 500 if TikTok API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
        
    Example:
        ```json
        {
            "user_info": {
                "open_id": "123456789",
                "union_id": "987654321",
                "display_name": "Example User",
                "avatar_url": "https://..."
            }
        }
        ```
    """
    try:
        client = TikTokApiClient()
        user_info = client.get_me()
        return TikTokUserInfoResponse(user_info=user_info)
    except TikTokApiError as exc:
        logger.error(f"Failed to get TikTok user info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"TikTok API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error getting TikTok user info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class UploadVideoRequest(BaseModel):
    """Request model for uploading a video."""
    caption: str | None = None
    privacy_level: str = "PUBLIC_TO_EVERYONE"


class UploadVideoResponse(BaseModel):
    """Response model for video upload."""
    publish_id: str
    upload_url: str | None = None
    status: str
    message: str | None = None


# Note: Limiter temporarily removed due to FastAPI/Pydantic v2 compatibility issue with UploadFile + response_model
@router.post("/upload", response_model=UploadVideoResponse, tags=["tiktok"])
async def upload_video(
    request: Request,
    video: UploadFile = File(...),
    caption: str | None = Form(None),
    privacy_level: str = Form("PUBLIC_TO_EVERYONE"),
):
    """
    Upload a video to TikTok.
    
    Uploads a video file to TikTok. This is a multi-step process:
    1. Initialize upload (get upload URL and publish_id)
    2. Upload video file to the provided URL
    3. Publish video using publish_id
    
    Args:
        video: Video file to upload (required).
        caption: Optional caption text for the video.
        privacy_level: Privacy level (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY).
    
    Returns:
        UploadVideoResponse: Upload initialization result containing:
            - publish_id (str): Publish ID for the uploaded video
            - upload_url (str | None): URL for video upload (if two-phase upload)
            - status (str): Upload status
            - message (str | None): Additional information
    
    Raises:
        HTTPException:
            - 400 if validation fails (missing video file)
            - 500 if TikTok API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "publish_id": "abc123",
            "upload_url": "https://...",
            "status": "initialized",
            "message": "Video upload initialized. Use upload_url to complete file upload, then call publish_video with publish_id."
        }
        ```
    """
    try:
        if not video:
            raise HTTPException(
                status_code=400,
                detail="Video file is required",
            )
        
        # Save uploaded file temporarily
        # In production, this should be handled more securely
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            content = await video.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            client = TikTokApiClient()
            upload_data = client.upload_video(
                video_path=tmp_path,
                caption=caption,
                privacy_level=privacy_level,
            )
            
            return UploadVideoResponse(
                publish_id=upload_data["publish_id"],
                upload_url=upload_data.get("upload_url"),
                status=upload_data.get("status", "initialized"),
                message=upload_data.get("message"),
            )
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except TikTokApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to upload TikTok video: {exc}")
        
        if "required" in error_msg.lower() or "not configured" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"TikTok API error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"TikTok API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error uploading TikTok video")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class PublishVideoRequest(BaseModel):
    """Request model for publishing a video."""
    publish_id: str


class PublishVideoResponse(BaseModel):
    """Response model for published video."""
    publish_id: str
    status: str


@router.post("/publish", response_model=PublishVideoResponse, tags=["tiktok"])
@limiter.limit("10/minute")
def publish_video(request: Request, req: PublishVideoRequest) -> PublishVideoResponse:
    """
    Publish an uploaded video to TikTok.
    
    Publishes a video that has been uploaded to TikTok using the publish_id
    from the upload_video endpoint.
    
    Args:
        req: Publish video request containing:
            - publish_id (str): Publish ID from upload_video (required)
    
    Returns:
        PublishVideoResponse: Publication result containing:
            - publish_id (str): Publish ID
            - status (str): Publication status
    
    Raises:
        HTTPException:
            - 400 if validation fails (missing publish_id)
            - 500 if TikTok API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "publish_id": "abc123",
            "status": "published"
        }
        ```
    """
    try:
        if not req.publish_id or not req.publish_id.strip():
            raise HTTPException(
                status_code=400,
                detail="publish_id is required",
            )
        
        client = TikTokApiClient()
        publish_data = client.publish_video(publish_id=req.publish_id)
        
        return PublishVideoResponse(
            publish_id=publish_data["publish_id"],
            status=publish_data.get("status", "unknown"),
        )
    except TikTokApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to publish TikTok video: {exc}")
        
        if "required" in error_msg.lower() or "not configured" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"TikTok API error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"TikTok API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error publishing TikTok video")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

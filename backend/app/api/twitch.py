"""Twitch API endpoints for Twitch API integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.logging import get_logger
from app.core.middleware import limiter
from app.services.twitch_client import TwitchApiClient, TwitchApiError

logger = get_logger(__name__)

router = APIRouter()


class TwitchConnectionTestResponse(BaseModel):
    """Response model for Twitch connection test."""
    connected: bool
    user_info: dict | None = None
    error: str | None = None


class TwitchUserInfoResponse(BaseModel):
    """Response model for Twitch user information."""
    user_info: dict


class StreamInfoResponse(BaseModel):
    """Response model for stream information."""
    stream_info: dict | None = None
    is_live: bool


class SimulateStreamRequest(BaseModel):
    """Request model for simulating stream start."""
    title: str
    game_id: str | None = None
    language: str = "en"


class SimulateStreamResponse(BaseModel):
    """Response model for stream simulation."""
    status: str
    message: str
    stream_data: dict


@router.get("/status", tags=["twitch"])
def get_twitch_status() -> dict:
    """
    Get Twitch API client status.
    
    Returns the current configuration status of the Twitch API client,
    including whether an access token and client ID are configured, and base URL.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether access token and client ID are configured
            - base_url (str): Base URL for API requests
    
    Example:
        ```json
        {
            "configured": true,
            "base_url": "https://api.twitch.tv/helix"
        }
        ```
    """
    client = TwitchApiClient()
    has_token = client.access_token is not None
    has_client_id = client.client_id is not None
    
    return {
        "configured": has_token and has_client_id,
        "base_url": client.base_url,
    }


@router.get("/test-connection", response_model=TwitchConnectionTestResponse, tags=["twitch"])
def test_twitch_connection() -> TwitchConnectionTestResponse:
    """
    Test connection to Twitch API.
    
    Attempts to connect to Twitch API and fetch authenticated user info.
    This endpoint verifies that the configured access token and client ID are valid
    and can successfully authenticate with Twitch's API.
    
    Returns:
        TwitchConnectionTestResponse: Connection test result containing:
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
                "login": "example_user",
                "display_name": "Example User",
                "profile_image_url": "https://..."
            },
            "error": null
        }
        ```
    """
    try:
        client = TwitchApiClient()
        user_info = client.test_connection()
        return TwitchConnectionTestResponse(
            connected=True,
            user_info=user_info,
            error=None,
        )
    except TwitchApiError as exc:
        logger.error(f"Twitch connection test failed: {exc}")
        return TwitchConnectionTestResponse(
            connected=False,
            user_info=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during Twitch connection test")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/me", response_model=TwitchUserInfoResponse, tags=["twitch"])
def get_twitch_user_info() -> TwitchUserInfoResponse:
    """
    Get authenticated Twitch user information.
    
    Fetches information about the authenticated Twitch user, including
    user ID, login, display name, email, profile image, broadcaster type, and description.
    
    Returns:
        TwitchUserInfoResponse: User information containing:
            - user_info (dict): User information dictionary with:
                - id (str): User ID
                - login (str): Username
                - display_name (str): Display name
                - email (str | None): Email (if available)
                - profile_image_url (str | None): Profile image URL
                - broadcaster_type (str | None): Broadcaster type
                - description (str | None): User description
        
    Raises:
        HTTPException:
            - 500 if Twitch API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
        
    Example:
        ```json
        {
            "user_info": {
                "id": "123456789",
                "login": "example_user",
                "display_name": "Example User",
                "email": "user@example.com",
                "profile_image_url": "https://...",
                "broadcaster_type": "partner",
                "description": "Streamer description"
            }
        }
        ```
    """
    try:
        client = TwitchApiClient()
        user_info = client.get_me()
        return TwitchUserInfoResponse(user_info=user_info)
    except TwitchApiError as exc:
        logger.error(f"Failed to get Twitch user info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Twitch API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error getting Twitch user info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/stream/info", response_model=StreamInfoResponse, tags=["twitch"])
@limiter.limit("10/minute")
def get_stream_info(request: Request, user_id: str | None = None) -> StreamInfoResponse:
    """
    Get stream information for a user.
    
    Retrieves current stream information for the authenticated user or a specified user.
    Returns stream details if the user is currently live, or indicates that the stream is offline.
    
    Args:
        user_id: Optional user ID. If not provided, uses authenticated user.
    
    Returns:
        StreamInfoResponse: Stream information containing:
            - stream_info (dict | None): Stream information if live, None otherwise
            - is_live (bool): Whether the stream is currently live
    
    Raises:
        HTTPException:
            - 500 if Twitch API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "stream_info": {
                "id": "stream_id",
                "user_id": "123456789",
                "user_name": "example_user",
                "title": "Stream Title",
                "game_name": "Just Chatting",
                "viewer_count": 100,
                "started_at": "2025-01-01T00:00:00Z"
            },
            "is_live": true
        }
        ```
    """
    try:
        client = TwitchApiClient()
        stream_data = client.get_stream_info(user_id=user_id)
        return StreamInfoResponse(
            stream_info=stream_data.get("stream_info"),
            is_live=stream_data.get("is_live", False),
        )
    except TwitchApiError as exc:
        logger.error(f"Failed to get Twitch stream info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Twitch API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error getting Twitch stream info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/stream/simulate/start", response_model=SimulateStreamResponse, tags=["twitch"])
@limiter.limit("10/minute")
def simulate_start_stream(request: Request, req: SimulateStreamRequest) -> SimulateStreamResponse:
    """
    Simulate starting a stream (for testing/demo purposes).
    
    This endpoint simulates starting a stream for demonstration purposes.
    Note: Actual stream starting requires OBS or streaming software. This endpoint
    returns mock data for testing and demonstration.
    
    Args:
        req: Simulate stream request containing:
            - title (str): Stream title (required)
            - game_id (str | None): Optional game/category ID
            - language (str): Stream language (default: "en")
    
    Returns:
        SimulateStreamResponse: Stream simulation result containing:
            - status (str): Simulation status
            - message (str): Information message
            - stream_data (dict): Simulated stream data
    
    Raises:
        HTTPException:
            - 400 if validation fails (missing title)
            - 500 if Twitch API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "status": "simulated",
            "message": "Stream start simulated. Actual streaming requires OBS or streaming software.",
            "stream_data": {
                "user_id": "123456789",
                "user_name": "example_user",
                "title": "My Stream",
                "is_live": true,
                "simulated": true
            }
        }
        ```
    """
    try:
        if not req.title or not req.title.strip():
            raise HTTPException(
                status_code=400,
                detail="Stream title is required",
            )
        
        client = TwitchApiClient()
        stream_data = client.simulate_start_stream(
            title=req.title,
            game_id=req.game_id,
            language=req.language,
        )
        
        return SimulateStreamResponse(
            status=stream_data["status"],
            message=stream_data["message"],
            stream_data=stream_data["stream_data"],
        )
    except TwitchApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to simulate Twitch stream start: {exc}")
        
        if "required" in error_msg.lower() or "not configured" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Twitch API error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Twitch API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error simulating Twitch stream start")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/stream/simulate/stop", response_model=SimulateStreamResponse, tags=["twitch"])
@limiter.limit("10/minute")
def simulate_stop_stream(request: Request) -> SimulateStreamResponse:
    """
    Simulate stopping a stream (for testing/demo purposes).
    
    This endpoint simulates stopping a stream for demonstration purposes.
    Note: Actual stream stopping requires OBS or streaming software. This endpoint
    returns mock data for testing and demonstration.
    
    Returns:
        SimulateStreamResponse: Stream simulation result containing:
            - status (str): Simulation status
            - message (str): Information message
            - stream_data (dict): Simulated stream data
    
    Raises:
        HTTPException:
            - 500 if Twitch API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "status": "simulated",
            "message": "Stream stop simulated. Actual streaming requires OBS or streaming software.",
            "stream_data": {
                "user_id": "123456789",
                "user_name": "example_user",
                "is_live": false,
                "simulated": true
            }
        }
        ```
    """
    try:
        client = TwitchApiClient()
        stream_data = client.simulate_stop_stream()
        
        return SimulateStreamResponse(
            status=stream_data["status"],
            message=stream_data["message"],
            stream_data=stream_data["stream_data"],
        )
    except TwitchApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to simulate Twitch stream stop: {exc}")
        
        if "required" in error_msg.lower() or "not configured" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Twitch API error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Twitch API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error simulating Twitch stream stop")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

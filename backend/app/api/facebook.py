"""Facebook Graph API endpoints for Facebook Graph API integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.facebook_client import FacebookApiClient, FacebookApiError

logger = get_logger(__name__)

router = APIRouter()


class FacebookConnectionTestResponse(BaseModel):
    """Response model for Facebook connection test."""
    connected: bool
    user_info: dict | None = None
    error: str | None = None


class FacebookUserInfoResponse(BaseModel):
    """Response model for Facebook user information."""
    user_info: dict


@router.get("/status", tags=["facebook"])
def get_facebook_status() -> dict:
    """
    Get Facebook Graph API client status.
    
    Returns the current configuration status of the Facebook Graph API client,
    including whether credentials are configured.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether Facebook credentials are configured
            - has_access_token (bool): Whether access token is configured
            - has_app_credentials (bool): Whether app ID and secret are configured
    
    Example:
        ```json
        {
            "configured": true,
            "has_access_token": true,
            "has_app_credentials": true
        }
        ```
    """
    client = FacebookApiClient()
    has_access_token = client.access_token is not None
    has_app_credentials = all([client.app_id, client.app_secret])
    
    return {
        "configured": has_access_token,
        "has_access_token": has_access_token,
        "has_app_credentials": has_app_credentials,
    }


@router.get("/test-connection", response_model=FacebookConnectionTestResponse, tags=["facebook"])
def test_facebook_connection() -> FacebookConnectionTestResponse:
    """
    Test connection to Facebook Graph API.
    
    Attempts to connect to Facebook Graph API and fetch authenticated user/page info.
    This endpoint verifies that the configured credentials are valid and can
    successfully authenticate with Facebook's API.
    
    Returns:
        FacebookConnectionTestResponse: Connection test result containing:
            - connected (bool): Whether connection was successful
            - user_info (dict | None): User/page information if connected, None otherwise
            - error (str | None): Error message if connection failed, None otherwise
        
    Raises:
        HTTPException: 500 if unexpected error occurs during connection test.
        
    Example:
        ```json
        {
            "connected": true,
            "user_info": {
                "id": "123456789",
                "name": "Example User",
                "email": "user@example.com"
            },
            "error": null
        }
        ```
    """
    try:
        client = FacebookApiClient()
        user_info = client.test_connection()
        return FacebookConnectionTestResponse(
            connected=True,
            user_info=user_info,
            error=None,
        )
    except FacebookApiError as exc:
        logger.error(f"Facebook connection test failed: {exc}")
        return FacebookConnectionTestResponse(
            connected=False,
            user_info=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during Facebook connection test")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/me", response_model=FacebookUserInfoResponse, tags=["facebook"])
def get_facebook_user_info() -> FacebookUserInfoResponse:
    """
    Get authenticated Facebook user/page information.
    
    Fetches information about the authenticated Facebook user or page, including
    user/page ID, display name, and email address (if available).
    
    Returns:
        FacebookUserInfoResponse: User/page information containing:
            - user_info (dict): User/page information dictionary with:
                - id (str): User/Page ID
                - name (str): Display name
                - email (str, optional): Email address (if available)
        
    Raises:
        HTTPException:
            - 500 if Facebook Graph API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
        
    Example:
        ```json
        {
            "user_info": {
                "id": "123456789",
                "name": "Example User",
                "email": "user@example.com"
            }
        }
        ```
    """
    try:
        client = FacebookApiClient()
        user_info = client.get_me()
        return FacebookUserInfoResponse(user_info=user_info)
    except FacebookApiError as exc:
        logger.error(f"Failed to get Facebook user info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Facebook Graph API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error getting Facebook user info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class CreatePostRequest(BaseModel):
    """Request model for creating a Facebook post."""
    message: str
    page_id: str | None = None
    link: str | None = None


class CreatePostResponse(BaseModel):
    """Response model for created Facebook post."""
    id: str
    message: str
    created_time: str | None = None


@router.post("/post", response_model=CreatePostResponse, tags=["facebook"])
def create_post(req: CreatePostRequest) -> CreatePostResponse:
    """
    Create a post on Facebook.
    
    Creates a new post on Facebook using the configured access token.
    Posts can be created on the authenticated user's feed or on a specific page.
    
    Args:
        req: CreatePostRequest containing:
            - message (str): Post message text (required)
            - page_id (str | None): Optional Facebook Page ID to post to. If None, posts to /me/feed
            - link (str | None): Optional link URL to attach to the post
    
    Returns:
        CreatePostResponse: Created post information containing:
            - id (str): Post ID
            - message (str): Post message text
            - created_time (str | None): Post creation timestamp
    
    Raises:
        HTTPException:
            - 400 if message is empty
            - 500 if Facebook Graph API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        Request:
        {
            "message": "Hello from AInfluencer!",
            "link": "https://example.com"
        }
        
        Response:
        {
            "id": "123456789_987654321",
            "message": "Hello from AInfluencer!",
            "created_time": "2025-12-15T12:00:00+0000"
        }
        ```
    """
    try:
        client = FacebookApiClient()
        post_data = client.create_post(
            message=req.message,
            page_id=req.page_id,
            link=req.link,
        )
        return CreatePostResponse(
            id=post_data["id"],
            message=post_data["message"],
            created_time=post_data.get("created_time"),
        )
    except FacebookApiError as exc:
        logger.error(f"Failed to create Facebook post: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Facebook Graph API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error creating Facebook post")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


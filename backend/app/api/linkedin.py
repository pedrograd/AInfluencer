"""LinkedIn API endpoints for LinkedIn API integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.logging import get_logger
from app.core.middleware import limiter
from app.services.linkedin_client import LinkedInApiClient, LinkedInApiError

logger = get_logger(__name__)

router = APIRouter()


class LinkedInConnectionTestResponse(BaseModel):
    """Response model for LinkedIn connection test."""
    connected: bool
    user_info: dict | None = None
    error: str | None = None


class LinkedInUserInfoResponse(BaseModel):
    """Response model for LinkedIn user information."""
    user_info: dict


@router.get("/status", tags=["linkedin"])
def get_linkedin_status() -> dict:
    """
    Get LinkedIn API client status.
    
    Returns the current configuration status of the LinkedIn API client,
    including whether an access token is configured, API version, and base URL.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether access token is configured
            - api_version (str): LinkedIn API version
            - base_url (str): Base URL for API requests
    
    Example:
        ```json
        {
            "configured": true,
            "api_version": "v2",
            "base_url": "https://api.linkedin.com"
        }
        ```
    """
    client = LinkedInApiClient()
    has_token = client.access_token is not None
    
    return {
        "configured": has_token,
        "api_version": client.api_version,
        "base_url": client.base_url,
    }


@router.get("/test-connection", response_model=LinkedInConnectionTestResponse, tags=["linkedin"])
def test_linkedin_connection() -> LinkedInConnectionTestResponse:
    """
    Test connection to LinkedIn API.
    
    Attempts to connect to LinkedIn API and fetch authenticated user info.
    This endpoint verifies that the configured access token is valid and can
    successfully authenticate with LinkedIn's API.
    
    Returns:
        LinkedInConnectionTestResponse: Connection test result containing:
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
                "firstName": {"en_US": "John"},
                "lastName": {"en_US": "Doe"}
            },
            "error": null
        }
        ```
    """
    try:
        client = LinkedInApiClient()
        user_info = client.test_connection()
        return LinkedInConnectionTestResponse(
            connected=True,
            user_info=user_info,
            error=None,
        )
    except LinkedInApiError as exc:
        logger.error(f"LinkedIn connection test failed: {exc}")
        return LinkedInConnectionTestResponse(
            connected=False,
            user_info=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during LinkedIn connection test")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/me", response_model=LinkedInUserInfoResponse, tags=["linkedin"])
def get_linkedin_user_info() -> LinkedInUserInfoResponse:
    """
    Get authenticated LinkedIn user information.
    
    Fetches information about the authenticated LinkedIn user, including
    user ID, first name, last name, and profile picture.
    
    Returns:
        LinkedInUserInfoResponse: User information containing:
            - user_info (dict): User information dictionary with:
                - id (str): User ID
                - firstName (dict): First name with localized strings
                - lastName (dict): Last name with localized strings
                - profilePicture (dict): Profile picture information
        
    Raises:
        HTTPException:
            - 500 if LinkedIn API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
        
    Example:
        ```json
        {
            "user_info": {
                "id": "123456789",
                "firstName": {"en_US": "John"},
                "lastName": {"en_US": "Doe"},
                "profilePicture": {...}
            }
        }
        ```
    """
    try:
        client = LinkedInApiClient()
        user_info = client.get_me()
        return LinkedInUserInfoResponse(user_info=user_info)
    except LinkedInApiError as exc:
        logger.error(f"Failed to get LinkedIn user info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"LinkedIn API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error getting LinkedIn user info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class CreatePostRequest(BaseModel):
    """Request model for creating a LinkedIn post."""
    text: str
    visibility: str = "PUBLIC"


class CreatePostResponse(BaseModel):
    """Response model for LinkedIn post creation."""
    id: str
    activity_id: str | None = None
    status: str


@router.post("/post", response_model=CreatePostResponse, tags=["linkedin"])
@limiter.limit("10/minute")
def create_linkedin_post(request: Request, req: CreatePostRequest) -> CreatePostResponse:
    """
    Create a post on LinkedIn.
    
    Creates a text post on LinkedIn with the specified content and visibility settings.
    
    Args:
        req: Create post request containing:
            - text (str): Post text content (required)
            - visibility (str): Post visibility (PUBLIC, CONNECTIONS) - default: PUBLIC
    
    Returns:
        CreatePostResponse: Post creation result containing:
            - id (str): Post ID
            - activity_id (str | None): Activity ID
            - status (str): Post status
    
    Raises:
        HTTPException:
            - 400 if validation fails (missing text)
            - 500 if LinkedIn API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "id": "urn:li:ugcPost:123456789",
            "activity_id": "123456789",
            "status": "published"
        }
        ```
    """
    try:
        if not req.text or not req.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Post text is required",
            )
        
        client = LinkedInApiClient()
        post_data = client.create_post(
            text=req.text,
            visibility=req.visibility,
        )
        
        return CreatePostResponse(
            id=post_data["id"],
            activity_id=post_data.get("activity_id"),
            status=post_data.get("status", "published"),
        )
    except LinkedInApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to create LinkedIn post: {exc}")
        
        if "required" in error_msg.lower() or "not configured" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"LinkedIn API error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"LinkedIn API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error creating LinkedIn post")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class CreateArticleRequest(BaseModel):
    """Request model for creating a LinkedIn article."""
    title: str
    content: str


class CreateArticleResponse(BaseModel):
    """Response model for LinkedIn article creation."""
    id: str
    status: str


@router.post("/article", response_model=CreateArticleResponse, tags=["linkedin"])
@limiter.limit("5/minute")
def create_linkedin_article(request: Request, req: CreateArticleRequest) -> CreateArticleResponse:
    """
    Create an article on LinkedIn (professional long-form content).
    
    Creates a long-form article on LinkedIn with the specified title and content.
    Articles are ideal for professional personas and thought leadership content.
    
    Args:
        req: Create article request containing:
            - title (str): Article title (required)
            - content (str): Article content - HTML or plain text (required)
    
    Returns:
        CreateArticleResponse: Article creation result containing:
            - id (str): Article ID
            - status (str): Article status
    
    Raises:
        HTTPException:
            - 400 if validation fails (missing title or content)
            - 500 if LinkedIn API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "id": "urn:li:ugcPost:123456789",
            "status": "published"
        }
        ```
    """
    try:
        if not req.title or not req.title.strip():
            raise HTTPException(
                status_code=400,
                detail="Article title is required",
            )
        
        if not req.content or not req.content.strip():
            raise HTTPException(
                status_code=400,
                detail="Article content is required",
            )
        
        client = LinkedInApiClient()
        article_data = client.create_article(
            title=req.title,
            content=req.content,
        )
        
        return CreateArticleResponse(
            id=article_data["id"],
            status=article_data.get("status", "published"),
        )
    except LinkedInApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to create LinkedIn article: {exc}")
        
        if "required" in error_msg.lower() or "not configured" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"LinkedIn API error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"LinkedIn API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error creating LinkedIn article")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

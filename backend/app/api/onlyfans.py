"""OnlyFans browser automation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.onlyfans_client import OnlyFansApiError, OnlyFansBrowserClient

logger = get_logger(__name__)

router = APIRouter()


class OnlyFansConnectionTestResponse(BaseModel):
    """Response model for OnlyFans connection test."""
    connected: bool
    url: str | None = None
    title: str | None = None
    error: str | None = None


class OnlyFansLoginRequest(BaseModel):
    """Request model for OnlyFans login."""
    username: str | None = None
    password: str | None = None


class OnlyFansLoginResponse(BaseModel):
    """Response model for OnlyFans login."""
    success: bool
    url: str
    error: str | None = None


class OnlyFansNavigateRequest(BaseModel):
    """Request model for navigating to a URL."""
    url: str


class OnlyFansNavigateResponse(BaseModel):
    """Response model for navigation."""
    success: bool
    url: str
    title: str


class OnlyFansPageInfoResponse(BaseModel):
    """Response model for page information."""
    url: str
    title: str
    content_length: int


class OnlyFansUploadContentRequest(BaseModel):
    """Request model for uploading content to OnlyFans."""
    file_path: str
    caption: str = ""
    price: float | None = None
    is_free: bool = False


class OnlyFansUploadContentResponse(BaseModel):
    """Response model for content upload."""
    success: bool
    content_id: str | None = None
    content_url: str | None = None
    error: str | None = None


class OnlyFansSendMessageRequest(BaseModel):
    """Request model for sending a message on OnlyFans."""
    recipient_username: str
    message: str


class OnlyFansSendMessageResponse(BaseModel):
    """Response model for sending a message."""
    success: bool
    message_id: str | None = None
    error: str | None = None


@router.get("/status", response_model=dict)
async def get_status() -> dict:
    """Get OnlyFans browser automation service status.
    
    Returns:
        Service status information.
    """
    return {
        "service": "onlyfans",
        "status": "available",
        "method": "browser_automation",
        "tool": "playwright",
    }


@router.post("/test-connection", response_model=OnlyFansConnectionTestResponse)
async def test_connection() -> OnlyFansConnectionTestResponse:
    """Test connection to OnlyFans using browser automation.
    
    Returns:
        Connection test result.
        
    Raises:
        HTTPException: If connection test fails.
    """
    try:
        async with OnlyFansBrowserClient() as client:
            result = await client.test_connection()
            return OnlyFansConnectionTestResponse(**result)
    except OnlyFansApiError as exc:
        logger.error(f"OnlyFans connection test failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during connection test: {exc}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {exc}") from exc


@router.post("/login", response_model=OnlyFansLoginResponse)
async def login(request: OnlyFansLoginRequest) -> OnlyFansLoginResponse:
    """Login to OnlyFans account using browser automation.
    
    Args:
        request: Login request with optional username and password.
        
    Returns:
        Login result.
        
    Raises:
        HTTPException: If login fails.
    """
    try:
        async with OnlyFansBrowserClient() as client:
            result = await client.login(
                username=request.username,
                password=request.password,
            )
            return OnlyFansLoginResponse(**result)
    except OnlyFansApiError as exc:
        logger.error(f"OnlyFans login failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during login: {exc}")
        raise HTTPException(status_code=500, detail=f"Login failed: {exc}") from exc


@router.post("/navigate", response_model=OnlyFansNavigateResponse)
async def navigate(request: OnlyFansNavigateRequest) -> OnlyFansNavigateResponse:
    """Navigate to a URL in the browser.
    
    Args:
        request: Navigation request with URL.
        
    Returns:
        Navigation result.
        
    Raises:
        HTTPException: If navigation fails.
    """
    try:
        async with OnlyFansBrowserClient() as client:
            result = await client.navigate(request.url)
            return OnlyFansNavigateResponse(**result)
    except OnlyFansApiError as exc:
        logger.error(f"OnlyFans navigation failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during navigation: {exc}")
        raise HTTPException(status_code=500, detail=f"Navigation failed: {exc}") from exc


@router.get("/page-info", response_model=OnlyFansPageInfoResponse)
async def get_page_info() -> OnlyFansPageInfoResponse:
    """Get current page information.
    
    Returns:
        Current page information.
        
    Raises:
        HTTPException: If page info retrieval fails.
    """
    try:
        async with OnlyFansBrowserClient() as client:
            result = await client.get_page_info()
            return OnlyFansPageInfoResponse(**result)
    except OnlyFansApiError as exc:
        logger.error(f"OnlyFans page info retrieval failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during page info retrieval: {exc}")
        raise HTTPException(status_code=500, detail=f"Page info retrieval failed: {exc}") from exc


@router.post("/upload-content", response_model=OnlyFansUploadContentResponse)
async def upload_content(request: OnlyFansUploadContentRequest) -> OnlyFansUploadContentResponse:
    """Upload content (image or video) to OnlyFans.
    
    Args:
        request: Upload request containing:
            - file_path (str): Path to the image or video file
            - caption (str): Optional caption/description
            - price (float | None): Price for paid content (required if is_free is False)
            - is_free (bool): Whether content should be free (default: False)
        
    Returns:
        Upload result containing:
            - success (bool): Whether upload was successful
            - content_id (str | None): OnlyFans content ID if successful
            - content_url (str | None): URL to uploaded content
            - error (str | None): Error message if upload failed
        
    Raises:
        HTTPException: If upload fails.
    """
    try:
        async with OnlyFansBrowserClient() as client:
            # Ensure logged in before uploading
            login_result = await client.login()
            if not login_result.get("success"):
                raise HTTPException(
                    status_code=401,
                    detail="Must be logged in to upload content. Please login first."
                )
            
            result = await client.upload_content(
                file_path=request.file_path,
                caption=request.caption,
                price=request.price,
                is_free=request.is_free,
            )
            return OnlyFansUploadContentResponse(**result)
    except OnlyFansApiError as exc:
        logger.error(f"OnlyFans content upload failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during content upload: {exc}")
        raise HTTPException(status_code=500, detail=f"Content upload failed: {exc}") from exc


@router.post("/send-message", response_model=OnlyFansSendMessageResponse)
async def send_message(request: OnlyFansSendMessageRequest) -> OnlyFansSendMessageResponse:
    """Send a message to a recipient on OnlyFans.
    
    Args:
        request: Send message request containing:
            - recipient_username (str): Username of the recipient to send message to
            - message (str): Message text to send
        
    Returns:
        Send message result containing:
            - success (bool): Whether message was sent successfully
            - message_id (str | None): Message ID if available
            - error (str | None): Error message if sending failed
        
    Raises:
        HTTPException: If message sending fails.
    """
    try:
        async with OnlyFansBrowserClient() as client:
            # Ensure logged in before sending messages
            login_result = await client.login()
            if not login_result.get("success"):
                raise HTTPException(
                    status_code=401,
                    detail="Must be logged in to send messages. Please login first."
                )
            
            result = await client.send_message(
                recipient_username=request.recipient_username,
                message=request.message,
            )
            return OnlyFansSendMessageResponse(**result)
    except OnlyFansApiError as exc:
        logger.error(f"OnlyFans message sending failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during message sending: {exc}")
        raise HTTPException(status_code=500, detail=f"Message sending failed: {exc}") from exc


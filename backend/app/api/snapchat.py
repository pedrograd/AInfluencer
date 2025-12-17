"""Snapchat browser automation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.snapchat_client import SnapchatApiError, SnapchatBrowserClient

logger = get_logger(__name__)

router = APIRouter()


class SnapchatConnectionTestResponse(BaseModel):
    """Response model for Snapchat connection test."""
    connected: bool
    url: str | None = None
    title: str | None = None
    error: str | None = None


class SnapchatLoginRequest(BaseModel):
    """Request model for Snapchat login."""
    username: str | None = None
    password: str | None = None


class SnapchatLoginResponse(BaseModel):
    """Response model for Snapchat login."""
    success: bool
    url: str
    error: str | None = None


class SnapchatNavigateRequest(BaseModel):
    """Request model for navigating to a URL."""
    url: str


class SnapchatNavigateResponse(BaseModel):
    """Response model for navigation."""
    success: bool
    url: str
    title: str


class SnapchatPageInfoResponse(BaseModel):
    """Response model for page information."""
    url: str
    title: str
    content_length: int


class SnapchatUploadSnapRequest(BaseModel):
    """Request model for uploading a snap to Snapchat."""
    file_path: str
    caption: str = ""
    duration: int = 10


class SnapchatUploadSnapResponse(BaseModel):
    """Response model for snap upload."""
    success: bool
    snap_id: str | None = None
    error: str | None = None


class SnapchatPostStoryRequest(BaseModel):
    """Request model for posting a story to Snapchat."""
    file_path: str
    caption: str = ""


class SnapchatPostStoryResponse(BaseModel):
    """Response model for story post."""
    success: bool
    story_id: str | None = None
    error: str | None = None


@router.get("/status", response_model=dict)
async def get_status() -> dict:
    """Get Snapchat browser automation service status.
    
    Returns:
        Service status information.
    """
    return {
        "service": "snapchat",
        "status": "available",
        "method": "browser_automation",
        "tool": "playwright",
    }


@router.post("/test-connection", response_model=SnapchatConnectionTestResponse)
async def test_connection() -> SnapchatConnectionTestResponse:
    """
    Test browser automation connection to Snapchat Web.
    
    Returns:
        Connection test result.
    """
    client = SnapchatBrowserClient()
    try:
        result = await client.test_connection()
        await client.close()
        return SnapchatConnectionTestResponse(**result)
    except Exception as exc:
        await client.close()
        logger.error(f"Snapchat connection test failed: {exc}")
        return SnapchatConnectionTestResponse(
            connected=False,
            url=None,
            title=None,
            error=str(exc),
        )


@router.post("/login", response_model=SnapchatLoginResponse)
async def login(request: SnapchatLoginRequest) -> SnapchatLoginResponse:
    """
    Login to Snapchat Web.
    
    Args:
        request: Login request with username and password.
    
    Returns:
        Login result.
    """
    client = SnapchatBrowserClient()
    try:
        result = await client.login(
            username=request.username,
            password=request.password,
        )
        # Keep client open for subsequent operations
        return SnapchatLoginResponse(**result)
    except SnapchatApiError as exc:
        await client.close()
        logger.error(f"Snapchat login failed: {exc}")
        return SnapchatLoginResponse(
            success=False,
            url="",
            error=str(exc),
        )
    except Exception as exc:
        await client.close()
        logger.exception("Unexpected error during Snapchat login")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/navigate", response_model=SnapchatNavigateResponse)
async def navigate(request: SnapchatNavigateRequest) -> SnapchatNavigateResponse:
    """
    Navigate to a specific URL.
    
    Args:
        request: Navigation request with URL.
    
    Returns:
        Navigation result.
    """
    client = SnapchatBrowserClient()
    try:
        result = await client.navigate(request.url)
        return SnapchatNavigateResponse(**result)
    except SnapchatApiError as exc:
        await client.close()
        logger.error(f"Snapchat navigation failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Navigation failed: {exc}",
        ) from exc
    except Exception as exc:
        await client.close()
        logger.exception("Unexpected error during Snapchat navigation")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/page-info", response_model=SnapchatPageInfoResponse)
async def get_page_info() -> SnapchatPageInfoResponse:
    """
    Get current page information.
    
    Returns:
        Page information.
    """
    client = SnapchatBrowserClient()
    try:
        result = await client.get_page_info()
        return SnapchatPageInfoResponse(**result)
    except SnapchatApiError as exc:
        await client.close()
        logger.error(f"Failed to get Snapchat page info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get page info: {exc}",
        ) from exc
    except Exception as exc:
        await client.close()
        logger.exception("Unexpected error getting Snapchat page info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/upload-snap", response_model=SnapchatUploadSnapResponse)
async def upload_snap(request: SnapchatUploadSnapRequest) -> SnapchatUploadSnapResponse:
    """
    Upload a snap (image/video) to Snapchat.
    
    Args:
        request: Upload request with file path, caption, and duration.
    
    Returns:
        Upload result.
    """
    client = SnapchatBrowserClient()
    try:
        result = await client.upload_snap(
            file_path=request.file_path,
            caption=request.caption,
            duration=request.duration,
        )
        return SnapchatUploadSnapResponse(**result)
    except SnapchatApiError as exc:
        await client.close()
        logger.error(f"Snapchat snap upload failed: {exc}")
        return SnapchatUploadSnapResponse(
            success=False,
            snap_id=None,
            error=str(exc),
        )
    except Exception as exc:
        await client.close()
        logger.exception("Unexpected error during Snapchat snap upload")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.post("/post-story", response_model=SnapchatPostStoryResponse)
async def post_story(request: SnapchatPostStoryRequest) -> SnapchatPostStoryResponse:
    """
    Post a story to Snapchat.
    
    Args:
        request: Story post request with file path and caption.
    
    Returns:
        Story post result.
    """
    client = SnapchatBrowserClient()
    try:
        result = await client.post_story(
            file_path=request.file_path,
            caption=request.caption,
        )
        return SnapchatPostStoryResponse(**result)
    except SnapchatApiError as exc:
        await client.close()
        logger.error(f"Snapchat story post failed: {exc}")
        return SnapchatPostStoryResponse(
            success=False,
            story_id=None,
            error=str(exc),
        )
    except Exception as exc:
        await client.close()
        logger.exception("Unexpected error during Snapchat story post")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

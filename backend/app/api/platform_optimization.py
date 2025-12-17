"""API endpoints for platform-specific image optimization."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.platform_image_optimization_service import (
    PlatformImageOptimizationService,
    Platform,
    PlatformImageOptimizationError,
)

router = APIRouter()
logger = get_logger(__name__)


class OptimizeImageRequest(BaseModel):
    """Request model for optimizing an image for a platform."""

    image_path: str = Field(..., description="Path to the image file (relative to images directory or absolute)")
    platform: str = Field(..., description="Target platform: instagram, twitter, facebook, telegram, youtube, tiktok, generic")
    maintain_aspect_ratio: bool = Field(default=True, description="Whether to maintain aspect ratio when resizing")


class OptimizeImageResponse(BaseModel):
    """Response model for image optimization."""

    success: bool
    optimized_path: str | None = None
    width: int | None = None
    height: int | None = None
    file_size_kb: float | None = None
    platform: str | None = None
    error: str | None = None


@router.post("/optimize-image", response_model=OptimizeImageResponse, tags=["platform-optimization"])
def optimize_image(request: Request, req: OptimizeImageRequest) -> OptimizeImageResponse:
    """
    Optimize an image for a specific platform.
    
    This endpoint automatically resizes, compresses, and converts images
    to meet platform-specific requirements for optimal quality and compliance.
    
    Supported platforms:
    - instagram: 1080x1080 (square), up to 1080x1350, max 8MB
    - twitter: 1200x675 (landscape), max 5MB
    - facebook: 1200x630 (landscape), max 4MB
    - telegram: 1280x1280 (flexible), max 10MB
    - youtube: 1280x720 (16:9), max 2MB
    - tiktok: 1080x1920 (vertical), max 10MB
    - generic: 1920x1080 (flexible), max 10MB
    
    Args:
        request: FastAPI request object
        req: Optimization request with image_path and platform
    
    Returns:
        OptimizeImageResponse with optimization results
    
    Raises:
        HTTPException: If optimization fails
    """
    try:
        optimizer = PlatformImageOptimizationService()
        
        # Optimize image
        optimized_path = optimizer.optimize_for_platform(
            image_path=req.image_path,
            platform=req.platform,
            maintain_aspect_ratio=req.maintain_aspect_ratio,
        )
        
        # Get image dimensions and file size
        try:
            from PIL import Image
            img = Image.open(optimized_path)
            width, height = img.size
            file_size_kb = optimized_path.stat().st_size / 1024
        except Exception:
            width = None
            height = None
            file_size_kb = None
        
        return OptimizeImageResponse(
            success=True,
            optimized_path=str(optimized_path),
            width=width,
            height=height,
            file_size_kb=file_size_kb,
            platform=req.platform,
            error=None,
        )
        
    except PlatformImageOptimizationError as exc:
        logger.error(f"Image optimization failed: {exc}")
        return OptimizeImageResponse(
            success=False,
            optimized_path=None,
            width=None,
            height=None,
            file_size_kb=None,
            platform=req.platform,
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error during image optimization: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image optimization failed: {str(exc)}")


@router.get("/platform-specs/{platform}", tags=["platform-optimization"])
def get_platform_specs(platform: str) -> dict:
    """
    Get platform-specific optimization specifications.
    
    Args:
        platform: Platform name (instagram, twitter, facebook, telegram, youtube, tiktok, generic)
    
    Returns:
        Dictionary with platform specifications including dimensions, formats, and limits
    """
    try:
        optimizer = PlatformImageOptimizationService()
        specs = optimizer.get_platform_specs(platform)
        return {
            "platform": platform,
            "specs": specs,
        }
    except Exception as exc:
        logger.error(f"Failed to get platform specs: {exc}")
        raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")

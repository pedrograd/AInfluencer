"""API endpoints for AI-powered photo editing."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.image_postprocess_service import ImagePostProcessService
from app.services.style_transfer_service import StyleTransferService

router = APIRouter()
logger = get_logger(__name__)


class PhotoEditRequest(BaseModel):
    """Request model for photo editing."""

    image_path: str = Field(..., description="Path to the image file (relative to images directory or absolute)")
    sharpen: bool = Field(default=False, description="Whether to apply sharpening")
    denoise: bool = Field(default=False, description="Whether to apply denoising")
    color_correct: bool = Field(default=False, description="Whether to apply color correction")
    brightness: float | None = Field(default=None, description="Brightness adjustment (-1.0 to 1.0, None = no change)")
    contrast: float | None = Field(default=None, description="Contrast adjustment (-1.0 to 1.0, None = no change)")
    auto_enhance: bool = Field(default=False, description="Whether to apply AI-powered auto-enhancement")
    skin_smoothing: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Skin smoothing strength (0.0 to 1.0, None = disabled)",
    )
    color_grading: str | None = Field(
        default=None,
        description='Color grading style: "natural", "warm", "cool", "vibrant", "cinematic" (None = disabled)',
    )


class PhotoEditResponse(BaseModel):
    """Response model for photo editing."""

    success: bool
    processed_image_path: str | None = None
    applied_operations: list[str] | None = None
    original_path: str | None = None
    error: str | None = None


@router.post("/edit", response_model=PhotoEditResponse, tags=["photo-editing"])
def edit_photo(request: Request, req: PhotoEditRequest) -> PhotoEditResponse:
    """
    Apply AI-powered photo editing to an image.
    
    This endpoint provides comprehensive photo editing capabilities including:
    - Basic adjustments: sharpening, denoising, color correction, brightness, contrast
    - AI-powered auto-enhancement: intelligent analysis-based improvements
    - Portrait enhancement: skin smoothing for natural-looking results
    - Color grading: multiple style presets (warm, cool, vibrant, cinematic)
    
    Args:
        request: FastAPI request object
        req: Photo editing request with image_path and editing options
    
    Returns:
        PhotoEditResponse with editing results
    
    Raises:
        HTTPException: If editing fails
    """
    try:
        # Validate color_grading if provided
        if req.color_grading is not None:
            valid_styles = ["natural", "warm", "cool", "vibrant", "cinematic"]
            if req.color_grading.lower() not in valid_styles:
                return PhotoEditResponse(
                    success=False,
                    error=f"Invalid color_grading style '{req.color_grading}'. Must be one of: {', '.join(valid_styles)}",
                )
        
        # Initialize service
        service = ImagePostProcessService()
        
        # Process image
        result = service.process_image(
            image_path=req.image_path,
            sharpen=req.sharpen,
            denoise=req.denoise,
            color_correct=req.color_correct,
            brightness=req.brightness,
            contrast=req.contrast,
            auto_enhance=req.auto_enhance,
            skin_smoothing=req.skin_smoothing,
            color_grading=req.color_grading.lower() if req.color_grading else None,
        )
        
        if not result.get("ok", False):
            return PhotoEditResponse(
                success=False,
                error=result.get("error", "Photo editing failed"),
            )
        
        return PhotoEditResponse(
            success=True,
            processed_image_path=result.get("processed_image_path"),
            applied_operations=result.get("applied_operations", []),
            original_path=result.get("original_path"),
            error=None,
        )
        
    except FileNotFoundError as exc:
        logger.error(f"Image not found: {exc}")
        return PhotoEditResponse(
            success=False,
            error=f"Image not found: {str(exc)}",
        )
    except ImportError as exc:
        logger.error(f"Missing dependency: {exc}")
        return PhotoEditResponse(
            success=False,
            error=f"Missing required dependency: {str(exc)}",
        )
    except Exception as exc:
        logger.error(f"Photo editing failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Photo editing failed: {str(exc)}")


@router.get("/status", tags=["photo-editing"])
def get_photo_editing_status() -> dict:
    """
    Get photo editing service status.
    
    Returns:
        dict: Service status information
    """
    return {
        "ok": True,
        "service": "photo-editing",
        "status": "available",
        "features": [
            "sharpening",
            "denoising",
            "color_correction",
            "brightness_contrast",
            "auto_enhancement",
            "skin_smoothing",
            "color_grading",
            "style_transfer",
        ],
        "color_grading_styles": ["natural", "warm", "cool", "vibrant", "cinematic"],
    }


class StyleTransferRequest(BaseModel):
    """Request model for style transfer."""

    content_image_path: str = Field(..., description="Path to the content image (relative to images directory or absolute)")
    style_image_path: str = Field(..., description="Path to the style reference image (relative to images directory or absolute)")
    strength: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Style transfer strength (0.0 to 1.0, default: 0.5)",
    )
    use_comfyui: bool = Field(
        default=True,
        description="Whether to use ComfyUI for neural style transfer (falls back to basic method if unavailable)",
    )


class StyleTransferResponse(BaseModel):
    """Response model for style transfer."""

    success: bool
    stylized_image_path: str | None = None
    content_image_path: str | None = None
    style_image_path: str | None = None
    strength: float | None = None
    method: str | None = None
    error: str | None = None


@router.post("/style-transfer", response_model=StyleTransferResponse, tags=["photo-editing"])
def transfer_style(request: Request, req: StyleTransferRequest) -> StyleTransferResponse:
    """
    Apply neural style transfer to an image.
    
    This endpoint applies the artistic style of a style reference image to a content image.
    Supports both ComfyUI-based neural style transfer (if available) and basic fallback
    image processing techniques.
    
    Args:
        request: FastAPI request object
        req: Style transfer request with content_image_path, style_image_path, strength, and use_comfyui flag
    
    Returns:
        StyleTransferResponse with stylized image path and metadata
    
    Raises:
        HTTPException: If style transfer fails
    """
    try:
        # Initialize service
        service = StyleTransferService()
        
        # Apply style transfer
        result = service.transfer_style(
            content_image_path=req.content_image_path,
            style_image_path=req.style_image_path,
            strength=req.strength,
            use_comfyui=req.use_comfyui,
        )
        
        if not result.get("ok", False):
            return StyleTransferResponse(
                success=False,
                error=result.get("error", "Style transfer failed"),
            )
        
        return StyleTransferResponse(
            success=True,
            stylized_image_path=result.get("stylized_image_path"),
            content_image_path=result.get("content_image_path"),
            style_image_path=result.get("style_image_path"),
            strength=result.get("strength"),
            method=result.get("method"),
            error=None,
        )
        
    except FileNotFoundError as exc:
        logger.error(f"Image not found: {exc}")
        return StyleTransferResponse(
            success=False,
            error=f"Image not found: {str(exc)}",
        )
    except ValueError as exc:
        logger.error(f"Invalid parameter: {exc}")
        return StyleTransferResponse(
            success=False,
            error=f"Invalid parameter: {str(exc)}",
        )
    except Exception as exc:
        logger.error(f"Style transfer failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Style transfer failed: {str(exc)}")

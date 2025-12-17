"""API endpoints for AI-powered photo editing."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.ar_filter_service import ARFilterService
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
            "background_replacement",
            "ar_filters",
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


class BackgroundReplacementRequest(BaseModel):
    """Request model for background replacement."""

    image_path: str = Field(..., description="Path to the source image (relative to images directory or absolute)")
    background_path: str | None = Field(
        default=None,
        description="Path to the background image (optional, if None uses background_color)",
    )
    background_color: tuple[int, int, int] | None = Field(
        default=None,
        description="RGB tuple for solid color background (default: white (255, 255, 255))",
    )
    method: str = Field(
        default="auto",
        description='Detection method: "auto" (default), "edges", "color"',
    )


class BackgroundReplacementResponse(BaseModel):
    """Response model for background replacement."""

    success: bool
    processed_image_path: str | None = None
    original_path: str | None = None
    background_type: str | None = None
    method: str | None = None
    error: str | None = None


@router.post("/background-replace", response_model=BackgroundReplacementResponse, tags=["photo-editing"])
def replace_background(request: Request, req: BackgroundReplacementRequest) -> BackgroundReplacementResponse:
    """
    Replace the background of an image with a new background.
    
    This endpoint supports:
    - Solid color backgrounds (background_color)
    - Image backgrounds (background_path)
    - Automatic foreground detection using edge detection and color analysis
    
    Args:
        request: FastAPI request object
        req: Background replacement request with image_path, background options, and method
    
    Returns:
        BackgroundReplacementResponse with processed image path and metadata
    
    Raises:
        HTTPException: If background replacement fails
    """
    try:
        # Validate method if provided
        if req.method is not None:
            valid_methods = ["auto", "edges", "color"]
            if req.method.lower() not in valid_methods:
                return BackgroundReplacementResponse(
                    success=False,
                    error=f"Invalid method '{req.method}'. Must be one of: {', '.join(valid_methods)}",
                )
        
        # Validate that either background_path or background_color is provided (or use default white)
        # This is handled in the service, so we can proceed
        
        # Initialize service
        service = ImagePostProcessService()
        
        # Replace background
        result = service.replace_background(
            image_path=req.image_path,
            background_path=req.background_path,
            background_color=req.background_color,
            method=req.method.lower() if req.method else "auto",
        )
        
        if not result.get("ok", False):
            return BackgroundReplacementResponse(
                success=False,
                error=result.get("error", "Background replacement failed"),
            )
        
        return BackgroundReplacementResponse(
            success=True,
            processed_image_path=result.get("processed_image_path"),
            original_path=result.get("original_path"),
            background_type=result.get("background_type"),
            method=result.get("method"),
            error=None,
        )
        
    except FileNotFoundError as exc:
        logger.error(f"Image not found: {exc}")
        return BackgroundReplacementResponse(
            success=False,
            error=f"Image not found: {str(exc)}",
        )
    except ImportError as exc:
        logger.error(f"Missing dependency: {exc}")
        return BackgroundReplacementResponse(
            success=False,
            error=f"Missing required dependency: {str(exc)}",
        )
    except Exception as exc:
        logger.error(f"Background replacement failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Background replacement failed: {str(exc)}")


class ARFilterRequest(BaseModel):
    """Request model for AR filter application."""

    image_path: str = Field(..., description="Path to the image file (relative to images directory or absolute)")
    filter_type: str = Field(
        default="color",
        description='Filter type: "color", "overlay", or "both"',
    )
    filter_name: str = Field(
        default="vintage",
        description='Color filter name: "sepia", "vintage", "black_white", "warm", "cool", "vibrant"',
    )
    intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Filter intensity (0.0 to 1.0, default: 0.5)",
    )
    overlay_type: str | None = Field(
        default=None,
        description='Overlay type: "glasses", "hat", "mustache", "custom" (None = no overlay)',
    )
    overlay_path: str | None = Field(
        default=None,
        description="Path to custom overlay image (required if overlay_type is 'custom')",
    )
    detect_faces: bool = Field(
        default=True,
        description="Whether to detect faces for overlay placement (default: True)",
    )


class ARFilterResponse(BaseModel):
    """Response model for AR filter application."""

    success: bool
    filtered_image_path: str | None = None
    faces_detected: int | None = None
    face_regions: list[dict[str, int]] | None = None
    applied_filters: list[str] | None = None
    original_path: str | None = None
    error: str | None = None


@router.post("/ar-filter", response_model=ARFilterResponse, tags=["photo-editing"])
def apply_ar_filter(request: Request, req: ARFilterRequest) -> ARFilterResponse:
    """
    Apply AR (Augmented Reality) filters to an image.
    
    This endpoint provides AR filter capabilities including:
    - Color filters: sepia, vintage, black & white, warm, cool, vibrant
    - Face detection: automatic face detection for overlay placement
    - Overlay effects: glasses, hats, mustaches, or custom overlays
    - Custom overlays: support for custom overlay images
    
    Args:
        request: FastAPI request object
        req: AR filter request with image_path, filter options, and overlay settings
    
    Returns:
        ARFilterResponse with filtered image path, face detection results, and applied filters
    
    Raises:
        HTTPException: If AR filter application fails
    """
    try:
        # Validate filter_type
        valid_filter_types = ["color", "overlay", "both"]
        if req.filter_type not in valid_filter_types:
            return ARFilterResponse(
                success=False,
                error=f"Invalid filter_type '{req.filter_type}'. Must be one of: {', '.join(valid_filter_types)}",
            )
        
        # Validate filter_name if color filter is requested
        if req.filter_type in ("color", "both"):
            valid_filter_names = ["sepia", "vintage", "black_white", "warm", "cool", "vibrant"]
            if req.filter_name not in valid_filter_names:
                return ARFilterResponse(
                    success=False,
                    error=f"Invalid filter_name '{req.filter_name}'. Must be one of: {', '.join(valid_filter_names)}",
                )
        
        # Validate overlay_type if overlay is requested
        if req.filter_type in ("overlay", "both"):
            if req.overlay_type is None:
                return ARFilterResponse(
                    success=False,
                    error="overlay_type is required when filter_type is 'overlay' or 'both'",
                )
            
            valid_overlay_types = ["glasses", "hat", "mustache", "custom"]
            if req.overlay_type not in valid_overlay_types:
                return ARFilterResponse(
                    success=False,
                    error=f"Invalid overlay_type '{req.overlay_type}'. Must be one of: {', '.join(valid_overlay_types)}",
                )
            
            # Validate overlay_path for custom overlays
            if req.overlay_type == "custom" and not req.overlay_path:
                return ARFilterResponse(
                    success=False,
                    error="overlay_path is required when overlay_type is 'custom'",
                )
        
        # Initialize service
        service = ARFilterService()
        
        # Apply AR filter
        result = service.apply_filter(
            image_path=req.image_path,
            filter_type=req.filter_type,
            filter_name=req.filter_name,
            intensity=req.intensity,
            overlay_type=req.overlay_type,
            overlay_path=req.overlay_path,
            detect_faces=req.detect_faces,
        )
        
        if not result.get("ok", False):
            return ARFilterResponse(
                success=False,
                error=result.get("error", "AR filter application failed"),
            )
        
        return ARFilterResponse(
            success=True,
            filtered_image_path=result.get("filtered_image_path"),
            faces_detected=result.get("faces_detected", 0),
            face_regions=result.get("face_regions", []),
            applied_filters=result.get("applied_filters", []),
            original_path=result.get("original_path"),
            error=None,
        )
        
    except FileNotFoundError as exc:
        logger.error(f"Image not found: {exc}")
        return ARFilterResponse(
            success=False,
            error=f"Image not found: {str(exc)}",
        )
    except ImportError as exc:
        logger.error(f"Missing dependency: {exc}")
        return ARFilterResponse(
            success=False,
            error=f"Missing required dependency: {str(exc)}",
        )
    except Exception as exc:
        logger.error(f"AR filter application failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AR filter application failed: {str(exc)}")

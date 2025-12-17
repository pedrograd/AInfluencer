"""White-label configuration API endpoints for branding customization.

This module provides API endpoints for managing white-label configuration including:
- Getting current white-label settings
- Updating white-label settings (app name, logo, colors, etc.)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.white_label import WhiteLabelConfig

router = APIRouter()

# Singleton ID for white-label config
SINGLETON_ID = "00000000-0000-0000-0000-000000000001"


class WhiteLabelConfigResponse(BaseModel):
    """Response model for white-label configuration."""

    app_name: str
    app_description: str | None
    logo_url: str | None
    favicon_url: str | None
    primary_color: str
    secondary_color: str
    is_active: bool

    class Config:
        from_attributes = True


class WhiteLabelConfigUpdateRequest(BaseModel):
    """Request model for updating white-label configuration."""

    app_name: str | None = None
    app_description: str | None = None
    logo_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    is_active: bool | None = None

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """Validate hex color format."""
        if v is None:
            return v
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be in hex format (e.g., #6366f1)")
        try:
            int(v[1:], 16)  # Validate hex digits
        except ValueError as exc:
            raise ValueError("Color must be a valid hex color code") from exc
        return v.lower()

    @field_validator("logo_url", "favicon_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate URL format (basic check)."""
        if v is None or v == "":
            return None
        if len(v) > 500:
            raise ValueError("URL must be 500 characters or less")
        return v


@router.get("", response_model=WhiteLabelConfigResponse)
async def get_white_label_config(db: AsyncSession = Depends(get_db)) -> WhiteLabelConfigResponse:
    """
    Get current white-label configuration.
    
    Returns the current white-label branding settings including app name,
    logo, colors, etc. If no config exists, returns default values.
    
    Returns:
        WhiteLabelConfigResponse: Current white-label configuration
    """
    result = await db.execute(
        select(WhiteLabelConfig).where(WhiteLabelConfig.id == SINGLETON_ID)
    )
    config = result.scalar_one_or_none()
    
    if config is None:
        # Return default config if none exists
        return WhiteLabelConfigResponse(
            app_name="AInfluencer",
            app_description=None,
            logo_url=None,
            favicon_url=None,
            primary_color="#6366f1",
            secondary_color="#8b5cf6",
            is_active=True,
        )
    
    return WhiteLabelConfigResponse.model_validate(config)


@router.put("", response_model=WhiteLabelConfigResponse)
async def update_white_label_config(
    req: WhiteLabelConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> WhiteLabelConfigResponse:
    """
    Update white-label configuration.
    
    Updates the white-label branding settings. Only provided fields are updated.
    Creates a new config if none exists.
    
    Args:
        req: White-label configuration update request
        
    Returns:
        WhiteLabelConfigResponse: Updated white-label configuration
        
    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Get or create config
        result = await db.execute(
            select(WhiteLabelConfig).where(WhiteLabelConfig.id == SINGLETON_ID)
        )
        config = result.scalar_one_or_none()
        
        if config is None:
            # Create new config with defaults
            config = WhiteLabelConfig(
                id=SINGLETON_ID,
                app_name="AInfluencer",
                primary_color="#6366f1",
                secondary_color="#8b5cf6",
                is_active=True,
            )
            db.add(config)
        
        # Update fields if provided
        if req.app_name is not None:
            config.app_name = req.app_name
        if req.app_description is not None:
            config.app_description = req.app_description if req.app_description != "" else None
        if req.logo_url is not None:
            config.logo_url = req.logo_url
        if req.favicon_url is not None:
            config.favicon_url = req.favicon_url
        if req.primary_color is not None:
            config.primary_color = req.primary_color
        if req.secondary_color is not None:
            config.secondary_color = req.secondary_color
        if req.is_active is not None:
            config.is_active = req.is_active
        
        await db.commit()
        await db.refresh(config)
        
        return WhiteLabelConfigResponse.model_validate(config)
        
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update white-label config: {str(exc)}") from exc

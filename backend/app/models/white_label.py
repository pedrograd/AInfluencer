"""White-label configuration database model for branding customization."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import Base


class WhiteLabelConfig(Base):
    """White-label configuration model for customizing app branding.
    
    This is a singleton model - there should only be one row in the table.
    Stores branding configuration like app name, logo, colors, etc.
    
    Attributes:
        id: Unique identifier (UUID) for the config (always use a fixed UUID for singleton).
        app_name: Application name displayed in UI (default: "AInfluencer").
        app_description: Application description/tagline (optional).
        logo_url: URL to logo image file (optional).
        favicon_url: URL to favicon file (optional).
        primary_color: Primary brand color in hex format (e.g., "#6366f1", default: "#6366f1").
        secondary_color: Secondary brand color in hex format (e.g., "#8b5cf6", default: "#8b5cf6").
        is_active: Whether white-label customization is enabled (default: True).
        created_at: Timestamp when config was created.
        updated_at: Timestamp when config was last updated.
    """

    __tablename__ = "white_label_config"

    id = Column(String(36), primary_key=True, default=lambda: "00000000-0000-0000-0000-000000000001")
    app_name = Column(String(255), nullable=False, default="AInfluencer")
    app_description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=False, default="#6366f1")  # Hex color
    secondary_color = Column(String(7), nullable=False, default="#8b5cf6")  # Hex color
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<WhiteLabelConfig(id={self.id}, app_name={self.app_name}, is_active={self.is_active})>"

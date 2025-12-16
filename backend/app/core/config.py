"""Application configuration settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.
    
    All settings use the AINFLUENCER_ prefix when set as environment variables.
    Settings can be overridden via environment variables or .env file.
    """

    model_config = SettingsConfigDict(env_prefix="AINFLUENCER_", env_file=".env", extra="ignore")

    app_env: str = "dev"
    """Application environment (dev, staging, production)."""
    
    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
    
    comfyui_base_url: str = "http://localhost:8188"
    """Base URL for ComfyUI API endpoint."""
    
    default_checkpoint: str | None = None
    """Default Stable Diffusion checkpoint model name to use when none is specified.
    
    If None, ComfyUI will use its default checkpoint. Users can override this
    per-generation via the checkpoint parameter in the generation API.
    """
    
    database_url: str = "postgresql+asyncpg://ainfluencer_user:password@localhost:5432/ainfluencer"
    """PostgreSQL database connection URL (asyncpg driver)."""
    
    redis_url: str = "redis://localhost:6379/0"
    """Redis connection URL."""
    
    instagram_access_token: str | None = None
    """Instagram Graph API access token for authenticated requests."""
    
    instagram_app_id: str | None = None
    """Instagram App ID (for OAuth and API configuration)."""
    
    instagram_app_secret: str | None = None
    """Instagram App Secret (for OAuth token exchange)."""
    
    jwt_secret_key: str = "change-me-in-production-use-random-secret-key"
    """Secret key for JWT token signing and verification.
    
    In production, this should be a strong random string set via environment variable.
    Default value is insecure and should be changed.
    """
    
    jwt_algorithm: str = "HS256"
    """JWT algorithm to use for token signing (default: HS256)."""


settings = Settings()

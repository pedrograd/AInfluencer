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
    
    twitter_bearer_token: str | None = None
    """Twitter Bearer Token for OAuth 2.0 authentication (preferred for read-only operations)."""
    
    twitter_consumer_key: str | None = None
    """Twitter API Consumer Key (for OAuth 1.0a authentication)."""
    
    twitter_consumer_secret: str | None = None
    """Twitter API Consumer Secret (for OAuth 1.0a authentication)."""
    
    twitter_access_token: str | None = None
    """Twitter Access Token (for OAuth 1.0a authentication)."""
    
    twitter_access_token_secret: str | None = None
    """Twitter Access Token Secret (for OAuth 1.0a authentication)."""
    
    facebook_access_token: str | None = None
    """Facebook Graph API access token for authenticated requests."""
    
    facebook_app_id: str | None = None
    """Facebook App ID (for OAuth and API configuration)."""
    
    facebook_app_secret: str | None = None
    """Facebook App Secret (for OAuth token exchange)."""
    
    telegram_bot_token: str | None = None
    """Telegram Bot Token from @BotFather for Telegram Bot API authentication."""
    
    onlyfans_username: str | None = None
    """OnlyFans username/email for browser automation login."""
    
    onlyfans_password: str | None = None
    """OnlyFans password for browser automation login."""
    
    jwt_secret_key: str = "change-me-in-production-use-random-secret-key"
    """Secret key for JWT token signing and verification.
    
    In production, this should be a strong random string set via environment variable.
    Default value is insecure and should be changed.
    """
    
    jwt_algorithm: str = "HS256"
    """JWT algorithm to use for token signing (default: HS256)."""
    
    stripe_secret_key: str | None = None
    """Stripe secret key for payment processing.
    
    Set this to your Stripe secret key (starts with 'sk_') to enable payment processing.
    For testing, use Stripe test keys from https://dashboard.stripe.com/test/apikeys
    """
    
    stripe_publishable_key: str | None = None
    """Stripe publishable key for frontend payment integration.
    
    Set this to your Stripe publishable key (starts with 'pk_') for frontend use.
    This key is safe to expose in client-side code.
    """
    
    youtube_client_id: str | None = None
    """Google OAuth 2.0 Client ID for YouTube Data API authentication.
    
    Set this to your Google OAuth 2.0 Client ID from Google Cloud Console.
    Required for YouTube API authentication.
    """
    
    youtube_client_secret: str | None = None
    """Google OAuth 2.0 Client Secret for YouTube Data API authentication.
    
    Set this to your Google OAuth 2.0 Client Secret from Google Cloud Console.
    Required for YouTube API authentication.
    """
    
    youtube_refresh_token: str | None = None
    """OAuth 2.0 refresh token for YouTube Data API authentication.
    
    Set this to the refresh token obtained after completing OAuth 2.0 flow.
    Required for authenticated YouTube API requests.
    """
    
    linkedin_access_token: str | None = None
    """LinkedIn API access token for OAuth 2.0 authentication.
    
    Set this to your LinkedIn API access token obtained from OAuth 2.0 flow.
    Required for authenticated LinkedIn API requests.
    """
    
    linkedin_client_id: str | None = None
    """LinkedIn API Client ID for OAuth 2.0 authentication.
    
    Set this to your LinkedIn API Client ID from LinkedIn Developer Portal.
    Required for LinkedIn OAuth 2.0 authentication.
    """
    
    linkedin_client_secret: str | None = None
    """LinkedIn API Client Secret for OAuth 2.0 authentication.
    
    Set this to your LinkedIn API Client Secret from LinkedIn Developer Portal.
    Required for LinkedIn OAuth 2.0 authentication.
    """
    
    tiktok_access_token: str | None = None
    """TikTok API access token for OAuth 2.0 authentication."""
    
    tiktok_client_key: str | None = None
    """TikTok API Client Key for OAuth 2.0 authentication."""
    
    tiktok_client_secret: str | None = None
    """TikTok API Client Secret for OAuth 2.0 authentication."""
    
    discord_bot_token: str | None = None
    """Discord Bot Token from Discord Developer Portal for Bot API authentication.
    
    Set this to your Discord Bot Token obtained from the Discord Developer Portal.
    Required for authenticated Discord Bot API requests.
    """


settings = Settings()

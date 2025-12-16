"""Twitter API client for Twitter API v2 integration."""

from __future__ import annotations

from typing import Any

import tweepy

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TwitterApiError(RuntimeError):
    """Error raised when Twitter API operations fail.
    
    This exception is raised for various Twitter-related errors including
    connection failures, API errors, authentication failures, and
    other Twitter API issues.
    """
    pass


class TwitterApiClient:
    """Client for interacting with Twitter API v2."""

    def __init__(
        self,
        bearer_token: str | None = None,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
        access_token: str | None = None,
        access_token_secret: str | None = None,
    ) -> None:
        """
        Initialize Twitter API client.

        Args:
            bearer_token: Twitter Bearer Token for OAuth 2.0 (preferred for read-only).
            consumer_key: Twitter API Consumer Key (for OAuth 1.0a).
            consumer_secret: Twitter API Consumer Secret (for OAuth 1.0a).
            access_token: Twitter Access Token (for OAuth 1.0a).
            access_token_secret: Twitter Access Token Secret (for OAuth 1.0a).
        """
        self.bearer_token = bearer_token or getattr(settings, "twitter_bearer_token", None)
        self.consumer_key = consumer_key or getattr(settings, "twitter_consumer_key", None)
        self.consumer_secret = consumer_secret or getattr(settings, "twitter_consumer_secret", None)
        self.access_token = access_token or getattr(settings, "twitter_access_token", None)
        self.access_token_secret = access_token_secret or getattr(settings, "twitter_access_token_secret", None)

        # Initialize Tweepy client
        # Prefer OAuth 2.0 (Bearer Token) for read-only operations
        # Use OAuth 1.0a for write operations
        if self.bearer_token:
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                wait_on_rate_limit=True,
            )
        elif all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            self.client = tweepy.Client(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True,
            )
        else:
            self.client = None
            logger.warning("Twitter API credentials not configured")

    def _ensure_client(self) -> tweepy.Client:
        """Ensure Twitter client is initialized.
        
        Returns:
            Initialized Tweepy client.
            
        Raises:
            TwitterApiError: If client is not initialized.
        """
        if not self.client:
            raise TwitterApiError("Twitter API credentials not configured")
        return self.client

    def get_me(self) -> dict[str, Any]:
        """
        Get authenticated user information.

        Returns:
            User information dictionary containing:
                - id (str): User ID
                - username (str): Twitter username
                - name (str): Display name
                - created_at (str): Account creation date
        """
        client = self._ensure_client()
        try:
            user = client.get_me(user_fields=["id", "username", "name", "created_at"])
            return {
                "id": user.data.id,
                "username": user.data.username,
                "name": user.data.name,
                "created_at": user.data.created_at.isoformat() if user.data.created_at else None,
            }
        except tweepy.TweepyException as exc:
            raise TwitterApiError(f"Failed to get user info: {exc}") from exc

    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to Twitter API by fetching authenticated user info.

        Returns:
            User information if connection is successful.

        Raises:
            TwitterApiError: If connection fails.
        """
        try:
            return self.get_me()
        except Exception as exc:
            raise TwitterApiError(f"Twitter API connection test failed: {exc}") from exc


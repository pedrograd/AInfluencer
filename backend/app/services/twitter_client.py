"""Twitter API client for Twitter API v2 integration."""

from __future__ import annotations

from typing import Any

try:
    import tweepy  # type: ignore
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    tweepy = None  # type: ignore[assignment]
    # Create a dummy TweepyException for type hints
    class TweepyException(Exception):  # type: ignore[misc]
        pass

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

if not TWEEPY_AVAILABLE:
    logger.warning(
        "tweepy is not available. Twitter features will be disabled. "
        "Install tweepy to enable Twitter integration: pip install tweepy==4.16.0"
    )


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
        if not TWEEPY_AVAILABLE:
            self.client = None
            logger.warning(
                "tweepy is not available. Twitter features are disabled. "
                "Dependency incompatible with Python 3.11 → disabled for MVP."
            )
        elif self.bearer_token:
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

    def _ensure_client(self) -> Any:  # type: ignore
        """Ensure Twitter client is initialized.
        
        Returns:
            Initialized Tweepy client.
            
        Raises:
            TwitterApiError: If client is not initialized or tweepy is not available.
        """
        if not TWEEPY_AVAILABLE:
            raise TwitterApiError(
                "tweepy is not available. Twitter features are disabled. "
                "Dependency incompatible with Python 3.11 → disabled for MVP."
            )
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

    def _ensure_write_client(self) -> Any:  # type: ignore
        """Ensure Twitter client is initialized with OAuth 1.0a for write operations.
        
        Write operations (posting tweets) require OAuth 1.0a credentials.
        OAuth 2.0 Bearer Token is read-only.
        
        Returns:
            Initialized Tweepy client with write permissions.
            
        Raises:
            TwitterApiError: If OAuth 1.0a credentials are not configured or tweepy is not available.
        """
        if not TWEEPY_AVAILABLE:
            raise TwitterApiError(
                "tweepy is not available. Twitter features are disabled. "
                "Dependency incompatible with Python 3.11 → disabled for MVP."
            )
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            raise TwitterApiError(
                "OAuth 1.0a credentials required for write operations. "
                "Please configure consumer_key, consumer_secret, access_token, and access_token_secret."
            )
        
        # Create write client with OAuth 1.0a if not already created or if current client is read-only
        if not hasattr(self, '_write_client') or self._write_client is None:
            self._write_client = tweepy.Client(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True,
            )
        
        return self._write_client

    def post_tweet(
        self,
        text: str,
        media_ids: list[str] | None = None,
        reply_to_tweet_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Post a tweet to Twitter.

        Args:
            text: Tweet text content (required, max 280 characters).
            media_ids: Optional list of media IDs to attach to the tweet.
            reply_to_tweet_id: Optional ID of tweet to reply to.

        Returns:
            Dictionary containing:
                - id (str): Tweet ID
                - text (str): Tweet text
                - created_at (str): Tweet creation timestamp

        Raises:
            TwitterApiError: If posting fails or OAuth 1.0a credentials are not configured.
        """
        if not text or not text.strip():
            raise TwitterApiError("Tweet text is required")
        
        if len(text) > 280:
            raise TwitterApiError(f"Tweet text exceeds 280 character limit (got {len(text)} characters)")
        
        client = self._ensure_write_client()
        
        try:
            # Prepare tweet parameters
            tweet_params: dict[str, Any] = {"text": text}
            
            if media_ids:
                tweet_params["media_ids"] = [str(mid) for mid in media_ids]
            
            if reply_to_tweet_id:
                tweet_params["in_reply_to_tweet_id"] = str(reply_to_tweet_id)
            
            # Post tweet
            response = client.create_tweet(**tweet_params)
            
            if not response.data:
                raise TwitterApiError("Twitter API returned no data for posted tweet")
            
            return {
                "id": response.data["id"],
                "text": response.data["text"],
                "created_at": response.data.get("created_at", ""),
            }
        except tweepy.TweepyException as exc:
            raise TwitterApiError(f"Failed to post tweet: {exc}") from exc

    def reply_to_tweet(
        self,
        text: str,
        reply_to_tweet_id: str,
        media_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Reply to a tweet on Twitter.

        Args:
            text: Reply text content (required, max 280 characters).
            reply_to_tweet_id: ID of tweet to reply to (required).
            media_ids: Optional list of media IDs to attach to the reply.

        Returns:
            Dictionary containing:
                - id (str): Reply tweet ID
                - text (str): Reply text
                - created_at (str): Reply creation timestamp
                - in_reply_to_tweet_id (str): ID of the original tweet

        Raises:
            TwitterApiError: If replying fails or OAuth 1.0a credentials are not configured.
        """
        if not text or not text.strip():
            raise TwitterApiError("Reply text is required")
        
        if not reply_to_tweet_id or not reply_to_tweet_id.strip():
            raise TwitterApiError("reply_to_tweet_id is required for replies")
        
        if len(text) > 280:
            raise TwitterApiError(f"Reply text exceeds 280 character limit (got {len(text)} characters)")
        
        # Use post_tweet with reply_to_tweet_id
        return self.post_tweet(
            text=text,
            media_ids=media_ids,
            reply_to_tweet_id=reply_to_tweet_id,
        )

    def retweet(
        self,
        tweet_id: str,
    ) -> dict[str, Any]:
        """
        Retweet a tweet on Twitter.

        Args:
            tweet_id: ID of tweet to retweet (required).

        Returns:
            Dictionary containing:
                - id (str): Retweet ID
                - retweeted_tweet_id (str): ID of the original tweet that was retweeted
                - created_at (str): Retweet creation timestamp

        Raises:
            TwitterApiError: If retweeting fails or OAuth 1.0a credentials are not configured.
        """
        if not tweet_id or not tweet_id.strip():
            raise TwitterApiError("tweet_id is required for retweets")
        
        client = self._ensure_write_client()
        
        try:
            # Retweet the tweet
            response = client.retweet(tweet_id=tweet_id)
            
            if not response.data:
                raise TwitterApiError("Twitter API returned no data for retweet")
            
            return {
                "id": response.data["id"],
                "retweeted_tweet_id": tweet_id,
                "created_at": response.data.get("created_at", ""),
            }
        except tweepy.TweepyException as exc:
            raise TwitterApiError(f"Failed to retweet: {exc}") from exc


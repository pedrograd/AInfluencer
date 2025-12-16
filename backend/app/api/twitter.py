"""Twitter API endpoints for Twitter API v2 integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.twitter_client import TwitterApiClient, TwitterApiError

logger = get_logger(__name__)

router = APIRouter()


class TwitterConnectionTestResponse(BaseModel):
    """Response model for Twitter connection test."""
    connected: bool
    user_info: dict | None = None
    error: str | None = None


class TwitterUserInfoResponse(BaseModel):
    """Response model for Twitter user information."""
    user_info: dict


@router.get("/status", tags=["twitter"])
def get_twitter_status() -> dict:
    """
    Get Twitter API client status.
    
    Returns the current configuration status of the Twitter API client,
    including whether credentials are configured.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether Twitter credentials are configured
            - auth_method (str): Authentication method ("bearer_token" or "oauth1a" or "none")
    
    Example:
        ```json
        {
            "configured": true,
            "auth_method": "bearer_token"
        }
        ```
    """
    client = TwitterApiClient()
    has_bearer = client.bearer_token is not None
    has_oauth1a = all([
        client.consumer_key,
        client.consumer_secret,
        client.access_token,
        client.access_token_secret,
    ])
    
    if has_bearer:
        auth_method = "bearer_token"
    elif has_oauth1a:
        auth_method = "oauth1a"
    else:
        auth_method = "none"
    
    return {
        "configured": has_bearer or has_oauth1a,
        "auth_method": auth_method,
    }


@router.get("/test-connection", response_model=TwitterConnectionTestResponse, tags=["twitter"])
def test_twitter_connection() -> TwitterConnectionTestResponse:
    """
    Test connection to Twitter API.
    
    Attempts to connect to Twitter API v2 and fetch authenticated user info.
    This endpoint verifies that the configured credentials are valid and can
    successfully authenticate with Twitter's API.
    
    Returns:
        TwitterConnectionTestResponse: Connection test result containing:
            - connected (bool): Whether connection was successful
            - user_info (dict | None): User information if connected, None otherwise
            - error (str | None): Error message if connection failed, None otherwise
        
    Raises:
        HTTPException: 500 if unexpected error occurs during connection test.
        
    Example:
        ```json
        {
            "connected": true,
            "user_info": {
                "id": "123456789",
                "username": "example_user",
                "name": "Example User",
                "created_at": "2020-01-01T00:00:00"
            },
            "error": null
        }
        ```
    """
    try:
        client = TwitterApiClient()
        user_info = client.test_connection()
        return TwitterConnectionTestResponse(
            connected=True,
            user_info=user_info,
            error=None,
        )
    except TwitterApiError as exc:
        logger.error(f"Twitter connection test failed: {exc}")
        return TwitterConnectionTestResponse(
            connected=False,
            user_info=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during Twitter connection test")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/me", response_model=TwitterUserInfoResponse, tags=["twitter"])
def get_twitter_user_info() -> TwitterUserInfoResponse:
    """
    Get authenticated Twitter user information.
    
    Fetches information about the authenticated Twitter user, including
    user ID, username, display name, and account creation date.
    
    Returns:
        TwitterUserInfoResponse: User information containing:
            - user_info (dict): User information dictionary with:
                - id (str): User ID
                - username (str): Twitter username
                - name (str): Display name
                - created_at (str): Account creation date (ISO format)
        
    Raises:
        HTTPException:
            - 500 if Twitter API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
        
    Example:
        ```json
        {
            "user_info": {
                "id": "123456789",
                "username": "example_user",
                "name": "Example User",
                "created_at": "2020-01-01T00:00:00"
            }
        }
        ```
    """
    try:
        client = TwitterApiClient()
        user_info = client.get_me()
        return TwitterUserInfoResponse(user_info=user_info)
    except TwitterApiError as exc:
        logger.error(f"Failed to get Twitter user info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Twitter API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error getting Twitter user info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class PostTweetRequest(BaseModel):
    """Request model for posting a tweet."""
    text: str
    media_ids: list[str] | None = None
    reply_to_tweet_id: str | None = None


class PostTweetResponse(BaseModel):
    """Response model for posted tweet."""
    id: str
    text: str
    created_at: str | None = None


@router.post("/tweet", response_model=PostTweetResponse, tags=["twitter"])
def post_tweet(req: PostTweetRequest) -> PostTweetResponse:
    """
    Post a tweet to Twitter.
    
    Posts a new tweet to Twitter using OAuth 1.0a credentials.
    Requires consumer_key, consumer_secret, access_token, and access_token_secret
    to be configured (OAuth 2.0 Bearer Token is read-only).
    
    Args:
        req: Post tweet request containing:
            - text (str): Tweet text content (required, max 280 characters)
            - media_ids (list[str] | None): Optional list of media IDs to attach
            - reply_to_tweet_id (str | None): Optional ID of tweet to reply to
    
    Returns:
        PostTweetResponse: Posted tweet information containing:
            - id (str): Tweet ID
            - text (str): Tweet text
            - created_at (str | None): Tweet creation timestamp
    
    Raises:
        HTTPException:
            - 400 if validation fails (empty text, exceeds character limit)
            - 500 if Twitter API error occurs
            - 500 if OAuth 1.0a credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "text": "Hello, Twitter! #AInfluencer",
            "media_ids": ["123456789"],
            "reply_to_tweet_id": null
        }
        ```
    """
    try:
        client = TwitterApiClient()
        tweet_data = client.post_tweet(
            text=req.text,
            media_ids=req.media_ids,
            reply_to_tweet_id=req.reply_to_tweet_id,
        )
        return PostTweetResponse(
            id=tweet_data["id"],
            text=tweet_data["text"],
            created_at=tweet_data.get("created_at"),
        )
    except TwitterApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to post tweet: {exc}")
        
        # Check if it's a validation error (400) or API error (500)
        if "required" in error_msg.lower() or "exceeds" in error_msg.lower() or "limit" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Validation error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Twitter API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error posting tweet")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class ReplyToTweetRequest(BaseModel):
    """Request model for replying to a tweet."""
    text: str
    reply_to_tweet_id: str
    media_ids: list[str] | None = None


class ReplyToTweetResponse(BaseModel):
    """Response model for reply tweet."""
    id: str
    text: str
    created_at: str | None = None
    in_reply_to_tweet_id: str


@router.post("/reply", response_model=ReplyToTweetResponse, tags=["twitter"])
def reply_to_tweet(req: ReplyToTweetRequest) -> ReplyToTweetResponse:
    """
    Reply to a tweet on Twitter.
    
    Posts a reply to an existing tweet using OAuth 1.0a credentials.
    Requires consumer_key, consumer_secret, access_token, and access_token_secret
    to be configured (OAuth 2.0 Bearer Token is read-only).
    
    Args:
        req: Reply request containing:
            - text (str): Reply text content (required, max 280 characters)
            - reply_to_tweet_id (str): ID of tweet to reply to (required)
            - media_ids (list[str] | None): Optional list of media IDs to attach
    
    Returns:
        ReplyToTweetResponse: Reply tweet information containing:
            - id (str): Reply tweet ID
            - text (str): Reply text
            - created_at (str | None): Reply creation timestamp
            - in_reply_to_tweet_id (str): ID of the original tweet
    
    Raises:
        HTTPException:
            - 400 if validation fails (empty text, missing reply_to_tweet_id, exceeds character limit)
            - 500 if Twitter API error occurs
            - 500 if OAuth 1.0a credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "text": "Great point! I agree. #AInfluencer",
            "reply_to_tweet_id": "1234567890123456789",
            "media_ids": null
        }
        ```
    """
    try:
        client = TwitterApiClient()
        reply_data = client.reply_to_tweet(
            text=req.text,
            reply_to_tweet_id=req.reply_to_tweet_id,
            media_ids=req.media_ids,
        )
        return ReplyToTweetResponse(
            id=reply_data["id"],
            text=reply_data["text"],
            created_at=reply_data.get("created_at"),
            in_reply_to_tweet_id=req.reply_to_tweet_id,
        )
    except TwitterApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to reply to tweet: {exc}")
        
        # Check if it's a validation error (400) or API error (500)
        if "required" in error_msg.lower() or "exceeds" in error_msg.lower() or "limit" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Validation error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Twitter API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error replying to tweet")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class RetweetRequest(BaseModel):
    """Request model for retweeting a tweet."""
    tweet_id: str


class RetweetResponse(BaseModel):
    """Response model for retweet."""
    id: str
    retweeted_tweet_id: str
    created_at: str | None = None


@router.post("/retweet", response_model=RetweetResponse, tags=["twitter"])
def retweet(req: RetweetRequest) -> RetweetResponse:
    """
    Retweet a tweet on Twitter.
    
    Retweets an existing tweet using OAuth 1.0a credentials.
    Requires consumer_key, consumer_secret, access_token, and access_token_secret
    to be configured (OAuth 2.0 Bearer Token is read-only).
    
    Args:
        req: Retweet request containing:
            - tweet_id (str): ID of tweet to retweet (required)
    
    Returns:
        RetweetResponse: Retweet information containing:
            - id (str): Retweet ID
            - retweeted_tweet_id (str): ID of the original tweet that was retweeted
            - created_at (str | None): Retweet creation timestamp
    
    Raises:
        HTTPException:
            - 400 if validation fails (missing tweet_id)
            - 500 if Twitter API error occurs
            - 500 if OAuth 1.0a credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "tweet_id": "1234567890123456789"
        }
        ```
    """
    try:
        client = TwitterApiClient()
        retweet_data = client.retweet(tweet_id=req.tweet_id)
        return RetweetResponse(
            id=retweet_data["id"],
            retweeted_tweet_id=retweet_data["retweeted_tweet_id"],
            created_at=retweet_data.get("created_at"),
        )
    except TwitterApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to retweet: {exc}")
        
        # Check if it's a validation error (400) or API error (500)
        if "required" in error_msg.lower() or "exceeds" in error_msg.lower() or "limit" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Validation error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Twitter API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error retweeting")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


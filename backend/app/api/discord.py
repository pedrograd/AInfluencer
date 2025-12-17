"""Discord API endpoints for Discord Bot API integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.logging import get_logger
from app.core.middleware import limiter
from app.services.discord_client import DiscordApiClient, DiscordApiError

logger = get_logger(__name__)

router = APIRouter()


class DiscordConnectionTestResponse(BaseModel):
    """Response model for Discord connection test."""
    connected: bool
    bot_info: dict | None = None
    error: str | None = None


class DiscordBotInfoResponse(BaseModel):
    """Response model for Discord bot information."""
    bot_info: dict


@router.get("/status", tags=["discord"])
def get_discord_status() -> dict:
    """
    Get Discord API client status.
    
    Returns the current configuration status of the Discord API client,
    including whether a bot token is configured, API version, and base URL.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether bot token is configured
            - api_version (str): Discord API version
            - base_url (str): Base URL for API requests
    
    Example:
        ```json
        {
            "configured": true,
            "api_version": "v10",
            "base_url": "https://discord.com/api"
        }
        ```
    """
    client = DiscordApiClient()
    has_token = client.bot_token is not None
    
    return {
        "configured": has_token,
        "api_version": client.api_version,
        "base_url": client.base_url,
    }


@router.get("/test-connection", response_model=DiscordConnectionTestResponse, tags=["discord"])
def test_discord_connection() -> DiscordConnectionTestResponse:
    """
    Test connection to Discord API.
    
    Attempts to connect to Discord API and fetch authenticated bot info.
    This endpoint verifies that the configured bot token is valid and can
    successfully authenticate with Discord's API.
    
    Returns:
        DiscordConnectionTestResponse: Connection test result containing:
            - connected (bool): Whether connection was successful
            - bot_info (dict | None): Bot information if connected, None otherwise
            - error (str | None): Error message if connection failed, None otherwise
        
    Raises:
        HTTPException: 500 if unexpected error occurs during connection test.
        
    Example:
        ```json
        {
            "connected": true,
            "bot_info": {
                "id": "123456789012345678",
                "username": "MyBot",
                "discriminator": "0",
                "bot": true
            },
            "error": null
        }
        ```
    """
    try:
        client = DiscordApiClient()
        bot_info = client.test_connection()
        return DiscordConnectionTestResponse(
            connected=True,
            bot_info=bot_info,
            error=None,
        )
    except DiscordApiError as exc:
        logger.error(f"Discord connection test failed: {exc}")
        return DiscordConnectionTestResponse(
            connected=False,
            bot_info=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during Discord connection test")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


@router.get("/me", response_model=DiscordBotInfoResponse, tags=["discord"])
def get_discord_bot_info() -> DiscordBotInfoResponse:
    """
    Get authenticated Discord bot information.
    
    Fetches information about the authenticated Discord bot, including
    bot ID, username, discriminator, avatar, and verification status.
    
    Returns:
        DiscordBotInfoResponse: Bot information containing:
            - bot_info (dict): Bot information dictionary with:
                - id (str): Bot user ID
                - username (str): Bot username
                - discriminator (str): Bot discriminator (legacy, may be "0")
                - avatar (str | None): Avatar hash
                - bot (bool): Whether this is a bot account
                - verified (bool): Whether the bot is verified
        
    Raises:
        HTTPException:
            - 500 if Discord API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
        
    Example:
        ```json
        {
            "bot_info": {
                "id": "123456789012345678",
                "username": "MyBot",
                "discriminator": "0",
                "avatar": "abc123...",
                "bot": true,
                "verified": false
            }
        }
        ```
    """
    try:
        client = DiscordApiClient()
        bot_info = client.get_me()
        return DiscordBotInfoResponse(bot_info=bot_info)
    except DiscordApiError as exc:
        logger.error(f"Failed to get Discord bot info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Discord API error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error getting Discord bot info")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc


class SendMessageRequest(BaseModel):
    """Request model for sending a Discord message."""
    channel_id: str
    content: str


class SendMessageResponse(BaseModel):
    """Response model for Discord message sending."""
    id: str
    channel_id: str
    content: str
    timestamp: str


@router.post("/message", response_model=SendMessageResponse, tags=["discord"])
@limiter.limit("10/minute")
def send_discord_message(request: Request, req: SendMessageRequest) -> SendMessageResponse:
    """
    Send a message to a Discord channel.
    
    Sends a text message to the specified Discord channel using the authenticated bot.
    
    Args:
        req: Send message request containing:
            - channel_id (str): Discord channel ID where the message will be sent (required)
            - content (str): Message text content (required)
    
    Returns:
        SendMessageResponse: Message sending result containing:
            - id (str): Message ID
            - channel_id (str): Channel ID
            - content (str): Message content
            - timestamp (str): Message timestamp
    
    Raises:
        HTTPException:
            - 400 if validation fails (missing channel_id or content)
            - 500 if Discord API error occurs
            - 500 if credentials are not configured
            - 500 if unexpected error occurs
    
    Example:
        ```json
        {
            "id": "987654321098765432",
            "channel_id": "123456789012345678",
            "content": "Hello, Discord!",
            "timestamp": "2025-12-17T13:00:00.000000+00:00"
        }
        ```
    """
    try:
        if not req.channel_id or not req.channel_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Channel ID is required",
            )
        
        if not req.content or not req.content.strip():
            raise HTTPException(
                status_code=400,
                detail="Message content is required",
            )
        
        client = DiscordApiClient()
        message_data = client.send_message(
            channel_id=req.channel_id,
            content=req.content,
        )
        
        return SendMessageResponse(
            id=message_data["id"],
            channel_id=message_data["channel_id"],
            content=message_data["content"],
            timestamp=message_data.get("timestamp", ""),
        )
    except DiscordApiError as exc:
        error_msg = str(exc)
        logger.error(f"Failed to send Discord message: {exc}")
        
        if "required" in error_msg.lower() or "not configured" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Discord API error: {exc}",
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Discord API error: {exc}",
            ) from exc
    except Exception as exc:
        logger.exception("Unexpected error sending Discord message")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

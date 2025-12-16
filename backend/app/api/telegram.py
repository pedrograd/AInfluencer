"""Telegram Bot API endpoints for Telegram Bot API integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.telegram_client import TelegramApiClient, TelegramApiError

logger = get_logger(__name__)

router = APIRouter()


class TelegramConnectionTestResponse(BaseModel):
    """Response model for Telegram connection test."""
    connected: bool
    bot_info: dict | None = None
    error: str | None = None


class TelegramBotInfoResponse(BaseModel):
    """Response model for Telegram bot information."""
    bot_info: dict


class SendMessageRequest(BaseModel):
    """Request model for sending a Telegram message."""
    chat_id: str | int
    text: str
    parse_mode: str | None = None
    disable_web_page_preview: bool = False
    disable_notification: bool = False


class SendMessageResponse(BaseModel):
    """Response model for sent Telegram message."""
    message: dict


class SendPhotoRequest(BaseModel):
    """Request model for sending a Telegram photo."""
    chat_id: str | int
    photo: str  # file_id, URL, or file path
    caption: str | None = None
    parse_mode: str | None = None
    disable_notification: bool = False


class SendPhotoResponse(BaseModel):
    """Response model for sent Telegram photo."""
    message: dict


class SendVideoRequest(BaseModel):
    """Request model for sending a Telegram video."""
    chat_id: str | int
    video: str  # file_id, URL, or file path
    caption: str | None = None
    parse_mode: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    disable_notification: bool = False


class SendVideoResponse(BaseModel):
    """Response model for sent Telegram video."""
    message: dict


class GetChatRequest(BaseModel):
    """Request model for getting chat information."""
    chat_id: str | int


class GetChatResponse(BaseModel):
    """Response model for chat information."""
    chat: dict


@router.get("/status", tags=["telegram"])
def get_telegram_status() -> dict:
    """
    Get Telegram Bot API client status.
    
    Returns the current configuration status of the Telegram Bot API client,
    including whether bot token is configured.
    
    Returns:
        dict: Status information containing:
            - configured (bool): Whether Telegram bot token is configured
            - auth_method (str): Authentication method ("bot_token" or "none")
    
    Example:
        ```json
        {
            "configured": true,
            "auth_method": "bot_token"
        }
        ```
    """
    client = TelegramApiClient()
    has_token = client.bot_token is not None
    
    if has_token:
        auth_method = "bot_token"
    else:
        auth_method = "none"
    
    return {
        "configured": has_token,
        "auth_method": auth_method,
    }


@router.get("/test-connection", response_model=TelegramConnectionTestResponse, tags=["telegram"])
async def test_telegram_connection() -> TelegramConnectionTestResponse:
    """
    Test connection to Telegram Bot API.
    
    Attempts to connect to Telegram Bot API and fetch bot information.
    This endpoint verifies that the configured bot token is valid and can
    successfully authenticate with Telegram's API.
    
    Returns:
        TelegramConnectionTestResponse: Connection test result containing:
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
                "id": 123456789,
                "is_bot": true,
                "first_name": "MyBot",
                "username": "my_bot",
                "can_join_groups": true,
                "can_read_all_group_messages": false,
                "supports_inline_queries": false
            },
            "error": null
        }
        ```
    """
    try:
        client = TelegramApiClient()
        bot_info = await client.test_connection()
        return TelegramConnectionTestResponse(
            connected=True,
            bot_info=bot_info,
            error=None,
        )
    except TelegramApiError as exc:
        logger.error(f"Telegram connection test failed: {exc}")
        return TelegramConnectionTestResponse(
            connected=False,
            bot_info=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception(f"Unexpected error during Telegram connection test: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.get("/me", response_model=TelegramBotInfoResponse, tags=["telegram"])
async def get_telegram_bot_info() -> TelegramBotInfoResponse:
    """
    Get Telegram bot information.
    
    Fetches information about the authenticated bot, including bot ID,
    username, and capabilities.
    
    Returns:
        TelegramBotInfoResponse: Bot information containing:
            - bot_info (dict): Bot information dictionary
    
    Raises:
        HTTPException: 400 if bot token is not configured.
        HTTPException: 500 if API request fails.
        
    Example:
        ```json
        {
            "bot_info": {
                "id": 123456789,
                "is_bot": true,
                "first_name": "MyBot",
                "username": "my_bot",
                "can_join_groups": true,
                "can_read_all_group_messages": false,
                "supports_inline_queries": false
            }
        }
        ```
    """
    try:
        client = TelegramApiClient()
        bot_info = await client.get_me()
        return TelegramBotInfoResponse(bot_info=bot_info)
    except TelegramApiError as exc:
        logger.error(f"Failed to get Telegram bot info: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error getting Telegram bot info: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/send-message", response_model=SendMessageResponse, tags=["telegram"])
async def send_telegram_message(req: SendMessageRequest) -> SendMessageResponse:
    """
    Send a text message to a Telegram chat.
    
    Sends a text message to the specified chat (channel, group, or private chat).
    
    Args:
        req: SendMessageRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
            - text: Text of the message to be sent (1-4096 characters)
            - parse_mode: Optional parse mode (None, "HTML", "Markdown", "MarkdownV2")
            - disable_web_page_preview: Disables link previews for links in this message
            - disable_notification: Sends the message silently
    
    Returns:
        SendMessageResponse: Sent message information
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        client = TelegramApiClient()
        message = await client.send_message(
            chat_id=req.chat_id,
            text=req.text,
            parse_mode=req.parse_mode,
            disable_web_page_preview=req.disable_web_page_preview,
            disable_notification=req.disable_notification,
        )
        return SendMessageResponse(message=message)
    except TelegramApiError as exc:
        logger.error(f"Failed to send Telegram message: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error sending Telegram message: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/send-photo", response_model=SendPhotoResponse, tags=["telegram"])
async def send_telegram_photo(req: SendPhotoRequest) -> SendPhotoResponse:
    """
    Send a photo to a Telegram chat.
    
    Sends a photo to the specified chat (channel, group, or private chat).
    
    Args:
        req: SendPhotoRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
            - photo: Photo to send (file_id, URL, or file path)
            - caption: Optional photo caption (0-1024 characters)
            - parse_mode: Optional parse mode (None, "HTML", "Markdown", "MarkdownV2")
            - disable_notification: Sends the message silently
    
    Returns:
        SendPhotoResponse: Sent message information
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        client = TelegramApiClient()
        message = await client.send_photo(
            chat_id=req.chat_id,
            photo=req.photo,
            caption=req.caption,
            parse_mode=req.parse_mode,
            disable_notification=req.disable_notification,
        )
        return SendPhotoResponse(message=message)
    except TelegramApiError as exc:
        logger.error(f"Failed to send Telegram photo: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error sending Telegram photo: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/send-video", response_model=SendVideoResponse, tags=["telegram"])
async def send_telegram_video(req: SendVideoRequest) -> SendVideoResponse:
    """
    Send a video to a Telegram chat.
    
    Sends a video to the specified chat (channel, group, or private chat).
    
    Args:
        req: SendVideoRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
            - video: Video to send (file_id, URL, or file path)
            - caption: Optional video caption (0-1024 characters)
            - parse_mode: Optional parse mode (None, "HTML", "Markdown", "MarkdownV2")
            - duration: Optional duration of sent video in seconds
            - width: Optional video width
            - height: Optional video height
            - disable_notification: Sends the message silently
    
    Returns:
        SendVideoResponse: Sent message information
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        client = TelegramApiClient()
        message = await client.send_video(
            chat_id=req.chat_id,
            video=req.video,
            caption=req.caption,
            parse_mode=req.parse_mode,
            duration=req.duration,
            width=req.width,
            height=req.height,
            disable_notification=req.disable_notification,
        )
        return SendVideoResponse(message=message)
    except TelegramApiError as exc:
        logger.error(f"Failed to send Telegram video: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error sending Telegram video: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/get-chat", response_model=GetChatResponse, tags=["telegram"])
async def get_telegram_chat(req: GetChatRequest) -> GetChatResponse:
    """
    Get information about a Telegram chat.
    
    Fetches information about the specified chat (channel, group, or private chat).
    
    Args:
        req: GetChatRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
    
    Returns:
        GetChatResponse: Chat information
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        client = TelegramApiClient()
        chat = await client.get_chat(chat_id=req.chat_id)
        return GetChatResponse(chat=chat)
    except TelegramApiError as exc:
        logger.error(f"Failed to get Telegram chat info: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error getting Telegram chat info: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


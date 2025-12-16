"""Telegram Bot API endpoints for Telegram Bot API integration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.telegram_client import TelegramApiClient, TelegramApiError
from app.services.telegram_message_automation_service import (
    TelegramMessageAutomationError,
    TelegramMessageAutomationService,
)

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


class GetChatMemberCountRequest(BaseModel):
    """Request model for getting chat member count."""
    chat_id: str | int


class GetChatMemberCountResponse(BaseModel):
    """Response model for chat member count."""
    member_count: dict


class GetChatAdministratorsRequest(BaseModel):
    """Request model for getting chat administrators."""
    chat_id: str | int


class GetChatAdministratorsResponse(BaseModel):
    """Response model for chat administrators."""
    administrators: dict


class GetChatMemberRequest(BaseModel):
    """Request model for getting chat member information."""
    chat_id: str | int
    user_id: int


class GetChatMemberResponse(BaseModel):
    """Response model for chat member information."""
    member: dict


class GetChannelStatisticsRequest(BaseModel):
    """Request model for getting channel statistics."""
    chat_id: str | int


class GetChannelStatisticsResponse(BaseModel):
    """Response model for channel statistics."""
    statistics: dict


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


@router.post("/get-member-count", response_model=GetChatMemberCountResponse, tags=["telegram"])
async def get_telegram_chat_member_count(req: GetChatMemberCountRequest) -> GetChatMemberCountResponse:
    """
    Get the number of members in a Telegram chat.
    
    Fetches the member count for the specified chat (channel, group, or supergroup).
    
    Args:
        req: GetChatMemberCountRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
    
    Returns:
        GetChatMemberCountResponse: Member count information
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        client = TelegramApiClient()
        member_count = await client.get_chat_member_count(chat_id=req.chat_id)
        return GetChatMemberCountResponse(member_count=member_count)
    except TelegramApiError as exc:
        logger.error(f"Failed to get Telegram chat member count: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error getting Telegram chat member count: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/get-administrators", response_model=GetChatAdministratorsResponse, tags=["telegram"])
async def get_telegram_chat_administrators(req: GetChatAdministratorsRequest) -> GetChatAdministratorsResponse:
    """
    Get a list of administrators in a Telegram chat.
    
    Fetches the list of administrators for the specified chat (channel, group, or supergroup).
    
    Args:
        req: GetChatAdministratorsRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
    
    Returns:
        GetChatAdministratorsResponse: Administrators information
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        client = TelegramApiClient()
        administrators = await client.get_chat_administrators(chat_id=req.chat_id)
        return GetChatAdministratorsResponse(administrators=administrators)
    except TelegramApiError as exc:
        logger.error(f"Failed to get Telegram chat administrators: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error getting Telegram chat administrators: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/get-member", response_model=GetChatMemberResponse, tags=["telegram"])
async def get_telegram_chat_member(req: GetChatMemberRequest) -> GetChatMemberResponse:
    """
    Get information about a member of a Telegram chat.
    
    Fetches information about a specific member in the specified chat (channel, group, or supergroup).
    
    Args:
        req: GetChatMemberRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
            - user_id: Unique identifier of the target user
    
    Returns:
        GetChatMemberResponse: Member information
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        client = TelegramApiClient()
        member = await client.get_chat_member(chat_id=req.chat_id, user_id=req.user_id)
        return GetChatMemberResponse(member=member)
    except TelegramApiError as exc:
        logger.error(f"Failed to get Telegram chat member: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error getting Telegram chat member: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/get-channel-statistics", response_model=GetChannelStatisticsResponse, tags=["telegram"])
async def get_telegram_channel_statistics(req: GetChannelStatisticsRequest) -> GetChannelStatisticsResponse:
    """
    Get comprehensive channel statistics.
    
    Fetches comprehensive statistics for the specified channel including:
    - Basic channel information
    - Member count
    - List of administrators
    - Whether the bot is an administrator
    
    Args:
        req: GetChannelStatisticsRequest containing:
            - chat_id: Unique identifier for the target channel or username of the target channel
    
    Returns:
        GetChannelStatisticsResponse: Comprehensive channel statistics
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        client = TelegramApiClient()
        statistics = await client.get_channel_statistics(chat_id=req.chat_id)
        return GetChannelStatisticsResponse(statistics=statistics)
    except TelegramApiError as exc:
        logger.error(f"Failed to get Telegram channel statistics: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error getting Telegram channel statistics: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


# Message Automation Endpoints

class SendScheduledMessageRequest(BaseModel):
    """Request model for sending a scheduled Telegram message."""
    chat_id: str | int
    text: str
    parse_mode: str | None = None
    disable_web_page_preview: bool = False
    disable_notification: bool = False


class SendScheduledMessageResponse(BaseModel):
    """Response model for scheduled Telegram message."""
    success: bool
    message: dict
    sent_at: str


class SendScheduledPhotoRequest(BaseModel):
    """Request model for sending a scheduled Telegram photo."""
    chat_id: str | int
    photo: str  # file_id, URL, or file path
    caption: str | None = None
    parse_mode: str | None = None
    disable_notification: bool = False


class SendScheduledPhotoResponse(BaseModel):
    """Response model for scheduled Telegram photo."""
    success: bool
    message: dict
    sent_at: str


class SendScheduledVideoRequest(BaseModel):
    """Request model for sending a scheduled Telegram video."""
    chat_id: str | int
    video: str  # file_id, URL, or file path
    caption: str | None = None
    parse_mode: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    disable_notification: bool = False


class SendScheduledVideoResponse(BaseModel):
    """Response model for scheduled Telegram video."""
    success: bool
    message: dict
    sent_at: str


class BatchMessageConfig(BaseModel):
    """Configuration for a single message in a batch."""
    text: str
    parse_mode: str | None = None
    disable_web_page_preview: bool = False
    disable_notification: bool = False


class SendBatchMessagesRequest(BaseModel):
    """Request model for sending batch Telegram messages."""
    chat_id: str | int
    messages: list[BatchMessageConfig]
    delay_seconds: int = 1


class SendBatchMessagesResponse(BaseModel):
    """Response model for batch Telegram messages."""
    success: bool
    total: int
    sent: int
    failed: int
    results: list[dict]
    errors: list[dict]
    sent_at: str


@router.post("/send-scheduled-message", response_model=SendScheduledMessageResponse, tags=["telegram", "automation"])
async def send_scheduled_telegram_message(
    req: SendScheduledMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> SendScheduledMessageResponse:
    """
    Send a scheduled message to a Telegram chat.
    
    Sends a text message to the specified chat (channel, group, or private chat).
    This endpoint is designed for automated/scheduled message sending.
    
    Args:
        req: SendScheduledMessageRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
            - text: Text of the message to be sent (1-4096 characters)
            - parse_mode: Optional parse mode (None, "HTML", "Markdown", "MarkdownV2")
            - disable_web_page_preview: Disables link previews for links in this message
            - disable_notification: Sends the message silently
        db: Database session dependency
    
    Returns:
        SendScheduledMessageResponse: Scheduled message sending result
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        service = TelegramMessageAutomationService(db)
        result = await service.send_scheduled_message(
            chat_id=req.chat_id,
            text=req.text,
            parse_mode=req.parse_mode,
            disable_web_page_preview=req.disable_web_page_preview,
            disable_notification=req.disable_notification,
        )
        return SendScheduledMessageResponse(
            success=result["success"],
            message=result["message"],
            sent_at=result["sent_at"],
        )
    except TelegramMessageAutomationError as exc:
        logger.error(f"Failed to send scheduled Telegram message: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error sending scheduled Telegram message: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/send-scheduled-photo", response_model=SendScheduledPhotoResponse, tags=["telegram", "automation"])
async def send_scheduled_telegram_photo(
    req: SendScheduledPhotoRequest,
    db: AsyncSession = Depends(get_db),
) -> SendScheduledPhotoResponse:
    """
    Send a scheduled photo to a Telegram chat.
    
    Sends a photo to the specified chat (channel, group, or private chat).
    This endpoint is designed for automated/scheduled photo sending.
    
    Args:
        req: SendScheduledPhotoRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
            - photo: Photo to send (file_id, URL, or file path)
            - caption: Optional photo caption (0-1024 characters)
            - parse_mode: Optional parse mode (None, "HTML", "Markdown", "MarkdownV2")
            - disable_notification: Sends the message silently
        db: Database session dependency
    
    Returns:
        SendScheduledPhotoResponse: Scheduled photo sending result
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        service = TelegramMessageAutomationService(db)
        result = await service.send_scheduled_photo(
            chat_id=req.chat_id,
            photo=req.photo,
            caption=req.caption,
            parse_mode=req.parse_mode,
            disable_notification=req.disable_notification,
        )
        return SendScheduledPhotoResponse(
            success=result["success"],
            message=result["message"],
            sent_at=result["sent_at"],
        )
    except TelegramMessageAutomationError as exc:
        logger.error(f"Failed to send scheduled Telegram photo: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error sending scheduled Telegram photo: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/send-scheduled-video", response_model=SendScheduledVideoResponse, tags=["telegram", "automation"])
async def send_scheduled_telegram_video(
    req: SendScheduledVideoRequest,
    db: AsyncSession = Depends(get_db),
) -> SendScheduledVideoResponse:
    """
    Send a scheduled video to a Telegram chat.
    
    Sends a video to the specified chat (channel, group, or private chat).
    This endpoint is designed for automated/scheduled video sending.
    
    Args:
        req: SendScheduledVideoRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
            - video: Video to send (file_id, URL, or file path)
            - caption: Optional video caption (0-1024 characters)
            - parse_mode: Optional parse mode (None, "HTML", "Markdown", "MarkdownV2")
            - duration: Optional duration of sent video in seconds
            - width: Optional video width
            - height: Optional video height
            - disable_notification: Sends the message silently
        db: Database session dependency
    
    Returns:
        SendScheduledVideoResponse: Scheduled video sending result
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        service = TelegramMessageAutomationService(db)
        result = await service.send_scheduled_video(
            chat_id=req.chat_id,
            video=req.video,
            caption=req.caption,
            parse_mode=req.parse_mode,
            duration=req.duration,
            width=req.width,
            height=req.height,
            disable_notification=req.disable_notification,
        )
        return SendScheduledVideoResponse(
            success=result["success"],
            message=result["message"],
            sent_at=result["sent_at"],
        )
    except TelegramMessageAutomationError as exc:
        logger.error(f"Failed to send scheduled Telegram video: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error sending scheduled Telegram video: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/send-batch-messages", response_model=SendBatchMessagesResponse, tags=["telegram", "automation"])
async def send_batch_telegram_messages(
    req: SendBatchMessagesRequest,
    db: AsyncSession = Depends(get_db),
) -> SendBatchMessagesResponse:
    """
    Send multiple messages to a Telegram chat with delays between them.
    
    Sends a batch of messages to the specified chat with configurable delays
    between messages. Useful for sending multiple messages in sequence.
    
    Args:
        req: SendBatchMessagesRequest containing:
            - chat_id: Unique identifier for the target chat or username of the target channel
            - messages: List of message configurations, each containing:
                - text: Message text (required)
                - parse_mode: Optional parse mode
                - disable_web_page_preview: Optional disable web page preview
                - disable_notification: Optional disable notification
            - delay_seconds: Delay in seconds between messages (default: 1)
        db: Database session dependency
    
    Returns:
        SendBatchMessagesResponse: Batch sending result with success/failure details
    
    Raises:
        HTTPException: 400 if request validation fails or API request fails.
        HTTPException: 500 if unexpected error occurs.
    """
    try:
        service = TelegramMessageAutomationService(db)
        # Convert BatchMessageConfig to dict format
        messages_dict = [
            {
                "text": msg.text,
                "parse_mode": msg.parse_mode,
                "disable_web_page_preview": msg.disable_web_page_preview,
                "disable_notification": msg.disable_notification,
            }
            for msg in req.messages
        ]
        result = await service.send_batch_messages(
            chat_id=req.chat_id,
            messages=messages_dict,
            delay_seconds=req.delay_seconds,
        )
        return SendBatchMessagesResponse(
            success=result["success"],
            total=result["total"],
            sent=result["sent"],
            failed=result["failed"],
            results=result["results"],
            errors=result["errors"],
            sent_at=result["sent_at"],
        )
    except TelegramMessageAutomationError as exc:
        logger.error(f"Failed to send batch Telegram messages: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"Unexpected error sending batch Telegram messages: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


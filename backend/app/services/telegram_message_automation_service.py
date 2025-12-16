"""Telegram message automation service for scheduled and automated messages."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.telegram_client import TelegramApiClient, TelegramApiError

logger = get_logger(__name__)


class TelegramMessageAutomationError(RuntimeError):
    """Error raised when Telegram message automation operations fail."""

    pass


class TelegramMessageAutomationService:
    """Service for automating Telegram message sending."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize Telegram message automation service.

        Args:
            db: Database session (for future database operations).
        """
        self.db = db
        self.telegram_client = TelegramApiClient()

    async def send_scheduled_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: str | None = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """
        Send a scheduled message to a Telegram chat.

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.
            text: Text of the message to be sent (1-4096 characters).
            parse_mode: Mode for parsing entities in the message text (None, "HTML", "Markdown", "MarkdownV2").
            disable_web_page_preview: Disables link previews for links in this message.
            disable_notification: Sends the message silently.

        Returns:
            Dictionary containing sent message information.

        Raises:
            TelegramMessageAutomationError: If message sending fails.
        """
        try:
            message = await self.telegram_client.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
            )
            logger.info(f"Successfully sent scheduled message to chat {chat_id}")
            return {
                "success": True,
                "message": message,
                "sent_at": datetime.now().isoformat(),
            }
        except TelegramApiError as exc:
            logger.error(f"Failed to send scheduled message to chat {chat_id}: {exc}")
            raise TelegramMessageAutomationError(f"Failed to send message: {exc}") from exc

    async def send_scheduled_photo(
        self,
        chat_id: str | int,
        photo: str | bytes,
        caption: str | None = None,
        parse_mode: str | None = None,
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """
        Send a scheduled photo to a Telegram chat.

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.
            photo: Photo to send. Can be a file_id, URL, or file bytes.
            caption: Photo caption (0-1024 characters).
            parse_mode: Mode for parsing entities in the caption (None, "HTML", "Markdown", "MarkdownV2").
            disable_notification: Sends the message silently.

        Returns:
            Dictionary containing sent message information.

        Raises:
            TelegramMessageAutomationError: If photo sending fails.
        """
        try:
            message = await self.telegram_client.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
            )
            logger.info(f"Successfully sent scheduled photo to chat {chat_id}")
            return {
                "success": True,
                "message": message,
                "sent_at": datetime.now().isoformat(),
            }
        except TelegramApiError as exc:
            logger.error(f"Failed to send scheduled photo to chat {chat_id}: {exc}")
            raise TelegramMessageAutomationError(f"Failed to send photo: {exc}") from exc

    async def send_scheduled_video(
        self,
        chat_id: str | int,
        video: str | bytes,
        caption: str | None = None,
        parse_mode: str | None = None,
        duration: int | None = None,
        width: int | None = None,
        height: int | None = None,
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """
        Send a scheduled video to a Telegram chat.

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.
            video: Video to send. Can be a file_id, URL, or file bytes.
            caption: Video caption (0-1024 characters).
            parse_mode: Mode for parsing entities in the caption (None, "HTML", "Markdown", "MarkdownV2").
            duration: Duration of sent video in seconds.
            width: Video width.
            height: Video height.
            disable_notification: Sends the message silently.

        Returns:
            Dictionary containing sent message information.

        Raises:
            TelegramMessageAutomationError: If video sending fails.
        """
        try:
            message = await self.telegram_client.send_video(
                chat_id=chat_id,
                video=video,
                caption=caption,
                parse_mode=parse_mode,
                duration=duration,
                width=width,
                height=height,
                disable_notification=disable_notification,
            )
            logger.info(f"Successfully sent scheduled video to chat {chat_id}")
            return {
                "success": True,
                "message": message,
                "sent_at": datetime.now().isoformat(),
            }
        except TelegramApiError as exc:
            logger.error(f"Failed to send scheduled video to chat {chat_id}: {exc}")
            raise TelegramMessageAutomationError(f"Failed to send video: {exc}") from exc

    async def send_batch_messages(
        self,
        chat_id: str | int,
        messages: list[dict[str, Any]],
        delay_seconds: int = 1,
    ) -> dict[str, Any]:
        """
        Send multiple messages to a Telegram chat with delays between them.

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.
            messages: List of message dictionaries, each containing:
                - text (str): Message text
                - parse_mode (str | None): Optional parse mode
                - disable_web_page_preview (bool): Optional disable web page preview
                - disable_notification (bool): Optional disable notification
            delay_seconds: Delay in seconds between messages (default: 1).

        Returns:
            Dictionary containing batch sending results.

        Raises:
            TelegramMessageAutomationError: If batch sending fails.
        """
        import asyncio

        results = []
        errors = []

        for i, msg_config in enumerate(messages):
            try:
                # Add delay between messages (except for the first one)
                if i > 0:
                    await asyncio.sleep(delay_seconds)

                text = msg_config.get("text", "")
                if not text:
                    errors.append({"index": i, "error": "Message text is required"})
                    continue

                message = await self.telegram_client.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=msg_config.get("parse_mode"),
                    disable_web_page_preview=msg_config.get("disable_web_page_preview", False),
                    disable_notification=msg_config.get("disable_notification", False),
                )
                results.append({"index": i, "success": True, "message": message})
            except TelegramApiError as exc:
                error_msg = f"Failed to send message {i}: {exc}"
                logger.error(error_msg)
                errors.append({"index": i, "error": str(exc)})

        return {
            "success": len(errors) == 0,
            "total": len(messages),
            "sent": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
            "sent_at": datetime.now().isoformat(),
        }


"""Telegram Bot API client for Telegram Bot API integration."""

from __future__ import annotations

from typing import Any

from telegram import Bot
from telegram.error import TelegramError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TelegramApiError(RuntimeError):
    """Error raised when Telegram API operations fail.
    
    This exception is raised for various Telegram-related errors including
    connection failures, API errors, authentication failures, and
    other Telegram API issues.
    """
    pass


class TelegramApiClient:
    """Client for interacting with Telegram Bot API."""

    def __init__(
        self,
        bot_token: str | None = None,
    ) -> None:
        """
        Initialize Telegram Bot API client.

        Args:
            bot_token: Telegram Bot Token from @BotFather.
        """
        self.bot_token = bot_token or getattr(settings, "telegram_bot_token", None)

        # Initialize Telegram Bot client
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
        else:
            self.bot = None
            logger.warning("Telegram Bot token not configured")

    def _ensure_bot(self) -> Bot:
        """Ensure Telegram Bot is initialized.
        
        Returns:
            Initialized Telegram Bot instance.
            
        Raises:
            TelegramApiError: If bot is not initialized.
        """
        if not self.bot:
            raise TelegramApiError("Telegram Bot token not configured")
        return self.bot

    async def get_me(self) -> dict[str, Any]:
        """
        Get bot information.

        Returns:
            Bot information dictionary containing:
                - id (int): Bot ID
                - is_bot (bool): Always True for bots
                - first_name (str): Bot's first name
                - username (str): Bot's username
                - can_join_groups (bool): Whether bot can join groups
                - can_read_all_group_messages (bool): Whether bot can read all group messages
                - supports_inline_queries (bool): Whether bot supports inline queries
        """
        bot = self._ensure_bot()
        try:
            bot_info = await bot.get_me()
            return {
                "id": bot_info.id,
                "is_bot": bot_info.is_bot,
                "first_name": bot_info.first_name,
                "username": bot_info.username,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries,
            }
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to get bot info: {exc}") from exc

    async def test_connection(self) -> dict[str, Any]:
        """
        Test connection to Telegram Bot API by fetching bot info.

        Returns:
            Bot information if connection is successful.

        Raises:
            TelegramApiError: If connection fails.
        """
        try:
            return await self.get_me()
        except Exception as exc:
            raise TelegramApiError(f"Telegram Bot API connection test failed: {exc}") from exc

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: str | None = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """
        Send a text message to a chat.

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.
            text: Text of the message to be sent (1-4096 characters).
            parse_mode: Mode for parsing entities in the message text (None, "HTML", "Markdown", "MarkdownV2").
            disable_web_page_preview: Disables link previews for links in this message.
            disable_notification: Sends the message silently.

        Returns:
            Dictionary containing sent message information:
                - message_id (int): Unique message identifier
                - chat (dict): Chat information
                - date (int): Date the message was sent (Unix time)
                - text (str): Message text
        """
        bot = self._ensure_bot()
        try:
            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
            )
            return {
                "message_id": message.message_id,
                "chat": {
                    "id": message.chat.id,
                    "type": message.chat.type,
                    "title": getattr(message.chat, "title", None),
                    "username": getattr(message.chat, "username", None),
                },
                "date": message.date,
                "text": message.text,
            }
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to send message: {exc}") from exc

    async def send_photo(
        self,
        chat_id: str | int,
        photo: str | bytes,
        caption: str | None = None,
        parse_mode: str | None = None,
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """
        Send a photo to a chat.

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.
            photo: Photo to send. Can be a file_id, URL, or file bytes.
            caption: Photo caption (0-1024 characters).
            parse_mode: Mode for parsing entities in the caption (None, "HTML", "Markdown", "MarkdownV2").
            disable_notification: Sends the message silently.

        Returns:
            Dictionary containing sent message information.
        """
        bot = self._ensure_bot()
        try:
            message = await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
            )
            return {
                "message_id": message.message_id,
                "chat": {
                    "id": message.chat.id,
                    "type": message.chat.type,
                    "title": getattr(message.chat, "title", None),
                    "username": getattr(message.chat, "username", None),
                },
                "date": message.date,
                "caption": message.caption,
            }
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to send photo: {exc}") from exc

    async def send_video(
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
        Send a video to a chat.

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
        """
        bot = self._ensure_bot()
        try:
            message = await bot.send_video(
                chat_id=chat_id,
                video=video,
                caption=caption,
                parse_mode=parse_mode,
                duration=duration,
                width=width,
                height=height,
                disable_notification=disable_notification,
            )
            return {
                "message_id": message.message_id,
                "chat": {
                    "id": message.chat.id,
                    "type": message.chat.type,
                    "title": getattr(message.chat, "title", None),
                    "username": getattr(message.chat, "username", None),
                },
                "date": message.date,
                "caption": message.caption,
            }
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to send video: {exc}") from exc

    async def get_chat(self, chat_id: str | int) -> dict[str, Any]:
        """
        Get information about a chat.

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.

        Returns:
            Dictionary containing chat information:
                - id (int): Unique identifier for this chat
                - type (str): Type of chat (private, group, supergroup, channel)
                - title (str | None): Title for supergroups, channels and group chats
                - username (str | None): Username for private chats, supergroups and channels
                - description (str | None): Description for groups, supergroups and channel chats
        """
        bot = self._ensure_bot()
        try:
            chat = await bot.get_chat(chat_id=chat_id)
            return {
                "id": chat.id,
                "type": chat.type,
                "title": getattr(chat, "title", None),
                "username": getattr(chat, "username", None),
                "description": getattr(chat, "description", None),
            }
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to get chat info: {exc}") from exc


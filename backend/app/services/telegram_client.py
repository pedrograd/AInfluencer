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

    async def get_chat_member_count(self, chat_id: str | int) -> dict[str, Any]:
        """
        Get the number of members in a chat (channel, group, or supergroup).

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.

        Returns:
            Dictionary containing:
                - chat_id (int): Chat identifier
                - member_count (int): Number of members in the chat
        """
        bot = self._ensure_bot()
        try:
            member_count = await bot.get_chat_member_count(chat_id=chat_id)
            return {
                "chat_id": chat_id if isinstance(chat_id, int) else None,
                "member_count": member_count,
            }
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to get chat member count: {exc}") from exc

    async def get_chat_administrators(self, chat_id: str | int) -> dict[str, Any]:
        """
        Get a list of administrators in a chat (channel, group, or supergroup).

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.

        Returns:
            Dictionary containing:
                - chat_id (int): Chat identifier
                - administrators (list): List of administrator dictionaries, each containing:
                    - user (dict): User information (id, is_bot, first_name, username)
                    - status (str): Administrator status (creator, administrator)
                    - can_be_edited (bool): Whether the bot can edit administrator privileges
                    - custom_title (str | None): Custom title for the administrator
                    - can_manage_chat (bool): Whether administrator can manage chat
                    - can_delete_messages (bool): Whether administrator can delete messages
                    - can_manage_video_chats (bool): Whether administrator can manage video chats
                    - can_restrict_members (bool): Whether administrator can restrict members
                    - can_promote_members (bool): Whether administrator can promote members
                    - can_change_info (bool): Whether administrator can change chat info
                    - can_invite_users (bool): Whether administrator can invite users
                    - can_post_messages (bool): Whether administrator can post messages (channels only)
                    - can_edit_messages (bool): Whether administrator can edit messages (channels only)
                    - can_pin_messages (bool): Whether administrator can pin messages
        """
        bot = self._ensure_bot()
        try:
            administrators = await bot.get_chat_administrators(chat_id=chat_id)
            admin_list = []
            for admin in administrators:
                admin_dict = {
                    "user": {
                        "id": admin.user.id,
                        "is_bot": admin.user.is_bot,
                        "first_name": admin.user.first_name,
                        "username": getattr(admin.user, "username", None),
                    },
                    "status": admin.status,
                }
                # Add optional fields if they exist
                if hasattr(admin, "can_be_edited"):
                    admin_dict["can_be_edited"] = admin.can_be_edited
                if hasattr(admin, "custom_title"):
                    admin_dict["custom_title"] = admin.custom_title
                if hasattr(admin, "can_manage_chat"):
                    admin_dict["can_manage_chat"] = admin.can_manage_chat
                if hasattr(admin, "can_delete_messages"):
                    admin_dict["can_delete_messages"] = admin.can_delete_messages
                if hasattr(admin, "can_manage_video_chats"):
                    admin_dict["can_manage_video_chats"] = admin.can_manage_video_chats
                if hasattr(admin, "can_restrict_members"):
                    admin_dict["can_restrict_members"] = admin.can_restrict_members
                if hasattr(admin, "can_promote_members"):
                    admin_dict["can_promote_members"] = admin.can_promote_members
                if hasattr(admin, "can_change_info"):
                    admin_dict["can_change_info"] = admin.can_change_info
                if hasattr(admin, "can_invite_users"):
                    admin_dict["can_invite_users"] = admin.can_invite_users
                if hasattr(admin, "can_post_messages"):
                    admin_dict["can_post_messages"] = admin.can_post_messages
                if hasattr(admin, "can_edit_messages"):
                    admin_dict["can_edit_messages"] = admin.can_edit_messages
                if hasattr(admin, "can_pin_messages"):
                    admin_dict["can_pin_messages"] = admin.can_pin_messages
                admin_list.append(admin_dict)
            return {
                "chat_id": chat_id if isinstance(chat_id, int) else None,
                "administrators": admin_list,
            }
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to get chat administrators: {exc}") from exc

    async def get_chat_member(self, chat_id: str | int, user_id: int) -> dict[str, Any]:
        """
        Get information about a member of a chat.

        Args:
            chat_id: Unique identifier for the target chat or username of the target channel.
            user_id: Unique identifier of the target user.

        Returns:
            Dictionary containing member information:
                - user (dict): User information (id, is_bot, first_name, username)
                - status (str): Member status (creator, administrator, member, restricted, left, kicked)
                - Additional fields based on status (can_be_edited, custom_title, etc.)
        """
        bot = self._ensure_bot()
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            member_dict = {
                "user": {
                    "id": member.user.id,
                    "is_bot": member.user.is_bot,
                    "first_name": member.user.first_name,
                    "username": getattr(member.user, "username", None),
                },
                "status": member.status,
            }
            # Add optional fields if they exist
            if hasattr(member, "can_be_edited"):
                member_dict["can_be_edited"] = member.can_be_edited
            if hasattr(member, "custom_title"):
                member_dict["custom_title"] = member.custom_title
            if hasattr(member, "can_manage_chat"):
                member_dict["can_manage_chat"] = member.can_manage_chat
            if hasattr(member, "can_delete_messages"):
                member_dict["can_delete_messages"] = member.can_delete_messages
            if hasattr(member, "can_manage_video_chats"):
                member_dict["can_manage_video_chats"] = member.can_manage_video_chats
            if hasattr(member, "can_restrict_members"):
                member_dict["can_restrict_members"] = member.can_restrict_members
            if hasattr(member, "can_promote_members"):
                member_dict["can_promote_members"] = member.can_promote_members
            if hasattr(member, "can_change_info"):
                member_dict["can_change_info"] = member.can_change_info
            if hasattr(member, "can_invite_users"):
                member_dict["can_invite_users"] = member.can_invite_users
            if hasattr(member, "can_post_messages"):
                member_dict["can_post_messages"] = member.can_post_messages
            if hasattr(member, "can_edit_messages"):
                member_dict["can_edit_messages"] = member.can_edit_messages
            if hasattr(member, "can_pin_messages"):
                member_dict["can_pin_messages"] = member.can_pin_messages
            return member_dict
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to get chat member: {exc}") from exc

    async def get_channel_statistics(self, chat_id: str | int) -> dict[str, Any]:
        """
        Get comprehensive channel statistics including info, member count, and administrators.

        Args:
            chat_id: Unique identifier for the target channel or username of the target channel.

        Returns:
            Dictionary containing:
                - chat_info (dict): Basic chat information
                - member_count (int): Number of members
                - administrators (list): List of administrators
                - bot_is_admin (bool): Whether the bot is an administrator
        """
        bot = self._ensure_bot()
        try:
            # Get bot info to check if bot is admin
            bot_info = await bot.get_me()
            bot_user_id = bot_info.id

            # Get all channel information in parallel
            chat_info = await self.get_chat(chat_id=chat_id)
            member_count_data = await self.get_chat_member_count(chat_id=chat_id)
            administrators_data = await self.get_chat_administrators(chat_id=chat_id)

            # Check if bot is admin
            bot_is_admin = False
            for admin in administrators_data["administrators"]:
                if admin["user"]["id"] == bot_user_id:
                    bot_is_admin = True
                    break

            return {
                "chat_info": chat_info,
                "member_count": member_count_data["member_count"],
                "administrators": administrators_data["administrators"],
                "bot_is_admin": bot_is_admin,
            }
        except TelegramError as exc:
            raise TelegramApiError(f"Failed to get channel statistics: {exc}") from exc


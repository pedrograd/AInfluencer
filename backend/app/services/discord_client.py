"""Discord API client for Discord Bot API integration."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DiscordApiError(RuntimeError):
    """Error raised when Discord API operations fail.
    
    This exception is raised for various Discord-related errors including
    connection failures, API errors, authentication failures, and
    other Discord API issues.
    """
    pass


class DiscordApiClient:
    """Client for interacting with Discord Bot API."""

    def __init__(
        self,
        bot_token: str | None = None,
    ) -> None:
        """
        Initialize Discord API client.

        Args:
            bot_token: Discord Bot Token from Discord Developer Portal.
        """
        self.bot_token = bot_token or getattr(settings, "discord_bot_token", None)
        
        self.base_url = "https://discord.com/api"
        self.api_version = "v10"
        
        if not self.bot_token:
            logger.warning("Discord Bot token not configured")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for Discord API requests.
        
        Returns:
            Dictionary containing authorization and content-type headers.
            
        Raises:
            DiscordApiError: If bot token is not configured.
        """
        if not self.bot_token:
            raise DiscordApiError("Discord Bot token not configured")
        
        return {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
            "User-Agent": "AInfluencer/1.0",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to Discord API.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path (without base URL).
            data: Optional request body data.
            
        Returns:
            JSON response from Discord API.
            
        Raises:
            DiscordApiError: If request fails or returns error.
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data else None,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text if exc.response else str(exc)
            raise DiscordApiError(
                f"Discord API request failed: {exc.response.status_code} - {error_detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise DiscordApiError(f"Discord API request error: {exc}") from exc

    def get_me(self) -> dict[str, Any]:
        """
        Get authenticated bot user information.

        Returns:
            Bot user information dictionary containing:
                - id (str): Bot user ID
                - username (str): Bot username
                - discriminator (str): Bot discriminator (legacy, may be "0")
                - avatar (str | None): Avatar hash
                - bot (bool): Whether this is a bot account
                - verified (bool): Whether the bot is verified
        """
        try:
            response = self._make_request("GET", "/users/@me")
            
            return {
                "id": response.get("id", ""),
                "username": response.get("username", ""),
                "discriminator": response.get("discriminator", "0"),
                "avatar": response.get("avatar"),
                "bot": response.get("bot", True),
                "verified": response.get("verified", False),
            }
        except Exception as exc:
            raise DiscordApiError(f"Failed to get bot info: {exc}") from exc

    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to Discord API by fetching authenticated bot info.

        Returns:
            Bot user information if connection is successful.

        Raises:
            DiscordApiError: If connection fails.
        """
        try:
            return self.get_me()
        except Exception as exc:
            raise DiscordApiError(f"Discord API connection test failed: {exc}") from exc

    def send_message(
        self,
        channel_id: str,
        content: str,
    ) -> dict[str, Any]:
        """
        Send a message to a Discord channel.

        Args:
            channel_id: Discord channel ID where the message will be sent.
            content: Message text content.

        Returns:
            Dictionary containing:
                - id (str): Message ID
                - channel_id (str): Channel ID
                - content (str): Message content
                - timestamp (str): Message timestamp

        Raises:
            DiscordApiError: If message sending fails or credentials are not configured.
        """
        if not channel_id:
            raise DiscordApiError("Channel ID is required")
        if not content:
            raise DiscordApiError("Message content is required")
        
        try:
            message_data = {
                "content": content,
            }
            
            response = self._make_request(
                "POST",
                f"/channels/{channel_id}/messages",
                data=message_data,
            )
            
            return {
                "id": response.get("id", ""),
                "channel_id": response.get("channel_id", channel_id),
                "content": response.get("content", content),
                "timestamp": response.get("timestamp", ""),
            }
        except DiscordApiError:
            raise
        except Exception as exc:
            raise DiscordApiError(f"Failed to send message: {exc}") from exc

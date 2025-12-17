"""Twitch API client for Twitch API integration."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TwitchApiError(RuntimeError):
    """Error raised when Twitch API operations fail.
    
    This exception is raised for various Twitch-related errors including
    connection failures, API errors, authentication failures, and
    other Twitch API issues.
    """
    pass


class TwitchApiClient:
    """Client for interacting with Twitch API."""

    def __init__(
        self,
        access_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        """
        Initialize Twitch API client.

        Args:
            access_token: Twitch Access Token for OAuth 2.0 authentication.
            client_id: Twitch API Client ID (for OAuth 2.0).
            client_secret: Twitch API Client Secret (for OAuth 2.0).
        """
        self.access_token = access_token or getattr(settings, "twitch_access_token", None)
        self.client_id = client_id or getattr(settings, "twitch_client_id", None)
        self.client_secret = client_secret or getattr(settings, "twitch_client_secret", None)
        
        self.base_url = "https://api.twitch.tv/helix"
        
        if not self.access_token:
            logger.warning("Twitch API access token not configured")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for Twitch API requests.
        
        Returns:
            Dictionary containing authorization and content-type headers.
            
        Raises:
            TwitchApiError: If access token or client ID is not configured.
        """
        if not self.access_token:
            raise TwitchApiError("Twitch API access token not configured")
        if not self.client_id:
            raise TwitchApiError("Twitch API client ID not configured")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Client-Id": self.client_id,
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to Twitch API.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path (without base URL).
            data: Optional request body data.
            params: Optional query parameters.
            
        Returns:
            JSON response from Twitch API.
            
        Raises:
            TwitchApiError: If request fails or returns error.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data else None,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text if exc.response else str(exc)
            raise TwitchApiError(
                f"Twitch API request failed: {exc.response.status_code} - {error_detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise TwitchApiError(f"Twitch API request error: {exc}") from exc

    def get_me(self) -> dict[str, Any]:
        """
        Get authenticated user information.

        Returns:
            User information dictionary containing:
                - id (str): User ID
                - login (str): Username
                - display_name (str): Display name
                - email (str | None): Email (if available)
                - profile_image_url (str | None): Profile image URL
                - broadcaster_type (str | None): Broadcaster type
                - description (str | None): User description
        """
        try:
            response = self._make_request("GET", "/users")
            data = response.get("data", [])
            
            if not data:
                raise TwitchApiError("No user data returned from Twitch API")
            
            user_info = data[0]
            
            return {
                "id": user_info.get("id", ""),
                "login": user_info.get("login", ""),
                "display_name": user_info.get("display_name", ""),
                "email": user_info.get("email"),
                "profile_image_url": user_info.get("profile_image_url"),
                "broadcaster_type": user_info.get("broadcaster_type"),
                "description": user_info.get("description"),
            }
        except Exception as exc:
            raise TwitchApiError(f"Failed to get user info: {exc}") from exc

    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to Twitch API by fetching authenticated user info.

        Returns:
            User information if connection is successful.

        Raises:
            TwitchApiError: If connection fails.
        """
        try:
            return self.get_me()
        except Exception as exc:
            raise TwitchApiError(f"Twitch API connection test failed: {exc}") from exc

    def get_stream_info(self, user_id: str | None = None) -> dict[str, Any]:
        """
        Get stream information for a user.

        Args:
            user_id: Optional user ID. If not provided, uses authenticated user.

        Returns:
            Dictionary containing:
                - stream_info (dict | None): Stream information if live, None otherwise
                - is_live (bool): Whether the stream is currently live

        Raises:
            TwitchApiError: If request fails.
        """
        try:
            if not user_id:
                # Get authenticated user ID first
                user_info = self.get_me()
                user_id = user_info.get("id")
            
            if not user_id:
                raise TwitchApiError("User ID is required")
            
            response = self._make_request("GET", "/streams", params={"user_id": user_id})
            data = response.get("data", [])
            
            if data:
                stream_info = data[0]
                return {
                    "stream_info": {
                        "id": stream_info.get("id"),
                        "user_id": stream_info.get("user_id"),
                        "user_name": stream_info.get("user_name"),
                        "game_id": stream_info.get("game_id"),
                        "game_name": stream_info.get("game_name"),
                        "type": stream_info.get("type"),
                        "title": stream_info.get("title"),
                        "viewer_count": stream_info.get("viewer_count"),
                        "started_at": stream_info.get("started_at"),
                        "language": stream_info.get("language"),
                        "thumbnail_url": stream_info.get("thumbnail_url"),
                    },
                    "is_live": True,
                }
            else:
                return {
                    "stream_info": None,
                    "is_live": False,
                }
        except Exception as exc:
            raise TwitchApiError(f"Failed to get stream info: {exc}") from exc

    def simulate_start_stream(
        self,
        title: str,
        game_id: str | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Simulate starting a stream (for testing/demo purposes).

        Note: This is a simulation endpoint. Actual stream starting requires
        OBS or streaming software. This endpoint returns mock data for
        demonstration purposes.

        Args:
            title: Stream title.
            game_id: Optional game/category ID.
            language: Stream language (default: "en").

        Returns:
            Dictionary containing simulated stream information.
        """
        try:
            user_info = self.get_me()
            
            # Return simulated stream data
            return {
                "status": "simulated",
                "message": "Stream start simulated. Actual streaming requires OBS or streaming software.",
                "stream_data": {
                    "user_id": user_info.get("id"),
                    "user_name": user_info.get("login"),
                    "title": title,
                    "game_id": game_id,
                    "language": language,
                    "is_live": True,
                    "simulated": True,
                },
            }
        except Exception as exc:
            raise TwitchApiError(f"Failed to simulate stream start: {exc}") from exc

    def simulate_stop_stream(self) -> dict[str, Any]:
        """
        Simulate stopping a stream (for testing/demo purposes).

        Note: This is a simulation endpoint. Actual stream stopping requires
        OBS or streaming software. This endpoint returns mock data for
        demonstration purposes.

        Returns:
            Dictionary containing simulated stream stop information.
        """
        try:
            user_info = self.get_me()
            
            return {
                "status": "simulated",
                "message": "Stream stop simulated. Actual streaming requires OBS or streaming software.",
                "stream_data": {
                    "user_id": user_info.get("id"),
                    "user_name": user_info.get("login"),
                    "is_live": False,
                    "simulated": True,
                },
            }
        except Exception as exc:
            raise TwitchApiError(f"Failed to simulate stream stop: {exc}") from exc

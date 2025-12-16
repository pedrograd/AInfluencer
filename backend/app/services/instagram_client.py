"""Instagram API client for Instagram Graph API integration."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class InstagramApiError(RuntimeError):
    """Error raised when Instagram API operations fail.
    
    This exception is raised for various Instagram-related errors including
    connection failures, API errors, authentication failures, and
    other Instagram API issues.
    """
    pass


class InstagramApiClient:
    """Client for interacting with Instagram Graph API."""

    BASE_URL = "https://graph.instagram.com"
    API_VERSION = "v21.0"

    def __init__(
        self,
        access_token: str | None = None,
        api_version: str | None = None,
    ) -> None:
        """
        Initialize Instagram API client.

        Args:
            access_token: Instagram access token. If not provided, uses settings.
            api_version: Instagram Graph API version. Defaults to v21.0.
        """
        self.access_token = access_token or getattr(settings, "instagram_access_token", None)
        self.api_version = api_version or self.API_VERSION
        self.base_url = f"{self.BASE_URL}/{self.api_version}"

        if not self.access_token:
            logger.warning("Instagram access token not configured")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to Instagram Graph API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.).
            endpoint: API endpoint path (without base URL).
            params: Query parameters.
            json_data: JSON body for POST/PUT requests.
            timeout: Request timeout in seconds.

        Returns:
            JSON response data.

        Raises:
            InstagramApiError: If the request fails or returns an error.
        """
        if not self.access_token:
            raise InstagramApiError("Instagram access token not configured")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add access token to params
        request_params = params or {}
        request_params["access_token"] = self.access_token

        with httpx.Client(timeout=timeout) as client:
            try:
                if method.upper() == "GET":
                    response = client.get(url, params=request_params)
                elif method.upper() == "POST":
                    response = client.post(url, params=request_params, json=json_data)
                elif method.upper() == "DELETE":
                    response = client.delete(url, params=request_params)
                else:
                    raise InstagramApiError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except httpx.RequestError as exc:
                raise InstagramApiError(
                    f"Unable to reach Instagram API at {url}: {exc}"
                ) from exc
            except httpx.HTTPStatusError as exc:
                error_data = {}
                try:
                    error_data = exc.response.json()
                except Exception:
                    pass
                
                error_message = error_data.get("error", {}).get("message", exc.response.text)
                raise InstagramApiError(
                    f"Instagram API error ({exc.response.status_code}): {error_message}"
                ) from exc

    def get_user_info(self, user_id: str = "me", fields: list[str] | None = None) -> dict[str, Any]:
        """
        Get Instagram user information.

        Args:
            user_id: Instagram user ID. Defaults to "me" for authenticated user.
            fields: List of fields to retrieve. Defaults to id, username, account_type.

        Returns:
            User information dictionary.
        """
        default_fields = ["id", "username", "account_type"]
        fields_param = ",".join(fields or default_fields)
        
        return self._make_request("GET", f"{user_id}", params={"fields": fields_param})

    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to Instagram API by fetching user info.

        Returns:
            User information if connection is successful.

        Raises:
            InstagramApiError: If connection fails.
        """
        try:
            return self.get_user_info()
        except Exception as exc:
            raise InstagramApiError(f"Instagram API connection test failed: {exc}") from exc


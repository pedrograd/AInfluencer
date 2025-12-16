"""Facebook Graph API client for Facebook Graph API integration."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Facebook Graph API base URL
GRAPH_API_BASE_URL = "https://graph.facebook.com"
GRAPH_API_VERSION = "v18.0"


class FacebookApiError(RuntimeError):
    """Error raised when Facebook Graph API operations fail.
    
    This exception is raised for various Facebook-related errors including
    connection failures, API errors, authentication failures, and
    other Facebook Graph API issues.
    """
    pass


class FacebookApiClient:
    """Client for interacting with Facebook Graph API."""

    def __init__(
        self,
        access_token: str | None = None,
        app_id: str | None = None,
        app_secret: str | None = None,
    ) -> None:
        """
        Initialize Facebook Graph API client.

        Args:
            access_token: Facebook Graph API access token (required for API calls).
            app_id: Facebook App ID (for OAuth and token management).
            app_secret: Facebook App Secret (for OAuth and token management).
        """
        self.access_token = access_token or getattr(settings, "facebook_access_token", None)
        self.app_id = app_id or getattr(settings, "facebook_app_id", None)
        self.app_secret = app_secret or getattr(settings, "facebook_app_secret", None)
        
        self.base_url = f"{GRAPH_API_BASE_URL}/{GRAPH_API_VERSION}"
        
        if not self.access_token:
            logger.warning("Facebook Graph API access token not configured")

    def _ensure_access_token(self) -> str:
        """Ensure Facebook access token is configured.
        
        Returns:
            Facebook access token.
            
        Raises:
            FacebookApiError: If access token is not configured.
        """
        if not self.access_token:
            raise FacebookApiError("Facebook Graph API access token not configured")
        return self.access_token

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to Facebook Graph API.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path (e.g., "/me").
            params: Query parameters.
            json_data: JSON body data (for POST requests).
        
        Returns:
            JSON response from API.
            
        Raises:
            FacebookApiError: If request fails.
        """
        access_token = self._ensure_access_token()
        
        # Add access token to params
        if params is None:
            params = {}
        params["access_token"] = access_token
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = client.get(url, params=params)
                elif method.upper() == "POST":
                    response = client.post(url, params=params, json=json_data)
                else:
                    raise FacebookApiError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = "Unknown error"
            try:
                error_data = exc.response.json()
                error_detail = error_data.get("error", {}).get("message", str(exc))
            except Exception:
                error_detail = str(exc)
            raise FacebookApiError(f"Facebook Graph API error: {error_detail}") from exc
        except httpx.RequestError as exc:
            raise FacebookApiError(f"Facebook Graph API request failed: {exc}") from exc

    def get_me(self) -> dict[str, Any]:
        """
        Get authenticated user/page information.

        Returns:
            User/page information dictionary containing:
                - id (str): User/Page ID
                - name (str): Display name
                - email (str, optional): Email address (if available)
        """
        try:
            response = self._make_request("GET", "/me", params={"fields": "id,name,email"})
            return {
                "id": response.get("id"),
                "name": response.get("name"),
                "email": response.get("email"),
            }
        except FacebookApiError:
            raise
        except Exception as exc:
            raise FacebookApiError(f"Failed to get user info: {exc}") from exc

    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to Facebook Graph API by fetching authenticated user/page info.

        Returns:
            User/page information if connection is successful.

        Raises:
            FacebookApiError: If connection fails.
        """
        try:
            return self.get_me()
        except Exception as exc:
            raise FacebookApiError(f"Facebook Graph API connection test failed: {exc}") from exc


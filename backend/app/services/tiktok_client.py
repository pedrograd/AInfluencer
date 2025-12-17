"""TikTok API client for TikTok API integration."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TikTokApiError(RuntimeError):
    """Error raised when TikTok API operations fail.
    
    This exception is raised for various TikTok-related errors including
    connection failures, API errors, authentication failures, and
    other TikTok API issues.
    """
    pass


class TikTokApiClient:
    """Client for interacting with TikTok API."""

    def __init__(
        self,
        access_token: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        """
        Initialize TikTok API client.

        Args:
            access_token: TikTok Access Token for OAuth 2.0 authentication.
            client_key: TikTok API Client Key (for OAuth 2.0).
            client_secret: TikTok API Client Secret (for OAuth 2.0).
        """
        self.access_token = access_token or getattr(settings, "tiktok_access_token", None)
        self.client_key = client_key or getattr(settings, "tiktok_client_key", None)
        self.client_secret = client_secret or getattr(settings, "tiktok_client_secret", None)
        
        self.base_url = "https://open.tiktokapis.com"
        self.api_version = "v2"
        
        if not self.access_token:
            logger.warning("TikTok API access token not configured")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for TikTok API requests.
        
        Returns:
            Dictionary containing authorization and content-type headers.
            
        Raises:
            TikTokApiError: If access token is not configured.
        """
        if not self.access_token:
            raise TikTokApiError("TikTok API access token not configured")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to TikTok API.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path (without base URL).
            data: Optional request body data.
            
        Returns:
            JSON response from TikTok API.
            
        Raises:
            TikTokApiError: If request fails or returns error.
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
            raise TikTokApiError(
                f"TikTok API request failed: {exc.response.status_code} - {error_detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise TikTokApiError(f"TikTok API request error: {exc}") from exc

    def get_me(self) -> dict[str, Any]:
        """
        Get authenticated user information.

        Returns:
            User information dictionary containing:
                - open_id (str): User Open ID
                - union_id (str | None): User Union ID (if available)
                - avatar_url (str | None): User avatar URL
                - display_name (str | None): User display name
        """
        try:
            response = self._make_request("GET", "/user/info/")
            data = response.get("data", {})
            user_info = data.get("user", {})
            
            return {
                "open_id": user_info.get("open_id", ""),
                "union_id": user_info.get("union_id"),
                "avatar_url": user_info.get("avatar_url"),
                "display_name": user_info.get("display_name"),
            }
        except Exception as exc:
            raise TikTokApiError(f"Failed to get user info: {exc}") from exc

    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to TikTok API by fetching authenticated user info.

        Returns:
            User information if connection is successful.

        Raises:
            TikTokApiError: If connection fails.
        """
        try:
            return self.get_me()
        except Exception as exc:
            raise TikTokApiError(f"TikTok API connection test failed: {exc}") from exc

    def upload_video(
        self,
        video_path: str,
        caption: str | None = None,
        privacy_level: str = "PUBLIC_TO_EVERYONE",
    ) -> dict[str, Any]:
        """
        Upload a video to TikTok.

        Args:
            video_path: Path to video file to upload.
            caption: Optional caption text for the video.
            privacy_level: Privacy level (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY).

        Returns:
            Dictionary containing:
                - publish_id (str): Publish ID for the uploaded video
                - upload_url (str): URL for video upload (if two-phase upload)

        Raises:
            TikTokApiError: If upload fails or credentials are not configured.
        """
        if not video_path:
            raise TikTokApiError("Video path is required")
        
        # TikTok video upload is a multi-step process:
        # 1. Initialize upload (get upload URL)
        # 2. Upload video file
        # 3. Publish video
        
        try:
            # Step 1: Initialize upload
            init_data = {
                "source_info": {
                    "source": "FILE_UPLOAD",
                },
                "post_info": {
                    "title": caption or "",
                    "privacy_level": privacy_level,
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000,
                },
            }
            
            init_response = self._make_request("POST", "/video/init/", data=init_data)
            publish_id = init_response.get("data", {}).get("publish_id")
            upload_url = init_response.get("data", {}).get("upload_url")
            
            if not publish_id:
                raise TikTokApiError("Failed to initialize TikTok video upload")
            
            # Step 2: Upload video file (would need to read file and upload)
            # This is a simplified version - actual implementation would handle file upload
            # For now, return the publish_id and upload_url for manual completion
            
            return {
                "publish_id": publish_id,
                "upload_url": upload_url,
                "status": "initialized",
                "message": "Video upload initialized. Use upload_url to complete file upload, then call publish_video with publish_id.",
            }
        except TikTokApiError:
            raise
        except Exception as exc:
            raise TikTokApiError(f"Failed to upload video: {exc}") from exc

    def publish_video(self, publish_id: str) -> dict[str, Any]:
        """
        Publish an uploaded video to TikTok.

        Args:
            publish_id: Publish ID from upload_video initialization.

        Returns:
            Dictionary containing:
                - publish_id (str): Publish ID
                - status (str): Publication status

        Raises:
            TikTokApiError: If publishing fails.
        """
        if not publish_id:
            raise TikTokApiError("Publish ID is required")
        
        try:
            response = self._make_request("POST", f"/video/publish/", data={"publish_id": publish_id})
            data = response.get("data", {})
            
            return {
                "publish_id": publish_id,
                "status": data.get("status", "unknown"),
            }
        except Exception as exc:
            raise TikTokApiError(f"Failed to publish video: {exc}") from exc

"""LinkedIn API client for LinkedIn API integration."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LinkedInApiError(RuntimeError):
    """Error raised when LinkedIn API operations fail.
    
    This exception is raised for various LinkedIn-related errors including
    connection failures, API errors, authentication failures, and
    other LinkedIn API issues.
    """
    pass


class LinkedInApiClient:
    """Client for interacting with LinkedIn API."""

    def __init__(
        self,
        access_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        """
        Initialize LinkedIn API client.

        Args:
            access_token: LinkedIn Access Token for OAuth 2.0 authentication.
            client_id: LinkedIn API Client ID (for OAuth 2.0).
            client_secret: LinkedIn API Client Secret (for OAuth 2.0).
        """
        self.access_token = access_token or getattr(settings, "linkedin_access_token", None)
        self.client_id = client_id or getattr(settings, "linkedin_client_id", None)
        self.client_secret = client_secret or getattr(settings, "linkedin_client_secret", None)
        
        self.base_url = "https://api.linkedin.com"
        self.api_version = "v2"
        
        if not self.access_token:
            logger.warning("LinkedIn API access token not configured")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for LinkedIn API requests.
        
        Returns:
            Dictionary containing authorization and content-type headers.
            
        Raises:
            LinkedInApiError: If access token is not configured.
        """
        if not self.access_token:
            raise LinkedInApiError("LinkedIn API access token not configured")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to LinkedIn API.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path (without base URL).
            data: Optional request body data.
            
        Returns:
            JSON response from LinkedIn API.
            
        Raises:
            LinkedInApiError: If request fails or returns error.
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
            raise LinkedInApiError(
                f"LinkedIn API request failed: {exc.response.status_code} - {error_detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise LinkedInApiError(f"LinkedIn API request error: {exc}") from exc

    def get_me(self) -> dict[str, Any]:
        """
        Get authenticated user information.

        Returns:
            User information dictionary containing:
                - id (str): User ID
                - firstName (dict): First name with localized string
                - lastName (dict): Last name with localized string
                - profilePicture (dict): Profile picture URL
        """
        try:
            # LinkedIn v2 API - get user profile
            # Using projection to get specific fields
            projection = "(id,firstName,lastName,profilePicture(displayImage~:playableStreams))"
            response = self._make_request("GET", f"/me?projection={projection}")
            
            return {
                "id": response.get("id", ""),
                "firstName": response.get("firstName", {}).get("localized", {}),
                "lastName": response.get("lastName", {}).get("localized", {}),
                "profilePicture": response.get("profilePicture", {}),
            }
        except Exception as exc:
            raise LinkedInApiError(f"Failed to get user info: {exc}") from exc

    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to LinkedIn API by fetching authenticated user info.

        Returns:
            User information if connection is successful.

        Raises:
            LinkedInApiError: If connection fails.
        """
        try:
            return self.get_me()
        except Exception as exc:
            raise LinkedInApiError(f"LinkedIn API connection test failed: {exc}") from exc

    def create_post(
        self,
        text: str,
        visibility: str = "PUBLIC",
    ) -> dict[str, Any]:
        """
        Create a post on LinkedIn.

        Args:
            text: Post text content.
            visibility: Post visibility (PUBLIC, CONNECTIONS).

        Returns:
            Dictionary containing:
                - id (str): Post ID
                - activity_id (str): Activity ID
                - status (str): Post status

        Raises:
            LinkedInApiError: If post creation fails or credentials are not configured.
        """
        if not text:
            raise LinkedInApiError("Post text is required")
        
        try:
            # LinkedIn v2 API - create UGC post
            # First, get the authenticated user's URN
            user_info = self.get_me()
            author_urn = f"urn:li:person:{user_info.get('id')}"
            
            # Create post data
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text,
                        },
                        "shareMediaCategory": "NONE",
                    },
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility,
                },
            }
            
            response = self._make_request("POST", "/ugcPosts", data=post_data)
            
            return {
                "id": response.get("id", ""),
                "activity_id": response.get("activity", ""),
                "status": "published",
            }
        except LinkedInApiError:
            raise
        except Exception as exc:
            raise LinkedInApiError(f"Failed to create post: {exc}") from exc

    def create_article(
        self,
        title: str,
        content: str,
    ) -> dict[str, Any]:
        """
        Create an article on LinkedIn (professional long-form content).

        Args:
            title: Article title.
            content: Article content (HTML or plain text).

        Returns:
            Dictionary containing:
                - id (str): Article ID
                - status (str): Article status

        Raises:
            LinkedInApiError: If article creation fails.
        """
        if not title or not content:
            raise LinkedInApiError("Article title and content are required")
        
        try:
            # LinkedIn v2 API - create article
            # Get the authenticated user's URN
            user_info = self.get_me()
            author_urn = f"urn:li:person:{user_info.get('id')}"
            
            # Create article data
            article_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ArticleContent": {
                        "title": title,
                        "body": {
                            "text": content,
                        },
                    },
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
                },
            }
            
            response = self._make_request("POST", "/ugcPosts", data=article_data)
            
            return {
                "id": response.get("id", ""),
                "status": "published",
            }
        except LinkedInApiError:
            raise
        except Exception as exc:
            raise LinkedInApiError(f"Failed to create article: {exc}") from exc

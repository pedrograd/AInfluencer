"""YouTube Data API client for YouTube API integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# YouTube Data API v3 scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]


class YouTubeApiError(RuntimeError):
    """Error raised when YouTube Data API operations fail.
    
    This exception is raised for various YouTube-related errors including
    connection failures, API errors, authentication failures, and
    other YouTube Data API issues.
    """
    pass


class YouTubeApiClient:
    """Client for interacting with YouTube Data API v3."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        """
        Initialize YouTube Data API client.

        Args:
            client_id: Google OAuth 2.0 Client ID (for OAuth authentication).
            client_secret: Google OAuth 2.0 Client Secret (for OAuth authentication).
            refresh_token: OAuth 2.0 refresh token (for authenticated requests).
        """
        self.client_id = client_id or getattr(settings, "youtube_client_id", None)
        self.client_secret = client_secret or getattr(settings, "youtube_client_secret", None)
        self.refresh_token = refresh_token or getattr(settings, "youtube_refresh_token", None)
        
        self._service: Any | None = None
        
        if not all([self.client_id, self.client_secret]):
            logger.warning("YouTube OAuth 2.0 credentials not fully configured")

    def _get_credentials(self) -> Credentials:
        """Get OAuth 2.0 credentials for YouTube API.
        
        Returns:
            OAuth 2.0 credentials object.
            
        Raises:
            YouTubeApiError: If credentials are not configured or authentication fails.
        """
        if not all([self.client_id, self.client_secret]):
            raise YouTubeApiError("YouTube OAuth 2.0 credentials (client_id, client_secret) not configured")
        
        # Create credentials from refresh token if available
        if self.refresh_token:
            creds = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            
            # Refresh the token if needed
            if not creds.valid:
                try:
                    creds.refresh(Request())
                except Exception as exc:
                    raise YouTubeApiError(f"Failed to refresh YouTube OAuth token: {exc}") from exc
            
            return creds
        else:
            raise YouTubeApiError("YouTube refresh token not configured. Please complete OAuth flow to obtain refresh token.")

    def _get_service(self):
        """Get YouTube Data API service instance.
        
        Returns:
            YouTube Data API service instance.
            
        Raises:
            YouTubeApiError: If service creation fails.
        """
        if self._service is None:
            try:
                creds = self._get_credentials()
                self._service = build("youtube", "v3", credentials=creds)
            except YouTubeApiError:
                raise
            except Exception as exc:
                raise YouTubeApiError(f"Failed to create YouTube API service: {exc}") from exc
        
        return self._service

    def get_me(self) -> dict[str, Any]:
        """
        Get authenticated YouTube channel information.

        Returns:
            Channel information dictionary containing:
                - id (str): Channel ID
                - title (str): Channel title
                - description (str): Channel description
                - custom_url (str, optional): Custom URL
                - subscriber_count (int, optional): Subscriber count
        """
        try:
            service = self._get_service()
            request = service.channels().list(
                part="snippet,statistics,contentDetails",
                mine=True,
            )
            response = request.execute()
            
            if not response.get("items"):
                raise YouTubeApiError("No channel found for authenticated user")
            
            channel = response["items"][0]
            snippet = channel.get("snippet", {})
            statistics = channel.get("statistics", {})
            
            return {
                "id": channel.get("id"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "custom_url": snippet.get("customUrl"),
                "subscriber_count": int(statistics.get("subscriberCount", 0)) if statistics.get("subscriberCount") else None,
            }
        except HttpError as exc:
            error_detail = exc.error_details[0].get("message", str(exc)) if exc.error_details else str(exc)
            raise YouTubeApiError(f"YouTube API error: {error_detail}") from exc
        except YouTubeApiError:
            raise
        except Exception as exc:
            raise YouTubeApiError(f"Failed to get channel info: {exc}") from exc

    def test_connection(self) -> dict[str, Any]:
        """
        Test connection to YouTube Data API by fetching authenticated channel info.

        Returns:
            Channel information if connection is successful.

        Raises:
            YouTubeApiError: If connection fails.
        """
        try:
            return self.get_me()
        except Exception as exc:
            raise YouTubeApiError(f"YouTube Data API connection test failed: {exc}") from exc

    def upload_video(
        self,
        video_path: str | Path,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        category_id: str = "22",  # Default: People & Blogs
        privacy_status: str = "private",  # private, unlisted, public
        thumbnail_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Upload a video to YouTube.

        Args:
            video_path: Path to the video file to upload.
            title: Video title (required, max 100 characters).
            description: Video description (optional).
            tags: List of tags for the video (optional).
            category_id: YouTube category ID (default: "22" for People & Blogs).
            privacy_status: Privacy status - "private", "unlisted", or "public" (default: "private").
            thumbnail_path: Path to thumbnail image file (optional).

        Returns:
            Dictionary containing:
                - video_id (str): YouTube video ID
                - video_url (str): URL to the uploaded video
                - title (str): Video title
                - description (str): Video description
                - privacy_status (str): Privacy status

        Raises:
            YouTubeApiError: If upload fails.
        """
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            raise YouTubeApiError(f"Video file not found: {video_path}")

        if not title or len(title) > 100:
            raise YouTubeApiError("Video title is required and must be 100 characters or less")

        if privacy_status not in ["private", "unlisted", "public"]:
            raise YouTubeApiError(f"Invalid privacy_status: {privacy_status}. Must be 'private', 'unlisted', or 'public'")

        try:
            service = self._get_service()

            # Build video metadata
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": category_id,
                },
                "status": {
                    "privacyStatus": privacy_status,
                },
            }

            # Create media file upload object
            media = MediaFileUpload(
                str(video_path_obj),
                chunksize=-1,  # Use resumable upload
                resumable=True,
            )

            # Initialize the upload
            insert_request = service.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            # Execute the upload (resumable)
            logger.info(f"Starting YouTube video upload: {video_path_obj.name}")
            response = None
            error = None
            retry = 0
            while response is None:
                try:
                    status, response = insert_request.next_chunk()
                    if response is not None:
                        if "id" in response:
                            video_id = response["id"]
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            logger.info(f"YouTube video uploaded successfully: {video_id}")
                            
                            # Upload thumbnail if provided
                            if thumbnail_path:
                                thumbnail_path_obj = Path(thumbnail_path)
                                if thumbnail_path_obj.exists():
                                    try:
                                        service.thumbnails().set(
                                            videoId=video_id,
                                            media_body=MediaFileUpload(str(thumbnail_path_obj)),
                                        ).execute()
                                        logger.info(f"Thumbnail uploaded for video: {video_id}")
                                    except Exception as thumb_exc:
                                        logger.warning(f"Failed to upload thumbnail: {thumb_exc}")
                            
                            return {
                                "video_id": video_id,
                                "video_url": video_url,
                                "title": title,
                                "description": description,
                                "privacy_status": privacy_status,
                            }
                        else:
                            raise YouTubeApiError(f"YouTube upload response missing video ID: {response}")
                except HttpError as exc:
                    if exc.resp.status in [500, 502, 503, 504]:
                        # Retry on server errors
                        retry += 1
                        if retry > 3:
                            error = exc
                            break
                        logger.warning(f"YouTube upload retry {retry}/3 due to server error: {exc}")
                    else:
                        error = exc
                        break
                except Exception as exc:
                    error = exc
                    break

            if error:
                error_detail = error.error_details[0].get("message", str(error)) if hasattr(error, "error_details") and error.error_details else str(error)
                raise YouTubeApiError(f"YouTube video upload failed: {error_detail}") from error

            raise YouTubeApiError("YouTube video upload failed: No response received")

        except HttpError as exc:
            error_detail = exc.error_details[0].get("message", str(exc)) if exc.error_details else str(exc)
            raise YouTubeApiError(f"YouTube API error during upload: {error_detail}") from exc
        except YouTubeApiError:
            raise
        except Exception as exc:
            raise YouTubeApiError(f"Failed to upload video to YouTube: {exc}") from exc


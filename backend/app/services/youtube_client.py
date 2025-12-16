"""YouTube Data API client for YouTube API integration."""

from __future__ import annotations

import subprocess
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

    def _get_video_metadata(self, video_path: Path) -> dict[str, Any]:
        """
        Get video metadata (duration, width, height) using ffprobe.
        
        Args:
            video_path: Path to video file.
            
        Returns:
            Dictionary containing:
                - duration (float | None): Video duration in seconds, None if unavailable
                - width (int | None): Video width in pixels, None if unavailable
                - height (int | None): Video height in pixels, None if unavailable
                - aspect_ratio (str | None): Aspect ratio (e.g., "9:16"), None if unavailable
        """
        metadata = {
            "duration": None,
            "width": None,
            "height": None,
            "aspect_ratio": None,
        }
        
        try:
            # Get duration
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                try:
                    metadata["duration"] = float(result.stdout.strip())
                except ValueError:
                    pass
            
            # Get video dimensions
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    try:
                        width = int(lines[0].strip())
                        height = int(lines[1].strip())
                        metadata["width"] = width
                        metadata["height"] = height
                        
                        # Calculate aspect ratio (simplified to common ratios)
                        if width > 0 and height > 0:
                            ratio = width / height
                            # Check for 9:16 (0.5625) with tolerance
                            if abs(ratio - 0.5625) < 0.1:
                                metadata["aspect_ratio"] = "9:16"
                            # Check for 16:9 (1.777...) with tolerance
                            elif abs(ratio - 1.777) < 0.1:
                                metadata["aspect_ratio"] = "16:9"
                            else:
                                metadata["aspect_ratio"] = f"{width}:{height}"
                    except (ValueError, IndexError):
                        pass
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # ffprobe not available or failed - metadata will be None
            pass
        except Exception:
            # Any other error - metadata will be None
            pass
        
        return metadata

    def upload_short(
        self,
        video_path: str | Path,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        privacy_status: str = "private",  # private, unlisted, public
        thumbnail_path: str | Path | None = None,
        validate_duration: bool = True,
        validate_aspect_ratio: bool = True,
    ) -> dict[str, Any]:
        """
        Upload a YouTube Short (vertical video, 60 seconds or less).
        
        YouTube Shorts are automatically detected by YouTube when videos meet these criteria:
        - Duration: 60 seconds or less
        - Aspect ratio: Vertical (9:16 recommended)
        - Has "#Shorts" in title or description (optional but recommended)
        
        Args:
            video_path: Path to the video file to upload.
            title: Video title (required, max 100 characters). Should include "#Shorts" for best results.
            description: Video description (optional). Can include "#Shorts" tag.
            tags: List of tags for the video (optional). "#Shorts" will be automatically added if not present.
            privacy_status: Privacy status - "private", "unlisted", or "public" (default: "private").
            thumbnail_path: Path to thumbnail image file (optional).
            validate_duration: Whether to validate video duration is 60 seconds or less (default: True).
            validate_aspect_ratio: Whether to validate aspect ratio is vertical (default: True).
        
        Returns:
            Dictionary containing:
                - video_id (str): YouTube video ID
                - video_url (str): URL to the uploaded video
                - title (str): Video title
                - description (str): Video description
                - privacy_status (str): Privacy status
                - is_short (bool): Whether video meets Shorts criteria
        
        Raises:
            YouTubeApiError: If upload fails or validation fails.
        """
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            raise YouTubeApiError(f"Video file not found: {video_path}")

        if not title or len(title) > 100:
            raise YouTubeApiError("Video title is required and must be 100 characters or less")

        if privacy_status not in ["private", "unlisted", "public"]:
            raise YouTubeApiError(f"Invalid privacy_status: {privacy_status}. Must be 'private', 'unlisted', or 'public'")

        # Validate video metadata if requested
        metadata = self._get_video_metadata(video_path_obj)
        
        if validate_duration and metadata.get("duration") is not None:
            duration = metadata["duration"]
            if duration > 60:
                raise YouTubeApiError(
                    f"YouTube Shorts must be 60 seconds or less. Video duration: {duration:.2f} seconds"
                )
            if duration < 1:
                raise YouTubeApiError(
                    f"YouTube Shorts must be at least 1 second. Video duration: {duration:.2f} seconds"
                )
        elif validate_duration:
            logger.warning("Cannot validate video duration (ffprobe not available). Uploading anyway.")

        if validate_aspect_ratio and metadata.get("aspect_ratio") is not None:
            aspect_ratio = metadata["aspect_ratio"]
            if aspect_ratio != "9:16":
                logger.warning(
                    f"Video aspect ratio is {aspect_ratio}, not 9:16. "
                    "YouTube may not recognize this as a Short. Recommended: 9:16 (vertical)."
                )
        elif validate_aspect_ratio:
            logger.warning("Cannot validate aspect ratio (ffprobe not available). Uploading anyway.")

        # Ensure "#Shorts" is in title or description
        shorts_tag = "#Shorts"
        has_shorts_in_title = shorts_tag.lower() in title.lower()
        has_shorts_in_description = shorts_tag.lower() in description.lower()
        
        if not has_shorts_in_title and not has_shorts_in_description:
            logger.warning(
                f"Title and description don't contain '{shorts_tag}'. "
                "Adding '#Shorts' tag for better Shorts detection."
            )
            # Add to description if there's room
            if description:
                description = f"{description} {shorts_tag}"
            else:
                description = shorts_tag

        # Ensure "#Shorts" is in tags
        tags_list = tags or []
        if not any(tag.lower() == "shorts" or shorts_tag.lower() in tag.lower() for tag in tags_list):
            tags_list.append("Shorts")

        # Use category 22 (People & Blogs) which is common for Shorts
        category_id = "22"

        try:
            # Use the existing upload_video method with Shorts-optimized settings
            result = self.upload_video(
                video_path=video_path_obj,
                title=title,
                description=description,
                tags=tags_list,
                category_id=category_id,
                privacy_status=privacy_status,
                thumbnail_path=thumbnail_path,
            )
            
            # Add Shorts indicator to result
            result["is_short"] = True
            
            return result
        except YouTubeApiError:
            raise
        except Exception as exc:
            raise YouTubeApiError(f"Failed to upload YouTube Short: {exc}") from exc


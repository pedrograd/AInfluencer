"""Instagram posting service using instagrapi library.

This service handles posting images, reels, and stories to Instagram
using the instagrapi library (unofficial but stable Instagram API).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes

from app.core.logging import get_logger

logger = get_logger(__name__)


class InstagramPostingError(RuntimeError):
    """Error raised when Instagram posting operations fail."""

    pass


class InstagramPostingService:
    """Service for posting content to Instagram using instagrapi."""

    def __init__(self, username: str | None = None, password: str | None = None, session_file: str | None = None):
        """
        Initialize Instagram posting service.

        Args:
            username: Instagram username for authentication.
            password: Instagram password for authentication.
            session_file: Path to session file for persistent login (optional).
        """
        self.username = username
        self.password = password
        self.session_file = session_file
        self.client: Client | None = None

    def _get_client(self) -> Client:
        """
        Get or create Instagram client instance.

        Returns:
            Authenticated Instagram client.

        Raises:
            InstagramPostingError: If authentication fails.
        """
        if self.client is not None:
            return self.client

        if not self.username or not self.password:
            raise InstagramPostingError("Instagram username and password are required")

        self.client = Client()

        # Load session if available
        if self.session_file and Path(self.session_file).exists():
            try:
                self.client.load_settings(self.session_file)
                self.client.login(self.username, self.password)
                logger.info(f"Loaded Instagram session from {self.session_file}")
            except Exception as exc:
                logger.warning(f"Failed to load session, creating new login: {exc}")
                self._login()
        else:
            self._login()

        # Save session if session_file is provided
        if self.session_file:
            try:
                self.client.dump_settings(self.session_file)
            except Exception as exc:
                logger.warning(f"Failed to save session: {exc}")

        return self.client

    def _login(self) -> None:
        """Perform Instagram login."""
        if not self.client:
            raise InstagramPostingError("Client not initialized")

        try:
            self.client.login(self.username, self.password)
            logger.info(f"Successfully logged in to Instagram as {self.username}")
        except LoginRequired as exc:
            raise InstagramPostingError(f"Instagram login required: {exc}") from exc
        except PleaseWaitFewMinutes as exc:
            raise InstagramPostingError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            raise InstagramPostingError(f"Instagram login failed: {exc}") from exc

    def post_image(
        self,
        image_path: str | Path,
        caption: str = "",
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Post a single image to Instagram feed.

        Args:
            image_path: Path to the image file.
            caption: Post caption text.
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).

        Returns:
            Dictionary with post information including platform_post_id and platform_post_url.

        Raises:
            InstagramPostingError: If posting fails.
        """
        try:
            client = self._get_client()
            image_path = Path(image_path)

            if not image_path.exists():
                raise InstagramPostingError(f"Image file not found: {image_path}")

            # Build caption with hashtags and mentions
            full_caption = caption
            if mentions:
                mention_text = " ".join([f"@{m}" for m in mentions])
                full_caption = f"{full_caption} {mention_text}".strip()
            if hashtags:
                hashtag_text = " ".join([f"#{h}" for h in hashtags])
                full_caption = f"{full_caption} {hashtag_text}".strip()

            # Post image
            media = client.photo_upload(str(image_path), caption=full_caption)

            logger.info(f"Successfully posted image to Instagram: {media.id}")

            return {
                "platform_post_id": str(media.id),
                "platform_post_url": f"https://www.instagram.com/p/{media.code}/",
                "media_type": "photo",
                "media": media.dict() if hasattr(media, "dict") else str(media),
            }

        except PleaseWaitFewMinutes as exc:
            raise InstagramPostingError(
                f"Instagram rate limit: Please wait a few minutes: {exc}"
            ) from exc
        except Exception as exc:
            raise InstagramPostingError(f"Failed to post image to Instagram: {exc}") from exc

    def post_carousel(
        self,
        image_paths: list[str | Path],
        caption: str = "",
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Post multiple images as a carousel to Instagram feed.

        Args:
            image_paths: List of paths to image files (2-10 images).
            caption: Post caption text.
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).

        Returns:
            Dictionary with post information including platform_post_id and platform_post_url.

        Raises:
            InstagramPostingError: If posting fails.
        """
        try:
            client = self._get_client()

            if len(image_paths) < 2:
                raise InstagramPostingError("Carousel requires at least 2 images")
            if len(image_paths) > 10:
                raise InstagramPostingError("Carousel can have at most 10 images")

            # Validate all images exist
            image_paths = [Path(p) for p in image_paths]
            for path in image_paths:
                if not path.exists():
                    raise InstagramPostingError(f"Image file not found: {path}")

            # Build caption with hashtags and mentions
            full_caption = caption
            if mentions:
                mention_text = " ".join([f"@{m}" for m in mentions])
                full_caption = f"{full_caption} {mention_text}".strip()
            if hashtags:
                hashtag_text = " ".join([f"#{h}" for h in hashtags])
                full_caption = f"{full_caption} {hashtag_text}".strip()

            # Post carousel
            media = client.album_upload([str(p) for p in image_paths], caption=full_caption)

            logger.info(f"Successfully posted carousel to Instagram: {media.id}")

            return {
                "platform_post_id": str(media.id),
                "platform_post_url": f"https://www.instagram.com/p/{media.code}/",
                "media_type": "carousel",
                "media": media.dict() if hasattr(media, "dict") else str(media),
            }

        except PleaseWaitFewMinutes as exc:
            raise InstagramPostingError(
                f"Instagram rate limit: Please wait a few minutes: {exc}"
            ) from exc
        except Exception as exc:
            raise InstagramPostingError(f"Failed to post carousel to Instagram: {exc}") from exc

    def post_reel(
        self,
        video_path: str | Path,
        caption: str = "",
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
        thumbnail_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Post a reel (short video) to Instagram.

        Args:
            video_path: Path to the video file.
            caption: Post caption text.
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).
            thumbnail_path: Path to thumbnail image (optional).

        Returns:
            Dictionary with post information including platform_post_id and platform_post_url.

        Raises:
            InstagramPostingError: If posting fails.
        """
        try:
            client = self._get_client()
            video_path = Path(video_path)

            if not video_path.exists():
                raise InstagramPostingError(f"Video file not found: {video_path}")

            # Build caption with hashtags and mentions
            full_caption = caption
            if mentions:
                mention_text = " ".join([f"@{m}" for m in mentions])
                full_caption = f"{full_caption} {mention_text}".strip()
            if hashtags:
                hashtag_text = " ".join([f"#{h}" for h in hashtags])
                full_caption = f"{full_caption} {hashtag_text}".strip()

            # Post reel
            thumbnail = str(thumbnail_path) if thumbnail_path and Path(thumbnail_path).exists() else None
            media = client.clip_upload(str(video_path), caption=full_caption, thumbnail=thumbnail)

            logger.info(f"Successfully posted reel to Instagram: {media.id}")

            return {
                "platform_post_id": str(media.id),
                "platform_post_url": f"https://www.instagram.com/reel/{media.code}/",
                "media_type": "reel",
                "media": media.dict() if hasattr(media, "dict") else str(media),
            }

        except PleaseWaitFewMinutes as exc:
            raise InstagramPostingError(
                f"Instagram rate limit: Please wait a few minutes: {exc}"
            ) from exc
        except Exception as exc:
            raise InstagramPostingError(f"Failed to post reel to Instagram: {exc}") from exc

    def post_story(
        self,
        image_path: str | Path | None = None,
        video_path: str | Path | None = None,
        caption: str | None = None,
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Post a story (image or video) to Instagram.

        Args:
            image_path: Path to the image file (for image story).
            video_path: Path to the video file (for video story).
            caption: Story caption/text overlay (optional).
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).

        Returns:
            Dictionary with post information including platform_post_id.

        Raises:
            InstagramPostingError: If posting fails.
        """
        try:
            client = self._get_client()

            if not image_path and not video_path:
                raise InstagramPostingError("Either image_path or video_path must be provided")

            if image_path and video_path:
                raise InstagramPostingError("Cannot provide both image_path and video_path")

            # Build caption with hashtags and mentions
            full_caption = caption or ""
            if mentions:
                mention_text = " ".join([f"@{m}" for m in mentions])
                full_caption = f"{full_caption} {mention_text}".strip()
            if hashtags:
                hashtag_text = " ".join([f"#{h}" for h in hashtags])
                full_caption = f"{full_caption} {hashtag_text}".strip()

            # Post story
            if image_path:
                image_path = Path(image_path)
                if not image_path.exists():
                    raise InstagramPostingError(f"Image file not found: {image_path}")
                media = client.photo_upload_to_story(str(image_path), caption=full_caption)
                media_type = "story_photo"
            else:
                video_path = Path(video_path)
                if not video_path.exists():
                    raise InstagramPostingError(f"Video file not found: {video_path}")
                media = client.video_upload_to_story(str(video_path), caption=full_caption)
                media_type = "story_video"

            logger.info(f"Successfully posted story to Instagram: {media.id}")

            return {
                "platform_post_id": str(media.id),
                "platform_post_url": None,  # Stories don't have permanent URLs
                "media_type": media_type,
                "media": media.dict() if hasattr(media, "dict") else str(media),
            }

        except PleaseWaitFewMinutes as exc:
            raise InstagramPostingError(
                f"Instagram rate limit: Please wait a few minutes: {exc}"
            ) from exc
        except Exception as exc:
            raise InstagramPostingError(f"Failed to post story to Instagram: {exc}") from exc

    def close(self) -> None:
        """Close the Instagram client and cleanup resources."""
        if self.client:
            try:
                # Save session before closing
                if self.session_file:
                    self.client.dump_settings(self.session_file)
            except Exception as exc:
                logger.warning(f"Failed to save session on close: {exc}")
            self.client = None


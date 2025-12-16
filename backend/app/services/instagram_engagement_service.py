"""Instagram engagement service using instagrapi library.

This service handles engagement actions (comments, likes, follows) on Instagram
using the instagrapi library (unofficial but stable Instagram API).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes

from app.core.logging import get_logger

logger = get_logger(__name__)


class InstagramEngagementError(RuntimeError):
    """Error raised when Instagram engagement operations fail."""

    pass


class InstagramEngagementService:
    """Service for engagement actions on Instagram using instagrapi."""

    def __init__(self, username: str | None = None, password: str | None = None, session_file: str | None = None):
        """
        Initialize Instagram engagement service.

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
            InstagramEngagementError: If authentication fails.
        """
        if self.client is not None:
            return self.client

        if not self.username or not self.password:
            raise InstagramEngagementError("Instagram username and password are required")

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
            raise InstagramEngagementError("Client not initialized")

        try:
            self.client.login(self.username, self.password)
            logger.info(f"Successfully logged in to Instagram as {self.username}")
        except LoginRequired as exc:
            raise InstagramEngagementError(f"Instagram login required: {exc}") from exc
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            raise InstagramEngagementError(f"Instagram login failed: {exc}") from exc

    def comment_on_post(
        self,
        media_id: str,
        comment_text: str,
    ) -> dict[str, Any]:
        """
        Comment on an Instagram post.

        Args:
            media_id: Instagram media ID (post ID) to comment on.
            comment_text: Text of the comment to post.

        Returns:
            Dictionary with comment_id and success status.

        Raises:
            InstagramEngagementError: If commenting fails.
        """
        client = self._get_client()

        try:
            comment = client.media_comment(media_id, comment_text)
            logger.info(f"Successfully commented on post {media_id}")
            return {
                "success": True,
                "comment_id": str(comment.pk) if hasattr(comment, "pk") else None,
                "media_id": media_id,
                "comment_text": comment_text,
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to comment on post {media_id}: {exc}")
            raise InstagramEngagementError(f"Failed to comment on post: {exc}") from exc

    def like_post(
        self,
        media_id: str,
    ) -> dict[str, Any]:
        """
        Like an Instagram post.

        Args:
            media_id: Instagram media ID (post ID) to like.

        Returns:
            Dictionary with success status.

        Raises:
            InstagramEngagementError: If liking fails.
        """
        client = self._get_client()

        try:
            client.media_like(media_id)
            logger.info(f"Successfully liked post {media_id}")
            return {
                "success": True,
                "media_id": media_id,
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to like post {media_id}: {exc}")
            raise InstagramEngagementError(f"Failed to like post: {exc}") from exc

    def unlike_post(
        self,
        media_id: str,
    ) -> dict[str, Any]:
        """
        Unlike an Instagram post.

        Args:
            media_id: Instagram media ID (post ID) to unlike.

        Returns:
            Dictionary with success status.

        Raises:
            InstagramEngagementError: If unliking fails.
        """
        client = self._get_client()

        try:
            client.media_unlike(media_id)
            logger.info(f"Successfully unliked post {media_id}")
            return {
                "success": True,
                "media_id": media_id,
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to unlike post {media_id}: {exc}")
            raise InstagramEngagementError(f"Failed to unlike post: {exc}") from exc

    def close(self) -> None:
        """Close the Instagram client session."""
        if self.client:
            try:
                # Save session before closing
                if self.session_file:
                    self.client.dump_settings(self.session_file)
            except Exception as exc:
                logger.warning(f"Failed to save session on close: {exc}")
            self.client = None


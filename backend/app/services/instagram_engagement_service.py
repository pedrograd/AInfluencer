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

    def follow_user(
        self,
        user_id: str | int,
    ) -> dict[str, Any]:
        """
        Follow an Instagram user.

        Args:
            user_id: Instagram user ID or username to follow.

        Returns:
            Dictionary with success status and friendship status.

        Raises:
            InstagramEngagementError: If following fails.
        """
        client = self._get_client()

        try:
            # If user_id is a username (string), get user ID first
            if isinstance(user_id, str) and not user_id.isdigit():
                user_info = client.user_info_by_username(user_id)
                user_id = user_info.pk

            friendship = client.user_follow(user_id)
            logger.info(f"Successfully followed user {user_id}")
            return {
                "success": True,
                "user_id": str(user_id),
                "following": friendship.following if hasattr(friendship, "following") else True,
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to follow user {user_id}: {exc}")
            raise InstagramEngagementError(f"Failed to follow user: {exc}") from exc

    def unfollow_user(
        self,
        user_id: str | int,
    ) -> dict[str, Any]:
        """
        Unfollow an Instagram user.

        Args:
            user_id: Instagram user ID or username to unfollow.

        Returns:
            Dictionary with success status.

        Raises:
            InstagramEngagementError: If unfollowing fails.
        """
        client = self._get_client()

        try:
            # If user_id is a username (string), get user ID first
            if isinstance(user_id, str) and not user_id.isdigit():
                user_info = client.user_info_by_username(user_id)
                user_id = user_info.pk

            friendship = client.user_unfollow(user_id)
            logger.info(f"Successfully unfollowed user {user_id}")
            return {
                "success": True,
                "user_id": str(user_id),
                "following": friendship.following if hasattr(friendship, "following") else False,
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to unfollow user {user_id}: {exc}")
            raise InstagramEngagementError(f"Failed to unfollow user: {exc}") from exc

    def send_dm(
        self,
        thread_id: str | int,
        message_text: str,
    ) -> dict[str, Any]:
        """
        Send a direct message on Instagram.

        Args:
            thread_id: Instagram thread ID or user ID to send message to.
            message_text: Text of the message to send.

        Returns:
            Dictionary with success status and message ID.

        Raises:
            InstagramEngagementError: If sending DM fails.
        """
        client = self._get_client()

        try:
            # Send direct message
            # Note: instagrapi uses direct_send for sending DMs
            result = client.direct_send(message_text, [thread_id] if isinstance(thread_id, (str, int)) else thread_id)
            logger.info(f"Successfully sent DM to thread {thread_id}")
            return {
                "success": True,
                "thread_id": str(thread_id),
                "message_id": str(result.get("thread_id", "")) if isinstance(result, dict) else None,
                "message_text": message_text,
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to send DM to thread {thread_id}: {exc}")
            raise InstagramEngagementError(f"Failed to send DM: {exc}") from exc

    def get_inbox(self, limit: int = 20) -> dict[str, Any]:
        """
        Get DM inbox (all threads).

        Args:
            limit: Maximum number of threads to retrieve (default: 20).

        Returns:
            Dictionary with threads list and metadata.

        Raises:
            InstagramEngagementError: If getting inbox fails.
        """
        client = self._get_client()

        try:
            # Get inbox threads
            threads = client.direct_threads(limit=limit)
            logger.info(f"Retrieved {len(threads)} DM threads from inbox")

            # Convert threads to dictionaries
            threads_list = []
            for thread in threads:
                thread_dict = {
                    "thread_id": str(thread.id) if hasattr(thread, "id") else None,
                    "thread_v2_id": str(thread.thread_v2_id) if hasattr(thread, "thread_v2_id") else None,
                    "users": [
                        {
                            "user_id": str(user.pk) if hasattr(user, "pk") else None,
                            "username": user.username if hasattr(user, "username") else None,
                            "full_name": user.full_name if hasattr(user, "full_name") else None,
                        }
                        for user in (thread.users if hasattr(thread, "users") else [])
                    ],
                    "is_unread": thread.inviter.is_unread if hasattr(thread, "inviter") and hasattr(thread.inviter, "is_unread") else False,
                    "last_activity_at": str(thread.last_activity_at) if hasattr(thread, "last_activity_at") else None,
                }
                threads_list.append(thread_dict)

            return {
                "success": True,
                "threads": threads_list,
                "count": len(threads_list),
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to get inbox: {exc}")
            raise InstagramEngagementError(f"Failed to get inbox: {exc}") from exc

    def get_thread_messages(self, thread_id: str | int, limit: int = 20) -> dict[str, Any]:
        """
        Get messages from a specific DM thread.

        Args:
            thread_id: Instagram thread ID.
            limit: Maximum number of messages to retrieve (default: 20).

        Returns:
            Dictionary with messages list and metadata.

        Raises:
            InstagramEngagementError: If getting thread messages fails.
        """
        client = self._get_client()

        try:
            # Get thread messages
            thread = client.direct_thread(thread_id)
            messages = thread.messages[:limit] if hasattr(thread, "messages") else []

            logger.info(f"Retrieved {len(messages)} messages from thread {thread_id}")

            # Convert messages to dictionaries
            messages_list = []
            for msg in messages:
                message_dict = {
                    "message_id": str(msg.id) if hasattr(msg, "id") else None,
                    "user_id": str(msg.user_id) if hasattr(msg, "user_id") else None,
                    "text": msg.text if hasattr(msg, "text") else None,
                    "timestamp": str(msg.timestamp) if hasattr(msg, "timestamp") else None,
                    "is_sent_by_me": msg.user_id == client.user_id if hasattr(msg, "user_id") and hasattr(client, "user_id") else False,
                }
                messages_list.append(message_dict)

            return {
                "success": True,
                "thread_id": str(thread_id),
                "messages": messages_list,
                "count": len(messages_list),
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to get thread messages for thread {thread_id}: {exc}")
            raise InstagramEngagementError(f"Failed to get thread messages: {exc}") from exc

    def get_unread_threads(self) -> dict[str, Any]:
        """
        Get unread DM threads.

        Returns:
            Dictionary with unread threads list.

        Raises:
            InstagramEngagementError: If getting unread threads fails.
        """
        try:
            # Get all threads and filter for unread
            inbox_result = self.get_inbox(limit=100)
            unread_threads = [
                thread for thread in inbox_result.get("threads", []) if thread.get("is_unread", False)
            ]

            logger.info(f"Found {len(unread_threads)} unread DM threads")

            return {
                "success": True,
                "threads": unread_threads,
                "count": len(unread_threads),
            }
        except Exception as exc:
            logger.error(f"Failed to get unread threads: {exc}")
            raise InstagramEngagementError(f"Failed to get unread threads: {exc}") from exc

    def mark_thread_read(self, thread_id: str | int) -> dict[str, Any]:
        """
        Mark a DM thread as read.

        Args:
            thread_id: Instagram thread ID to mark as read.

        Returns:
            Dictionary with success status.

        Raises:
            InstagramEngagementError: If marking thread as read fails.
        """
        client = self._get_client()

        try:
            # Mark thread as read
            client.direct_thread_mark_read(thread_id)
            logger.info(f"Marked thread {thread_id} as read")
            return {
                "success": True,
                "thread_id": str(thread_id),
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to mark thread {thread_id} as read: {exc}")
            raise InstagramEngagementError(f"Failed to mark thread as read: {exc}") from exc

    def get_user_stories(
        self,
        user_id: str | int,
        amount: int | None = None,
    ) -> dict[str, Any]:
        """
        Get stories from an Instagram user.

        Args:
            user_id: Instagram user ID or username.
            amount: Maximum number of stories to retrieve (None for all).

        Returns:
            Dictionary with stories list and metadata.

        Raises:
            InstagramEngagementError: If getting stories fails.
        """
        client = self._get_client()

        try:
            # If user_id is a username (string), get user ID first
            if isinstance(user_id, str) and not user_id.isdigit():
                user_info = client.user_info_by_username(user_id)
                user_id = user_info.pk

            stories = client.user_stories(user_id, amount=amount)
            logger.info(f"Retrieved {len(stories)} stories from user {user_id}")

            # Convert stories to dictionaries
            stories_list = []
            for story in stories:
                story_dict = {
                    "story_id": str(story.pk) if hasattr(story, "pk") else None,
                    "user_id": str(story.user.pk) if hasattr(story, "user") and hasattr(story.user, "pk") else None,
                    "username": story.user.username if hasattr(story, "user") and hasattr(story.user, "username") else None,
                    "taken_at": str(story.taken_at) if hasattr(story, "taken_at") else None,
                    "expiring_at": str(story.expiring_at) if hasattr(story, "expiring_at") else None,
                    "media_type": story.media_type if hasattr(story, "media_type") else None,
                    "viewer_count": story.viewer_count if hasattr(story, "viewer_count") else None,
                    "viewers": [str(v.pk) if hasattr(v, "pk") else None for v in story.viewers] if hasattr(story, "viewers") else [],
                }
                stories_list.append(story_dict)

            return {
                "success": True,
                "user_id": str(user_id),
                "stories": stories_list,
                "count": len(stories_list),
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to get stories from user {user_id}: {exc}")
            raise InstagramEngagementError(f"Failed to get user stories: {exc}") from exc

    def mark_stories_seen(
        self,
        story_pks: list[int],
        skipped_story_pks: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Mark Instagram stories as seen (viewed).

        Args:
            story_pks: List of story primary keys (IDs) to mark as seen.
            skipped_story_pks: Optional list of story IDs that were skipped (default: None).

        Returns:
            Dictionary with success status.

        Raises:
            InstagramEngagementError: If marking stories as seen fails.
        """
        client = self._get_client()

        try:
            skipped = skipped_story_pks or []
            result = client.story_seen(story_pks, skipped)
            logger.info(f"Marked {len(story_pks)} stories as seen (skipped: {len(skipped)})")
            return {
                "success": result,
                "story_pks": story_pks,
                "skipped_story_pks": skipped,
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to mark stories as seen: {exc}")
            raise InstagramEngagementError(f"Failed to mark stories as seen: {exc}") from exc

    def like_story(
        self,
        story_id: str | int,
    ) -> dict[str, Any]:
        """
        Like an Instagram story.

        Args:
            story_id: Instagram story ID to like.

        Returns:
            Dictionary with success status.

        Raises:
            InstagramEngagementError: If liking story fails.
        """
        client = self._get_client()

        try:
            result = client.story_like(str(story_id), revert=False)
            logger.info(f"Successfully liked story {story_id}")
            return {
                "success": result,
                "story_id": str(story_id),
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to like story {story_id}: {exc}")
            raise InstagramEngagementError(f"Failed to like story: {exc}") from exc

    def unlike_story(
        self,
        story_id: str | int,
    ) -> dict[str, Any]:
        """
        Unlike an Instagram story.

        Args:
            story_id: Instagram story ID to unlike.

        Returns:
            Dictionary with success status.

        Raises:
            InstagramEngagementError: If unliking story fails.
        """
        client = self._get_client()

        try:
            result = client.story_unlike(str(story_id))
            logger.info(f"Successfully unliked story {story_id}")
            return {
                "success": result,
                "story_id": str(story_id),
            }
        except PleaseWaitFewMinutes as exc:
            raise InstagramEngagementError(
                f"Instagram rate limit: Please wait a few minutes before trying again: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to unlike story {story_id}: {exc}")
            raise InstagramEngagementError(f"Failed to unlike story: {exc}") from exc

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


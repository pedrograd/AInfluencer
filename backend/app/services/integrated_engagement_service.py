"""Integrated engagement service using platform accounts.

This service handles engagement actions (comments, likes) on Instagram
using platform accounts stored in the database instead of direct credentials.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.platform_account import PlatformAccount
from app.services.instagram_engagement_service import (
    InstagramEngagementService,
    InstagramEngagementError,
)

logger = get_logger(__name__)


class IntegratedEngagementError(RuntimeError):
    """Error raised when integrated engagement operations fail."""

    pass


class IntegratedEngagementService:
    """Service for engagement actions using platform accounts."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize integrated engagement service.

        Args:
            db: Database session for accessing platform accounts.
        """
        self.db = db

    async def _get_platform_account(self, platform_account_id: UUID) -> PlatformAccount:
        """
        Get platform account by ID.

        Args:
            platform_account_id: Platform account UUID.

        Returns:
            PlatformAccount object.

        Raises:
            IntegratedEngagementError: If platform account not found or not connected.
        """
        result = await self.db.execute(
            select(PlatformAccount).where(PlatformAccount.id == platform_account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            raise IntegratedEngagementError(f"Platform account {platform_account_id} not found")

        if account.platform != "instagram":
            raise IntegratedEngagementError(
                f"Platform account {platform_account_id} is not an Instagram account (platform: {account.platform})"
            )

        if not account.is_connected:
            raise IntegratedEngagementError(
                f"Platform account {platform_account_id} is not connected (status: {account.connection_status})"
            )

        return account

    def _extract_instagram_credentials(self, account: PlatformAccount) -> tuple[str, str, str | None]:
        """
        Extract Instagram credentials from platform account auth_data.

        Args:
            account: PlatformAccount object.

        Returns:
            Tuple of (username, password, session_file).

        Raises:
            IntegratedEngagementError: If credentials are missing or invalid.
        """
        if not account.auth_data:
            raise IntegratedEngagementError(f"Platform account {account.id} has no auth_data")

        auth_data = account.auth_data

        # For instagrapi, we need username and password
        # auth_data can contain: username, password, session_file (optional)
        username = auth_data.get("username")
        password = auth_data.get("password")

        if not username or not password:
            raise IntegratedEngagementError(
                f"Platform account {account.id} missing username or password in auth_data"
            )

        session_file = auth_data.get("session_file")  # Optional

        return username, password, session_file

    async def comment_on_post(
        self,
        platform_account_id: UUID,
        media_id: str,
        comment_text: str,
    ) -> dict:
        """
        Comment on an Instagram post using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            media_id: Instagram media ID (post ID) to comment on.
            comment_text: Text of the comment to post.

        Returns:
            Dictionary with comment_id and success status.

        Raises:
            IntegratedEngagementError: If commenting fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.comment_on_post(
                media_id=media_id,
                comment_text=comment_text,
            )
            logger.info(
                f"Successfully commented on post {media_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to comment on post using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to comment on post: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def like_post(
        self,
        platform_account_id: UUID,
        media_id: str,
    ) -> dict:
        """
        Like an Instagram post using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            media_id: Instagram media ID (post ID) to like.

        Returns:
            Dictionary with success status.

        Raises:
            IntegratedEngagementError: If liking fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.like_post(media_id=media_id)
            logger.info(
                f"Successfully liked post {media_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to like post using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to like post: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def unlike_post(
        self,
        platform_account_id: UUID,
        media_id: str,
    ) -> dict:
        """
        Unlike an Instagram post using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            media_id: Instagram media ID (post ID) to unlike.

        Returns:
            Dictionary with success status.

        Raises:
            IntegratedEngagementError: If unliking fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.unlike_post(media_id=media_id)
            logger.info(
                f"Successfully unliked post {media_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to unlike post using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to unlike post: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def follow_user(
        self,
        platform_account_id: UUID,
        target_user_id: str | int,
    ) -> dict:
        """
        Follow an Instagram user using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            target_user_id: Instagram user ID or username to follow.

        Returns:
            Dictionary with follow result.

        Raises:
            IntegratedEngagementError: If following fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.follow_user(user_id=target_user_id)
            logger.info(
                f"Successfully followed user {target_user_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to follow user using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to follow user: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def unfollow_user(
        self,
        platform_account_id: UUID,
        target_user_id: str | int,
    ) -> dict:
        """
        Unfollow an Instagram user using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            target_user_id: Instagram user ID or username to unfollow.

        Returns:
            Dictionary with unfollow result.

        Raises:
            IntegratedEngagementError: If unfollowing fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.unfollow_user(user_id=target_user_id)
            logger.info(
                f"Successfully unfollowed user {target_user_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to unfollow user using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to unfollow user: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def send_dm(
        self,
        platform_account_id: UUID,
        thread_id: str | int,
        message_text: str,
    ) -> dict:
        """
        Send a direct message on Instagram using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            thread_id: Instagram thread ID or user ID to send message to.
            message_text: Text of the message to send.

        Returns:
            Dictionary with DM result.

        Raises:
            IntegratedEngagementError: If sending DM fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.send_dm(thread_id=thread_id, message_text=message_text)
            logger.info(
                f"Successfully sent DM to thread {thread_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to send DM using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to send DM: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def get_inbox(
        self,
        platform_account_id: UUID,
        limit: int = 20,
    ) -> dict:
        """
        Get DM inbox (all threads) for Instagram platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            limit: Maximum number of threads to retrieve (default: 20).

        Returns:
            Dictionary with threads list and metadata.

        Raises:
            IntegratedEngagementError: If getting inbox fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.get_inbox(limit=limit)
            logger.info(
                f"Retrieved inbox for platform account {platform_account_id}: {result.get('count', 0)} threads"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to get inbox using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to get inbox: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def get_thread_messages(
        self,
        platform_account_id: UUID,
        thread_id: str | int,
        limit: int = 20,
    ) -> dict:
        """
        Get messages from a specific DM thread for Instagram platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            thread_id: Instagram thread ID.
            limit: Maximum number of messages to retrieve (default: 20).

        Returns:
            Dictionary with messages list and metadata.

        Raises:
            IntegratedEngagementError: If getting thread messages fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.get_thread_messages(thread_id=thread_id, limit=limit)
            logger.info(
                f"Retrieved {result.get('count', 0)} messages from thread {thread_id} for platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(
                f"Failed to get thread messages using platform account {platform_account_id}: {exc}"
            )
            raise IntegratedEngagementError(f"Failed to get thread messages: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def get_unread_threads(
        self,
        platform_account_id: UUID,
    ) -> dict:
        """
        Get unread DM threads for Instagram platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).

        Returns:
            Dictionary with unread threads list.

        Raises:
            IntegratedEngagementError: If getting unread threads fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.get_unread_threads()
            logger.info(
                f"Found {result.get('count', 0)} unread threads for platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(
                f"Failed to get unread threads using platform account {platform_account_id}: {exc}"
            )
            raise IntegratedEngagementError(f"Failed to get unread threads: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def mark_thread_read(
        self,
        platform_account_id: UUID,
        thread_id: str | int,
    ) -> dict:
        """
        Mark a DM thread as read for Instagram platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            thread_id: Instagram thread ID to mark as read.

        Returns:
            Dictionary with success status.

        Raises:
            IntegratedEngagementError: If marking thread as read fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.mark_thread_read(thread_id=thread_id)
            logger.info(
                f"Marked thread {thread_id} as read for platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(
                f"Failed to mark thread as read using platform account {platform_account_id}: {exc}"
            )
            raise IntegratedEngagementError(f"Failed to mark thread as read: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def get_user_stories(
        self,
        platform_account_id: UUID,
        user_id: str | int,
        amount: int | None = None,
    ) -> dict:
        """
        Get stories from an Instagram user using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            user_id: Instagram user ID or username to get stories from.
            amount: Maximum number of stories to retrieve (None for all).

        Returns:
            Dictionary with stories list and metadata.

        Raises:
            IntegratedEngagementError: If getting stories fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.get_user_stories(user_id=user_id, amount=amount)
            logger.info(
                f"Retrieved {result.get('count', 0)} stories from user {user_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(
                f"Failed to get user stories using platform account {platform_account_id}: {exc}"
            )
            raise IntegratedEngagementError(f"Failed to get user stories: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def mark_stories_seen(
        self,
        platform_account_id: UUID,
        story_pks: list[int],
        skipped_story_pks: list[int] | None = None,
    ) -> dict:
        """
        Mark Instagram stories as seen (viewed) using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            story_pks: List of story primary keys (IDs) to mark as seen.
            skipped_story_pks: Optional list of story IDs that were skipped (default: None).

        Returns:
            Dictionary with success status.

        Raises:
            IntegratedEngagementError: If marking stories as seen fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.mark_stories_seen(
                story_pks=story_pks, skipped_story_pks=skipped_story_pks
            )
            logger.info(
                f"Marked {len(story_pks)} stories as seen using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(
                f"Failed to mark stories as seen using platform account {platform_account_id}: {exc}"
            )
            raise IntegratedEngagementError(f"Failed to mark stories as seen: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def like_story(
        self,
        platform_account_id: UUID,
        story_id: str | int,
    ) -> dict:
        """
        Like an Instagram story using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            story_id: Instagram story ID to like.

        Returns:
            Dictionary with success status.

        Raises:
            IntegratedEngagementError: If liking story fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.like_story(story_id=story_id)
            logger.info(
                f"Successfully liked story {story_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(
                f"Failed to like story using platform account {platform_account_id}: {exc}"
            )
            raise IntegratedEngagementError(f"Failed to like story: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def unlike_story(
        self,
        platform_account_id: UUID,
        story_id: str | int,
    ) -> dict:
        """
        Unlike an Instagram story using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            story_id: Instagram story ID to unlike.

        Returns:
            Dictionary with success status.

        Raises:
            IntegratedEngagementError: If unliking story fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.unlike_story(story_id=story_id)
            logger.info(
                f"Successfully unliked story {story_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(
                f"Failed to unlike story using platform account {platform_account_id}: {exc}"
            )
            raise IntegratedEngagementError(f"Failed to unlike story: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def get_hashtag_posts(
        self,
        platform_account_id: UUID,
        hashtag: str,
        amount: int = 9,
    ) -> dict:
        """
        Get posts from a hashtag using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            hashtag: Hashtag name (without #).
            amount: Maximum number of posts to retrieve (default: 9).

        Returns:
            Dictionary with posts list and metadata.

        Raises:
            IntegratedEngagementError: If getting hashtag posts fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.get_hashtag_posts(hashtag=hashtag, amount=amount)
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to get hashtag posts using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to get hashtag posts: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def get_user_posts(
        self,
        platform_account_id: UUID,
        user_id: str | int,
        amount: int = 12,
    ) -> dict:
        """
        Get posts from a user using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            user_id: Instagram user ID or username.
            amount: Maximum number of posts to retrieve (default: 12).

        Returns:
            Dictionary with posts list and metadata.

        Raises:
            IntegratedEngagementError: If getting user posts fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.get_user_posts(user_id=user_id, amount=amount)
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to get user posts using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to get user posts: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def like_posts_from_hashtag(
        self,
        platform_account_id: UUID,
        hashtag: str,
        amount: int = 9,
        max_likes: int | None = None,
    ) -> dict:
        """
        Like posts from a hashtag using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            hashtag: Hashtag name (without #).
            amount: Maximum number of posts to retrieve (default: 9).
            max_likes: Maximum number of posts to like (None = like all retrieved posts).

        Returns:
            Dictionary with like results.

        Raises:
            IntegratedEngagementError: If liking posts fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.like_posts_from_hashtag(
                hashtag=hashtag,
                amount=amount,
                max_likes=max_likes,
            )
            logger.info(
                f"Successfully liked posts from hashtag #{hashtag} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to like posts from hashtag using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to like posts from hashtag: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()

    async def like_posts_from_user(
        self,
        platform_account_id: UUID,
        user_id: str | int,
        amount: int = 12,
        max_likes: int | None = None,
    ) -> dict:
        """
        Like posts from a user using platform account.

        Args:
            platform_account_id: Platform account UUID (must be Instagram and connected).
            user_id: Instagram user ID or username.
            amount: Maximum number of posts to retrieve (default: 12).
            max_likes: Maximum number of posts to like (None = like all retrieved posts).

        Returns:
            Dictionary with like results.

        Raises:
            IntegratedEngagementError: If liking posts fails.
        """
        account = await self._get_platform_account(platform_account_id)
        username, password, session_file = self._extract_instagram_credentials(account)

        engagement_service = None
        try:
            engagement_service = InstagramEngagementService(
                username=username,
                password=password,
                session_file=session_file,
            )
            result = engagement_service.like_posts_from_user(
                user_id=user_id,
                amount=amount,
                max_likes=max_likes,
            )
            logger.info(
                f"Successfully liked posts from user {user_id} using platform account {platform_account_id}"
            )
            return result
        except InstagramEngagementError as exc:
            logger.error(f"Failed to like posts from user using platform account {platform_account_id}: {exc}")
            raise IntegratedEngagementError(f"Failed to like posts from user: {exc}") from exc
        finally:
            if engagement_service:
                engagement_service.close()


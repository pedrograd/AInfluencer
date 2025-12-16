"""Integrated posting service that connects content library, platform accounts, and posting services."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.content import Content
from app.models.platform_account import PlatformAccount
from app.models.post import Post
from app.services.content_service import ContentService
from app.services.instagram_posting_service import InstagramPostingService, InstagramPostingError
from app.services.post_service import PostService

logger = get_logger(__name__)


class IntegratedPostingError(RuntimeError):
    """Error raised when integrated posting operations fail."""

    pass


class IntegratedPostingService:
    """Service for posting content to platforms using content library and platform accounts."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize integrated posting service.

        Args:
            db: Database session for accessing content and platform accounts.
        """
        self.db = db
        self.content_service = ContentService(db)
        self.post_service = PostService(db)

    async def _get_platform_account(self, platform_account_id: UUID) -> PlatformAccount:
        """
        Get platform account by ID.

        Args:
            platform_account_id: Platform account UUID.

        Returns:
            PlatformAccount object.

        Raises:
            IntegratedPostingError: If platform account not found or not connected.
        """
        result = await self.db.execute(
            select(PlatformAccount).where(PlatformAccount.id == platform_account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            raise IntegratedPostingError(f"Platform account {platform_account_id} not found")

        if not account.is_connected:
            raise IntegratedPostingError(
                f"Platform account {platform_account_id} is not connected (status: {account.connection_status})"
            )

        return account

    async def _get_content(self, content_id: UUID) -> Content:
        """
        Get content by ID.

        Args:
            content_id: Content UUID.

        Returns:
            Content object.

        Raises:
            IntegratedPostingError: If content not found or not approved.
        """
        content = await self.content_service.get_content(content_id, include_character=False)

        if not content:
            raise IntegratedPostingError(f"Content {content_id} not found")

        if not content.is_approved:
            raise IntegratedPostingError(
                f"Content {content_id} is not approved (status: {content.approval_status})"
            )

        return content

    def _extract_instagram_credentials(self, account: PlatformAccount) -> tuple[str, str, str | None]:
        """
        Extract Instagram credentials from platform account auth_data.

        Args:
            account: PlatformAccount object.

        Returns:
            Tuple of (username, password, session_file).

        Raises:
            IntegratedPostingError: If credentials are missing or invalid.
        """
        if not account.auth_data:
            raise IntegratedPostingError(f"Platform account {account.id} has no auth_data")

        auth_data = account.auth_data

        # For instagrapi, we need username and password
        # auth_data can contain: username, password, session_file (optional)
        username = auth_data.get("username")
        password = auth_data.get("password")

        if not username or not password:
            raise IntegratedPostingError(
                f"Platform account {account.id} missing username or password in auth_data"
            )

        session_file = auth_data.get("session_file")  # Optional

        return username, password, session_file

    async def post_image_to_instagram(
        self,
        content_id: UUID,
        platform_account_id: UUID,
        caption: str = "",
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
    ) -> Post:
        """
        Post an image to Instagram using content from the library.

        Args:
            content_id: Content UUID (must be image type and approved).
            platform_account_id: Platform account UUID (must be Instagram and connected).
            caption: Post caption text.
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).

        Returns:
            Post object with published status.

        Raises:
            IntegratedPostingError: If posting fails.
        """
        # Get content
        content = await self._get_content(content_id)

        if content.content_type != "image":
            raise IntegratedPostingError(f"Content {content_id} is not an image (type: {content.content_type})")

        # Get platform account
        account = await self._get_platform_account(platform_account_id)

        if account.platform != "instagram":
            raise IntegratedPostingError(
                f"Platform account {platform_account_id} is not Instagram (platform: {account.platform})"
            )

        # Extract credentials
        username, password, session_file = self._extract_instagram_credentials(account)

        # Verify content file exists
        image_path = Path(content.file_path)
        if not image_path.exists():
            raise IntegratedPostingError(f"Content file not found: {image_path}")

        # Create post record (draft status)
        post = await self.post_service.create_post(
            character_id=content.character_id,
            platform_account_id=platform_account_id,
            platform="instagram",
            post_type="post",
            content_id=content_id,
            caption=caption,
            hashtags=hashtags,
            mentions=mentions,
            status="draft",
        )

        # Post to Instagram
        posting_service = None
        try:
            posting_service = InstagramPostingService(
                username=username,
                password=password,
                session_file=session_file,
            )

            result = posting_service.post_image(
                image_path=image_path,
                caption=caption,
                hashtags=hashtags,
                mentions=mentions,
            )

            # Update post with platform response
            post.platform_post_id = result.get("platform_post_id")
            post.platform_post_url = result.get("platform_post_url")
            post.status = "published"
            post.published_at = post.updated_at

            # Update content usage
            content.times_used += 1
            content.last_used_at = post.published_at

            await self.db.commit()
            await self.db.refresh(post)

            logger.info(
                f"Successfully posted image {content_id} to Instagram as post {post.id} "
                f"(platform_post_id: {post.platform_post_id})"
            )

            return post

        except InstagramPostingError as exc:
            # Update post with error
            post.status = "failed"
            post.error_message = str(exc)
            post.retry_count += 1
            await self.db.commit()

            logger.error(f"Failed to post image {content_id} to Instagram: {exc}")
            raise IntegratedPostingError(f"Instagram posting failed: {exc}") from exc

        finally:
            if posting_service:
                posting_service.close()

    async def post_carousel_to_instagram(
        self,
        content_ids: list[UUID],
        platform_account_id: UUID,
        caption: str = "",
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
    ) -> Post:
        """
        Post multiple images as a carousel to Instagram.

        Args:
            content_ids: List of content UUIDs (must be images and approved).
            platform_account_id: Platform account UUID (must be Instagram and connected).
            caption: Post caption text.
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).

        Returns:
            Post object with published status.

        Raises:
            IntegratedPostingError: If posting fails.
        """
        if len(content_ids) < 2:
            raise IntegratedPostingError("Carousel requires at least 2 images")
        if len(content_ids) > 10:
            raise IntegratedPostingError("Carousel can have at most 10 images")

        # Get all content items
        contents = []
        for content_id in content_ids:
            content = await self._get_content(content_id)
            if content.content_type != "image":
                raise IntegratedPostingError(
                    f"Content {content_id} is not an image (type: {content.content_type})"
                )
            contents.append(content)

        # Verify all content belongs to same character
        character_id = contents[0].character_id
        for content in contents[1:]:
            if content.character_id != character_id:
                raise IntegratedPostingError("All carousel images must belong to the same character")

        # Get platform account
        account = await self._get_platform_account(platform_account_id)

        if account.platform != "instagram":
            raise IntegratedPostingError(
                f"Platform account {platform_account_id} is not Instagram (platform: {account.platform})"
            )

        # Extract credentials
        username, password, session_file = self._extract_instagram_credentials(account)

        # Verify all content files exist
        image_paths = []
        for content in contents:
            image_path = Path(content.file_path)
            if not image_path.exists():
                raise IntegratedPostingError(f"Content file not found: {image_path}")
            image_paths.append(image_path)

        # Create post record (draft status)
        primary_content_id = content_ids[0]
        additional_content_ids = content_ids[1:]

        post = await self.post_service.create_post(
            character_id=character_id,
            platform_account_id=platform_account_id,
            platform="instagram",
            post_type="carousel",
            content_id=primary_content_id,
            additional_content_ids=additional_content_ids,
            caption=caption,
            hashtags=hashtags,
            mentions=mentions,
            status="draft",
        )

        # Post to Instagram
        posting_service = None
        try:
            posting_service = InstagramPostingService(
                username=username,
                password=password,
                session_file=session_file,
            )

            result = posting_service.post_carousel(
                image_paths=image_paths,
                caption=caption,
                hashtags=hashtags,
                mentions=mentions,
            )

            # Update post with platform response
            post.platform_post_id = result.get("platform_post_id")
            post.platform_post_url = result.get("platform_post_url")
            post.status = "published"
            post.published_at = post.updated_at

            # Update content usage
            for content in contents:
                content.times_used += 1
                content.last_used_at = post.published_at

            await self.db.commit()
            await self.db.refresh(post)

            logger.info(
                f"Successfully posted carousel ({len(content_ids)} images) to Instagram as post {post.id} "
                f"(platform_post_id: {post.platform_post_id})"
            )

            return post

        except InstagramPostingError as exc:
            # Update post with error
            post.status = "failed"
            post.error_message = str(exc)
            post.retry_count += 1
            await self.db.commit()

            logger.error(f"Failed to post carousel to Instagram: {exc}")
            raise IntegratedPostingError(f"Instagram posting failed: {exc}") from exc

        finally:
            if posting_service:
                posting_service.close()

    async def post_reel_to_instagram(
        self,
        content_id: UUID,
        platform_account_id: UUID,
        caption: str = "",
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
        thumbnail_content_id: UUID | None = None,
    ) -> Post:
        """
        Post a reel (video) to Instagram using content from the library.

        Args:
            content_id: Content UUID (must be video type and approved).
            platform_account_id: Platform account UUID (must be Instagram and connected).
            caption: Post caption text.
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).
            thumbnail_content_id: Optional thumbnail content UUID (must be image).

        Returns:
            Post object with published status.

        Raises:
            IntegratedPostingError: If posting fails.
        """
        # Get content
        content = await self._get_content(content_id)

        if content.content_type != "video":
            raise IntegratedPostingError(f"Content {content_id} is not a video (type: {content.content_type})")

        # Get platform account
        account = await self._get_platform_account(platform_account_id)

        if account.platform != "instagram":
            raise IntegratedPostingError(
                f"Platform account {platform_account_id} is not Instagram (platform: {account.platform})"
            )

        # Extract credentials
        username, password, session_file = self._extract_instagram_credentials(account)

        # Verify content file exists
        video_path = Path(content.file_path)
        if not video_path.exists():
            raise IntegratedPostingError(f"Content file not found: {video_path}")

        # Get thumbnail if provided
        thumbnail_path = None
        if thumbnail_content_id:
            thumbnail_content = await self._get_content(thumbnail_content_id)
            if thumbnail_content.content_type != "image":
                raise IntegratedPostingError(
                    f"Thumbnail content {thumbnail_content_id} is not an image (type: {thumbnail_content.content_type})"
                )
            thumbnail_path = Path(thumbnail_content.file_path)
            if not thumbnail_path.exists():
                raise IntegratedPostingError(f"Thumbnail file not found: {thumbnail_path}")

        # Create post record (draft status)
        post = await self.post_service.create_post(
            character_id=content.character_id,
            platform_account_id=platform_account_id,
            platform="instagram",
            post_type="reel",
            content_id=content_id,
            caption=caption,
            hashtags=hashtags,
            mentions=mentions,
            status="draft",
        )

        # Post to Instagram
        posting_service = None
        try:
            posting_service = InstagramPostingService(
                username=username,
                password=password,
                session_file=session_file,
            )

            result = posting_service.post_reel(
                video_path=video_path,
                caption=caption,
                hashtags=hashtags,
                mentions=mentions,
                thumbnail_path=thumbnail_path,
            )

            # Update post with platform response
            post.platform_post_id = result.get("platform_post_id")
            post.platform_post_url = result.get("platform_post_url")
            post.status = "published"
            post.published_at = post.updated_at

            # Update content usage
            content.times_used += 1
            content.last_used_at = post.published_at

            await self.db.commit()
            await self.db.refresh(post)

            logger.info(
                f"Successfully posted reel {content_id} to Instagram as post {post.id} "
                f"(platform_post_id: {post.platform_post_id})"
            )

            return post

        except InstagramPostingError as exc:
            # Update post with error
            post.status = "failed"
            post.error_message = str(exc)
            post.retry_count += 1
            await self.db.commit()

            logger.error(f"Failed to post reel {content_id} to Instagram: {exc}")
            raise IntegratedPostingError(f"Instagram posting failed: {exc}") from exc

        finally:
            if posting_service:
                posting_service.close()

    async def post_story_to_instagram(
        self,
        content_id: UUID,
        platform_account_id: UUID,
        caption: str | None = None,
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
        is_video: bool = False,
    ) -> Post:
        """
        Post a story (image or video) to Instagram using content from the library.

        Args:
            content_id: Content UUID (must be image or video type and approved).
            platform_account_id: Platform account UUID (must be Instagram and connected).
            caption: Story caption/text overlay.
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).
            is_video: Whether content is video (False for image).

        Returns:
            Post object with published status.

        Raises:
            IntegratedPostingError: If posting fails.
        """
        if not content_id:
            raise IntegratedPostingError("content_id is required")

        # Get content
        content = await self._get_content(content_id)

        expected_type = "video" if is_video else "image"
        if content.content_type != expected_type:
            raise IntegratedPostingError(
                f"Content {content_id} is not {expected_type} (type: {content.content_type})"
            )

        # Get platform account
        account = await self._get_platform_account(platform_account_id)

        if account.platform != "instagram":
            raise IntegratedPostingError(
                f"Platform account {platform_account_id} is not Instagram (platform: {account.platform})"
            )

        # Extract credentials
        username, password, session_file = self._extract_instagram_credentials(account)

        # Verify content file exists
        media_path = Path(content.file_path)
        if not media_path.exists():
            raise IntegratedPostingError(f"Content file not found: {media_path}")

        # Create post record (draft status)
        post = await self.post_service.create_post(
            character_id=content.character_id,
            platform_account_id=platform_account_id,
            platform="instagram",
            post_type="story",
            content_id=content_id,
            caption=caption,
            hashtags=hashtags,
            mentions=mentions,
            status="draft",
        )

        # Post to Instagram
        posting_service = None
        try:
            posting_service = InstagramPostingService(
                username=username,
                password=password,
                session_file=session_file,
            )

            if is_video:
                result = posting_service.post_story(
                    video_path=media_path,
                    caption=caption,
                    hashtags=hashtags,
                    mentions=mentions,
                )
            else:
                result = posting_service.post_story(
                    image_path=media_path,
                    caption=caption,
                    hashtags=hashtags,
                    mentions=mentions,
                )

            # Update post with platform response
            post.platform_post_id = result.get("platform_post_id")
            post.platform_post_url = result.get("platform_post_url")
            post.status = "published"
            post.published_at = post.updated_at

            # Update content usage
            content.times_used += 1
            content.last_used_at = post.published_at

            await self.db.commit()
            await self.db.refresh(post)

            logger.info(
                f"Successfully posted story {content_id} to Instagram as post {post.id} "
                f"(platform_post_id: {post.platform_post_id})"
            )

            return post

        except InstagramPostingError as exc:
            # Update post with error
            post.status = "failed"
            post.error_message = str(exc)
            post.retry_count += 1
            await self.db.commit()

            logger.error(f"Failed to post story {content_id} to Instagram: {exc}")
            raise IntegratedPostingError(f"Instagram posting failed: {exc}") from exc

        finally:
            if posting_service:
                posting_service.close()


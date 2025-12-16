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
from app.services.twitter_client import TwitterApiClient, TwitterApiError
from app.services.facebook_client import FacebookApiClient, FacebookApiError

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

    def _extract_twitter_credentials(self, account: PlatformAccount) -> tuple[str, str, str, str]:
        """
        Extract Twitter credentials from platform account auth_data.

        Args:
            account: PlatformAccount object.

        Returns:
            Tuple of (consumer_key, consumer_secret, access_token, access_token_secret).

        Raises:
            IntegratedPostingError: If credentials are missing or invalid.
        """
        if not account.auth_data:
            raise IntegratedPostingError(f"Platform account {account.id} has no auth_data")

        auth_data = account.auth_data

        # For Twitter OAuth 1.0a, we need consumer_key, consumer_secret, access_token, access_token_secret
        consumer_key = auth_data.get("consumer_key")
        consumer_secret = auth_data.get("consumer_secret")
        access_token = auth_data.get("access_token")
        access_token_secret = auth_data.get("access_token_secret")

        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            raise IntegratedPostingError(
                f"Platform account {account.id} missing Twitter OAuth 1.0a credentials in auth_data"
            )

        return consumer_key, consumer_secret, access_token, access_token_secret

    def _extract_facebook_credentials(self, account: PlatformAccount) -> tuple[str, str | None, str | None]:
        """
        Extract Facebook credentials from platform account auth_data.

        Args:
            account: PlatformAccount object.

        Returns:
            Tuple of (access_token, app_id, app_secret).

        Raises:
            IntegratedPostingError: If credentials are missing or invalid.
        """
        if not account.auth_data:
            raise IntegratedPostingError(f"Platform account {account.id} has no auth_data")

        auth_data = account.auth_data

        # For Facebook Graph API, we need access_token (app_id and app_secret are optional)
        access_token = auth_data.get("access_token")
        app_id = auth_data.get("app_id")
        app_secret = auth_data.get("app_secret")

        if not access_token:
            raise IntegratedPostingError(
                f"Platform account {account.id} missing Facebook access_token in auth_data"
            )

        return access_token, app_id, app_secret

    async def cross_post_image(
        self,
        content_id: UUID,
        platform_account_ids: list[UUID],
        caption: str = "",
        hashtags: list[str] | None = None,
        mentions: list[str] | None = None,
    ) -> dict[str, Post]:
        """
        Cross-post an image to multiple platforms simultaneously.

        Posts the same content to multiple platforms (Instagram, Twitter, Facebook)
        using their respective platform accounts. Each platform is posted to independently,
        and failures on one platform do not prevent posting to others.

        Args:
            content_id: Content UUID (must be image type and approved).
            platform_account_ids: List of platform account UUIDs to post to.
            caption: Post caption/text content.
            hashtags: List of hashtags (without #).
            mentions: List of usernames to mention (without @).

        Returns:
            Dictionary mapping platform names to Post objects (successful posts only).

        Raises:
            IntegratedPostingError: If content validation fails or no valid platform accounts provided.
        """
        # Get content
        content = await self._get_content(content_id)

        if content.content_type != "image":
            raise IntegratedPostingError(f"Content {content_id} is not an image (type: {content.content_type})")

        if not platform_account_ids:
            raise IntegratedPostingError("At least one platform account ID is required")

        # Verify content file exists
        image_path = Path(content.file_path)
        if not image_path.exists():
            raise IntegratedPostingError(f"Content file not found: {image_path}")

        # Get all platform accounts
        accounts = []
        for account_id in platform_account_ids:
            account = await self._get_platform_account(account_id)
            accounts.append(account)

        # Verify all accounts belong to same character
        character_id = accounts[0].character_id
        for account in accounts[1:]:
            if account.character_id != character_id:
                raise IntegratedPostingError("All platform accounts must belong to the same character")

        if content.character_id != character_id:
            raise IntegratedPostingError("Content must belong to the same character as platform accounts")

        # Post to each platform
        results: dict[str, Post] = {}
        errors: dict[str, str] = {}

        for account in accounts:
            platform = account.platform
            try:
                if platform == "instagram":
                    post = await self.post_image_to_instagram(
                        content_id=content_id,
                        platform_account_id=account.id,
                        caption=caption,
                        hashtags=hashtags,
                        mentions=mentions,
                    )
                    results[platform] = post
                    logger.info(f"Successfully cross-posted to Instagram: post {post.id}")

                elif platform == "twitter":
                    # Extract Twitter credentials
                    consumer_key, consumer_secret, access_token, access_token_secret = (
                        self._extract_twitter_credentials(account)
                    )

                    # Create Twitter client
                    twitter_client = TwitterApiClient(
                        consumer_key=consumer_key,
                        consumer_secret=consumer_secret,
                        access_token=access_token,
                        access_token_secret=access_token_secret,
                    )

                    # Build tweet text from caption and hashtags
                    tweet_text = caption
                    if hashtags:
                        hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                        if tweet_text:
                            tweet_text = f"{tweet_text} {hashtag_text}"
                        else:
                            tweet_text = hashtag_text

                    # Note: Twitter API v2 requires media upload first, then attach media_ids
                    # For now, we'll post text-only. Media upload can be added later.
                    if len(tweet_text) > 280:
                        tweet_text = tweet_text[:277] + "..."

                    # Post tweet
                    tweet_result = twitter_client.post_tweet(text=tweet_text)

                    # Create post record
                    post = await self.post_service.create_post(
                        character_id=character_id,
                        platform_account_id=account.id,
                        platform="twitter",
                        post_type="tweet",
                        content_id=content_id,
                        caption=tweet_text,
                        hashtags=hashtags,
                        mentions=mentions,
                        status="published",
                    )

                    # Update post with platform response
                    post.platform_post_id = tweet_result.get("id")
                    post.published_at = post.updated_at

                    # Update content usage
                    content.times_used += 1
                    content.last_used_at = post.published_at

                    await self.db.commit()
                    await self.db.refresh(post)

                    results[platform] = post
                    logger.info(f"Successfully cross-posted to Twitter: post {post.id}")

                elif platform == "facebook":
                    # Extract Facebook credentials
                    access_token, app_id, app_secret = self._extract_facebook_credentials(account)

                    # Create Facebook client
                    facebook_client = FacebookApiClient(
                        access_token=access_token,
                        app_id=app_id,
                        app_secret=app_secret,
                    )

                    # Build post message from caption and hashtags
                    post_message = caption
                    if hashtags:
                        hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                        if post_message:
                            post_message = f"{post_message} {hashtag_text}"
                        else:
                            post_message = hashtag_text

                    # Get page_id from account if available
                    page_id = account.account_id

                    # Post to Facebook
                    post_result = facebook_client.create_post(
                        message=post_message,
                        page_id=page_id,
                    )

                    # Create post record
                    post = await self.post_service.create_post(
                        character_id=character_id,
                        platform_account_id=account.id,
                        platform="facebook",
                        post_type="post",
                        content_id=content_id,
                        caption=post_message,
                        hashtags=hashtags,
                        mentions=mentions,
                        status="published",
                    )

                    # Update post with platform response
                    post.platform_post_id = post_result.get("id")
                    post.published_at = post.updated_at

                    # Update content usage
                    content.times_used += 1
                    content.last_used_at = post.published_at

                    await self.db.commit()
                    await self.db.refresh(post)

                    results[platform] = post
                    logger.info(f"Successfully cross-posted to Facebook: post {post.id}")

                else:
                    errors[platform] = f"Cross-posting not yet supported for platform: {platform}"
                    logger.warning(f"Cross-posting not supported for platform: {platform}")

            except Exception as exc:
                error_msg = str(exc)
                errors[platform] = error_msg
                logger.error(f"Failed to cross-post to {platform}: {exc}", exc_info=True)

        # Log summary
        if results:
            logger.info(
                f"Cross-posting completed: {len(results)} successful, {len(errors)} failed. "
                f"Platforms: {', '.join(results.keys())}"
            )
        if errors:
            logger.warning(f"Cross-posting errors: {errors}")

        if not results:
            raise IntegratedPostingError(
                f"Cross-posting failed for all platforms. Errors: {errors}"
            )

        return results


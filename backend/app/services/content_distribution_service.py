"""Content distribution service for distributing content to platforms based on calendar entries."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.content import Content, ScheduledPost
from app.models.platform_account import PlatformAccount
from app.services.content_intelligence_service import ContentIntelligenceService, ContentCalendarEntry
from app.services.content_service import ContentService
from app.services.integrated_posting_service import IntegratedPostingService
from app.services.character_content_service import CharacterContentService, CharacterContentRequest

logger = get_logger(__name__)


class ContentDistributionError(RuntimeError):
    """Error raised when content distribution operations fail."""

    pass


class ContentDistributionService:
    """Service for distributing content to platforms based on calendar entries."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize content distribution service.

        Args:
            db: Database session for accessing content, platform accounts, and scheduled posts.
        """
        self.db = db
        self.content_service = ContentService(db)
        self.posting_service = IntegratedPostingService(db)
        self.intelligence_service = ContentIntelligenceService()
        self.character_content_service = CharacterContentService()

    async def _get_platform_accounts_for_character(
        self, character_id: UUID, platform: str | None = None
    ) -> list[PlatformAccount]:
        """
        Get platform accounts for a character.

        Args:
            character_id: Character UUID.
            platform: Optional platform filter.

        Returns:
            List of platform accounts (connected only).
        """
        query = select(PlatformAccount).where(
            PlatformAccount.character_id == character_id,
            PlatformAccount.is_connected == True,  # noqa: E712
        )

        if platform:
            query = query.where(PlatformAccount.platform == platform.lower())

        result = await self.db.execute(query)
        accounts = result.scalars().all()

        return list(accounts)

    async def _find_content_for_entry(
        self, entry: ContentCalendarEntry, character_id: UUID
    ) -> Content | None:
        """
        Find existing content for a calendar entry.

        Args:
            entry: Content calendar entry.
            character_id: Character UUID.

        Returns:
            Content object if found, None otherwise.
        """
        # Search for approved content matching the entry criteria
        query = select(Content).where(
            Content.character_id == character_id,
            Content.content_type == entry.content_type,
            Content.is_approved == True,  # noqa: E712
        )

        # Order by creation date (newest first)
        query = query.order_by(Content.created_at.desc())

        result = await self.db.execute(query)
        content = result.scalar_one_or_none()

        return content

    async def _generate_content_for_entry(
        self, entry: ContentCalendarEntry, character_id: UUID
    ) -> Content | None:
        """
        Generate new content for a calendar entry.

        Args:
            entry: Content calendar entry.
            character_id: Character UUID.

        Returns:
            Generated Content object if successful, None otherwise.
        """
        try:
            # Build content request
            request = CharacterContentRequest(
                content_type=entry.content_type,
                prompt=entry.topic or f"{entry.content_type} content for {entry.platform}",
                style_preferences={},
            )

            # Get character (we'll need to import Character model)
            from app.models.character import Character

            result = await self.db.execute(
                select(Character).where(Character.id == character_id)
            )
            character = result.scalar_one_or_none()

            if not character:
                logger.error(f"Character {character_id} not found")
                return None

            # Generate content
            content_result = await self.character_content_service.generate_content(
                request=request,
                character=character,
            )

            if not content_result or not content_result.content_id:
                logger.error(f"Failed to generate content for entry: {entry}")
                return None

            # Get the generated content
            content = await self.content_service.get_content(content_result.content_id)

            return content

        except Exception as exc:
            logger.error(f"Error generating content for entry {entry}: {exc}")
            return None

    async def _adapt_content_for_platform(
        self, entry: ContentCalendarEntry, content: Content
    ) -> dict[str, Any]:
        """
        Adapt content metadata for platform-specific requirements.

        Args:
            entry: Content calendar entry.
            content: Content object.

        Returns:
            Dictionary with platform-adapted metadata (caption, hashtags, etc.).
        """
        platform = entry.platform.lower()

        # Get base caption from content or entry
        base_caption = content.caption or entry.caption_template or ""

        # Platform-specific adaptations
        adaptations: dict[str, Any] = {
            "caption": base_caption,
            "hashtags": [],
            "mentions": [],
        }

        if platform == "instagram":
            # Instagram: Add hashtags, emojis
            if not adaptations["hashtags"]:
                adaptations["hashtags"] = self._generate_hashtags(content, count=10)
            # Instagram allows longer captions
            adaptations["caption"] = base_caption

        elif platform == "twitter":
            # Twitter: Short captions, limited hashtags
            if len(base_caption) > 280:
                adaptations["caption"] = base_caption[:277] + "..."
            adaptations["hashtags"] = self._generate_hashtags(content, count=2)

        elif platform == "facebook":
            # Facebook: Longer captions, fewer hashtags
            adaptations["hashtags"] = self._generate_hashtags(content, count=3)

        elif platform == "telegram":
            # Telegram: Full caption, no hashtag limit
            adaptations["hashtags"] = self._generate_hashtags(content, count=5)

        elif platform == "onlyfans":
            # OnlyFans: Teaser text, minimal hashtags
            if len(base_caption) > 200:
                adaptations["caption"] = base_caption[:197] + "..."
            adaptations["hashtags"] = []

        elif platform == "youtube":
            # YouTube: Full description, tags
            adaptations["hashtags"] = self._generate_hashtags(content, count=15)

        return adaptations

    def _generate_hashtags(self, content: Content, count: int = 5) -> list[str]:
        """
        Generate hashtags for content.

        Args:
            content: Content object.
            count: Number of hashtags to generate.

        Returns:
            List of hashtag strings (without #).
        """
        # Simple hashtag generation based on content tags
        hashtags: list[str] = []

        if content.tags:
            # Use existing tags
            hashtags.extend([tag.lower().replace(" ", "") for tag in content.tags[:count]])

        # Add content type hashtag
        if content.content_type:
            type_tag = content.content_type.lower()
            if type_tag not in hashtags:
                hashtags.append(type_tag)

        # Fill remaining slots with generic tags
        generic_tags = ["ai", "content", "digital", "art", "creative"]
        for tag in generic_tags:
            if len(hashtags) >= count:
                break
            if tag not in hashtags:
                hashtags.append(tag)

        return hashtags[:count]

    async def distribute_calendar_entry(
        self,
        entry: ContentCalendarEntry,
        character_id: UUID,
        schedule: bool = True,
        generate_if_missing: bool = True,
    ) -> dict[str, Any]:
        """
        Distribute a single calendar entry to platforms.

        Args:
            entry: Content calendar entry.
            character_id: Character UUID.
            schedule: If True, create ScheduledPost; if False, post immediately.
            generate_if_missing: If True, generate content if not found.

        Returns:
            Dictionary with distribution result.

        Raises:
            ContentDistributionError: If distribution fails.
        """
        if not entry.character_id:
            entry.character_id = character_id

        # Get platform accounts
        platform_accounts = await self._get_platform_accounts_for_character(
            character_id, entry.platform
        )

        if not platform_accounts:
            raise ContentDistributionError(
                f"No connected {entry.platform} account found for character {character_id}"
            )

        # Find or generate content
        content = await self._find_content_for_entry(entry, character_id)

        if not content and generate_if_missing:
            logger.info(f"Content not found for entry, generating new content: {entry}")
            content = await self._generate_content_for_entry(entry, character_id)

        if not content:
            raise ContentDistributionError(
                f"No content available for entry (type: {entry.content_type}, platform: {entry.platform})"
            )

        # Adapt content for platform
        adaptations = await self._adapt_content_for_platform(entry, content)

        # Determine posting time
        posting_time = entry.scheduled_time or datetime.now()

        if schedule:
            # Create scheduled post
            scheduled_post = ScheduledPost(
                character_id=character_id,
                content_id=content.id,
                scheduled_time=posting_time,
                platform=entry.platform,
                caption=adaptations["caption"],
                post_settings={
                    "hashtags": adaptations["hashtags"],
                    "mentions": adaptations["mentions"],
                },
                status="pending",
            )

            self.db.add(scheduled_post)
            await self.db.commit()
            await self.db.refresh(scheduled_post)

            logger.info(
                f"Created scheduled post {scheduled_post.id} for {entry.platform} at {posting_time}"
            )

            return {
                "success": True,
                "scheduled_post_id": str(scheduled_post.id),
                "content_id": str(content.id),
                "platform": entry.platform,
                "scheduled_time": posting_time.isoformat(),
                "status": "scheduled",
            }

        else:
            # Post immediately
            account_ids = [acc.id for acc in platform_accounts]

            if entry.content_type == "image":
                # Use cross-post for images
                results = await self.posting_service.cross_post_image(
                    content_id=content.id,
                    platform_account_ids=account_ids,
                    caption=adaptations["caption"],
                    hashtags=adaptations["hashtags"],
                    mentions=adaptations["mentions"],
                )

                logger.info(f"Posted content {content.id} to {len(results)} platforms")

                return {
                    "success": True,
                    "content_id": str(content.id),
                    "platforms": list(results.keys()),
                    "posts": {platform: str(post.id) for platform, post in results.items()},
                    "status": "posted",
                }

            else:
                # For other content types, post individually
                results: dict[str, Any] = {}
                for account in platform_accounts:
                    try:
                        if account.platform == "instagram":
                            post = await self.posting_service.post_image_to_instagram(
                                content_id=content.id,
                                platform_account_id=account.id,
                                caption=adaptations["caption"],
                                hashtags=adaptations["hashtags"],
                                mentions=adaptations["mentions"],
                            )
                            results[account.platform] = post
                        # Add other platforms as needed
                    except Exception as exc:
                        logger.error(f"Failed to post to {account.platform}: {exc}")
                        results[account.platform] = {"error": str(exc)}

                return {
                    "success": len(results) > 0,
                    "content_id": str(content.id),
                    "platforms": list(results.keys()),
                    "results": results,
                    "status": "posted",
                }

    async def distribute_calendar_entries(
        self,
        entries: list[ContentCalendarEntry],
        character_id: UUID,
        schedule: bool = True,
        generate_if_missing: bool = True,
    ) -> dict[str, Any]:
        """
        Distribute multiple calendar entries to platforms.

        Args:
            entries: List of content calendar entries.
            character_id: Character UUID.
            schedule: If True, create ScheduledPost; if False, post immediately.
            generate_if_missing: If True, generate content if not found.

        Returns:
            Dictionary with distribution results.
        """
        results: dict[str, Any] = {
            "total": len(entries),
            "succeeded": 0,
            "failed": 0,
            "results": [],
        }

        for entry in entries:
            try:
                result = await self.distribute_calendar_entry(
                    entry, character_id, schedule=schedule, generate_if_missing=generate_if_missing
                )
                results["succeeded"] += 1
                results["results"].append({"entry": entry, "result": result, "error": None})
            except Exception as exc:
                results["failed"] += 1
                logger.error(f"Failed to distribute entry {entry}: {exc}")
                results["results"].append({"entry": entry, "result": None, "error": str(exc)})

        logger.info(
            f"Distributed {results['succeeded']}/{results['total']} calendar entries "
            f"({results['failed']} failed)"
        )

        return results

    async def execute_scheduled_posts(
        self, character_id: UUID | None = None, max_posts: int = 10
    ) -> dict[str, Any]:
        """
        Execute scheduled posts that are due.

        Args:
            character_id: Optional character ID filter.
            max_posts: Maximum number of posts to execute in one batch.

        Returns:
            Dictionary with execution results.
        """
        now = datetime.now()

        query = select(ScheduledPost).where(
            ScheduledPost.status == "pending",
            ScheduledPost.scheduled_time <= now,
        )

        if character_id:
            query = query.where(ScheduledPost.character_id == character_id)

        query = query.order_by(ScheduledPost.scheduled_time.asc()).limit(max_posts)

        result = await self.db.execute(query)
        scheduled_posts = result.scalars().all()

        execution_results: dict[str, Any] = {
            "total": len(scheduled_posts),
            "succeeded": 0,
            "failed": 0,
            "results": [],
        }

        for scheduled_post in scheduled_posts:
            try:
                # Get content
                content = await self.content_service.get_content(scheduled_post.content_id)

                if not content:
                    raise ContentDistributionError(
                        f"Content {scheduled_post.content_id} not found"
                    )

                # Get platform accounts
                platform_accounts = await self._get_platform_accounts_for_character(
                    scheduled_post.character_id, scheduled_post.platform
                )

                if not platform_accounts:
                    raise ContentDistributionError(
                        f"No connected {scheduled_post.platform} account found"
                    )

                # Extract post settings
                post_settings = scheduled_post.post_settings or {}
                hashtags = post_settings.get("hashtags", [])
                mentions = post_settings.get("mentions", [])

                # Post content
                account_ids = [acc.id for acc in platform_accounts]

                if content.content_type == "image":
                    results = await self.posting_service.cross_post_image(
                        content_id=content.id,
                        platform_account_ids=account_ids,
                        caption=scheduled_post.caption or "",
                        hashtags=hashtags,
                        mentions=mentions,
                    )

                    # Update scheduled post
                    scheduled_post.status = "posted"
                    scheduled_post.posted_at = datetime.now()
                    await self.db.commit()

                    execution_results["succeeded"] += 1
                    execution_results["results"].append(
                        {
                            "scheduled_post_id": str(scheduled_post.id),
                            "success": True,
                            "platforms": list(results.keys()),
                        }
                    )

                else:
                    # For other content types, handle individually
                    # This is a simplified version - you'd add platform-specific posting logic
                    scheduled_post.status = "failed"
                    scheduled_post.error_message = f"Content type {content.content_type} not yet supported for scheduled posting"
                    await self.db.commit()

                    execution_results["failed"] += 1
                    execution_results["results"].append(
                        {
                            "scheduled_post_id": str(scheduled_post.id),
                            "success": False,
                            "error": scheduled_post.error_message,
                        }
                    )

            except Exception as exc:
                logger.error(f"Failed to execute scheduled post {scheduled_post.id}: {exc}")

                scheduled_post.status = "failed"
                scheduled_post.error_message = str(exc)
                scheduled_post.retry_count += 1
                await self.db.commit()

                execution_results["failed"] += 1
                execution_results["results"].append(
                    {
                        "scheduled_post_id": str(scheduled_post.id),
                        "success": False,
                        "error": str(exc),
                    }
                )

        logger.info(
            f"Executed {execution_results['succeeded']}/{execution_results['total']} scheduled posts "
            f"({execution_results['failed']} failed)"
        )

        return execution_results


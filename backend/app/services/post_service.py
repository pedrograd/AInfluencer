"""Post management service for creating and managing posts."""

from __future__ import annotations

from uuid import UUID
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.post import Post
from app.models.character import Character
from app.models.content import Content

logger = get_logger(__name__)


class PostService:
    """Service for post management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize post service with database session."""
        self.db = db

    async def create_post(
        self,
        character_id: UUID,
        platform_account_id: UUID,
        platform: str,
        post_type: str,
        content_id: Optional[UUID] = None,
        additional_content_ids: Optional[list[UUID]] = None,
        caption: Optional[str] = None,
        hashtags: Optional[list[str]] = None,
        mentions: Optional[list[str]] = None,
        status: str = "draft",
    ) -> Post:
        """Create a new post record.
        
        Args:
            character_id: UUID of the character creating the post
            platform_account_id: UUID of the platform account to use
            platform: Platform name (instagram, twitter, facebook, etc.)
            post_type: Type of post (post, story, reel, short, tweet, message)
            content_id: Primary content ID (image/video)
            additional_content_ids: Additional content IDs for carousels
            caption: Post caption/text
            hashtags: List of hashtags
            mentions: List of mentioned usernames
            status: Post status (draft, scheduled, published, failed, deleted)
            
        Returns:
            Created Post object
            
        Raises:
            ValueError: If character or content validation fails
        """
        # Verify character exists
        character_result = await self.db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = character_result.scalar_one_or_none()
        if not character:
            raise ValueError(f"Character {character_id} not found")

        # Verify content exists if provided
        if content_id:
            content_result = await self.db.execute(
                select(Content).where(Content.id == content_id)
            )
            content = content_result.scalar_one_or_none()
            if not content:
                raise ValueError(f"Content {content_id} not found")

        # Verify additional content IDs if provided
        if additional_content_ids:
            for additional_id in additional_content_ids:
                additional_result = await self.db.execute(
                    select(Content).where(Content.id == additional_id)
                )
                additional_content = additional_result.scalar_one_or_none()
                if not additional_content:
                    raise ValueError(f"Additional content {additional_id} not found")

        # Create post
        post = Post(
            character_id=character_id,
            platform_account_id=platform_account_id,
            platform=platform,
            post_type=post_type,
            content_id=content_id,
            additional_content_ids=additional_content_ids,
            caption=caption,
            hashtags=hashtags,
            mentions=mentions,
            status=status,
        )

        self.db.add(post)
        await self.db.flush()
        await self.db.refresh(post)
        return post

    async def get_post(self, post_id: UUID) -> Post | None:
        """Get post by ID."""
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    async def list_posts(
        self,
        character_id: Optional[UUID] = None,
        platform: Optional[str] = None,
        post_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Post], int]:
        """List posts with optional filters.
        
        Returns:
            Tuple of (list of posts, total count)
        """
        query = select(Post)
        count_query = select(func.count()).select_from(Post)

        conditions = []
        if character_id:
            conditions.append(Post.character_id == character_id)
        if platform:
            conditions.append(Post.platform == platform)
        if post_type:
            conditions.append(Post.post_type == post_type)
        if status:
            conditions.append(Post.status == status)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar_one()

        # Get paginated results
        query = query.order_by(Post.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        posts = result.scalars().all()

        return list(posts), total_count


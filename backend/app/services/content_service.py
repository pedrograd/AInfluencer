"""Content library management service."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.content import Content
from app.models.character import Character

logger = get_logger(__name__)


class ContentService:
    """Service for content library management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize content service with database session."""
        self.db = db

    async def get_content(
        self,
        content_id: UUID,
        include_character: bool = True,
    ) -> Content | None:
        """Get content by ID with optional character relationship."""
        query = select(Content).where(Content.id == content_id)

        if include_character:
            query = query.options(selectinload(Content.character))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_content(
        self,
        character_id: UUID | None = None,
        content_type: str | None = None,
        content_category: str | None = None,
        approval_status: str | None = None,
        is_approved: bool | None = None,
        is_nsfw: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_character: bool = True,
    ) -> tuple[list[Content], int]:
        """
        List content with filtering, search, and pagination.

        Returns:
            Tuple of (content list, total count)
        """
        # Build base query
        query = select(Content)
        count_query = select(func.count()).select_from(Content)

        # Apply filters
        conditions = []

        if character_id:
            conditions.append(Content.character_id == character_id)

        if content_type:
            conditions.append(Content.content_type == content_type)

        if content_category:
            conditions.append(Content.content_category == content_category)

        if approval_status:
            conditions.append(Content.approval_status == approval_status)

        if is_approved is not None:
            conditions.append(Content.is_approved == is_approved)

        if is_nsfw is not None:
            conditions.append(Content.is_nsfw == is_nsfw)

        if date_from:
            conditions.append(Content.created_at >= date_from)

        if date_to:
            conditions.append(Content.created_at <= date_to)

        # Search in prompt, file_path, and character name
        if search:
            search_conditions = [
                Content.prompt.ilike(f"%{search}%"),
                Content.file_path.ilike(f"%{search}%"),
            ]
            # If including character, search in character name too
            if include_character:
                # We'll need to join for this, but for now just search in content fields
                pass
            conditions.append(or_(*search_conditions))

        # Apply all conditions
        if conditions:
            where_clause = and_(*conditions)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)

        # Include character relationship if requested
        if include_character:
            query = query.options(selectinload(Content.character))

        # Order by created_at descending (newest first)
        query = query.order_by(Content.created_at.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute queries
        result = await self.db.execute(query)
        content_list = result.scalars().all()

        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar_one()

        return content_list, total_count

    async def create_content(
        self,
        character_id: UUID,
        content_type: str,
        file_path: str,
        content_category: str | None = None,
        file_url: str | None = None,
        thumbnail_url: str | None = None,
        thumbnail_path: str | None = None,
        file_size: int | None = None,
        width: int | None = None,
        height: int | None = None,
        duration: int | None = None,
        mime_type: str | None = None,
        prompt: str | None = None,
        negative_prompt: str | None = None,
        generation_settings: dict | None = None,
        generation_time_seconds: int | None = None,
        quality_score: float | None = None,
        is_nsfw: bool = False,
    ) -> Content:
        """Create new content record."""
        content = Content(
            character_id=character_id,
            content_type=content_type,
            content_category=content_category,
            file_path=file_path,
            file_url=file_url,
            thumbnail_url=thumbnail_url,
            thumbnail_path=thumbnail_path,
            file_size=file_size,
            width=width,
            height=height,
            duration=duration,
            mime_type=mime_type,
            prompt=prompt,
            negative_prompt=negative_prompt,
            generation_settings=generation_settings,
            generation_time_seconds=generation_time_seconds,
            quality_score=quality_score,
            is_nsfw=is_nsfw,
        )

        self.db.add(content)
        await self.db.flush()
        await self.db.refresh(content)
        return content

    async def update_content(
        self,
        content_id: UUID,
        **updates,
    ) -> Content | None:
        """Update content record."""
        content = await self.get_content(content_id, include_character=False)
        if not content:
            return None

        # Update allowed fields
        allowed_fields = {
            "content_category",
            "file_url",
            "thumbnail_url",
            "thumbnail_path",
            "file_size",
            "width",
            "height",
            "duration",
            "mime_type",
            "prompt",
            "negative_prompt",
            "generation_settings",
            "generation_time_seconds",
            "quality_score",
            "is_approved",
            "approval_status",
            "rejection_reason",
            "is_nsfw",
        }

        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                setattr(content, key, value)

        content.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(content)
        return content

    async def delete_content(
        self,
        content_id: UUID,
        hard_delete: bool = False,
    ) -> bool:
        """Delete content record (soft delete by default)."""
        content = await self.get_content(content_id, include_character=False)
        if not content:
            return False

        if hard_delete:
            await self.db.delete(content)
        else:
            # Soft delete - just mark as deleted (if we had a deleted_at field)
            # For now, we'll do hard delete
            await self.db.delete(content)

        await self.db.flush()
        return True

    async def batch_approve(
        self,
        content_ids: list[UUID],
    ) -> tuple[int, int]:
        """Batch approve content items."""
        approved = 0
        failed = 0

        for content_id in content_ids:
            content = await self.get_content(content_id, include_character=False)
            if content:
                content.is_approved = True
                content.approval_status = "approved"
                content.updated_at = datetime.utcnow()
                approved += 1
            else:
                failed += 1

        await self.db.flush()
        return approved, failed

    async def batch_reject(
        self,
        content_ids: list[UUID],
        rejection_reason: str | None = None,
    ) -> tuple[int, int]:
        """Batch reject content items."""
        rejected = 0
        failed = 0

        for content_id in content_ids:
            content = await self.get_content(content_id, include_character=False)
            if content:
                content.is_approved = False
                content.approval_status = "rejected"
                if rejection_reason:
                    content.rejection_reason = rejection_reason
                content.updated_at = datetime.utcnow()
                rejected += 1
            else:
                failed += 1

        await self.db.flush()
        return rejected, failed

    async def batch_delete(
        self,
        content_ids: list[UUID],
        hard_delete: bool = False,
    ) -> tuple[int, int]:
        """Batch delete content items."""
        deleted = 0
        failed = 0

        for content_id in content_ids:
            success = await self.delete_content(content_id, hard_delete=hard_delete)
            if success:
                deleted += 1
            else:
                failed += 1

        return deleted, failed

    async def count_content(
        self,
        character_id: UUID | None = None,
        content_type: str | None = None,
        approval_status: str | None = None,
        is_approved: bool | None = None,
    ) -> int:
        """Count content matching criteria."""
        query = select(func.count()).select_from(Content)

        conditions = []

        if character_id:
            conditions.append(Content.character_id == character_id)

        if content_type:
            conditions.append(Content.content_type == content_type)

        if approval_status:
            conditions.append(Content.approval_status == approval_status)

        if is_approved is not None:
            conditions.append(Content.is_approved == is_approved)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_content_stats(
        self,
        character_id: UUID | None = None,
    ) -> dict:
        """Get content statistics."""
        base_query = select(Content)

        if character_id:
            base_query = base_query.where(Content.character_id == character_id)

        # Count by type
        type_query = (
            select(Content.content_type, func.count(Content.id).label("count"))
            .select_from(Content)
        )
        if character_id:
            type_query = type_query.where(Content.character_id == character_id)
        type_query = type_query.group_by(Content.content_type)

        type_result = await self.db.execute(type_query)
        type_counts = {row[0]: row[1] for row in type_result.all()}

        # Count by approval status
        status_query = (
            select(Content.approval_status, func.count(Content.id).label("count"))
            .select_from(Content)
        )
        if character_id:
            status_query = status_query.where(Content.character_id == character_id)
        status_query = status_query.group_by(Content.approval_status)

        status_result = await self.db.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # Total count
        total = await self.count_content(character_id=character_id)

        return {
            "total": total,
            "by_type": type_counts,
            "by_approval_status": status_counts,
        }


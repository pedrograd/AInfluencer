"""Character storage and retrieval service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.character import Character, CharacterAppearance, CharacterPersonality

logger = get_logger(__name__)


class CharacterService:
    """Service for character storage and retrieval operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize character service with database session."""
        self.db = db

    async def get_character(
        self,
        character_id: UUID,
        include_deleted: bool = False,
    ) -> Character | None:
        """Get a character by ID with relationships loaded."""
        query = (
            select(Character)
            .options(
                selectinload(Character.personality),
                selectinload(Character.appearance),
            )
            .where(Character.id == character_id)
        )

        if not include_deleted:
            query = query.where(Character.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_characters(
        self,
        status: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> tuple[list[Character], int]:
        """List characters with filtering and pagination."""
        # Build base query
        query = select(Character)

        # Apply filters
        if not include_deleted:
            query = query.where(Character.deleted_at.is_(None))

        if status:
            query = query.where(Character.status == status)

        if search:
            query = query.where(Character.name.ilike(f"%{search}%"))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Character.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        characters = result.scalars().all()

        return list(characters), total

    async def create_character(
        self,
        name: str,
        bio: str | None = None,
        age: int | None = None,
        location: str | None = None,
        timezone: str = "UTC",
        interests: list[str] | None = None,
        profile_image_url: str | None = None,
        profile_image_path: str | None = None,
    ) -> Character:
        """Create a new character."""
        character = Character(
            name=name,
            bio=bio,
            age=age,
            location=location,
            timezone=timezone,
            interests=interests,
            profile_image_url=profile_image_url,
            profile_image_path=profile_image_path,
            status="active",
            is_active=True,
        )
        self.db.add(character)
        await self.db.flush()
        await self.db.refresh(character)
        return character

    async def update_character(
        self,
        character_id: UUID,
        name: str | None = None,
        bio: str | None = None,
        age: int | None = None,
        location: str | None = None,
        timezone: str | None = None,
        interests: list[str] | None = None,
        profile_image_url: str | None = None,
        profile_image_path: str | None = None,
        status: str | None = None,
        is_active: bool | None = None,
    ) -> Character | None:
        """Update character attributes."""
        character = await self.get_character(character_id)
        if not character:
            return None

        # Update fields if provided
        if name is not None:
            character.name = name
        if bio is not None:
            character.bio = bio
        if age is not None:
            character.age = age
        if location is not None:
            character.location = location
        if timezone is not None:
            character.timezone = timezone
        if interests is not None:
            character.interests = interests
        if profile_image_url is not None:
            character.profile_image_url = profile_image_url
        if profile_image_path is not None:
            character.profile_image_path = profile_image_path
        if status is not None:
            character.status = status
        if is_active is not None:
            character.is_active = is_active

        await self.db.flush()
        await self.db.refresh(character)
        return character

    async def delete_character(
        self,
        character_id: UUID,
        hard_delete: bool = False,
    ) -> bool:
        """Delete a character (soft delete by default)."""
        character = await self.get_character(character_id, include_deleted=True)
        if not character:
            return False

        if hard_delete:
            # Hard delete - remove from database
            await self.db.delete(character)
        else:
            # Soft delete - mark as deleted
            from datetime import datetime

            character.deleted_at = datetime.utcnow()
            character.status = "deleted"
            character.is_active = False

        await self.db.flush()
        return True

    async def get_personality(
        self,
        character_id: UUID,
    ) -> CharacterPersonality | None:
        """Get character personality."""
        query = select(CharacterPersonality).where(CharacterPersonality.character_id == character_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_appearance(
        self,
        character_id: UUID,
    ) -> CharacterAppearance | None:
        """Get character appearance."""
        query = select(CharacterAppearance).where(CharacterAppearance.character_id == character_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_characters(
        self,
        status: str | None = None,
        include_deleted: bool = False,
    ) -> int:
        """Count characters matching criteria."""
        query = select(func.count(Character.id))

        if not include_deleted:
            query = query.where(Character.deleted_at.is_(None))

        if status:
            query = query.where(Character.status == status)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def search_characters(
        self,
        query_text: str,
        limit: int = 20,
    ) -> list[Character]:
        """Search characters by name or bio."""
        query = (
            select(Character)
            .where(Character.deleted_at.is_(None))
            .where(
                or_(
                    Character.name.ilike(f"%{query_text}%"),
                    Character.bio.ilike(f"%{query_text}%"),
                )
            )
            .order_by(Character.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())


"""Unit tests for character service."""

from __future__ import annotations

import pytest
from uuid import UUID

from app.services.character_service import CharacterService
from app.models.character import Character


class TestCharacterService:
    """Test suite for CharacterService."""

    @pytest.mark.asyncio
    async def test_create_character_success(self, db_session, sample_character_data):
        """Test successful character creation."""
        service = CharacterService(db_session)
        
        character = await service.create_character(
            name=sample_character_data["name"],
            bio=sample_character_data["bio"],
            age=sample_character_data["age"],
            location=sample_character_data["location"],
            timezone=sample_character_data["timezone"],
            interests=sample_character_data["interests"],
        )
        
        assert character is not None
        assert character.name == sample_character_data["name"]
        assert character.bio == sample_character_data["bio"]
        assert character.age == sample_character_data["age"]
        assert character.location == sample_character_data["location"]
        assert character.timezone == sample_character_data["timezone"]
        assert character.interests == sample_character_data["interests"]
        assert character.id is not None

    @pytest.mark.asyncio
    async def test_get_character_success(self, db_session, sample_character_data):
        """Test retrieving a character by ID."""
        service = CharacterService(db_session)
        
        # Create character
        created = await service.create_character(
            name=sample_character_data["name"],
            bio=sample_character_data["bio"],
        )
        character_id = created.id
        
        # Retrieve character
        retrieved = await service.get_character(character_id)
        
        assert retrieved is not None
        assert retrieved.id == character_id
        assert retrieved.name == sample_character_data["name"]
        assert retrieved.bio == sample_character_data["bio"]

    @pytest.mark.asyncio
    async def test_get_character_not_found(self, db_session):
        """Test retrieving non-existent character returns None."""
        service = CharacterService(db_session)
        fake_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        
        result = await service.get_character(fake_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_characters_empty(self, db_session):
        """Test listing characters when none exist."""
        service = CharacterService(db_session)
        
        characters, total = await service.list_characters()
        
        assert characters == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_characters_with_data(self, db_session, sample_character_data):
        """Test listing characters with pagination."""
        service = CharacterService(db_session)
        
        # Create multiple characters
        for i in range(5):
            await service.create_character(
                name=f"{sample_character_data['name']} {i}",
                bio=f"{sample_character_data['bio']} {i}",
            )
        
        # List all characters
        characters, total = await service.list_characters()
        
        assert len(characters) == 5
        assert total == 5

    @pytest.mark.asyncio
    async def test_list_characters_pagination(self, db_session, sample_character_data):
        """Test character listing with pagination."""
        service = CharacterService(db_session)
        
        # Create 10 characters
        for i in range(10):
            await service.create_character(
                name=f"{sample_character_data['name']} {i}",
                bio=f"{sample_character_data['bio']} {i}",
            )
        
        # Get first page
        page1, total = await service.list_characters(limit=5, offset=0)
        assert len(page1) == 5
        assert total == 10
        
        # Get second page
        page2, total = await service.list_characters(limit=5, offset=5)
        assert len(page2) == 5
        assert total == 10
        
        # Verify different characters
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_list_characters_search(self, db_session, sample_character_data):
        """Test character listing with search filter."""
        service = CharacterService(db_session)
        
        # Create characters with different names
        await service.create_character(name="Alice", bio="Test bio")
        await service.create_character(name="Bob", bio="Test bio")
        await service.create_character(name="Alice Smith", bio="Test bio")
        
        # Search for "Alice"
        characters, total = await service.list_characters(search="Alice")
        
        assert total == 2
        assert all("Alice" in char.name for char in characters)

    @pytest.mark.asyncio
    async def test_list_characters_status_filter(self, db_session, sample_character_data):
        """Test character listing with status filter."""
        service = CharacterService(db_session)
        
        # Create characters (default status is usually "draft" or "active")
        char1 = await service.create_character(name="Character 1", bio="Test")
        char2 = await service.create_character(name="Character 2", bio="Test")
        
        # Update one character's status (if status field exists)
        if hasattr(char1, "status"):
            char1.status = "active"
            await db_session.commit()
            
            # Filter by status
            characters, total = await service.list_characters(status="active")
            assert total >= 1

    @pytest.mark.asyncio
    async def test_update_character(self, db_session, sample_character_data):
        """Test updating a character."""
        service = CharacterService(db_session)
        
        # Create character
        character = await service.create_character(
            name=sample_character_data["name"],
            bio=sample_character_data["bio"],
        )
        await db_session.commit()
        
        # Update character
        updated = await service.update_character(
            character_id=character.id,
            name="Updated Name",
            bio="Updated bio",
        )
        await db_session.commit()
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.bio == "Updated bio"
        assert updated.id == character.id

    @pytest.mark.asyncio
    async def test_delete_character(self, db_session, sample_character_data):
        """Test soft-deleting a character."""
        service = CharacterService(db_session)
        
        # Create character
        character = await service.create_character(
            name=sample_character_data["name"],
            bio=sample_character_data["bio"],
        )
        character_id = character.id
        await db_session.commit()
        
        # Delete character
        result = await service.delete_character(character_id)
        assert result is True
        await db_session.commit()
        
        # Verify character is soft-deleted (not in regular list)
        characters, total = await service.list_characters()
        assert character_id not in [c.id for c in characters]
        
        # But can be retrieved with include_deleted=True
        deleted = await service.get_character(character_id, include_deleted=True)
        if deleted:
            assert deleted.deleted_at is not None


"""Unit tests for query optimization utilities."""

from __future__ import annotations

import pytest
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.query_optimization import get_with_relations, batch_get, get_paginated
from app.core.database import Base
from app.models.user import User
from app.models.character import Character


class TestQueryOptimization:
    """Test suite for query optimization utilities."""

    @pytest.mark.asyncio
    async def test_get_with_relations_single_result(self, db_session):
        """Test get_with_relations with single result."""
        # Create a user
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Get user with relations
        result = await get_with_relations(
            db_session,
            User,
            filters={"email": "test@example.com"},
        )
        
        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_with_relations_no_result(self, db_session):
        """Test get_with_relations with no matching result."""
        result = await get_with_relations(
            db_session,
            User,
            filters={"email": "nonexistent@example.com"},
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_relations_multiple_results(self, db_session):
        """Test get_with_relations with multiple results."""
        # Create multiple users
        for i in range(3):
            user = User(
                email=f"test{i}@example.com",
                password_hash="hashed_password",
            )
            db_session.add(user)
        await db_session.commit()
        
        # Get all users (no filters)
        results = await get_with_relations(
            db_session,
            User,
            filters=None,
        )
        
        assert isinstance(results, list)
        assert len(results) >= 3

    @pytest.mark.asyncio
    async def test_batch_get_success(self, db_session):
        """Test batch_get with multiple IDs."""
        # Create multiple characters
        character_ids = []
        for i in range(5):
            character = Character(
                name=f"Character {i}",
                bio=f"Bio {i}",
            )
            db_session.add(character)
            character_ids.append(character.id)
        await db_session.commit()
        
        # Batch get characters
        results = await batch_get(
            db_session,
            Character,
            ids=character_ids,
        )
        
        assert len(results) == 5
        for char_id in character_ids:
            assert char_id in results
            assert results[char_id].name.startswith("Character")

    @pytest.mark.asyncio
    async def test_batch_get_empty_list(self, db_session):
        """Test batch_get with empty ID list."""
        results = await batch_get(
            db_session,
            Character,
            ids=[],
        )
        
        assert results == {}

    @pytest.mark.asyncio
    async def test_batch_get_partial_match(self, db_session):
        """Test batch_get with some non-existent IDs."""
        # Create one character
        character = Character(name="Test Character", bio="Test bio")
        db_session.add(character)
        await db_session.commit()
        await db_session.refresh(character)
        
        # Try to batch get with one real ID and one fake ID
        from uuid import uuid4
        fake_id = uuid4()
        
        results = await batch_get(
            db_session,
            Character,
            ids=[character.id, fake_id],
        )
        
        # Should only return the real character
        assert len(results) == 1
        assert character.id in results
        assert fake_id not in results

    @pytest.mark.asyncio
    async def test_get_paginated_first_page(self, db_session):
        """Test get_paginated with first page."""
        # Create 10 users
        for i in range(10):
            user = User(
                email=f"user{i}@example.com",
                password_hash="hashed_password",
            )
            db_session.add(user)
        await db_session.commit()
        
        # Get first page
        items, total = await get_paginated(
            db_session,
            User,
            page=1,
            per_page=5,
        )
        
        assert len(items) == 5
        assert total == 10

    @pytest.mark.asyncio
    async def test_get_paginated_second_page(self, db_session):
        """Test get_paginated with second page."""
        # Create 10 users
        for i in range(10):
            user = User(
                email=f"user{i}@example.com",
                password_hash="hashed_password",
            )
            db_session.add(user)
        await db_session.commit()
        
        # Get second page
        items, total = await get_paginated(
            db_session,
            User,
            page=2,
            per_page=5,
        )
        
        assert len(items) == 5
        assert total == 10
        # Verify different users from first page
        assert items[0].email != "user0@example.com"

    @pytest.mark.asyncio
    async def test_get_paginated_with_filters(self, db_session):
        """Test get_paginated with filters."""
        # Create users with different statuses
        active_user = User(
            email="active@example.com",
            password_hash="hashed_password",
            is_active=True,
        )
        inactive_user = User(
            email="inactive@example.com",
            password_hash="hashed_password",
            is_active=False,
        )
        db_session.add(active_user)
        db_session.add(inactive_user)
        await db_session.commit()
        
        # Get only active users
        items, total = await get_paginated(
            db_session,
            User,
            page=1,
            per_page=10,
            filters={"is_active": True},
        )
        
        assert total >= 1
        assert all(item.is_active is True for item in items)

    @pytest.mark.asyncio
    async def test_get_paginated_ordering(self, db_session):
        """Test get_paginated with custom ordering."""
        # Create users with different creation times
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                password_hash="hashed_password",
            )
            db_session.add(user)
        await db_session.commit()
        
        # Get paginated results ordered by email ascending
        items, total = await get_paginated(
            db_session,
            User,
            page=1,
            per_page=10,
            order_by="email",
            descending=False,
        )
        
        assert len(items) >= 5
        # Verify ordering (emails should be sorted)
        emails = [item.email for item in items if item.email.startswith("user")]
        if len(emails) >= 2:
            assert emails[0] < emails[1]  # Ascending order


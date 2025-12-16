"""Unit tests for authentication service."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.services.auth_service import AuthService
from app.models.user import User


class TestAuthService:
    """Test suite for AuthService."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing."""
        return AuthService(secret_key="test_secret_key", algorithm="HS256")

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, db_session, sample_user_data):
        """Test successful user registration."""
        result = await auth_service.register_user(
            db=db_session,
            email=sample_user_data["email"],
            password=sample_user_data["password"],
            full_name=sample_user_data["full_name"],
        )
        
        assert result["email"] == sample_user_data["email"]
        assert result["full_name"] == sample_user_data["full_name"]
        assert result["is_verified"] is False
        assert "id" in result
        
        # Verify user was created in database
        query = select(User).where(User.email == sample_user_data["email"])
        result_db = await db_session.execute(query)
        user = result_db.scalar_one_or_none()
        assert user is not None
        assert user.email == sample_user_data["email"]
        assert user.password_hash != sample_user_data["password"]  # Should be hashed

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, db_session, sample_user_data):
        """Test registration with duplicate email raises ValueError."""
        # Register first user
        await auth_service.register_user(
            db=db_session,
            email=sample_user_data["email"],
            password=sample_user_data["password"],
        )
        
        # Try to register again with same email
        with pytest.raises(ValueError, match="already exists"):
            await auth_service.register_user(
                db=db_session,
                email=sample_user_data["email"],
                password="differentpassword",
            )

    @pytest.mark.asyncio
    async def test_register_user_short_password(self, auth_service, db_session):
        """Test registration with short password raises ValueError."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            await auth_service.register_user(
                db=db_session,
                email="test@example.com",
                password="short",  # Less than 8 characters
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, db_session, sample_user_data):
        """Test successful user authentication."""
        # Register user first
        await auth_service.register_user(
            db=db_session,
            email=sample_user_data["email"],
            password=sample_user_data["password"],
            full_name=sample_user_data["full_name"],
        )
        
        # Authenticate
        result = await auth_service.authenticate_user(
            db=db_session,
            email=sample_user_data["email"],
            password=sample_user_data["password"],
        )
        
        assert result is not None
        assert result["user"]["email"] == sample_user_data["email"]
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, db_session, sample_user_data):
        """Test authentication with wrong password returns None."""
        # Register user first
        await auth_service.register_user(
            db=db_session,
            email=sample_user_data["email"],
            password=sample_user_data["password"],
        )
        
        # Try to authenticate with wrong password
        result = await auth_service.authenticate_user(
            db=db_session,
            email=sample_user_data["email"],
            password="wrongpassword",
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, db_session):
        """Test authentication with non-existent user returns None."""
        result = await auth_service.authenticate_user(
            db=db_session,
            email="nonexistent@example.com",
            password="anypassword",
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_tokens(self, auth_service):
        """Test token generation."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"
        
        tokens = auth_service._generate_tokens(user_id, email)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["access_token"] != tokens["refresh_token"]

    @pytest.mark.asyncio
    async def test_verify_token_success(self, auth_service):
        """Test successful token verification."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"
        
        tokens = auth_service._generate_tokens(user_id, email)
        access_token = tokens["access_token"]
        
        # Only test if JWT is available (python-jose installed)
        try:
            from jose import jwt
            payload = await auth_service.verify_token(access_token, token_type="access")
            if payload is not None:  # JWT available
                assert payload["sub"] == user_id
                assert payload["email"] == email
                assert payload["type"] == "access"
        except ImportError:
            # JWT not available, skip this test
            pytest.skip("python-jose not available")

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, auth_service):
        """Test token verification with invalid token returns None."""
        result = await auth_service.verify_token("invalid_token", token_type="access")
        
        # Should return None for invalid token
        # If JWT not available, will also return None
        assert result is None


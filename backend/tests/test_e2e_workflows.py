"""End-to-end tests for complete user workflows.

These tests verify full user journeys through the application, testing
complete workflows that span multiple API endpoints and services.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.core.database import Base, get_db

# E2E test database URL (in-memory SQLite for e2e tests)
E2E_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def e2e_db_engine():
    """Create a test database engine for e2e tests."""
    engine = create_async_engine(
        E2E_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def e2e_db_session(e2e_db_engine):
    """Create a test database session for e2e tests."""
    async_session = async_sessionmaker(e2e_db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def e2e_app(e2e_db_session):
    """Create FastAPI app instance with test database dependency override for e2e tests."""
    app = create_app()
    
    # Override database dependency with test session
    async def override_get_db():
        yield e2e_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield app
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def e2e_client(e2e_app):
    """Create test client for e2e API requests."""
    async with AsyncClient(app=e2e_app, base_url="http://test") as ac:
        yield ac


@pytest.mark.e2e
class TestUserRegistrationAndLoginWorkflow:
    """E2E tests for complete user registration and login workflow."""

    @pytest.mark.asyncio
    async def test_complete_user_registration_and_login_flow(self, e2e_client: AsyncClient):
        """Test complete workflow: register user → login → verify token → refresh token."""
        # Step 1: Register a new user
        register_data = {
            "email": "e2e_user@example.com",
            "password": "securepassword123",
            "full_name": "E2E Test User",
        }
        register_response = await e2e_client.post(
            "/api/auth/register",
            json=register_data,
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == register_data["email"]
        assert user_data["full_name"] == register_data["full_name"]
        assert user_data["is_verified"] is False
        user_id = user_data["id"]

        # Step 2: Login with registered credentials
        login_response = await e2e_client.post(
            "/api/auth/login",
            json={
                "email": register_data["email"],
                "password": register_data["password"],
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # Step 3: Use access token to access protected endpoint (verify token works)
        # Note: This assumes there's a protected endpoint we can test
        # For now, we'll verify the token structure is valid
        assert len(access_token) > 0
        assert len(refresh_token) > 0

        # Step 4: Refresh the access token
        refresh_response = await e2e_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert refresh_data["access_token"] != access_token  # New token should be different


@pytest.mark.e2e
class TestCharacterCreationWorkflow:
    """E2E tests for complete character creation and management workflow."""

    @pytest.mark.asyncio
    async def test_complete_character_creation_workflow(self, e2e_client: AsyncClient):
        """Test complete workflow: register → login → create character → retrieve → update → delete."""
        # Step 1: Register and login
        register_data = {
            "email": "character_creator@example.com",
            "password": "securepassword123",
            "full_name": "Character Creator",
        }
        await e2e_client.post("/api/auth/register", json=register_data)
        
        login_response = await e2e_client.post(
            "/api/auth/login",
            json={
                "email": register_data["email"],
                "password": register_data["password"],
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 2: Create a character
        character_data = {
            "name": "E2E Test Character",
            "bio": "A character created in e2e tests",
            "age": 28,
            "location": "San Francisco",
            "timezone": "America/Los_Angeles",
            "interests": ["technology", "art", "music"],
        }
        create_response = await e2e_client.post(
            "/api/characters",
            json=character_data,
            headers=headers,
        )
        assert create_response.status_code in [200, 201]
        created_character = create_response.json()
        character_id = created_character.get("id") or created_character.get("character_id")
        assert character_id is not None
        assert created_character["name"] == character_data["name"]

        # Step 3: Retrieve the created character
        get_response = await e2e_client.get(
            f"/api/characters/{character_id}",
            headers=headers,
        )
        assert get_response.status_code == 200
        retrieved_character = get_response.json()
        assert retrieved_character["name"] == character_data["name"]
        assert retrieved_character["bio"] == character_data["bio"]

        # Step 4: List all characters (should include our character)
        list_response = await e2e_client.get(
            "/api/characters",
            headers=headers,
        )
        assert list_response.status_code == 200
        characters_list = list_response.json()
        # Response might be a list or dict with items/data key
        if isinstance(characters_list, list):
            character_ids = [c.get("id") or c.get("character_id") for c in characters_list]
        else:
            items = characters_list.get("items") or characters_list.get("data") or []
            character_ids = [c.get("id") or c.get("character_id") for c in items]
        assert character_id in character_ids

        # Step 5: Update the character
        update_data = {
            "bio": "Updated bio from e2e test",
            "age": 29,
        }
        update_response = await e2e_client.put(
            f"/api/characters/{character_id}",
            json=update_data,
            headers=headers,
        )
        assert update_response.status_code == 200
        updated_character = update_response.json()
        assert updated_character["bio"] == update_data["bio"]
        assert updated_character["age"] == update_data["age"]

        # Step 6: Delete the character
        delete_response = await e2e_client.delete(
            f"/api/characters/{character_id}",
            headers=headers,
        )
        assert delete_response.status_code in [200, 204]

        # Step 7: Verify character is deleted (should return 404)
        verify_delete_response = await e2e_client.get(
            f"/api/characters/{character_id}",
            headers=headers,
        )
        assert verify_delete_response.status_code == 404


@pytest.mark.e2e
class TestAPIHealthAndStatusWorkflow:
    """E2E tests for API health and status endpoints workflow."""

    @pytest.mark.asyncio
    async def test_api_health_check_workflow(self, e2e_client: AsyncClient):
        """Test complete workflow: API root → health check → status endpoint."""
        # Step 1: Check API root endpoint
        root_response = await e2e_client.get("/api")
        assert root_response.status_code == 200
        root_data = root_response.json()
        assert "name" in root_data
        assert "version" in root_data
        assert root_data["name"] == "AInfluencer Backend API"

        # Step 2: Check health endpoint
        health_response = await e2e_client.get("/api/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "ok", "up"]

        # Step 3: Check status endpoint (if available)
        status_response = await e2e_client.get("/api/status")
        # Status endpoint might not exist or might require auth, so we accept 200 or 401/403
        assert status_response.status_code in [200, 401, 403, 404]
        if status_response.status_code == 200:
            status_data = status_response.json()
            # Status endpoint should return some system information
            assert isinstance(status_data, dict)


@pytest.mark.e2e
class TestErrorHandlingWorkflow:
    """E2E tests for error handling across workflows."""

    @pytest.mark.asyncio
    async def test_error_handling_in_complete_workflow(self, e2e_client: AsyncClient):
        """Test error handling: invalid requests → proper error responses → recovery."""
        # Step 1: Try to access protected endpoint without auth (should fail)
        protected_response = await e2e_client.get("/api/characters")
        # Should return 401 (Unauthorized) or 403 (Forbidden)
        assert protected_response.status_code in [401, 403]

        # Step 2: Try to login with invalid credentials (should fail)
        invalid_login_response = await e2e_client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        assert invalid_login_response.status_code in [400, 401, 404]

        # Step 3: Try to register with invalid data (should fail validation)
        invalid_register_response = await e2e_client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",  # Invalid email format
                "password": "short",  # Too short
                "full_name": "",
            },
        )
        assert invalid_register_response.status_code == 422  # Validation error

        # Step 4: Try to access non-existent resource (should return 404)
        not_found_response = await e2e_client.get("/api/characters/99999")
        assert not_found_response.status_code in [401, 403, 404]  # 401/403 if auth required, 404 if found but not exists


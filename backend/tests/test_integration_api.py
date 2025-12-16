"""Integration tests for API endpoints.

These tests verify the full request/response cycle through the FastAPI application,
including database operations, authentication, and service integrations.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.core.database import Base, get_db

# Integration test database URL (in-memory SQLite for integration tests)
INTEGRATION_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db_engine():
    """Create a test database engine for integration tests."""
    engine = create_async_engine(
        INTEGRATION_TEST_DATABASE_URL,
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
async def test_db_session(test_db_engine):
    """Create a test database session for integration tests."""
    async_session = async_sessionmaker(test_db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def app(test_db_session):
    """Create FastAPI app instance with test database dependency override."""
    app = create_app()
    
    # Override database dependency with test session
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield app
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    """Create test client for API requests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        "name": "Test Character",
        "bio": "A test character for integration testing",
        "age": 25,
        "location": "Test Location",
        "timezone": "UTC",
        "interests": ["testing", "coding"],
    }


@pytest.mark.integration
class TestAuthAPI:
    """Integration tests for authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, sample_user_data):
        """Test successful user registration via API."""
        response = await client.post(
            "/api/auth/register",
            json=sample_user_data,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert data["is_verified"] is False
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient, sample_user_data):
        """Test registration with duplicate email returns error."""
        # Register first user
        response1 = await client.post(
            "/api/auth/register",
            json=sample_user_data,
        )
        assert response1.status_code == 201
        
        # Try to register again with same email
        response2 = await client.post(
            "/api/auth/register",
            json=sample_user_data,
        )
        assert response2.status_code == 400
        assert "email" in response2.json().get("detail", "").lower() or "already" in response2.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_register_user_short_password(self, client: AsyncClient, sample_user_data):
        """Test registration with short password returns validation error."""
        invalid_data = {**sample_user_data, "password": "short"}
        response = await client.post(
            "/api/auth/register",
            json=invalid_data,
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user_data):
        """Test successful user login via API."""
        # Register user first
        register_response = await client.post(
            "/api/auth/register",
            json=sample_user_data,
        )
        assert register_response.status_code == 201
        
        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == sample_user_data["email"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, sample_user_data):
        """Test login with wrong password returns error."""
        # Register user first
        await client.post(
            "/api/auth/register",
            json=sample_user_data,
        )
        
        # Try to login with wrong password
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": "wrongpassword",
            },
        )
        
        assert login_response.status_code == 401
        assert "invalid" in login_response.json().get("detail", "").lower() or "password" in login_response.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user returns error."""
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword",
            },
        )
        
        assert login_response.status_code == 401
        assert "not found" in login_response.json().get("detail", "").lower() or "invalid" in login_response.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, sample_user_data):
        """Test successful token refresh via API."""
        # Register and login
        await client.post("/api/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        refresh_response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test token refresh with invalid token returns error."""
        refresh_response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )
        
        assert refresh_response.status_code == 401


@pytest.mark.integration
class TestCharacterAPI:
    """Integration tests for character API endpoints."""

    @pytest.fixture
    async def auth_token(self, client: AsyncClient, sample_user_data):
        """Get authentication token for protected endpoints."""
        # Register and login
        await client.post("/api/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        return login_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_create_character_success(self, client: AsyncClient, auth_token, sample_character_data):
        """Test successful character creation via API."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = await client.post(
            "/api/characters",
            json=sample_character_data,
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_character_data["name"]
        assert data["bio"] == sample_character_data["bio"]
        assert data["age"] == sample_character_data["age"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_character_without_auth(self, client: AsyncClient, sample_character_data):
        """Test character creation without authentication (may or may not require auth)."""
        response = await client.post(
            "/api/characters",
            json=sample_character_data,
        )
        
        # Character endpoints may or may not require auth
        # If auth is required, expect 401; if not, expect 201
        assert response.status_code in (201, 401)

    @pytest.mark.asyncio
    async def test_get_character_success(self, client: AsyncClient, auth_token, sample_character_data):
        """Test successful character retrieval via API."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create character
        create_response = await client.post(
            "/api/characters",
            json=sample_character_data,
            headers=headers,
        )
        character_id = create_response.json()["id"]
        
        # Get character
        get_response = await client.get(
            f"/api/characters/{character_id}",
            headers=headers,
        )
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == character_id
        assert data["name"] == sample_character_data["name"]

    @pytest.mark.asyncio
    async def test_get_character_not_found(self, client: AsyncClient, auth_token):
        """Test character retrieval with nonexistent ID returns error."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = await client.get(
            "/api/characters/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_characters_success(self, client: AsyncClient, auth_token, sample_character_data):
        """Test successful character listing via API."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create multiple characters
        for i in range(3):
            character_data = {**sample_character_data, "name": f"{sample_character_data['name']} {i+1}"}
            await client.post(
                "/api/characters",
                json=character_data,
                headers=headers,
            )
        
        # List characters
        list_response = await client.get(
            "/api/characters",
            headers=headers,
        )
        
        assert list_response.status_code == 200
        data = list_response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_update_character_success(self, client: AsyncClient, auth_token, sample_character_data):
        """Test successful character update via API."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create character
        create_response = await client.post(
            "/api/characters",
            json=sample_character_data,
            headers=headers,
        )
        character_id = create_response.json()["id"]
        
        # Update character
        update_data = {"name": "Updated Character Name", "bio": "Updated bio"}
        update_response = await client.put(
            f"/api/characters/{character_id}",
            json=update_data,
            headers=headers,
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Character Name"
        assert data["bio"] == "Updated bio"

    @pytest.mark.asyncio
    async def test_delete_character_success(self, client: AsyncClient, auth_token, sample_character_data):
        """Test successful character deletion via API."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create character
        create_response = await client.post(
            "/api/characters",
            json=sample_character_data,
            headers=headers,
        )
        character_id = create_response.json()["id"]
        
        # Delete character
        delete_response = await client.delete(
            f"/api/characters/{character_id}",
            headers=headers,
        )
        
        assert delete_response.status_code == 200 or delete_response.status_code == 204
        
        # Verify character is deleted
        get_response = await client.get(
            f"/api/characters/{character_id}",
            headers=headers,
        )
        assert get_response.status_code == 404


@pytest.mark.integration
class TestAPIHealth:
    """Integration tests for API health and status endpoints."""

    @pytest.mark.asyncio
    async def test_api_root(self, client: AsyncClient):
        """Test API root endpoint."""
        response = await client.get("/api")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "AInfluencer Backend API"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy" or data["status"] == "ok"


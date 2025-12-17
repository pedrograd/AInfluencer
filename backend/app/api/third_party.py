"""Third-party API integration endpoints.

Provides REST endpoints for:
- API key management (create, list, revoke, delete)
- Public API endpoints for third-party integrations
- Webhook management (future)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_from_token
from app.core.database import get_db
from app.core.middleware import limiter
from app.models.api_key import APIKey
from app.models.user import User
from app.services.api_key_service import api_key_service

router = APIRouter()


# Request/Response Models
class CreateAPIKeyRequest(BaseModel):
    """Request model for creating an API key."""

    name: str = Field(..., min_length=1, max_length=255, description="Human-readable name for the API key")
    scopes: list[str] | None = Field(None, description="List of permission scopes (default: ['read:*'])")
    rate_limit: int = Field(1000, ge=1, le=100000, description="Maximum requests per hour (default: 1000)")
    expires_in_days: int | None = Field(None, ge=1, description="Number of days until expiration (None for no expiration)")


class CreateAPIKeyResponse(BaseModel):
    """Response model for creating an API key."""

    id: str
    key: str  # Only returned once at creation
    name: str
    scopes: list[str]
    rate_limit: int
    expires_at: str | None
    created_at: str


class APIKeyResponse(BaseModel):
    """Response model for API key information (without the actual key)."""

    id: str
    name: str
    scopes: list[str]
    rate_limit: int
    is_active: bool
    expires_at: str | None
    last_used_at: str | None
    created_at: str


class APIKeyListResponse(BaseModel):
    """Response model for listing API keys."""

    keys: list[APIKeyResponse]


# API Key Authentication Dependency
async def get_api_key_from_header(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """Extract and verify API key from X-API-Key header, return API key record.
    
    This dependency extracts the API key from the X-API-Key header,
    verifies it, and returns the authenticated API key record.
    
    Args:
        x_api_key: X-API-Key header value.
        db: Database session.
        
    Returns:
        APIKey: Authenticated API key object.
        
    Raises:
        HTTPException: If API key is missing, invalid, expired, or inactive.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    api_key = await api_key_service.verify_api_key(db, x_api_key)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not api_key.is_valid():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive or expired",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


async def get_user_from_api_key(
    api_key: APIKey = Depends(get_api_key_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the user associated with an API key.
    
    Args:
        api_key: Authenticated API key (from dependency).
        db: Database session.
        
    Returns:
        User: User associated with the API key.
        
    Raises:
        HTTPException: If user not found or inactive.
    """
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with API key not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


# API Key Management Endpoints
@router.post("/keys", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_api_key(
    http_request: Request,
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> CreateAPIKeyResponse:
    """Create a new API key for the authenticated user.
    
    The API key value is only returned once at creation. Store it securely.
    
    Args:
        request: API key creation request.
        current_user: Authenticated user (from JWT token).
        db: Database session.
        
    Returns:
        CreateAPIKeyResponse: Created API key information including the key value.
        
    Raises:
        HTTPException: If creation fails.
    """
    try:
        key_data = await api_key_service.create_api_key(
            db=db,
            user_id=str(current_user.id),
            name=request.name,
            scopes=request.scopes,
            rate_limit=request.rate_limit,
            expires_in_days=request.expires_in_days,
        )
        return CreateAPIKeyResponse(**key_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/keys", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> APIKeyListResponse:
    """List all API keys for the authenticated user.
    
    Args:
        current_user: Authenticated user (from JWT token).
        db: Database session.
        
    Returns:
        APIKeyListResponse: List of API keys (without the actual key values).
    """
    keys = await api_key_service.list_api_keys(db, str(current_user.id))
    return APIKeyListResponse(keys=[APIKeyResponse(**key) for key in keys])


@router.post("/keys/{key_id}/revoke", status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def revoke_api_key(
    http_request: Request,
    key_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Revoke (deactivate) an API key.
    
    Args:
        key_id: UUID of the API key to revoke.
        current_user: Authenticated user (from JWT token).
        db: Database session.
        
    Returns:
        Success message.
        
    Raises:
        HTTPException: If key not found or unauthorized.
    """
    success = await api_key_service.revoke_api_key(db, key_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or unauthorized",
        )
    return {"success": True, "message": "API key revoked successfully"}


@router.delete("/keys/{key_id}", status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def delete_api_key(
    http_request: Request,
    key_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete an API key (soft delete).
    
    Args:
        key_id: UUID of the API key to delete.
        current_user: Authenticated user (from JWT token).
        db: Database session.
        
    Returns:
        Success message.
        
    Raises:
        HTTPException: If key not found or unauthorized.
    """
    success = await api_key_service.delete_api_key(db, key_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or unauthorized",
        )
    return {"success": True, "message": "API key deleted successfully"}


@router.get("/keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """Get details of a specific API key.
    
    Args:
        key_id: UUID of the API key.
        current_user: Authenticated user (from JWT token).
        db: Database session.
        
    Returns:
        APIKeyResponse: API key information (without the actual key value).
        
    Raises:
        HTTPException: If key not found or unauthorized.
    """
    from sqlalchemy import select

    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
            APIKey.deleted_at.is_(None),
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or unauthorized",
        )

    return APIKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        scopes=api_key.scopes,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        created_at=api_key.created_at.isoformat(),
    )

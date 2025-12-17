"""Public API endpoints for third-party integrations.

This module provides a subset of API endpoints that can be accessed using
API keys instead of JWT tokens. These endpoints are designed for third-party
integrations and have rate limiting and scope-based access control.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.third_party import get_api_key_from_header, get_user_from_api_key
from app.core.database import get_db
from app.core.middleware import limiter
from app.models.api_key import APIKey
from app.models.character import Character
from app.models.user import User

router = APIRouter(prefix="/public", tags=["public-api"])


def require_scope(scope: str):
    """Dependency factory for requiring a specific API key scope.
    
    Args:
        scope: Required permission scope (e.g., "read:characters").
        
    Returns:
        Dependency function that checks if the API key has the required scope.
    """
    async def check_scope(
        api_key: APIKey = Depends(get_api_key_from_header),
    ) -> APIKey:
        if not api_key.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key does not have required scope: {scope}",
            )
        return api_key

    return check_scope


@router.get("/health")
async def public_health() -> dict[str, Any]:
    """Public health check endpoint (no authentication required).
    
    Returns:
        Health status information.
    """
    return {
        "status": "ok",
        "service": "AInfluencer Public API",
        "version": "1.0.0",
    }


@router.get("/characters", response_model=list[dict[str, Any]])
async def list_characters_public(
    api_key: APIKey = Depends(require_scope("read:characters")),
    current_user: User = Depends(get_user_from_api_key),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List characters for the API key owner (public API endpoint).
    
    This endpoint requires an API key with "read:characters" scope.
    
    Args:
        api_key: Authenticated API key (from dependency).
        current_user: User associated with the API key.
        db: Database session.
        limit: Maximum number of characters to return (default: 50, max: 100).
        offset: Number of characters to skip (default: 0).
        
    Returns:
        List of character dictionaries.
        
    Raises:
        HTTPException: If scope check fails or database error.
    """
    if limit > 100:
        limit = 100

    result = await db.execute(
        select(Character)
        .where(Character.user_id == current_user.id)
        .limit(limit)
        .offset(offset)
        .order_by(Character.created_at.desc())
    )
    characters = result.scalars().all()

    return [
        {
            "id": str(char.id),
            "name": char.name,
            "description": char.description,
            "personality": char.personality.personality_traits if char.personality else None,
            "created_at": char.created_at.isoformat() if char.created_at else None,
        }
        for char in characters
    ]


@router.get("/characters/{character_id}", response_model=dict[str, Any])
async def get_character_public(
    character_id: str,
    api_key: APIKey = Depends(require_scope("read:characters")),
    current_user: User = Depends(get_user_from_api_key),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a specific character by ID (public API endpoint).
    
    This endpoint requires an API key with "read:characters" scope.
    
    Args:
        character_id: UUID of the character.
        api_key: Authenticated API key (from dependency).
        current_user: User associated with the API key.
        db: Database session.
        
    Returns:
        Character dictionary.
        
    Raises:
        HTTPException: If character not found, unauthorized, or scope check fails.
    """
    from uuid import UUID

    try:
        char_uuid = UUID(character_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid character ID format",
        )

    result = await db.execute(
        select(Character).where(
            Character.id == char_uuid,
            Character.user_id == current_user.id,
        )
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found or unauthorized",
        )

    return {
        "id": str(character.id),
        "name": character.name,
        "description": character.description,
        "personality": character.personality.personality_traits if character.personality else None,
        "created_at": character.created_at.isoformat() if character.created_at else None,
        "updated_at": character.updated_at.isoformat() if character.updated_at else None,
    }


@router.get("/me", response_model=dict[str, Any])
async def get_api_user_info(
    api_key: APIKey = Depends(get_api_key_from_header),
    current_user: User = Depends(get_user_from_api_key),
) -> dict[str, Any]:
    """Get information about the user associated with the API key.
    
    Args:
        api_key: Authenticated API key (from dependency).
        current_user: User associated with the API key.
        
    Returns:
        User information dictionary.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "api_key": {
            "id": str(api_key.id),
            "name": api_key.name,
            "scopes": api_key.scopes,
            "rate_limit": api_key.rate_limit,
        },
    }

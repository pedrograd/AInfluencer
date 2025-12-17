"""API Key service for third-party integrations.

This service provides functionality for:
- Generating secure API keys
- Hashing and verifying API keys
- Managing API key lifecycle (create, revoke, list)
- Scope validation
"""

from __future__ import annotations

import secrets
from typing import Any

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.api_key import APIKey
from app.models.user import User

logger = get_logger(__name__)


class APIKeyService:
    """Service for managing API keys."""

    @staticmethod
    def generate_key() -> str:
        """Generate a secure random API key.
        
        Returns:
            A URL-safe base64-encoded random string suitable for use as an API key.
        """
        # Generate 32 bytes of random data and encode as URL-safe base64
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for secure storage.
        
        Args:
            key: Plain text API key.
            
        Returns:
            Bcrypt hash of the API key.
        """
        return bcrypt.hashpw(key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_key(key: str, key_hash: str) -> bool:
        """Verify an API key against its hash.
        
        Args:
            key: Plain text API key to verify.
            key_hash: Stored hash of the API key.
            
        Returns:
            True if the key matches the hash, False otherwise.
        """
        try:
            return bcrypt.checkpw(key.encode("utf-8"), key_hash.encode("utf-8"))
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return False

    async def create_api_key(
        self,
        db: AsyncSession,
        user_id: str,
        name: str,
        scopes: list[str] | None = None,
        rate_limit: int = 1000,
        expires_in_days: int | None = None,
    ) -> dict[str, Any]:
        """Create a new API key for a user.
        
        Args:
            db: Database session.
            user_id: UUID of the user who owns the key.
            name: Human-readable name for the key.
            scopes: List of permission scopes (default: ["read:*"]).
            rate_limit: Maximum requests per hour (default: 1000).
            expires_in_days: Number of days until expiration (None for no expiration).
            
        Returns:
            Dictionary containing the API key data including the plain text key
            (only returned once at creation).
            
        Raises:
            ValueError: If user not found or invalid parameters.
        """
        # Verify user exists
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Generate and hash key
        plain_key = self.generate_key()
        key_hash = self.hash_key(plain_key)

        # Set default scopes if not provided
        if scopes is None:
            scopes = ["read:*"]

        # Calculate expiration if specified
        from datetime import datetime, timedelta
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create API key record
        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            scopes=scopes,
            rate_limit=rate_limit,
            expires_at=expires_at,
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        logger.info(f"Created API key {api_key.id} for user {user_id}")

        return {
            "id": str(api_key.id),
            "key": plain_key,  # Only returned once
            "name": api_key.name,
            "scopes": api_key.scopes,
            "rate_limit": api_key.rate_limit,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created_at": api_key.created_at.isoformat(),
        }

    async def verify_api_key(self, db: AsyncSession, key: str) -> APIKey | None:
        """Verify an API key and return the key record if valid.
        
        Args:
            db: Database session.
            key: Plain text API key to verify.
            
        Returns:
            APIKey object if valid, None otherwise.
        """
        # Get all active API keys (this is a limitation - in production, you'd want
        # a more efficient lookup, but for MVP this is acceptable)
        result = await db.execute(
            select(APIKey).where(
                APIKey.is_active == True,  # noqa: E712
                APIKey.deleted_at.is_(None),
            )
        )
        api_keys = result.scalars().all()

        # Check each key (in production, use a more efficient method)
        for api_key in api_keys:
            if self.verify_key(key, api_key.key_hash):
                # Check if expired
                if api_key.is_expired():
                    logger.warning(f"API key {api_key.id} has expired")
                    return None

                # Update last_used_at
                from datetime import datetime
                api_key.last_used_at = datetime.utcnow()
                await db.commit()

                return api_key

        return None

    async def list_api_keys(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """List all API keys for a user.
        
        Args:
            db: Database session.
            user_id: UUID of the user.
            
        Returns:
            List of API key dictionaries (without the actual key value).
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.user_id == user_id,
                APIKey.deleted_at.is_(None),
            ).order_by(APIKey.created_at.desc())
        )
        api_keys = result.scalars().all()

        return [
            {
                "id": str(key.id),
                "name": key.name,
                "scopes": key.scopes,
                "rate_limit": key.rate_limit,
                "is_active": key.is_active,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "created_at": key.created_at.isoformat(),
            }
            for key in api_keys
        ]

    async def revoke_api_key(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str,
    ) -> bool:
        """Revoke (deactivate) an API key.
        
        Args:
            db: Database session.
            key_id: UUID of the API key to revoke.
            user_id: UUID of the user (for authorization check).
            
        Returns:
            True if revoked successfully, False if not found or unauthorized.
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.id == key_id,
                APIKey.user_id == user_id,
                APIKey.deleted_at.is_(None),
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        api_key.is_active = False
        await db.commit()

        logger.info(f"Revoked API key {key_id} for user {user_id}")
        return True

    async def delete_api_key(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str,
    ) -> bool:
        """Soft-delete an API key.
        
        Args:
            db: Database session.
            key_id: UUID of the API key to delete.
            user_id: UUID of the user (for authorization check).
            
        Returns:
            True if deleted successfully, False if not found or unauthorized.
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.id == key_id,
                APIKey.user_id == user_id,
                APIKey.deleted_at.is_(None),
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        from datetime import datetime
        api_key.deleted_at = datetime.utcnow()
        api_key.is_active = False
        await db.commit()

        logger.info(f"Deleted API key {key_id} for user {user_id}")
        return True


# Singleton instance
api_key_service = APIKeyService()

"""Health check API endpoint for service monitoring.

This module provides a simple health check endpoint that returns the API
operational status. Used by monitoring systems and load balancers to verify
service availability.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.redis_client import get_redis

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """
    Health check endpoint.
    
    Returns a status response indicating the API and Redis are operational.
    Used by monitoring systems and load balancers to verify service availability.
    
    Returns:
        dict: Status response with "ok" status and Redis connectivity check
    """
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    
    return {
        "status": "ok",
        "redis": redis_status
    }

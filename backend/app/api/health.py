"""Health check API endpoint for service monitoring.

This module provides a simple health check endpoint that returns the API
operational status. Used by monitoring systems and load balancers to verify
service availability.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """
    Health check endpoint.
    
    Returns a simple status response indicating the API is operational.
    Used by monitoring systems and load balancers to verify service availability.
    
    Returns:
        dict: Status response with "ok" status
    """
    return {"status": "ok"}

"""Comprehensive caching strategies for the AInfluencer application.

This module provides caching utilities for:
- API response caching (GET endpoints)
- Query result caching (via query_cache.py)
- Cache invalidation strategies
- Cache key management
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from functools import wraps
from typing import Any, Callable, TypeVar

from fastapi import Request, Response
from starlette.responses import JSONResponse

from app.core.redis_client import get_redis

T = TypeVar("T")

# Cache TTL constants (in seconds)
CACHE_TTL = {
    "character": 300,  # 5 minutes - character data
    "content_metadata": 600,  # 10 minutes - content metadata
    "platform_status": 60,  # 1 minute - platform account status
    "analytics": 900,  # 15 minutes - analytics data
    "system_status": 5,  # 5 seconds - system status (frequently changing)
    "api_response": 60,  # 1 minute - general API responses
    "checkpoint_list": 60,  # 1 minute - ComfyUI checkpoint lists
    "sampler_list": 60,  # 1 minute - ComfyUI sampler lists
    "scheduler_list": 60,  # 1 minute - ComfyUI scheduler lists
}


def generate_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """Generate a cache key from prefix and arguments.
    
    Args:
        prefix: Cache key prefix (e.g., "character", "api:status")
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key
        
    Returns:
        Cache key string in format "prefix:hash"
        
    Example:
        >>> generate_cache_key("character", "char_123")
        'character:hash_of_char_123'
        >>> generate_cache_key("api:status", user_id="123", filter="active")
        'api:status:hash_of_user_id=123&filter=active'
    """
    # Sort kwargs for consistent key generation
    sorted_kwargs = sorted(kwargs.items())
    
    # Create a deterministic string representation
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted_kwargs])
    key_string = "&".join(key_parts)
    
    # Hash the key string for shorter cache keys
    if key_string:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:12]
        return f"{prefix}:{key_hash}"
    return prefix


async def get_cached_response(cache_key: str) -> dict[str, Any] | None:
    """Get a cached API response.
    
    Args:
        cache_key: Cache key for the response
        
    Returns:
        Cached response data as dict, or None if not found
    """
    redis = await get_redis()
    cached_data = await redis.get(cache_key)
    if cached_data:
        try:
            return json.loads(cached_data)
        except (json.JSONDecodeError, TypeError):
            return None
    return None


async def set_cached_response(cache_key: str, data: dict[str, Any], ttl: int) -> None:
    """Cache an API response.
    
    Args:
        cache_key: Cache key for the response
        data: Response data to cache
        ttl: Time-to-live in seconds
    """
    redis = await get_redis()
    await redis.setex(cache_key, ttl, json.dumps(data))


def cache_response(ttl: int = CACHE_TTL["api_response"], key_prefix: str | None = None):
    """Decorator to cache FastAPI endpoint responses.
    
    This decorator caches GET endpoint responses in Redis for the specified TTL.
    Cache keys are generated from the request path and query parameters.
    Works with both sync and async endpoints.
    
    Args:
        ttl: Time-to-live in seconds (default: 60 seconds)
        key_prefix: Optional prefix for cache keys (default: "api:response")
        
    Example:
        ```python
        @router.get("/characters/{character_id}")
        @cache_response(ttl=300, key_prefix="character")
        async def get_character(character_id: str, request: Request):
            return {"id": character_id, "name": "Character Name"}
        ```
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract request from kwargs or args
            request: Request | None = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                # Generate cache key from path and query params
                prefix = key_prefix or f"api:{func.__name__}"
                query_params = dict(request.query_params)
                cache_key = generate_cache_key(prefix, request.url.path, **query_params)
                
                # Try to get from cache
                cached = await get_cached_response(cache_key)
                if cached is not None:
                    return JSONResponse(content=cached)
            
            # Execute the function (async)
            result = await func(*args, **kwargs)
            
            # Cache the result
            if request:
                prefix = key_prefix or f"api:{func.__name__}"
                query_params = dict(request.query_params)
                cache_key = generate_cache_key(prefix, request.url.path, **query_params)
                
                if isinstance(result, dict):
                    await set_cached_response(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we need to run async operations
            import asyncio
            
            # Extract request from kwargs or args
            request: Request | None = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                # Generate cache key from path and query params
                prefix = key_prefix or f"api:{func.__name__}"
                query_params = dict(request.query_params)
                cache_key = generate_cache_key(prefix, request.url.path, **query_params)
                
                # Try to get from cache (sync wrapper for async call)
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                cached = loop.run_until_complete(get_cached_response(cache_key))
                if cached is not None:
                    return JSONResponse(content=cached)
            
            # Execute the function (sync)
            result = func(*args, **kwargs)
            
            # Cache the result
            if request and isinstance(result, dict):
                prefix = key_prefix or f"api:{func.__name__}"
                query_params = dict(request.query_params)
                cache_key = generate_cache_key(prefix, request.url.path, **query_params)
                
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(set_cached_response(cache_key, result, ttl))
            
            return result
        
        # Determine if function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


async def invalidate_cache_by_pattern(pattern: str) -> int:
    """Invalidate all cache keys matching a pattern.
    
    This is a convenience wrapper around query_cache.invalidate_cache_pattern.
    
    Args:
        pattern: Redis pattern (e.g., "character:*", "api:status:*")
        
    Returns:
        Number of keys deleted
        
    Example:
        >>> await invalidate_cache_by_pattern("character:*")
        5  # 5 character cache entries deleted
    """
    from app.services.query_cache import invalidate_cache_pattern
    return await invalidate_cache_pattern(pattern)


async def invalidate_character_cache(character_id: str | None = None) -> int:
    """Invalidate character-related cache entries.
    
    Args:
        character_id: Optional specific character ID to invalidate.
                     If None, invalidates all character caches.
        
    Returns:
        Number of keys deleted
    """
    if character_id:
        from app.services.query_cache import invalidate_cache
        await invalidate_cache(f"character:{character_id}")
        return 1
    return await invalidate_cache_by_pattern("character:*")


async def invalidate_content_cache(content_id: str | None = None) -> int:
    """Invalidate content-related cache entries.
    
    Args:
        content_id: Optional specific content ID to invalidate.
                   If None, invalidates all content caches.
        
    Returns:
        Number of keys deleted
    """
    if content_id:
        from app.services.query_cache import invalidate_cache
        await invalidate_cache(f"content:{content_id}")
        return 1
    return await invalidate_cache_by_pattern("content:*")


async def invalidate_api_cache(endpoint: str | None = None) -> int:
    """Invalidate API response cache entries.
    
    Args:
        endpoint: Optional specific endpoint to invalidate (e.g., "status", "characters").
                 If None, invalidates all API response caches.
        
    Returns:
        Number of keys deleted
    """
    if endpoint:
        pattern = f"api:{endpoint}:*"
    else:
        pattern = "api:*"
    return await invalidate_cache_by_pattern(pattern)


def get_cache_ttl(cache_type: str) -> int:
    """Get the TTL for a specific cache type.
    
    Args:
        cache_type: Cache type (e.g., "character", "content_metadata", "api_response")
        
    Returns:
        TTL in seconds, or default 60 if type not found
    """
    return CACHE_TTL.get(cache_type, 60)


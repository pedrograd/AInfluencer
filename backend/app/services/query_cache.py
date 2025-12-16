"""Query caching service for database query optimization.

This module provides utilities for caching database query results in Redis
to reduce database load and improve response times for frequently accessed data.
"""

from __future__ import annotations

import json
from typing import Any, Callable, TypeVar

from app.core.redis_client import get_redis

T = TypeVar("T")


async def get_cached_query(
    cache_key: str,
    query_fn: Callable[[], Any],
    ttl: int = 300,
    deserialize_fn: Callable[[str], T] | None = None,
) -> T:
    """Execute a query with Redis caching.
    
    Args:
        cache_key: Unique cache key for this query result
        query_fn: Async function that executes the database query
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        deserialize_fn: Optional function to deserialize cached JSON data
        
    Returns:
        The query result (either from cache or freshly executed)
        
    Example:
        ```python
        async def get_character(character_id: str):
            cache_key = f"character:{character_id}"
            return await get_cached_query(
                cache_key,
                lambda: db.query(Character).filter(Character.id == character_id).first(),
                ttl=300,
                deserialize_fn=lambda data: Character(**json.loads(data))
            )
        ```
    """
    redis = await get_redis()
    
    # Try to get from cache
    cached_data = await redis.get(cache_key)
    if cached_data:
        if deserialize_fn:
            return deserialize_fn(cached_data)
        try:
            return json.loads(cached_data)
        except (json.JSONDecodeError, TypeError):
            # If deserialization fails, execute query
            pass
    
    # Cache miss - execute query
    result = await query_fn()
    
    # Cache the result
    if result is not None:
        if isinstance(result, (dict, list, str, int, float, bool, type(None))):
            serialized = json.dumps(result)
        else:
            # For ORM objects, serialize to dict if possible
            if hasattr(result, "__dict__"):
                serialized = json.dumps({k: v for k, v in result.__dict__.items() if not k.startswith("_")})
            else:
                serialized = json.dumps(str(result))
        
        await redis.setex(cache_key, ttl, serialized)
    
    return result


async def invalidate_cache(cache_key: str) -> None:
    """Invalidate a specific cache key.
    
    Args:
        cache_key: The cache key to invalidate
    """
    redis = await get_redis()
    await redis.delete(cache_key)


async def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate all cache keys matching a pattern.
    
    Args:
        pattern: Redis pattern (e.g., "character:*", "content:*")
        
    Returns:
        Number of keys deleted
    """
    redis = await get_redis()
    keys = []
    async for key in redis.scan_iter(match=pattern):
        keys.append(key)
    
    if keys:
        return await redis.delete(*keys)
    return 0


async def get_cached_list(
    cache_key: str,
    query_fn: Callable[[], Any],
    ttl: int = 300,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Execute a list query with Redis caching.
    
    Args:
        cache_key: Unique cache key for this query result
        query_fn: Async function that executes the database query
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        limit: Optional limit to apply to cached results
        
    Returns:
        List of query results (either from cache or freshly executed)
    """
    redis = await get_redis()
    
    # Try to get from cache
    cached_data = await redis.get(cache_key)
    if cached_data:
        try:
            result = json.loads(cached_data)
            if isinstance(result, list):
                if limit:
                    return result[:limit]
                return result
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Cache miss - execute query
    result = await query_fn()
    
    # Convert to list of dicts if needed
    if result is not None:
        if not isinstance(result, list):
            result = [result]
        
        # Serialize ORM objects to dicts
        serialized_list = []
        for item in result:
            if isinstance(item, dict):
                serialized_list.append(item)
            elif hasattr(item, "__dict__"):
                serialized_list.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            else:
                serialized_list.append({"value": str(item)})
        
        # Cache the result
        await redis.setex(cache_key, ttl, json.dumps(serialized_list))
        
        if limit:
            return serialized_list[:limit]
        return serialized_list
    
    return []


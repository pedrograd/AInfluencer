# Caching Strategy

This document describes the comprehensive caching strategy for the AInfluencer application.

## Overview

Caching is implemented at multiple levels to improve performance and reduce database/API load:

1. **Query Caching** - Database query results cached in Redis
2. **API Response Caching** - GET endpoint responses cached in Redis
3. **In-Memory Caching** - ComfyUI client caches checkpoint/sampler/scheduler lists
4. **Connection Pooling** - HTTP client connection pooling for external APIs

## Cache TTL Configuration

Cache time-to-live (TTL) values are configured in `backend/app/services/caching_strategy.py`:

| Cache Type | TTL | Description |
|------------|-----|-------------|
| `character` | 300s (5 min) | Character data |
| `content_metadata` | 600s (10 min) | Content metadata |
| `platform_status` | 60s (1 min) | Platform account status |
| `analytics` | 900s (15 min) | Analytics data |
| `system_status` | 5s | System status (frequently changing) |
| `api_response` | 60s (1 min) | General API responses |
| `checkpoint_list` | 60s (1 min) | ComfyUI checkpoint lists |
| `sampler_list` | 60s (1 min) | ComfyUI sampler lists |
| `scheduler_list` | 60s (1 min) | ComfyUI scheduler lists |

## Implementation

### 1. Query Caching

Query caching is implemented in `backend/app/services/query_cache.py`:

```python
from app.services.query_cache import get_cached_query

async def get_character(character_id: str):
    cache_key = f"character:{character_id}"
    return await get_cached_query(
        cache_key,
        lambda: db.query(Character).filter(Character.id == character_id).first(),
        ttl=300,
    )
```

### 2. API Response Caching

API response caching is implemented via the `@cache_response` decorator:

```python
from app.services.caching_strategy import cache_response

@router.get("/characters/{character_id}")
@cache_response(ttl=300, key_prefix="character")
async def get_character(character_id: str, request: Request):
    return {"id": character_id, "name": "Character Name"}
```

**Note:** The decorator requires `request: Request` as a dependency parameter to generate cache keys from path and query parameters.

### 3. Cache Invalidation

Cache invalidation utilities are provided in `caching_strategy.py`:

```python
from app.services.caching_strategy import (
    invalidate_character_cache,
    invalidate_content_cache,
    invalidate_api_cache,
    invalidate_cache_by_pattern,
)

# Invalidate specific character cache
await invalidate_character_cache(character_id="char_123")

# Invalidate all character caches
await invalidate_character_cache()

# Invalidate content cache
await invalidate_content_cache(content_id="content_456")

# Invalidate API endpoint cache
await invalidate_api_cache(endpoint="status")

# Invalidate by pattern
await invalidate_cache_by_pattern("character:*")
```

## Cache Key Format

Cache keys follow a consistent format:

- Query cache: `{type}:{id}` (e.g., `character:char_123`)
- API response cache: `api:{endpoint}:{hash}` (e.g., `api:status:abc123def456`)
- Pattern-based: `{prefix}:*` for wildcard invalidation

## Best Practices

1. **Use appropriate TTLs**: Shorter TTLs for frequently changing data, longer for stable data
2. **Invalidate on updates**: Always invalidate relevant caches when data is modified
3. **Monitor cache hit rates**: Track cache performance to optimize TTLs
4. **Use query caching for expensive queries**: Cache database queries that are expensive or frequently accessed
5. **Cache GET endpoints only**: Only cache idempotent GET endpoints, never POST/PUT/DELETE

## Cache Invalidation Strategy

### On Character Update
```python
# Update character
character.name = "New Name"
db.commit()

# Invalidate character cache
await invalidate_character_cache(character_id=character.id)
```

### On Content Update
```python
# Update content
content.status = "approved"
db.commit()

# Invalidate content cache
await invalidate_content_cache(content_id=content.id)
```

### On System Status Change
```python
# System status changes frequently, so we use short TTL (5s)
# No manual invalidation needed - cache expires quickly
```

## Performance Considerations

1. **Redis Memory**: Monitor Redis memory usage as cache grows
2. **Cache Warming**: Consider pre-warming frequently accessed caches on startup
3. **Cache Compression**: For large objects, consider compression before caching
4. **Cache Sharding**: For high-traffic applications, consider sharding cache keys

## Monitoring

Cache performance can be monitored via:

- Redis `INFO stats` command for hit/miss rates
- Application logs for cache operations
- Redis memory usage monitoring

## Future Enhancements

1. **Cache warming**: Pre-populate frequently accessed caches
2. **Cache compression**: Compress large cached objects
3. **Distributed caching**: Support for Redis cluster
4. **Cache analytics**: Detailed cache hit/miss metrics
5. **Adaptive TTL**: Adjust TTL based on access patterns


"""
Redis Cache Service for Performance Optimization
"""
import redis
import json
import logging
import os
from typing import Optional, Any, Union
from functools import wraps
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """Service for Redis caching operations"""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_password = os.getenv("REDIS_PASSWORD")
        
        try:
            # Parse Redis URL
            if redis_url.startswith("redis://"):
                # Extract password from URL if present
                if "@" in redis_url:
                    parts = redis_url.split("@")
                    auth_part = parts[0].replace("redis://", "").replace(":", "")
                    if auth_part:
                        redis_password = auth_part
                    redis_url = f"redis://{parts[1]}"
                
                # Connect to Redis
                self.redis_client = redis.from_url(
                    redis_url,
                    password=redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                logger.info("Redis cache connected successfully")
            else:
                self.redis_client = None
                self.enabled = False
                logger.warning("Redis URL not configured, caching disabled")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.redis_client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL (seconds)"""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.enabled:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache"""
        if not self.enabled:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key"""
        if not self.enabled:
            return False
        
        try:
            return self.redis_client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False

# Global cache service instance
cache_service = CacheService()

def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

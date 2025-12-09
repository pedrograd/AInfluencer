"""
Rate Limiter Service
Manages rate limiting for platform integrations
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for platform API calls"""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[datetime] = []
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        
        # Remove old requests outside time window
        cutoff = now - timedelta(seconds=self.time_window)
        self.requests = [r for r in self.requests if r > cutoff]
        
        # If at limit, wait until oldest request expires
        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            wait_time = self.time_window - (now - oldest_request).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                # Remove expired requests after waiting
                now = datetime.now()
                cutoff = now - timedelta(seconds=self.time_window)
                self.requests = [r for r in self.requests if r > cutoff]
        
        # Record this request
        self.requests.append(datetime.now())
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without waiting"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        self.requests = [r for r in self.requests if r > cutoff]
        return len(self.requests) < self.max_requests
    
    def get_wait_time(self) -> float:
        """Get time to wait before next request can be made"""
        if self.can_make_request():
            return 0.0
        
        now = datetime.now()
        oldest_request = self.requests[0]
        wait_time = self.time_window - (now - oldest_request).total_seconds()
        return max(0.0, wait_time)
    
    def reset(self) -> None:
        """Reset rate limiter"""
        self.requests = []


class PlatformRateLimiter:
    """Rate limiter manager for multiple platforms"""
    
    # Platform-specific rate limits (requests per time window)
    PLATFORM_LIMITS = {
        "instagram": {
            "posts": {"max": 5, "window": 86400},  # 5 per day
            "likes": {"max": 200, "window": 86400},  # 200 per day
            "comments": {"max": 30, "window": 86400},  # 30 per day
            "follows": {"max": 100, "window": 86400},  # 100 per day
        },
        "twitter": {
            "tweets": {"max": 300, "window": 10800},  # 300 per 3 hours
            "media_uploads": {"max": 50, "window": 3600},  # 50 per hour
            "follows": {"max": 400, "window": 86400},  # 400 per day
        },
        "facebook": {
            "posts": {"max": 50, "window": 3600},  # 50 per hour
            "photos": {"max": 30, "window": 3600},  # 30 per hour
        },
        "telegram": {
            "messages": {"max": 30, "window": 60},  # 30 per minute
            "photos": {"max": 20, "window": 60},  # 20 per minute
            "videos": {"max": 10, "window": 60},  # 10 per minute
        },
        "onlyfans": {
            "posts": {"max": 10, "window": 3600},  # 10 per hour (conservative)
            "photos": {"max": 20, "window": 3600},  # 20 per hour
            "videos": {"max": 5, "window": 3600},  # 5 per hour
        },
        "youtube": {
            "uploads": {"max": 6, "window": 86400},  # 6 per day
            "shorts": {"max": 10, "window": 86400},  # 10 per day
        }
    }
    
    def __init__(self):
        """Initialize platform rate limiter"""
        self.limiters: Dict[str, Dict[str, RateLimiter]] = defaultdict(dict)
    
    def get_limiter(self, platform: str, action: str) -> RateLimiter:
        """Get or create rate limiter for platform action"""
        if platform not in self.PLATFORM_LIMITS:
            logger.warning(f"Unknown platform: {platform}, using default limits")
            return RateLimiter(max_requests=10, time_window=3600)
        
        if action not in self.PLATFORM_LIMITS[platform]:
            logger.warning(f"Unknown action {action} for platform {platform}, using default limits")
            return RateLimiter(max_requests=10, time_window=3600)
        
        key = f"{platform}:{action}"
        if key not in self.limiters[platform]:
            limits = self.PLATFORM_LIMITS[platform][action]
            self.limiters[platform][action] = RateLimiter(
                max_requests=limits["max"],
                time_window=limits["window"]
            )
        
        return self.limiters[platform][action]
    
    def wait_if_needed(self, platform: str, action: str) -> None:
        """Wait if rate limit would be exceeded"""
        limiter = self.get_limiter(platform, action)
        limiter.wait_if_needed()
    
    def can_make_request(self, platform: str, action: str) -> bool:
        """Check if request can be made"""
        limiter = self.get_limiter(platform, action)
        return limiter.can_make_request()
    
    def get_wait_time(self, platform: str, action: str) -> float:
        """Get wait time for platform action"""
        limiter = self.get_limiter(platform, action)
        return limiter.get_wait_time()
    
    def reset(self, platform: Optional[str] = None, action: Optional[str] = None) -> None:
        """Reset rate limiter(s)"""
        if platform and action:
            key = f"{platform}:{action}"
            if platform in self.limiters and action in self.limiters[platform]:
                self.limiters[platform][action].reset()
        elif platform:
            if platform in self.limiters:
                for limiter in self.limiters[platform].values():
                    limiter.reset()
        else:
            for platform_limiters in self.limiters.values():
                for limiter in platform_limiters.values():
                    limiter.reset()

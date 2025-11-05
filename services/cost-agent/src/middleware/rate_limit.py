"""
Rate Limiting Middleware.

Implements rate limiting per customer and endpoint using Redis or in-memory storage.
"""

import os
import time
from fastapi import Request, HTTPException, status
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import Redis, fall back to in-memory storage
try:
    from redis import Redis
    redis_client = Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        decode_responses=True,
        socket_connect_timeout=1
    )
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connection established for rate limiting")
except Exception as e:
    logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
    REDIS_AVAILABLE = False
    redis_client = None


class InMemoryRateLimiter:
    """In-memory rate limiter (fallback when Redis is not available)."""
    
    def __init__(self):
        self._storage: Dict[str, Tuple[int, int]] = {}  # key -> (count, timestamp)
    
    def incr(self, key: str) -> int:
        """Increment counter for key."""
        current_time = int(time.time())
        
        if key in self._storage:
            count, timestamp = self._storage[key]
            # Check if key is still valid based on its expiry pattern
            if "minute" in key:
                if current_time // 60 == timestamp // 60:
                    count += 1
                else:
                    count = 1
            elif "hour" in key:
                if current_time // 3600 == timestamp // 3600:
                    count += 1
                else:
                    count = 1
            self._storage[key] = (count, current_time)
            return count
        else:
            self._storage[key] = (1, current_time)
            return 1
    
    def expire(self, key: str, seconds: int):
        """Set expiration (no-op for in-memory, handled in incr)."""
        pass
    
    def cleanup(self):
        """Clean up expired keys."""
        current_time = int(time.time())
        keys_to_delete = []
        
        for key, (count, timestamp) in self._storage.items():
            if "minute" in key and current_time - timestamp > 60:
                keys_to_delete.append(key)
            elif "hour" in key and current_time - timestamp > 3600:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._storage[key]


# Initialize rate limiter storage
if REDIS_AVAILABLE:
    _storage = redis_client
else:
    _storage = InMemoryRateLimiter()


class RateLimiter:
    """Rate limiter using Redis or in-memory storage."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self._storage = _storage
    
    async def check_rate_limit(
        self,
        customer_id: str,
        endpoint: str
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            customer_id: Customer ID
            endpoint: Endpoint path
        
        Returns:
            True if allowed
        
        Raises:
            HTTPException: If rate limit exceeded
        """
        current_time = int(time.time())
        
        # Clean up in-memory storage periodically
        if not REDIS_AVAILABLE and hasattr(self._storage, 'cleanup'):
            if current_time % 60 == 0:  # Every minute
                self._storage.cleanup()
        
        # Check per-minute limit
        minute_key = f"rate_limit:{customer_id}:{endpoint}:minute:{current_time // 60}"
        minute_count = self._storage.incr(minute_key)
        self._storage.expire(minute_key, 60)
        
        if minute_count > self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for customer {customer_id} on {endpoint}: "
                f"{minute_count}/{self.requests_per_minute} per minute"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute. Try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str((current_time // 60 + 1) * 60),
                    "Retry-After": str(60 - (current_time % 60))
                }
            )
        
        # Check per-hour limit
        hour_key = f"rate_limit:{customer_id}:{endpoint}:hour:{current_time // 3600}"
        hour_count = self._storage.incr(hour_key)
        self._storage.expire(hour_key, 3600)
        
        if hour_count > self.requests_per_hour:
            logger.warning(
                f"Hourly rate limit exceeded for customer {customer_id} on {endpoint}: "
                f"{hour_count}/{self.requests_per_hour} per hour"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_hour} requests per hour. Try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_hour),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str((current_time // 3600 + 1) * 3600),
                    "Retry-After": str(3600 - (current_time % 3600))
                }
            )
        
        # Add rate limit headers to response
        remaining_minute = self.requests_per_minute - minute_count
        remaining_hour = self.requests_per_hour - hour_count
        
        logger.debug(
            f"Rate limit check passed for customer {customer_id}: "
            f"{minute_count}/{self.requests_per_minute} per minute, "
            f"{hour_count}/{self.requests_per_hour} per hour"
        )
        
        return True
    
    def get_rate_limit_headers(
        self,
        customer_id: str,
        endpoint: str
    ) -> Dict[str, str]:
        """
        Get rate limit headers for response.
        
        Args:
            customer_id: Customer ID
            endpoint: Endpoint path
        
        Returns:
            Dictionary of rate limit headers
        """
        current_time = int(time.time())
        
        # Get current counts
        minute_key = f"rate_limit:{customer_id}:{endpoint}:minute:{current_time // 60}"
        hour_key = f"rate_limit:{customer_id}:{endpoint}:hour:{current_time // 3600}"
        
        try:
            if REDIS_AVAILABLE:
                minute_count = int(redis_client.get(minute_key) or 0)
                hour_count = int(redis_client.get(hour_key) or 0)
            else:
                minute_count = self._storage._storage.get(minute_key, (0, 0))[0]
                hour_count = self._storage._storage.get(hour_key, (0, 0))[0]
        except:
            minute_count = 0
            hour_count = 0
        
        remaining_minute = max(0, self.requests_per_minute - minute_count)
        remaining_hour = max(0, self.requests_per_hour - hour_count)
        
        return {
            "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
            "X-RateLimit-Remaining-Minute": str(remaining_minute),
            "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
            "X-RateLimit-Remaining-Hour": str(remaining_hour),
            "X-RateLimit-Reset-Minute": str((current_time // 60 + 1) * 60),
            "X-RateLimit-Reset-Hour": str((current_time // 3600 + 1) * 3600)
        }


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000
)

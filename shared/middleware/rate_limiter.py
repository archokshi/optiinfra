"""
Rate Limiting Middleware

Implements token bucket algorithm for API rate limiting.
"""

import time
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size (defaults to requests_per_minute)
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.burst_size, self.refill_rate)
        )
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier (IP address or API key)
            
        Returns:
            True if request allowed, False if rate limited
        """
        self._cleanup_old_buckets()
        bucket = self.buckets[client_id]
        return bucket.consume()
    
    def _cleanup_old_buckets(self):
        """Remove old buckets to prevent memory leak."""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            # Remove buckets not used in last hour
            cutoff = now - 3600
            self.buckets = defaultdict(
                lambda: TokenBucket(self.burst_size, self.refill_rate),
                {
                    k: v for k, v in self.buckets.items()
                    if v.last_refill > cutoff
                }
            )
            self.last_cleanup = now


# Global rate limiters for different endpoints
rate_limiters = {
    "default": RateLimiter(requests_per_minute=60, burst_size=100),
    "analysis": RateLimiter(requests_per_minute=30, burst_size=50),
    "recommendations": RateLimiter(requests_per_minute=20, burst_size=30),
    "health": RateLimiter(requests_per_minute=120, burst_size=200),
}


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response or 429 Too Many Requests
    """
    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key")
    client_id = api_key if api_key else client_ip
    
    # Determine rate limiter based on path
    path = request.url.path
    if "/health" in path:
        limiter = rate_limiters["health"]
    elif "/analyze" in path or "/analysis" in path:
        limiter = rate_limiters["analysis"]
    elif "/recommend" in path:
        limiter = rate_limiters["recommendations"]
    else:
        limiter = rate_limiters["default"]
    
    # Check rate limit
    if not limiter.is_allowed(client_id):
        logger.warning(f"Rate limit exceeded for {client_id} on {path}")
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": "Rate limit exceeded. Please try again later.",
                "retry_after": 60
            },
            headers={"Retry-After": "60"}
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(
        int(limiter.buckets[client_id].tokens)
    )
    
    return response

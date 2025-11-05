# PHASE5-5.7 PART1: API Security - Code Implementation

**Phase**: PHASE5-5.7  
**Component**: Portal & Production - API Security  
**Estimated Time**: 25 minutes (Code) + 20 minutes (Validation)  
**Dependencies**: PHASE5-5.6 (CI/CD Pipeline), ALL agents

---

## Overview

Implement comprehensive API security including rate limiting, request validation, authentication, and security headers for all agent APIs and the portal.

---

## Step 1: Create Rate Limiting Middleware

### File: `shared/middleware/rate_limiter.py`

```python
"""
Rate Limiting Middleware

Implements token bucket algorithm for API rate limiting.
"""

import time
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException
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
```

---

## Step 2: Create Request Validation Middleware

### File: `shared/middleware/request_validator.py`

```python
"""
Request Validation Middleware

Validates incoming requests for security and data integrity.
"""

import re
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RequestValidator:
    """Request validation for security."""
    
    # Maximum request sizes
    MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_QUERY_LENGTH = 2048
    MAX_HEADER_SIZE = 8192
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--|\#|\/\*)",
        r"(\bEXEC\b|\bEXECUTE\b)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
    ]
    
    def __init__(self):
        """Initialize validator."""
        self.sql_regex = re.compile(
            "|".join(self.SQL_INJECTION_PATTERNS),
            re.IGNORECASE
        )
        self.xss_regex = re.compile(
            "|".join(self.XSS_PATTERNS),
            re.IGNORECASE
        )
        self.path_regex = re.compile(
            "|".join(self.PATH_TRAVERSAL_PATTERNS),
            re.IGNORECASE
        )
    
    def validate_request_size(self, request: Request) -> Optional[str]:
        """
        Validate request size.
        
        Args:
            request: FastAPI request
            
        Returns:
            Error message if invalid, None if valid
        """
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.MAX_JSON_SIZE:
                    return f"Request body too large. Maximum {self.MAX_JSON_SIZE} bytes"
            except ValueError:
                return "Invalid content-length header"
        
        # Check query string length
        if len(str(request.url.query)) > self.MAX_QUERY_LENGTH:
            return f"Query string too long. Maximum {self.MAX_QUERY_LENGTH} characters"
        
        # Check header size
        header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if header_size > self.MAX_HEADER_SIZE:
            return f"Headers too large. Maximum {self.MAX_HEADER_SIZE} bytes"
        
        return None
    
    def check_sql_injection(self, value: str) -> bool:
        """
        Check for SQL injection patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if suspicious pattern found
        """
        return bool(self.sql_regex.search(value))
    
    def check_xss(self, value: str) -> bool:
        """
        Check for XSS patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if suspicious pattern found
        """
        return bool(self.xss_regex.search(value))
    
    def check_path_traversal(self, value: str) -> bool:
        """
        Check for path traversal patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if suspicious pattern found
        """
        return bool(self.path_regex.search(value))
    
    def validate_string(self, value: str, field_name: str) -> Optional[str]:
        """
        Validate string for security issues.
        
        Args:
            value: String to validate
            field_name: Name of field for error message
            
        Returns:
            Error message if invalid, None if valid
        """
        if self.check_sql_injection(value):
            logger.warning(f"SQL injection attempt detected in {field_name}: {value[:100]}")
            return f"Invalid characters in {field_name}"
        
        if self.check_xss(value):
            logger.warning(f"XSS attempt detected in {field_name}: {value[:100]}")
            return f"Invalid characters in {field_name}"
        
        if self.check_path_traversal(value):
            logger.warning(f"Path traversal attempt detected in {field_name}: {value[:100]}")
            return f"Invalid characters in {field_name}"
        
        return None


# Global validator instance
validator = RequestValidator()


async def validation_middleware(request: Request, call_next):
    """
    Request validation middleware.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response or 400 Bad Request
    """
    # Validate request size
    size_error = validator.validate_request_size(request)
    if size_error:
        logger.warning(f"Request size validation failed: {size_error}")
        return JSONResponse(
            status_code=400,
            content={"error": "Bad Request", "message": size_error}
        )
    
    # Validate query parameters
    for key, value in request.query_params.items():
        error = validator.validate_string(str(value), f"query parameter '{key}'")
        if error:
            return JSONResponse(
                status_code=400,
                content={"error": "Bad Request", "message": error}
            )
    
    # Validate path parameters
    for key, value in request.path_params.items():
        error = validator.validate_string(str(value), f"path parameter '{key}'")
        if error:
            return JSONResponse(
                status_code=400,
                content={"error": "Bad Request", "message": error}
            )
    
    response = await call_next(request)
    return response
```

---

## Step 3: Create Security Headers Middleware

### File: `shared/middleware/security_headers.py`

```python
"""
Security Headers Middleware

Adds security headers to all responses.
"""

from fastapi import Request
from fastapi.responses import Response


async def security_headers_middleware(request: Request, call_next):
    """
    Add security headers to response.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response with security headers
    """
    response: Response = await call_next(request)
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Strict Transport Security (HTTPS only)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=()"
    )
    
    return response
```

---

## Step 4: Create API Key Authentication

### File: `shared/middleware/api_auth.py`

```python
"""
API Key Authentication Middleware

Validates API keys for agent-to-agent communication.
"""

import hashlib
import secrets
from typing import Optional, Set
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API keys for authentication."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.valid_keys: Set[str] = set()
        self.key_hashes: Set[str] = set()
    
    def generate_key(self) -> str:
        """
        Generate a new API key.
        
        Returns:
            New API key
        """
        key = secrets.token_urlsafe(32)
        self.add_key(key)
        return key
    
    def add_key(self, key: str):
        """
        Add an API key.
        
        Args:
            key: API key to add
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self.valid_keys.add(key)
        self.key_hashes.add(key_hash)
    
    def validate_key(self, key: str) -> bool:
        """
        Validate an API key.
        
        Args:
            key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not key:
            return False
        
        # Check direct match (for development)
        if key in self.valid_keys:
            return True
        
        # Check hash match (for production)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key_hash in self.key_hashes
    
    def revoke_key(self, key: str):
        """
        Revoke an API key.
        
        Args:
            key: API key to revoke
        """
        self.valid_keys.discard(key)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self.key_hashes.discard(key_hash)


# Global API key manager
api_key_manager = APIKeyManager()


async def api_key_middleware(request: Request, call_next):
    """
    API key authentication middleware.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response or 401 Unauthorized
    """
    # Skip authentication for health checks and public endpoints
    public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    
    # Validate API key
    if not api_key_manager.validate_key(api_key):
        logger.warning(f"Invalid API key attempt from {request.client.host if request.client else 'unknown'}")
        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized",
                "message": "Invalid or missing API key"
            },
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    response = await call_next(request)
    return response
```

---

## Step 5: Update Agent Main Files

### Update: `services/cost-agent/src/main.py`

Add middleware to the FastAPI application:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.middleware.rate_limiter import rate_limit_middleware
from shared.middleware.request_validator import validation_middleware
from shared.middleware.security_headers import security_headers_middleware
from shared.middleware.api_auth import api_key_middleware

app = FastAPI(
    title="Cost Agent API",
    description="AI-powered cost optimization agent",
    version="1.0.0"
)

# Add security middleware (order matters!)
app.middleware("http")(security_headers_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(validation_middleware)
app.middleware("http")(api_key_middleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Portal URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# ... rest of the application
```

---

## Step 6: Create Input Validation Schemas

### File: `shared/validation/schemas.py`

```python
"""
Pydantic schemas for input validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CostAnalysisRequest(BaseModel):
    """Cost analysis request schema."""
    
    cloud_provider: str = Field(..., regex="^(aws|gcp|azure)$")
    time_range: str = Field(..., regex="^(1h|6h|12h|24h|7d|30d)$")
    resource_types: Optional[List[str]] = Field(default=None, max_items=50)
    filters: Optional[Dict[str, Any]] = Field(default=None)
    
    @validator("resource_types")
    def validate_resource_types(cls, v):
        """Validate resource types."""
        if v:
            allowed_types = ["compute", "storage", "network", "database", "other"]
            for rt in v:
                if rt not in allowed_types:
                    raise ValueError(f"Invalid resource type: {rt}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "cloud_provider": "aws",
                "time_range": "24h",
                "resource_types": ["compute", "storage"],
                "filters": {"region": "us-east-1"}
            }
        }


class PerformanceAnalysisRequest(BaseModel):
    """Performance analysis request schema."""
    
    application_id: str = Field(..., min_length=1, max_length=100)
    metric_types: List[str] = Field(..., min_items=1, max_items=20)
    time_range: str = Field(..., regex="^(1h|6h|12h|24h|7d|30d)$")
    
    @validator("metric_types")
    def validate_metric_types(cls, v):
        """Validate metric types."""
        allowed_metrics = [
            "latency", "throughput", "error_rate", "cpu", "memory",
            "disk_io", "network_io", "response_time"
        ]
        for metric in v:
            if metric not in allowed_metrics:
                raise ValueError(f"Invalid metric type: {metric}")
        return v


class RecommendationRequest(BaseModel):
    """Recommendation request schema."""
    
    context: str = Field(..., min_length=10, max_length=5000)
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")
    categories: Optional[List[str]] = Field(default=None, max_items=10)
    
    @validator("context")
    def validate_context(cls, v):
        """Validate context doesn't contain suspicious content."""
        from shared.middleware.request_validator import validator
        error = validator.validate_string(v, "context")
        if error:
            raise ValueError(error)
        return v
```

---

## Step 7: Create Security Configuration

### File: `shared/config/security.py`

```python
"""
Security Configuration

Centralized security settings.
"""

from pydantic import BaseSettings
from typing import List


class SecuritySettings(BaseSettings):
    """Security settings."""
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    
    # API Authentication
    API_KEY_ENABLED: bool = True
    API_KEY_HEADER: str = "X-API-Key"
    
    # Request validation
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_QUERY_LENGTH: int = 2048
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Security headers
    ENABLE_HSTS: bool = True
    ENABLE_CSP: bool = True
    
    # Session
    SESSION_TIMEOUT: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        env_prefix = "SECURITY_"


# Global security settings
security_settings = SecuritySettings()
```

---

## Step 8: Create Security Tests

### File: `shared/tests/test_security.py`

```python
"""
Security Tests

Tests for security middleware and validation.
"""

import pytest
from fastapi.testclient import TestClient
from shared.middleware.rate_limiter import RateLimiter
from shared.middleware.request_validator import RequestValidator


class TestRateLimiter:
    """Test rate limiting."""
    
    def test_rate_limit_allows_requests(self):
        """Test rate limiter allows requests within limit."""
        limiter = RateLimiter(requests_per_minute=10, burst_size=10)
        
        # Should allow 10 requests
        for _ in range(10):
            assert limiter.is_allowed("test_client")
    
    def test_rate_limit_blocks_excess(self):
        """Test rate limiter blocks excess requests."""
        limiter = RateLimiter(requests_per_minute=5, burst_size=5)
        
        # Use up all tokens
        for _ in range(5):
            assert limiter.is_allowed("test_client")
        
        # Next request should be blocked
        assert not limiter.is_allowed("test_client")


class TestRequestValidator:
    """Test request validation."""
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        validator = RequestValidator()
        
        # Should detect SQL injection
        assert validator.check_sql_injection("'; DROP TABLE users; --")
        assert validator.check_sql_injection("UNION SELECT * FROM passwords")
        
        # Should allow normal queries
        assert not validator.check_sql_injection("normal search query")
    
    def test_xss_detection(self):
        """Test XSS pattern detection."""
        validator = RequestValidator()
        
        # Should detect XSS
        assert validator.check_xss("<script>alert('xss')</script>")
        assert validator.check_xss("javascript:alert(1)")
        assert validator.check_xss("<img onerror='alert(1)'>")
        
        # Should allow normal HTML
        assert not validator.check_xss("<p>Normal paragraph</p>")
    
    def test_path_traversal_detection(self):
        """Test path traversal detection."""
        validator = RequestValidator()
        
        # Should detect path traversal
        assert validator.check_path_traversal("../../etc/passwd")
        assert validator.check_path_traversal("..\\windows\\system32")
        
        # Should allow normal paths
        assert not validator.check_path_traversal("/api/v1/users")
```

---

## Summary

**Files Created:**
1. `shared/middleware/rate_limiter.py` - Token bucket rate limiting
2. `shared/middleware/request_validator.py` - Input validation & security checks
3. `shared/middleware/security_headers.py` - Security headers
4. `shared/middleware/api_auth.py` - API key authentication
5. `shared/validation/schemas.py` - Pydantic validation schemas
6. `shared/config/security.py` - Security configuration
7. `shared/tests/test_security.py` - Security tests

**Features:**
- ✅ Rate limiting (token bucket algorithm)
- ✅ Request validation (SQL injection, XSS, path traversal)
- ✅ Security headers (CSP, HSTS, X-Frame-Options, etc.)
- ✅ API key authentication
- ✅ Input validation with Pydantic
- ✅ Configurable security settings
- ✅ Comprehensive security tests

**Security Measures:**
- ✅ Rate limiting per client
- ✅ Request size limits
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ Path traversal prevention
- ✅ CORS configuration
- ✅ API key authentication
- ✅ Security headers

---

**Next**: PHASE5-5.7_PART2_Execution_and_Validation.md

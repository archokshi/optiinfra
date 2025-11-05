"""
Standalone Authentication Tests.

Tests authentication system without requiring full app startup.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.api_key import APIKeyManager
from src.auth.jwt_handler import JWTHandler
from src.middleware.rate_limit import RateLimiter


class TestAPIKeyManager:
    """Test API key management."""
    
    @pytest.mark.asyncio
    async def test_generate_key(self):
        """Test API key generation."""
        key = APIKeyManager.generate_key()
        assert key.startswith("sk_")
        assert len(key) > 10
    
    @pytest.mark.asyncio
    async def test_hash_key(self):
        """Test API key hashing."""
        key = "sk_test_key_123"
        hash1 = APIKeyManager.hash_key(key)
        hash2 = APIKeyManager.hash_key(key)
        
        assert hash1 == hash2  # Same key produces same hash
        assert len(hash1) == 64  # SHA-256 produces 64 char hex
    
    @pytest.mark.asyncio
    async def test_create_and_validate_key(self):
        """Test creating and validating API key."""
        # Create key
        plain_key, key_record = await APIKeyManager.create_key(
            customer_id="cust-test",
            name="Test Key",
            expires_days=365
        )
        
        assert plain_key.startswith("sk_")
        assert key_record.customer_id == "cust-test"
        assert key_record.name == "Test Key"
        assert key_record.is_active == True
        
        # Validate key
        validated = await APIKeyManager.validate_key(plain_key)
        assert validated is not None
        assert validated.customer_id == "cust-test"
        assert validated.requests_count == 1
    
    @pytest.mark.asyncio
    async def test_validate_invalid_key(self):
        """Test validating invalid key."""
        result = await APIKeyManager.validate_key("sk_invalid_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_keys(self):
        """Test listing API keys."""
        # Create a key
        await APIKeyManager.create_key(
            customer_id="cust-list-test",
            name="List Test Key",
            expires_days=1
        )
        
        # List keys
        keys = await APIKeyManager.list_keys("cust-list-test")
        assert len(keys) >= 1
        assert any(k.name == "List Test Key" for k in keys)
    
    @pytest.mark.asyncio
    async def test_revoke_key(self):
        """Test revoking API key."""
        # Create key
        plain_key, key_record = await APIKeyManager.create_key(
            customer_id="cust-revoke-test",
            name="Revoke Test Key",
            expires_days=1
        )
        
        # Revoke it
        success = await APIKeyManager.revoke_key(key_record.id)
        assert success == True
        
        # Try to validate revoked key
        validated = await APIKeyManager.validate_key(plain_key)
        assert validated is None
    
    @pytest.mark.asyncio
    async def test_delete_key(self):
        """Test deleting API key."""
        # Create key
        plain_key, key_record = await APIKeyManager.create_key(
            customer_id="cust-delete-test",
            name="Delete Test Key",
            expires_days=1
        )
        
        # Delete it
        success = await APIKeyManager.delete_key(key_record.id)
        assert success == True
        
        # Try to validate deleted key
        validated = await APIKeyManager.validate_key(plain_key)
        assert validated is None


class TestJWTHandler:
    """Test JWT token handling."""
    
    def test_create_token(self):
        """Test JWT token creation."""
        token = JWTHandler.create_token({"sub": "test_user", "customer_id": "cust-123"})
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_decode_token(self):
        """Test JWT token decoding."""
        # Create token
        token = JWTHandler.create_token({"sub": "test_user", "customer_id": "cust-123"})
        
        # Decode it
        payload = JWTHandler.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test_user"
        assert payload["customer_id"] == "cust-123"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        result = JWTHandler.decode_token("invalid.token.here")
        assert result is None
    
    def test_create_access_token(self):
        """Test creating access token."""
        token = JWTHandler.create_access_token(
            subject="user@example.com",
            customer_id="cust-123"
        )
        
        assert isinstance(token, str)
        
        # Decode and verify
        payload = JWTHandler.decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["customer_id"] == "cust-123"
        assert payload["type"] == "access"
    
    def test_create_refresh_token(self):
        """Test creating refresh token."""
        token = JWTHandler.create_refresh_token(
            subject="user@example.com",
            customer_id="cust-123"
        )
        
        assert isinstance(token, str)
        
        # Decode and verify
        payload = JWTHandler.decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["customer_id"] == "cust-123"
        assert payload["type"] == "refresh"


class TestRateLimiter:
    """Test rate limiting."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)
        assert limiter.requests_per_minute == 10
        assert limiter.requests_per_hour == 100
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_success(self):
        """Test rate limit check passes."""
        limiter = RateLimiter(requests_per_minute=100, requests_per_hour=1000)
        
        # Should pass
        result = await limiter.check_rate_limit("cust-test", "/test-endpoint")
        assert result == True
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_headers(self):
        """Test getting rate limit headers."""
        limiter = RateLimiter(requests_per_minute=60, requests_per_hour=1000)
        
        headers = limiter.get_rate_limit_headers("cust-test", "/test-endpoint")
        assert "X-RateLimit-Limit-Minute" in headers
        assert "X-RateLimit-Remaining-Minute" in headers
        assert "X-RateLimit-Limit-Hour" in headers
        assert "X-RateLimit-Remaining-Hour" in headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Security Tests

Tests for security middleware and validation.
"""

import pytest
import time
from shared.middleware.rate_limiter import RateLimiter, TokenBucket
from shared.middleware.request_validator import RequestValidator
from shared.middleware.api_auth import APIKeyManager


class TestTokenBucket:
    """Test token bucket implementation."""
    
    def test_token_bucket_initialization(self):
        """Test token bucket initializes correctly."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.tokens == 10
        assert bucket.refill_rate == 1.0
    
    def test_token_consumption(self):
        """Test token consumption."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        # Should consume 1 token
        assert bucket.consume(1)
        assert bucket.tokens == 9
        
        # Should consume 5 tokens
        assert bucket.consume(5)
        assert bucket.tokens == 4
    
    def test_insufficient_tokens(self):
        """Test behavior when insufficient tokens."""
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        
        # Consume all tokens
        assert bucket.consume(5)
        
        # Should fail to consume more
        assert not bucket.consume(1)
    
    def test_token_refill(self):
        """Test token refill over time."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/second
        
        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0
        
        # Wait 0.5 seconds (should refill ~5 tokens)
        time.sleep(0.5)
        bucket._refill()
        assert bucket.tokens >= 4  # Allow some margin


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
    
    def test_different_clients_independent(self):
        """Test different clients have independent limits."""
        limiter = RateLimiter(requests_per_minute=5, burst_size=5)
        
        # Client 1 uses all tokens
        for _ in range(5):
            assert limiter.is_allowed("client1")
        
        # Client 2 should still have tokens
        assert limiter.is_allowed("client2")


class TestRequestValidator:
    """Test request validation."""
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        validator = RequestValidator()
        
        # Should detect SQL injection
        assert validator.check_sql_injection("'; DROP TABLE users; --")
        assert validator.check_sql_injection("UNION SELECT * FROM passwords")
        assert validator.check_sql_injection("DELETE FROM users WHERE 1=1")
        assert validator.check_sql_injection("INSERT INTO admin VALUES ('hacker')")
        
        # Should allow normal queries
        assert not validator.check_sql_injection("normal search query")
        assert not validator.check_sql_injection("user@example.com")
    
    def test_xss_detection(self):
        """Test XSS pattern detection."""
        validator = RequestValidator()
        
        # Should detect XSS
        assert validator.check_xss("<script>alert('xss')</script>")
        assert validator.check_xss("javascript:alert(1)")
        assert validator.check_xss("<img onerror='alert(1)'>")
        assert validator.check_xss("<iframe src='evil.com'>")
        
        # Should allow normal HTML
        assert not validator.check_xss("Normal text content")
        assert not validator.check_xss("Email: user@example.com")
    
    def test_path_traversal_detection(self):
        """Test path traversal detection."""
        validator = RequestValidator()
        
        # Should detect path traversal
        assert validator.check_path_traversal("../../etc/passwd")
        assert validator.check_path_traversal("..\\windows\\system32")
        assert validator.check_path_traversal("%2e%2e/config")
        
        # Should allow normal paths
        assert not validator.check_path_traversal("/api/v1/users")
        assert not validator.check_path_traversal("data/file.txt")
    
    def test_validate_string(self):
        """Test string validation."""
        validator = RequestValidator()
        
        # Should reject malicious strings
        assert validator.validate_string("'; DROP TABLE users; --", "input") is not None
        assert validator.validate_string("<script>alert(1)</script>", "input") is not None
        assert validator.validate_string("../../etc/passwd", "input") is not None
        
        # Should allow safe strings
        assert validator.validate_string("normal text", "input") is None
        assert validator.validate_string("user@example.com", "input") is None


class TestAPIKeyManager:
    """Test API key management."""
    
    def test_generate_key(self):
        """Test API key generation."""
        manager = APIKeyManager()
        key = manager.generate_key()
        
        assert key is not None
        assert len(key) > 20  # Should be reasonably long
        assert manager.validate_key(key)
    
    def test_add_and_validate_key(self):
        """Test adding and validating keys."""
        manager = APIKeyManager()
        key = "test-api-key-12345"
        
        manager.add_key(key)
        assert manager.validate_key(key)
    
    def test_invalid_key(self):
        """Test invalid key rejection."""
        manager = APIKeyManager()
        
        assert not manager.validate_key("invalid-key")
        assert not manager.validate_key(None)
        assert not manager.validate_key("")
    
    def test_revoke_key(self):
        """Test key revocation."""
        manager = APIKeyManager()
        key = manager.generate_key()
        
        # Key should be valid
        assert manager.validate_key(key)
        
        # Revoke key
        manager.revoke_key(key)
        
        # Key should no longer be valid
        assert not manager.validate_key(key)


class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def test_rate_limit_and_validation_together(self):
        """Test rate limiting and validation work together."""
        limiter = RateLimiter(requests_per_minute=10, burst_size=10)
        validator = RequestValidator()
        
        # Normal request should pass both
        assert limiter.is_allowed("client1")
        assert validator.validate_string("normal query", "query") is None
        
        # Malicious request should fail validation
        assert validator.validate_string("'; DROP TABLE users; --", "query") is not None
        
        # Rate limit should still work
        for _ in range(9):
            limiter.is_allowed("client1")
        assert not limiter.is_allowed("client1")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

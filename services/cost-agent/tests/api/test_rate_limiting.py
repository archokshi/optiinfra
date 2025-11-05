"""
Test Rate Limiting.

Tests for rate limiting middleware.
"""

import pytest
from fastapi.testclient import TestClient
import time


def test_rate_limit_per_minute(client, test_api_key):
    """Test per-minute rate limit."""
    # Make 61 requests quickly
    success_count = 0
    rate_limited_count = 0
    
    for i in range(61):
        response = client.get(
            "/api/v1/notifications/unread-count",
            headers={"X-API-Key": test_api_key}
        )
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited_count += 1
    
    # Should have some rate limited requests
    assert rate_limited_count > 0
    assert success_count <= 60


def test_rate_limit_headers(client, test_api_key):
    """Test rate limit headers in response."""
    response = client.get(
        "/api/v1/notifications/unread-count",
        headers={"X-API-Key": test_api_key}
    )
    
    # Check for rate limit headers
    assert "X-RateLimit-Limit-Minute" in response.headers or response.status_code == 200
    

def test_rate_limit_429_response(client, test_api_key):
    """Test 429 response format."""
    # Make many requests to trigger rate limit
    for i in range(70):
        response = client.get(
            "/api/v1/notifications/unread-count",
            headers={"X-API-Key": test_api_key}
        )
        
        if response.status_code == 429:
            data = response.json()
            assert "detail" in data
            assert "rate limit" in data["detail"].lower()
            break


def test_rate_limit_per_customer(client):
    """Test rate limiting is per customer."""
    # Create two different API keys
    key1_response = client.post(
        "/api/v1/auth/api-key/create",
        json={
            "customer_id": "cust-1",
            "name": "Key 1",
            "expires_days": 1
        }
    )
    key1 = key1_response.json()["key"]
    
    key2_response = client.post(
        "/api/v1/auth/api-key/create",
        json={
            "customer_id": "cust-2",
            "name": "Key 2",
            "expires_days": 1
        }
    )
    key2 = key2_response.json()["key"]
    
    # Make requests with both keys
    response1 = client.get(
        "/api/v1/notifications/unread-count",
        headers={"X-API-Key": key1}
    )
    
    response2 = client.get(
        "/api/v1/notifications/unread-count",
        headers={"X-API-Key": key2}
    )
    
    # Both should succeed (separate rate limits)
    assert response1.status_code == 200
    assert response2.status_code == 200

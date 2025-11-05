"""
LMCache API Tests

Tests for LMCache API endpoints.
"""

import pytest
from fastapi import status


def test_get_lmcache_status(client):
    """Test LMCache status endpoint."""
    response = client.get("/lmcache/status")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "metrics" in data
    assert "config" in data
    assert "instance_id" in data


def test_get_cache_config(client):
    """Test get cache config endpoint."""
    response = client.get("/lmcache/config")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "max_size_mb" in data
    assert "eviction_policy" in data


def test_update_cache_config(client):
    """Test update cache config endpoint."""
    new_config = {
        "enabled": True,
        "max_size_mb": 2048.0,
        "eviction_policy": "lru",
        "enable_prefix_caching": True,
        "min_prefix_length": 10,
        "cache_warmup": False,
        "auto_eviction": True,
        "enable_sharing": True,
        "max_concurrent_users": 100
    }
    
    response = client.post("/lmcache/config", json=new_config)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["max_size_mb"] == 2048.0


def test_optimize_cache(client):
    """Test cache optimization endpoint."""
    response = client.post("/lmcache/optimize")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert data["success"] == True


def test_clear_cache(client):
    """Test clear cache endpoint."""
    response = client.delete("/lmcache/clear")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data

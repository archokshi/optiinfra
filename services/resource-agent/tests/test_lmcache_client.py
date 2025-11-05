"""
LMCache Client Tests

Tests for LMCache client.
"""

import pytest
from src.lmcache.client import LMCacheClient
from src.models.lmcache_metrics import CacheConfig, EvictionPolicy


def test_lmcache_client_initialization():
    """Test LMCache client initialization."""
    client = LMCacheClient()
    assert client is not None
    assert client.config is not None


def test_get_metrics():
    """Test getting cache metrics."""
    client = LMCacheClient()
    metrics = client.get_metrics()
    
    assert metrics is not None
    assert 0 <= metrics.hit_rate_percent <= 100
    assert metrics.total_size_mb > 0


def test_get_config():
    """Test getting configuration."""
    config = CacheConfig(max_size_mb=2048.0)
    client = LMCacheClient(config=config)
    
    retrieved_config = client.get_config()
    assert retrieved_config.max_size_mb == 2048.0


def test_update_config():
    """Test updating configuration."""
    client = LMCacheClient()
    
    new_config = CacheConfig(
        max_size_mb=4096.0,
        eviction_policy=EvictionPolicy.LFU
    )
    
    success = client.update_config(new_config)
    assert success
    assert client.config.max_size_mb == 4096.0


def test_optimize():
    """Test cache optimization."""
    client = LMCacheClient()
    result = client.optimize()
    
    assert result is not None
    assert result.success
    assert result.optimization_time_ms >= 0


def test_clear_cache():
    """Test clearing cache."""
    client = LMCacheClient()
    success = client.clear_cache()
    assert success


def test_get_status():
    """Test getting complete status."""
    client = LMCacheClient()
    status = client.get_status(instance_id="test")
    
    assert status is not None
    assert status.instance_id == "test"
    assert status.metrics is not None
    assert status.config is not None

"""
Configuration API Tests

Tests for configuration API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_get_config(client: TestClient):
    """Test getting agent configuration."""
    response = client.get("/api/v1/config")
    
    assert response.status_code == 200
    data = response.json()
    assert "agent_id" in data
    assert "agent_type" in data
    assert "port" in data
    assert "log_level" in data
    assert "environment" in data
    assert "version" in data


@pytest.mark.unit
def test_get_capabilities(client: TestClient):
    """Test getting agent capabilities."""
    response = client.get("/api/v1/capabilities")
    
    assert response.status_code == 200
    data = response.json()
    assert "capabilities" in data
    assert "supported_platforms" in data
    assert "optimization_types" in data
    assert "workflow_features" in data
    
    # Verify specific capabilities
    assert "performance_monitoring" in data["capabilities"]
    assert "bottleneck_detection" in data["capabilities"]
    assert "gradual_rollout" in data["capabilities"]
    
    # Verify platforms
    assert "vllm" in data["supported_platforms"]
    assert "tgi" in data["supported_platforms"]
    assert "sglang" in data["supported_platforms"]
    
    # Verify optimization types
    assert "kv_cache" in data["optimization_types"]
    assert "quantization" in data["optimization_types"]
    assert "batching" in data["optimization_types"]

"""
Health Check Tests

Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "agent_id" in data
    assert "uptime_seconds" in data


@pytest.mark.unit
def test_detailed_health_check(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert isinstance(data["components"], dict)


@pytest.mark.unit
def test_service_info(client: TestClient):
    """Test service info endpoint."""
    response = client.get("/api/v1/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "OptiInfra Performance Agent"
    assert "capabilities" in data
    assert len(data["capabilities"]) > 0

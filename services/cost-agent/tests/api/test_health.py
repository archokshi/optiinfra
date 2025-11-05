"""
Test Health Endpoints.

Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test basic health check."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "ok"]


def test_health_check_no_auth_required(client):
    """Test health check doesn't require authentication."""
    response = client.get("/api/v1/health")
    
    # Should work without auth
    assert response.status_code == 200


def test_detailed_health_check(client):
    """Test detailed health check."""
    response = client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # May have additional fields like database status, etc.

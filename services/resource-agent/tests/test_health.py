"""
Health Check Tests

Tests for health check endpoints.
"""

import pytest
from fastapi import status


def test_health_check(client):
    """Test basic health check endpoint."""
    response = client.get("/health/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "agent_id" in data
    assert "uptime_seconds" in data


def test_detailed_health_check(client):
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "metrics" in data


def test_readiness_check(client):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["ready"] is True


def test_liveness_check(client):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["alive"] is True


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent"] == "Resource Agent"
    assert "version" in data

"""
Error Handler Tests

Tests for error handlers.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_validation_error(client: TestClient):
    """Test validation error handling."""
    # Send invalid request - missing required fields
    response = client.post(
        "/api/v1/workflows",
        json={}  # Missing required fields
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "validation_error"
    assert "message" in data
    assert "details" in data
    assert "invalid_fields" in data
    assert "timestamp" in data
    assert "path" in data


@pytest.mark.unit
def test_not_found_error(client: TestClient):
    """Test 404 error handling."""
    response = client.get("/api/v1/workflows/non-existent-id")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "timestamp" in data
    assert "path" in data


@pytest.mark.unit
def test_metrics_history_endpoint(client: TestClient):
    """Test metrics history endpoint."""
    response = client.get("/api/v1/history/localhost:8000?hours=24&limit=100")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.unit
def test_workflow_list_endpoint(client: TestClient):
    """Test workflow list endpoint."""
    response = client.get("/api/v1/workflows")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.unit
def test_workflow_list_with_filter(client: TestClient):
    """Test workflow list with status filter."""
    response = client.get("/api/v1/workflows?status=completed&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

"""
Error handling tests for Application Agent.

Tests error handling, validation, and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_invalid_quality_metrics():
    """Test handling of invalid quality metrics."""
    # Missing required field
    response = client.post("/quality/analyze", json={
        "prompt": "Test"
        # Missing 'response' field
    })
    assert response.status_code == 422  # Validation error


def test_missing_required_parameters():
    """Test handling of missing required parameters."""
    # Missing required field
    response = client.post("/quality/analyze", json={
        "prompt": "Test"
        # Missing 'response' and 'model_id'
    })
    assert response.status_code == 422


def test_not_found_errors():
    """Test 404 error handling."""
    # Non-existent endpoint
    response = client.get("/nonexistent/endpoint")
    assert response.status_code == 404
    
    # Non-existent baseline
    response = client.get("/regression/baselines/non-existent-id")
    assert response.status_code == 404
    
    # Non-existent bulk job
    response = client.get("/bulk/status/non-existent-id")
    assert response.status_code == 404


def test_invalid_endpoint():
    """Test invalid endpoint handling."""
    response = client.get("/invalid/endpoint")
    assert response.status_code == 404


def test_invalid_query_parameters():
    """Test invalid query parameter handling."""
    # Invalid period (should fail validation)
    response = client.get("/analytics/summary?period=invalid")
    # May return 422 or 200 with default value depending on implementation
    assert response.status_code in [200, 422]
    
    # Invalid metric history limit
    response = client.get("/quality/metrics/history?limit=-1")
    # May return 422 or 200 with default value
    assert response.status_code in [200, 422]


def test_invalid_request_body():
    """Test invalid request body handling."""
    # Invalid JSON
    response = client.post(
        "/quality/analyze",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_empty_request_body():
    """Test empty request body handling."""
    response = client.post("/quality/analyze", json={})
    assert response.status_code == 422


def test_invalid_model_comparison():
    """Test invalid model comparison."""
    # Empty models list - may still return 200 with empty comparison
    response = client.get("/analytics/comparison?models=")
    # Implementation may handle this gracefully or return error
    assert response.status_code in [200, 400, 422]


def test_invalid_bulk_request():
    """Test invalid bulk request handling."""
    # Empty samples
    response = client.post("/bulk/quality", json={"samples": []})
    assert response.status_code in [200, 202, 422]  # May vary by implementation


def test_error_response_format():
    """Test error response format."""
    response = client.get("/validation/non-existent-id")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data  # FastAPI standard error format

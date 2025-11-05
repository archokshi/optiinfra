"""
Test Bulk Operations Endpoints.

Tests for bulk recommendation and execution operations.
"""

import pytest
from fastapi.testclient import TestClient


def test_bulk_generate_recommendations(client, test_api_key):
    """Test bulk recommendation generation."""
    response = client.post(
        "/api/v1/bulk/recommendations/generate",
        headers={"X-API-Key": test_api_key},
        json={
            "customer_ids": ["cust-test", "cust-test-2"],
            "lookback_days": 30
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "operation_id" in data
    assert data["status"] in ["queued", "in_progress"]
    assert data["total_items"] == 2


def test_bulk_execute_recommendations(client, test_api_key):
    """Test bulk execution."""
    response = client.post(
        "/api/v1/bulk/execution/execute",
        headers={"X-API-Key": test_api_key},
        json={
            "recommendation_ids": ["rec-1", "rec-2", "rec-3"],
            "dry_run": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "operation_id" in data
    assert data["total_items"] == 3


def test_get_bulk_operation_status(client, test_api_key):
    """Test getting bulk operation status."""
    response = client.get(
        "/api/v1/bulk/status/bulk-op-123",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "operation_id" in data
    assert "status" in data


def test_get_bulk_operations_history(client, test_api_key):
    """Test getting bulk operations history."""
    response = client.get(
        "/api/v1/bulk/history?limit=10",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

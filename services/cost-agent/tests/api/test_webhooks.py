"""
Test Webhook Endpoints.

Tests for webhook registration and management.
"""

import pytest
from fastapi.testclient import TestClient


def test_register_webhook(client, test_api_key):
    """Test webhook registration."""
    response = client.post(
        "/api/v1/webhooks/register",
        headers={"X-API-Key": test_api_key},
        json={
            "url": "https://example.com/webhook",
            "events": ["recommendation.created", "execution.completed"],
            "description": "Test webhook"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["url"] == "https://example.com/webhook"
    assert len(data["events"]) == 2


def test_list_webhooks(client, test_api_key):
    """Test listing webhooks."""
    response = client.get(
        "/api/v1/webhooks/list",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_webhook(client, test_api_key):
    """Test updating webhook."""
    response = client.put(
        "/api/v1/webhooks/webhook-123",
        headers={"X-API-Key": test_api_key},
        json={
            "url": "https://example.com/webhook-updated",
            "events": ["recommendation.created"],
            "description": "Updated webhook"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://example.com/webhook-updated"


def test_delete_webhook(client, test_api_key):
    """Test deleting webhook."""
    response = client.delete(
        "/api/v1/webhooks/webhook-123",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200


def test_test_webhook(client, test_api_key):
    """Test sending test event to webhook."""
    response = client.post(
        "/api/v1/webhooks/webhook-123/test",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

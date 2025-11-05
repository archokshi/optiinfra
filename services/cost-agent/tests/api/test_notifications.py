"""
Test Notification Endpoints.

Tests for notification management.
"""

import pytest
from fastapi.testclient import TestClient


def test_list_notifications(client, test_api_key):
    """Test listing notifications."""
    response = client.get(
        "/api/v1/notifications/list?limit=50",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_unread_notifications(client, test_api_key):
    """Test listing unread notifications."""
    response = client.get(
        "/api/v1/notifications/list?unread_only=true",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_mark_notifications_read(client, test_api_key):
    """Test marking notifications as read."""
    response = client.post(
        "/api/v1/notifications/mark-read",
        headers={"X-API-Key": test_api_key},
        json=["notif-1", "notif-2"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "count" in data


def test_mark_all_notifications_read(client, test_api_key):
    """Test marking all notifications as read."""
    response = client.post(
        "/api/v1/notifications/mark-all-read",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200


def test_delete_notification(client, test_api_key):
    """Test deleting notification."""
    response = client.delete(
        "/api/v1/notifications/notif-123",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200


def test_get_unread_count(client, test_api_key):
    """Test getting unread notification count."""
    response = client.get(
        "/api/v1/notifications/unread-count",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_category" in data

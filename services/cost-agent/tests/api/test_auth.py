"""
Test Authentication Endpoints.

Tests for API key and JWT authentication.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_api_key(client):
    """Test API key creation."""
    response = client.post(
        "/api/v1/auth/api-key/create",
        json={
            "customer_id": "cust-test",
            "name": "Test Key",
            "expires_days": 365
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    assert data["key"].startswith("sk_")
    assert data["customer_id"] == "cust-test"
    assert data["name"] == "Test Key"


def test_list_api_keys(client, test_api_key):
    """Test listing API keys."""
    response = client.get(
        "/api/v1/auth/api-key/list?customer_id=cust-test",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_jwt_token(client):
    """Test JWT token creation."""
    response = client.post(
        "/api/v1/auth/token",
        json={
            "username": "testuser",
            "password": "testpass"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client, test_api_key):
    """Test getting current user info."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "customer_id" in data
    assert data["customer_id"] == "cust-test"


def test_protected_endpoint_without_auth(client):
    """Test accessing protected endpoint without auth."""
    response = client.get("/api/v1/bulk/history")
    
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_key(client):
    """Test accessing protected endpoint with invalid key."""
    response = client.get(
        "/api/v1/bulk/history",
        headers={"X-API-Key": "sk_invalid_key"}
    )
    
    assert response.status_code == 401


def test_revoke_api_key(client, test_api_key):
    """Test revoking API key."""
    # First, create a key to revoke
    create_response = client.post(
        "/api/v1/auth/api-key/create",
        json={
            "customer_id": "cust-test",
            "name": "Key to Revoke",
            "expires_days": 1
        }
    )
    key_id = create_response.json()["id"]
    
    # Revoke it
    response = client.post(
        f"/api/v1/auth/api-key/{key_id}/revoke",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200


def test_delete_api_key(client, test_api_key):
    """Test deleting API key."""
    # First, create a key to delete
    create_response = client.post(
        "/api/v1/auth/api-key/create",
        json={
            "customer_id": "cust-test",
            "name": "Key to Delete",
            "expires_days": 1
        }
    )
    key_id = create_response.json()["id"]
    
    # Delete it
    response = client.delete(
        f"/api/v1/auth/api-key/{key_id}",
        headers={"X-API-Key": test_api_key}
    )
    
    assert response.status_code == 200

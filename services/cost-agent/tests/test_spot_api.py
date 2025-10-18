"""
Tests for spot migration API endpoint.
"""

from fastapi.testclient import TestClient


def test_spot_migration_endpoint_exists(client: TestClient):
    """Test that /spot-migration endpoint exists"""
    response = client.post(
        "/spot-migration",
        json={
            "customer_id": "test-customer-001",
            "auto_approve": True,
        },
    )
    assert response.status_code == 200


def test_spot_migration_response_structure(client: TestClient):
    """Test spot migration response structure"""
    response = client.post(
        "/spot-migration",
        json={
            "customer_id": "test-customer-001",
            "auto_approve": True,
        },
    )

    data = response.json()
    assert "request_id" in data
    assert "customer_id" in data
    assert "timestamp" in data
    assert "instances_analyzed" in data
    assert "opportunities_found" in data
    assert "total_savings" in data
    assert "workflow_status" in data
    assert "final_savings" in data
    assert "success" in data


def test_spot_migration_analyzes_instances(client: TestClient):
    """Test that spot migration analyzes instances"""
    response = client.post(
        "/spot-migration",
        json={
            "customer_id": "test-customer-001",
            "auto_approve": True,
        },
    )

    data = response.json()
    assert data["instances_analyzed"] > 0
    assert "opportunities" in data


def test_spot_migration_finds_savings(client: TestClient):
    """Test that spot migration finds savings"""
    response = client.post(
        "/spot-migration",
        json={
            "customer_id": "test-customer-001",
            "auto_approve": True,
        },
    )

    data = response.json()
    assert data["total_savings"] >= 0
    assert data["final_savings"] >= 0


def test_spot_migration_has_agent_approvals(client: TestClient):
    """Test that spot migration includes agent approvals"""
    response = client.post(
        "/spot-migration",
        json={
            "customer_id": "test-customer-001",
            "auto_approve": True,
        },
    )

    data = response.json()
    assert data.get("performance_approval") is not None
    assert data.get("resource_approval") is not None
    assert data.get("application_approval") is not None


def test_spot_migration_has_execution_phases(client: TestClient):
    """Test that spot migration includes execution phases"""
    response = client.post(
        "/spot-migration",
        json={
            "customer_id": "test-customer-001",
            "auto_approve": True,
        },
    )

    data = response.json()
    # May be None if no opportunities found
    if data.get("opportunities_found", 0) > 0:
        # Only check if opportunities were found and migration succeeded
        if data.get("workflow_status") == "complete":
            assert data.get("execution_10_percent") is not None
            assert data.get("execution_50_percent") is not None
            assert data.get("execution_100_percent") is not None
    else:
        # No opportunities is valid - just check status
        assert data.get("workflow_status") in ["failed", "complete", "monitoring"]


def test_spot_migration_validates_customer_id(client: TestClient):
    """Test that customer_id is required"""
    response = client.post(
        "/spot-migration",
        json={
            "auto_approve": True,
        },
    )
    assert response.status_code == 422  # Validation error

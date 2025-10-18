"""
Tests for health endpoint.
"""

from fastapi.testclient import TestClient


def test_health_endpoint_returns_200(client: TestClient):
    """Test that health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_has_correct_structure(client: TestClient):
    """Test that health response has correct structure"""
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "agent_id" in data
    assert "agent_type" in data
    assert "uptime_seconds" in data


def test_health_status_is_healthy(client: TestClient):
    """Test that health status is 'healthy'"""
    response = client.get("/health")
    data = response.json()

    assert data["status"] == "healthy"


def test_health_agent_type_is_cost(client: TestClient):
    """Test that agent type is 'cost'"""
    response = client.get("/health")
    data = response.json()

    assert data["agent_type"] == "cost"


def test_health_version_is_present(client: TestClient):
    """Test that version is present"""
    response = client.get("/health")
    data = response.json()

    assert data["version"] == "0.1.0"


def test_root_endpoint_returns_200(client: TestClient):
    """Test that root endpoint returns 200 OK"""
    response = client.get("/")
    assert response.status_code == 200


def test_root_endpoint_has_capabilities(client: TestClient):
    """Test that root endpoint lists capabilities"""
    response = client.get("/")
    data = response.json()

    assert "capabilities" in data
    assert "spot_migration" in data["capabilities"]
    assert "reserved_instances" in data["capabilities"]
    assert "right_sizing" in data["capabilities"]


def test_health_uptime_increases(client: TestClient):
    """Test that uptime increases between calls"""
    import time

    response1 = client.get("/health")
    time.sleep(0.1)
    response2 = client.get("/health")

    uptime1 = response1.json()["uptime_seconds"]
    uptime2 = response2.json()["uptime_seconds"]

    assert uptime2 > uptime1

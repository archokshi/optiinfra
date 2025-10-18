"""
Tests for analysis API endpoint.
"""

from fastapi.testclient import TestClient


def test_analyze_endpoint_exists(client: TestClient):
    """Test that /analyze endpoint exists"""
    response = client.post(
        "/analyze",
        json={
            "resources": [
                {
                    "resource_id": "i-test",
                    "resource_type": "ec2",
                    "provider": "aws",
                    "region": "us-east-1",
                    "cost_per_month": 100.0,
                    "utilization": 0.2,
                    "tags": {},
                }
            ]
        },
    )
    assert response.status_code == 200


def test_analyze_endpoint_response_structure(client: TestClient):
    """Test that analyze response has correct structure"""
    response = client.post(
        "/analyze",
        json={
            "resources": [
                {
                    "resource_id": "i-test",
                    "resource_type": "ec2",
                    "provider": "aws",
                    "region": "us-east-1",
                    "cost_per_month": 100.0,
                    "utilization": 0.2,
                    "tags": {},
                }
            ]
        },
    )

    data = response.json()
    assert "request_id" in data
    assert "timestamp" in data
    assert "resources_analyzed" in data
    assert "total_waste_detected" in data
    assert "total_potential_savings" in data
    assert "recommendations" in data
    assert "summary" in data
    assert "workflow_status" in data


def test_analyze_detects_waste(client: TestClient):
    """Test that analysis detects waste"""
    response = client.post(
        "/analyze",
        json={
            "resources": [
                {
                    "resource_id": "i-wasteful",
                    "resource_type": "ec2",
                    "provider": "aws",
                    "region": "us-east-1",
                    "cost_per_month": 200.0,
                    "utilization": 0.1,  # Very low utilization
                    "tags": {},
                }
            ]
        },
    )

    data = response.json()
    assert data["total_waste_detected"] > 0
    assert len(data["recommendations"]) > 0


def test_analyze_with_multiple_resources(client: TestClient):
    """Test analysis with multiple resources"""
    response = client.post(
        "/analyze",
        json={
            "resources": [
                {
                    "resource_id": "i-test1",
                    "resource_type": "ec2",
                    "provider": "aws",
                    "region": "us-east-1",
                    "cost_per_month": 100.0,
                    "utilization": 0.2,
                    "tags": {},
                },
                {
                    "resource_id": "i-test2",
                    "resource_type": "ec2",
                    "provider": "aws",
                    "region": "us-west-2",
                    "cost_per_month": 150.0,
                    "utilization": 0.3,
                    "tags": {},
                },
            ]
        },
    )

    data = response.json()
    assert data["resources_analyzed"] == 2
    assert data["workflow_status"] == "complete"


def test_analyze_rejects_empty_resources(client: TestClient):
    """Test that empty resources list is rejected"""
    response = client.post("/analyze", json={"resources": []})
    assert response.status_code == 422  # Validation error


def test_analyze_validates_utilization_range(client: TestClient):
    """Test that utilization must be between 0 and 1"""
    response = client.post(
        "/analyze",
        json={
            "resources": [
                {
                    "resource_id": "i-invalid",
                    "resource_type": "ec2",
                    "provider": "aws",
                    "region": "us-east-1",
                    "cost_per_month": 100.0,
                    "utilization": 1.5,  # Invalid: > 1
                    "tags": {},
                }
            ]
        },
    )
    assert response.status_code == 422  # Validation error

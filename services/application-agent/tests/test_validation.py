"""
Tests for validation engine.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.validation import ABTestGroup

client = TestClient(app)


def test_create_validation():
    """Test creating a validation request."""
    request = {
        "name": "Test Validation",
        "model_name": "gpt-oss-20b",
        "baseline_quality": 85.0,
        "new_quality": 87.0
    }
    
    response = client.post("/validation/create", json=request)
    assert response.status_code == 201
    
    data = response.json()
    assert "validation_id" in data
    assert data["decision"] in ["approve", "reject", "manual_review"]
    assert "confidence" in data
    assert data["baseline_quality"] == 85.0
    assert data["new_quality"] == 87.0


def test_auto_approve_improvement():
    """Test auto-approve for quality improvement."""
    request = {
        "name": "Improvement Test",
        "model_name": "gpt-oss-20b",
        "baseline_quality": 80.0,
        "new_quality": 85.0
    }
    
    response = client.post("/validation/create", json=request)
    assert response.status_code == 201
    
    data = response.json()
    assert data["decision"] == "approve"
    assert data["quality_change"] > 0
    assert data["confidence"] > 0.8


def test_auto_reject_degradation():
    """Test auto-reject for significant quality drop."""
    request = {
        "name": "Degradation Test",
        "model_name": "gpt-oss-20b",
        "baseline_quality": 85.0,
        "new_quality": 75.0
    }
    
    response = client.post("/validation/create", json=request)
    assert response.status_code == 201
    
    data = response.json()
    assert data["decision"] == "reject"
    assert data["quality_change"] < 0
    assert abs(data["quality_change_percentage"]) > 5.0


def test_manual_review_borderline():
    """Test manual review for borderline cases."""
    request = {
        "name": "Borderline Test",
        "model_name": "gpt-oss-20b",
        "baseline_quality": 85.0,
        "new_quality": 82.0
    }
    
    response = client.post("/validation/create", json=request)
    assert response.status_code == 201
    
    data = response.json()
    # Could be approve or manual_review depending on exact threshold
    assert data["decision"] in ["approve", "manual_review"]


def test_setup_ab_test():
    """Test setting up an A/B test."""
    response = client.post(
        "/validation/ab-test",
        params={
            "name": "Quality Test",
            "control_group": "current",
            "treatment_group": "new",
            "metric": "overall_quality",
            "sample_size": 50
        }
    )
    
    assert response.status_code == 201
    
    data = response.json()
    assert "test_id" in data
    assert data["name"] == "Quality Test"
    assert data["control_group"] == "current"
    assert data["treatment_group"] == "new"


def test_add_observations():
    """Test adding observations to A/B test."""
    # Setup test
    setup_response = client.post(
        "/validation/ab-test",
        params={
            "name": "Observation Test",
            "control_group": "control",
            "treatment_group": "treatment"
        }
    )
    test_id = setup_response.json()["test_id"]
    
    # Add control observation
    obs1 = {
        "test_id": test_id,
        "group": "control",
        "value": 85.0
    }
    response1 = client.post("/validation/observation", json=obs1)
    assert response1.status_code == 201
    
    # Add treatment observation
    obs2 = {
        "test_id": test_id,
        "group": "treatment",
        "value": 88.0
    }
    response2 = client.post("/validation/observation", json=obs2)
    assert response2.status_code == 201


def test_ab_test_results():
    """Test getting A/B test results."""
    # Setup test
    setup_response = client.post(
        "/validation/ab-test",
        params={
            "name": "Results Test",
            "control_group": "control",
            "treatment_group": "treatment"
        }
    )
    test_id = setup_response.json()["test_id"]
    
    # Add multiple observations
    for i in range(10):
        client.post("/validation/observation", json={
            "test_id": test_id,
            "group": "control",
            "value": 85.0 + i * 0.1
        })
        client.post("/validation/observation", json={
            "test_id": test_id,
            "group": "treatment",
            "value": 88.0 + i * 0.1
        })
    
    # Get results
    response = client.get(f"/validation/results/{test_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "control_mean" in data
    assert "treatment_mean" in data
    assert "p_value" in data
    assert "statistically_significant" in data
    assert data["treatment_mean"] > data["control_mean"]


def test_make_decision():
    """Test making a validation decision."""
    response = client.post(
        "/validation/decide",
        params={
            "name": "Decision Test",
            "model_name": "gpt-oss-20b",
            "baseline_quality": 85.0,
            "new_quality": 90.0,
            "p_value": 0.01
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "approve"
    assert data["statistically_significant"] == True
    assert data["quality_change"] > 0


def test_validation_history():
    """Test getting validation history."""
    # Create a few validations first
    for i in range(3):
        client.post("/validation/create", json={
            "name": f"History Test {i}",
            "model_name": "gpt-oss-20b",
            "baseline_quality": 85.0,
            "new_quality": 85.0 + i
        })
    
    response = client.get("/validation/history")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "history" in data
    assert len(data["history"]) >= 3

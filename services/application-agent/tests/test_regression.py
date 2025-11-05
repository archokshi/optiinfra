"""
Tests for regression detection.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.quality_metrics import QualityRequest

client = TestClient(app)


def test_establish_baseline():
    """Test baseline establishment."""
    # First, add some quality metrics
    for i in range(10):
        request = {
            "prompt": f"Test prompt {i}",
            "response": f"Test response {i}",
            "model_name": "gpt-oss-20b"
        }
        client.post("/quality/analyze", json=request)
    
    # Establish baseline
    baseline_config = {
        "model_name": "gpt-oss-20b",
        "config_hash": "default",
        "sample_size": 10
    }
    
    response = client.post("/regression/baseline", json=baseline_config)
    assert response.status_code == 201
    
    data = response.json()
    assert "baseline_id" in data
    assert data["model_name"] == "gpt-oss-20b"
    assert "metrics" in data
    assert "average_quality" in data["metrics"]


def test_detect_no_regression():
    """Test regression detection when no regression exists."""
    # Establish baseline first
    for i in range(10):
        request = {
            "prompt": f"Good prompt {i}",
            "response": f"Good response {i}",
            "model_name": "test-model-1"
        }
        client.post("/quality/analyze", json=request)
    
    baseline_config = {
        "model_name": "test-model-1",
        "config_hash": "default",
        "sample_size": 10
    }
    client.post("/regression/baseline", json=baseline_config)
    
    # Detect regression with similar quality
    detection_request = {
        "model_name": "test-model-1",
        "config_hash": "default",
        "current_quality": 75.0  # Similar to baseline
    }
    
    response = client.post("/regression/detect", json=detection_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["regression_detected"] == False
    assert data["severity"] == "none"


def test_detect_minor_regression():
    """Test detection of minor regression."""
    # Establish baseline
    for i in range(10):
        request = {
            "prompt": f"Quality prompt {i}",
            "response": f"Quality response {i}",
            "model_name": "test-model-2"
        }
        client.post("/quality/analyze", json=request)
    
    baseline_config = {
        "model_name": "test-model-2",
        "config_hash": "default",
        "sample_size": 10
    }
    client.post("/regression/baseline", json=baseline_config)
    
    # Detect regression with 7% drop
    detection_request = {
        "model_name": "test-model-2",
        "config_hash": "default",
        "current_quality": 70.0  # ~7% drop from ~75
    }
    
    response = client.post("/regression/detect", json=detection_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["regression_detected"] == True
    assert data["severity"] in ["minor", "moderate"]
    assert "alert" in data


def test_detect_severe_regression():
    """Test detection of severe regression."""
    # Establish baseline
    for i in range(10):
        request = {
            "prompt": f"Test {i}",
            "response": f"Response {i}",
            "model_name": "test-model-3"
        }
        client.post("/quality/analyze", json=request)
    
    baseline_config = {
        "model_name": "test-model-3",
        "config_hash": "default",
        "sample_size": 10
    }
    client.post("/regression/baseline", json=baseline_config)
    
    # Detect regression with significant drop
    detection_request = {
        "model_name": "test-model-3",
        "config_hash": "default",
        "current_quality": 40.0  # Significant drop
    }
    
    response = client.post("/regression/detect", json=detection_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["regression_detected"] == True
    assert data["severity"] in ["moderate", "severe", "critical"]  # Accept any significant regression
    assert data["alert"]["level"] in ["warning", "critical"]


def test_list_baselines():
    """Test listing baselines."""
    response = client.get("/regression/baselines")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "baselines" in data
    assert isinstance(data["baselines"], list)


def test_get_alerts():
    """Test getting alerts."""
    response = client.get("/regression/alerts")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


def test_get_regression_history():
    """Test getting regression history."""
    response = client.get("/regression/history")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "history" in data
    assert isinstance(data["history"], list)


def test_baseline_not_found():
    """Test regression detection with no baseline."""
    detection_request = {
        "model_name": "nonexistent-model",
        "config_hash": "default",
        "current_quality": 75.0
    }
    
    response = client.post("/regression/detect", json=detection_request)
    assert response.status_code == 404

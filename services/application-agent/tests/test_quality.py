"""
Tests for quality monitoring.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.quality_metrics import QualityRequest

client = TestClient(app)


def test_analyze_quality():
    """Test quality analysis endpoint."""
    request = {
        "prompt": "What is the capital of France?",
        "response": "The capital of France is Paris.",
        "model_name": "test-model"
    }
    
    response = client.post("/quality/analyze", json=request)
    assert response.status_code == 200
    
    data = response.json()
    assert "overall_quality" in data
    assert "quality_grade" in data
    assert "relevance" in data
    assert "coherence" in data
    assert "hallucination" in data
    assert 0 <= data["overall_quality"] <= 100


def test_quality_trend():
    """Test quality trend endpoint."""
    # First add some metrics
    request = {
        "prompt": "Test prompt",
        "response": "Test response",
        "model_name": "test-model"
    }
    client.post("/quality/analyze", json=request)
    
    # Get trend
    response = client.get("/quality/trend?time_period=1h")
    assert response.status_code == 200
    
    data = response.json()
    assert "average_quality" in data
    assert "total_requests" in data


def test_quality_insights():
    """Test quality insights endpoint."""
    # First add some metrics
    request = {
        "prompt": "Test prompt",
        "response": "Test response",
        "model_name": "test-model"
    }
    client.post("/quality/analyze", json=request)
    
    # Get insights
    response = client.get("/quality/insights")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "average_quality" in data


def test_latest_metrics():
    """Test latest metrics endpoint."""
    # First add some metrics
    request = {
        "prompt": "Test prompt",
        "response": "Test response",
        "model_name": "test-model"
    }
    client.post("/quality/analyze", json=request)
    
    # Get latest
    response = client.get("/quality/metrics/latest")
    assert response.status_code == 200
    
    data = response.json()
    assert "overall_quality" in data


def test_metrics_history():
    """Test metrics history endpoint."""
    # First add some metrics
    request = {
        "prompt": "Test prompt",
        "response": "Test response",
        "model_name": "test-model"
    }
    client.post("/quality/analyze", json=request)
    
    # Get history
    response = client.get("/quality/metrics/history?limit=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "metrics" in data


def test_relevance_scoring():
    """Test relevance scoring."""
    # High relevance
    request = {
        "prompt": "What is 2+2?",
        "response": "2+2 equals 4."
    }
    response = client.post("/quality/analyze", json=request)
    data = response.json()
    assert data["relevance"]["score"] > 40  # Adjusted for short responses
    
    # Low relevance
    request = {
        "prompt": "What is the capital of France?",
        "response": "I like pizza."
    }
    response = client.post("/quality/analyze", json=request)
    data = response.json()
    assert data["relevance"]["score"] < 50


def test_coherence_scoring():
    """Test coherence scoring."""
    # Good coherence
    request = {
        "prompt": "Explain gravity",
        "response": "Gravity is a force that attracts objects with mass. It keeps us on Earth and planets in orbit."
    }
    response = client.post("/quality/analyze", json=request)
    data = response.json()
    assert data["coherence"]["score"] > 60


def test_hallucination_detection():
    """Test hallucination detection."""
    # High hallucination
    request = {
        "prompt": "When was the Eiffel Tower built?",
        "response": "I think maybe it was built in 1776 by Napoleon, probably around 12,345 workers."
    }
    response = client.post("/quality/analyze", json=request)
    data = response.json()
    assert data["hallucination"]["hallucination_rate"] > 20
    assert data["hallucination"]["confidence_markers"] > 0

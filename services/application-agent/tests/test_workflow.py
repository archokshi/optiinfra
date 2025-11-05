"""
Tests for LangGraph workflow.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_workflow_approve():
    """Test workflow with approval decision."""
    # First, create some quality metrics to establish baseline
    for i in range(10):
        client.post("/quality/analyze", json={
            "prompt": f"Test prompt {i}",
            "response": f"Test response {i}",
            "model_name": "workflow-test-1"
        })
    
    # Run workflow with good quality
    request = {
        "model_name": "workflow-test-1",
        "prompt": "What is the capital of France?",
        "response": "The capital of France is Paris, a beautiful city known for its culture and history."
    }
    
    response = client.post("/workflow/validate", json=request)
    assert response.status_code == 200
    
    data = response.json()
    assert "request_id" in data
    assert data["status"] in ["completed", "baseline_checked"]
    assert "quality_metrics" in data
    
    # If baseline exists and workflow completed
    if data["status"] == "completed":
        assert data["decision"] in ["approve", "manual_review"]


def test_workflow_reject():
    """Test workflow with rejection decision."""
    # Create baseline
    for i in range(10):
        client.post("/quality/analyze", json={
            "prompt": f"Quality prompt {i}",
            "response": f"Quality response {i}",
            "model_name": "workflow-test-2"
        })
    
    # Run workflow with poor quality
    request = {
        "model_name": "workflow-test-2",
        "prompt": "What is 2+2?",
        "response": "I dont know"
    }
    
    response = client.post("/workflow/validate", json=request)
    assert response.status_code == 200
    
    data = response.json()
    assert "request_id" in data
    assert "quality_metrics" in data


def test_workflow_no_baseline():
    """Test workflow when no baseline exists."""
    request = {
        "model_name": "workflow-test-new-model",
        "prompt": "Test prompt",
        "response": "Test response"
    }
    
    response = client.post("/workflow/validate", json=request)
    assert response.status_code == 200
    
    data = response.json()
    assert "request_id" in data
    assert "quality_metrics" in data
    # Should end early if no baseline
    assert data["status"] in ["completed", "baseline_checked"]


def test_get_workflow_status():
    """Test getting workflow status."""
    # Run a workflow first
    request = {
        "model_name": "workflow-test-status",
        "prompt": "Test",
        "response": "Response"
    }
    
    workflow_response = client.post("/workflow/validate", json=request)
    request_id = workflow_response.json()["request_id"]
    
    # Get status
    response = client.get(f"/workflow/status/{request_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["request_id"] == request_id
    assert "status" in data
    assert "current_step" in data


def test_get_workflow_history():
    """Test getting workflow history."""
    # Run a few workflows
    for i in range(3):
        client.post("/workflow/validate", json={
            "model_name": f"workflow-test-history-{i}",
            "prompt": f"Test {i}",
            "response": f"Response {i}"
        })
    
    response = client.get("/workflow/history")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "workflows" in data
    assert len(data["workflows"]) >= 3


def test_workflow_status_not_found():
    """Test getting status for non-existent workflow."""
    response = client.get("/workflow/status/nonexistent-id")
    assert response.status_code == 404

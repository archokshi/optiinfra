"""
Integration tests for Application Agent.

Tests end-to-end workflows across multiple components.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_e2e_quality_workflow():
    """Test end-to-end quality monitoring workflow."""
    # 1. Analyze quality metrics
    response = client.post("/quality/analyze", json={
        "prompt": "What is AI?",
        "response": "AI is artificial intelligence...",
        "model_id": "model-v1"
    })
    assert response.status_code == 200
    
    # 2. Get quality insights
    insights = client.get("/quality/insights")
    assert insights.status_code == 200
    assert "average_quality" in insights.json()
    
    # 3. Get latest metrics
    latest = client.get("/quality/metrics/latest")
    assert latest.status_code == 200


def test_regression_detection_workflow():
    """Test regression detection workflow."""
    # 1. Establish baseline
    baseline_response = client.post("/regression/baseline", json={
        "model_name": "model-v1",
        "config_hash": "v1.0.0",
        "sample_size": 100
    })
    assert baseline_response.status_code == 201
    baseline_id = baseline_response.json()["baseline_id"]
    
    # 2. Detect regression (no regression)
    no_regression = client.post("/regression/detect", json={
        "model_name": "model-v1",
        "config_hash": "v1.0.0",
        "current_quality": 86.0
    })
    assert no_regression.status_code == 200
    assert no_regression.json()["regression_detected"] == False
    
    # 3. Detect regression (with regression)
    with_regression = client.post("/regression/detect", json={
        "model_name": "model-v1",
        "config_hash": "v1.0.0",
        "current_quality": 70.0
    })
    assert with_regression.status_code == 200
    assert with_regression.json()["regression_detected"] == True


def test_validation_workflow():
    """Test validation engine workflow."""
    # 1. Create validation
    validation_response = client.post("/validation/create", json={
        "name": "test-validation",
        "model_name": "model-v1",
        "baseline_quality": 85.0,
        "new_quality": 87.0
    })
    assert validation_response.status_code == 201
    result = validation_response.json()
    assert "validation_id" in result
    assert "decision" in result
    
    # 2. Get validation history
    history = client.get("/validation/history")
    assert history.status_code == 200


def test_llm_integration_workflow():
    """Test LLM integration workflow."""
    # 1. Analyze with LLM
    analysis = client.post("/llm/analyze", json={
        "prompt": "What is AI?",
        "response": "AI is artificial intelligence..."
    })
    # May return 200 or 503 depending on LLM availability
    assert analysis.status_code in [200, 503]
    
    # 2. Get recommendations (if LLM available)
    recommendations = client.get("/config/recommendations")
    assert recommendations.status_code == 200


def test_configuration_optimization_workflow():
    """Test configuration optimization workflow."""
    # 1. Get current configuration
    current = client.get("/config/current")
    assert current.status_code == 200
    
    # 2. Analyze parameter impact
    analysis = client.post("/config/analyze?parameter=temperature&samples=100")
    assert analysis.status_code == 200
    
    # 3. Get recommendations
    recommendations = client.get("/config/recommendations")
    assert recommendations.status_code == 200
    
    # 4. Optimize configuration
    optimization = client.post("/config/optimize", json={
        "strategy": "balanced",
        "constraints": {}
    })
    assert optimization.status_code == 200


def test_bulk_operations_workflow():
    """Test bulk operations workflow."""
    # 1. Submit bulk quality job
    bulk_response = client.post("/bulk/quality", json={
        "samples": [
            {
                "prompt": "What is AI?",
                "response": "AI is...",
                "model_id": "model-v1"
            }
        ]
    })
    assert bulk_response.status_code == 202
    job_id = bulk_response.json()["job_id"]
    
    # 2. Check job status
    status = client.get(f"/bulk/status/{job_id}")
    assert status.status_code == 200
    assert status.json()["job_id"] == job_id


def test_analytics_workflow():
    """Test analytics workflow."""
    # 1. Get analytics summary
    summary = client.get("/analytics/summary")
    assert summary.status_code == 200
    assert "avg_quality" in summary.json()
    
    # 2. Get trends
    trends = client.get("/analytics/trends")
    assert trends.status_code == 200
    
    # 3. Compare models
    comparison = client.get("/analytics/comparison?models=model-v1,model-v2")
    assert comparison.status_code == 200


def test_admin_operations_workflow():
    """Test admin operations workflow."""
    # 1. Get agent stats
    stats = client.get("/admin/stats")
    assert stats.status_code == 200
    assert "uptime_seconds" in stats.json()
    
    # 2. Get logs
    logs = client.get("/admin/logs")
    assert logs.status_code == 200
    
    # 3. Reload configuration
    reload = client.post("/admin/config/reload")
    assert reload.status_code == 200


def test_complete_quality_validation_cycle():
    """Test complete quality validation cycle."""
    # 1. Analyze quality
    analyze = client.post("/quality/analyze", json={
        "prompt": "Test prompt",
        "response": "Test response",
        "model_id": "test-model"
    })
    assert analyze.status_code == 200
    
    # 2. Establish baseline
    baseline = client.post("/regression/baseline", json={
        "model_name": "test-model",
        "config_hash": "v1.0.0",
        "sample_size": 100
    })
    assert baseline.status_code == 201
    
    # 3. Create validation
    validation = client.post("/validation/create", json={
        "name": "test-validation",
        "model_name": "test-model",
        "baseline_quality": 85.0,
        "new_quality": 87.0
    })
    assert validation.status_code == 201
    
    # 4. Execute workflow
    workflow = client.post("/workflow/validate", json={
        "model_name": "test-model",
        "prompt": "Test prompt",
        "response": "Test response"
    })
    assert workflow.status_code == 200


def test_health_check_integration():
    """Test health check integration."""
    # Basic health check
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    
    # Detailed health check
    detailed = client.get("/health/detailed")
    assert detailed.status_code == 200
    assert "components" in detailed.json()

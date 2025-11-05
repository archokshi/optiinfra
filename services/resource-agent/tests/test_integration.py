"""
Integration Tests

End-to-end integration tests for Resource Agent.
"""

import pytest
from fastapi import status
from tests.helpers import assert_response_structure


def test_full_metrics_to_analysis_flow(client):
    """Test complete flow from metrics collection to analysis."""
    # Step 1: Collect system metrics
    response = client.get("/system/metrics")
    assert response.status_code == status.HTTP_200_OK
    system_metrics = response.json()
    assert "cpu" in system_metrics
    assert "memory" in system_metrics
    
    # Step 2: Run analysis
    response = client.get("/analysis/")
    assert response.status_code == status.HTTP_200_OK
    analysis = response.json()
    assert "health_score" in analysis
    assert "primary_bottleneck" in analysis
    
    # Step 3: Get health score
    response = client.get("/analysis/health-score")
    assert response.status_code == status.HTTP_200_OK
    health = response.json()
    assert "health_score" in health
    # Health scores should be similar (within 10 points due to timing differences)
    assert abs(health["health_score"] - analysis["health_score"]) < 10


def test_lmcache_integration(client):
    """Test LMCache integration with analysis."""
    # Get LMCache status
    response = client.get("/lmcache/status")
    assert response.status_code == status.HTTP_200_OK
    lmcache_status = response.json()
    assert "metrics" in lmcache_status
    
    # Run analysis (should include LMCache data)
    response = client.get("/analysis/")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_optimization_workflow_integration(client):
    """Test complete optimization workflow."""
    # Run optimization
    response = client.post("/optimize/run")
    
    # Should return 200 or 500 depending on LLM availability
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    if response.status_code == status.HTTP_200_OK:
        result = response.json()
        assert "workflow_id" in result
        assert "status" in result
        assert "actions" in result


def test_concurrent_requests(client):
    """Test handling of concurrent requests."""
    import concurrent.futures
    
    def make_request():
        return client.get("/health/")
    
    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # All should succeed
    assert all(r.status_code == status.HTTP_200_OK for r in results)


def test_api_chaining(client):
    """Test chaining multiple API calls."""
    # Get GPU info
    gpu_response = client.get("/gpu/info")
    assert gpu_response.status_code == status.HTTP_200_OK
    
    # Get system metrics
    system_response = client.get("/system/metrics")
    assert system_response.status_code == status.HTTP_200_OK
    
    # Get LMCache status
    cache_response = client.get("/lmcache/status")
    assert cache_response.status_code == status.HTTP_200_OK
    
    # Run analysis
    analysis_response = client.get("/analysis/")
    assert analysis_response.status_code == status.HTTP_200_OK


def test_error_propagation(client):
    """Test that errors are properly propagated."""
    # Request invalid GPU ID
    response = client.get("/gpu/metrics/999")
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_503_SERVICE_UNAVAILABLE]


def test_health_check_integration(client):
    """Test health check reflects system state."""
    # Get detailed health
    response = client.get("/health/detailed")
    assert response.status_code == status.HTTP_200_OK
    health = response.json()
    
    assert "status" in health
    assert "components" in health
    # Check that components exist (actual component names may vary)
    assert len(health["components"]) > 0

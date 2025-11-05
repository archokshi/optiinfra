"""
Stress Tests

Tests system behavior under extreme load.
"""

import pytest
import time
import concurrent.futures
from fastapi.testclient import TestClient


@pytest.mark.stress
@pytest.mark.slow
def test_health_endpoint_stress(client: TestClient):
    """Stress test health endpoint with 500 requests."""
    
    def make_request():
        try:
            response = client.get("/api/v1/health")
            return response.status_code
        except Exception:
            return 500
    
    # 500 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(make_request) for _ in range(500)]
        results = [f.result() for f in futures]
    
    # Allow some failures under stress
    success_rate = sum(1 for r in results if r == 200) / len(results)
    assert success_rate > 0.95  # 95% success rate


@pytest.mark.stress
@pytest.mark.slow
def test_mixed_endpoints_stress(client: TestClient):
    """Stress test with 1000 mixed requests."""
    
    endpoints = [
        "/api/v1/health",
        "/api/v1/config",
        "/api/v1/capabilities",
        "/api/v1/workflows"
    ]
    
    def make_request(endpoint):
        try:
            response = client.get(endpoint)
            return response.status_code == 200
        except Exception:
            return False
    
    # 1000 requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(make_request, endpoints[i % len(endpoints)])
            for i in range(1000)
        ]
        results = [f.result() for f in futures]
    
    success_rate = sum(1 for r in results if r) / len(results)
    assert success_rate > 0.90  # 90% success rate under stress


@pytest.mark.stress
@pytest.mark.slow
def test_sustained_load(client: TestClient):
    """Test sustained load over time."""
    
    def make_requests_batch():
        results = []
        for _ in range(10):
            try:
                response = client.get("/api/v1/health")
                results.append(response.status_code == 200)
            except Exception:
                results.append(False)
        return results
    
    # 10 batches of 10 requests each
    all_results = []
    for _ in range(10):
        batch_results = make_requests_batch()
        all_results.extend(batch_results)
        time.sleep(0.1)  # Small delay between batches
    
    success_rate = sum(1 for r in all_results if r) / len(all_results)
    assert success_rate > 0.95


@pytest.mark.stress
def test_rapid_sequential_requests(client: TestClient):
    """Test rapid sequential requests."""
    
    results = []
    for _ in range(200):
        try:
            response = client.get("/api/v1/health")
            results.append(response.status_code == 200)
        except Exception:
            results.append(False)
    
    success_rate = sum(1 for r in results if r) / len(results)
    assert success_rate > 0.98  # 98% success rate

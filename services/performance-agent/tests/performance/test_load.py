"""
Load Tests

Tests system behavior under concurrent load.
"""

import pytest
import time
import concurrent.futures
from fastapi.testclient import TestClient


@pytest.mark.performance
def test_health_endpoint_load(client: TestClient):
    """Test health endpoint under load."""
    
    def make_request():
        start = time.time()
        response = client.get("/api/v1/health")
        duration = time.time() - start
        return response.status_code, duration
    
    # 100 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]
    
    # Verify all succeeded
    status_codes = [r[0] for r in results]
    durations = [r[1] for r in results]
    
    assert all(code == 200 for code in status_codes)
    assert sum(durations) / len(durations) < 1.0  # Average < 1s
    assert max(durations) < 2.0  # Max < 2s


@pytest.mark.performance
def test_config_endpoint_load(client: TestClient):
    """Test config endpoint under load."""
    
    def make_request():
        response = client.get("/api/v1/config")
        return response.status_code
    
    # 50 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in futures]
    
    assert all(code == 200 for code in results)


@pytest.mark.performance
def test_capabilities_endpoint_load(client: TestClient):
    """Test capabilities endpoint under load."""
    
    def make_request():
        response = client.get("/api/v1/capabilities")
        return response.status_code
    
    # 50 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in futures]
    
    assert all(code == 200 for code in results)


@pytest.mark.performance
def test_workflow_list_endpoint_load(client: TestClient):
    """Test workflow list endpoint under load."""
    
    def make_request():
        response = client.get("/api/v1/workflows")
        return response.status_code
    
    # 30 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(30)]
        results = [f.result() for f in futures]
    
    assert all(code == 200 for code in results)


@pytest.mark.performance
def test_mixed_endpoint_load(client: TestClient):
    """Test mixed endpoints under load."""
    
    endpoints = [
        "/api/v1/health",
        "/api/v1/config",
        "/api/v1/capabilities",
        "/api/v1/workflows"
    ]
    
    def make_request(endpoint):
        response = client.get(endpoint)
        return response.status_code
    
    # 100 requests across different endpoints
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(make_request, endpoints[i % len(endpoints)])
            for i in range(100)
        ]
        results = [f.result() for f in futures]
    
    # All should succeed (200)
    assert all(code == 200 for code in results)


@pytest.mark.performance
def test_response_time_consistency(client: TestClient):
    """Test response time consistency under load."""
    
    def make_request():
        start = time.time()
        response = client.get("/api/v1/health")
        duration = time.time() - start
        return duration
    
    # 50 sequential requests to measure consistency
    durations = []
    for _ in range(50):
        durations.append(make_request())
    
    # Calculate statistics
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    
    # Response times should be consistent
    assert avg_duration < 0.5  # Average < 500ms
    assert max_duration < 1.0  # Max < 1s
    assert max_duration - min_duration < 0.5  # Variance < 500ms

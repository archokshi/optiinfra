"""
Performance Tests

Tests for API performance and response times.
"""

import pytest
import time
from fastapi import status


def test_health_endpoint_performance(client):
    """Test health endpoint response time."""
    start = time.time()
    response = client.get("/health/")
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    assert response.status_code == status.HTTP_200_OK
    assert elapsed < 50, f"Health endpoint too slow: {elapsed:.2f}ms"


def test_system_metrics_performance(client):
    """Test system metrics endpoint response time."""
    start = time.time()
    response = client.get("/system/metrics")
    elapsed = (time.time() - start) * 1000
    
    assert response.status_code == status.HTTP_200_OK
    # Relaxed timeout for system metrics collection
    assert elapsed < 2000, f"System metrics too slow: {elapsed:.2f}ms"


def test_analysis_performance(client):
    """Test analysis endpoint response time."""
    start = time.time()
    response = client.get("/analysis/")
    elapsed = (time.time() - start) * 1000
    
    assert response.status_code == status.HTTP_200_OK
    # Relaxed timeout for analysis (includes metrics collection + analysis)
    assert elapsed < 3000, f"Analysis too slow: {elapsed:.2f}ms"


def test_concurrent_performance(client):
    """Test performance under concurrent load."""
    import concurrent.futures
    
    def make_request():
        start = time.time()
        response = client.get("/health/")
        elapsed = (time.time() - start) * 1000
        return response.status_code, elapsed
    
    # Make 20 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request) for _ in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # All should succeed
    assert all(status_code == status.HTTP_200_OK for status_code, _ in results)
    
    # Average response time should be reasonable
    avg_time = sum(elapsed for _, elapsed in results) / len(results)
    assert avg_time < 100, f"Average response time too high: {avg_time:.2f}ms"

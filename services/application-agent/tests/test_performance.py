"""
Performance tests for Application Agent.

Tests API performance, latency, and throughput.
"""

import pytest
import time
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_api_latency():
    """Test API response latency."""
    endpoints = [
        "/health",
        "/quality/insights",
        "/config/current",
        "/analytics/summary"
    ]
    
    for endpoint in endpoints:
        start = time.time()
        response = client.get(endpoint)
        latency = (time.time() - start) * 1000  # Convert to ms
        
        assert response.status_code == 200
        assert latency < 100, f"{endpoint} latency {latency}ms exceeds 100ms"


def test_bulk_throughput():
    """Test bulk operations throughput."""
    samples = [
        {
            "prompt": f"Test prompt {i}",
            "response": f"Test response {i}",
            "model_id": "test-model"
        }
        for i in range(10)
    ]
    
    start = time.time()
    response = client.post("/bulk/quality", json={"samples": samples})
    duration = time.time() - start
    
    assert response.status_code == 202
    throughput = len(samples) / duration
    assert throughput > 10, f"Throughput {throughput} req/s is too low"


def test_concurrent_requests():
    """Test handling of concurrent requests."""
    import concurrent.futures
    
    def make_request():
        return client.get("/health")
    
    # Send 20 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request) for _ in range(20)]
        results = [f.result() for f in futures]
    
    # All requests should succeed
    assert all(r.status_code == 200 for r in results)


def test_memory_usage():
    """Test memory usage under load."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Make 100 requests
    for _ in range(100):
        client.get("/health")
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (< 50MB for 100 requests)
    assert memory_increase < 50, f"Memory increased by {memory_increase}MB"


def test_response_time_consistency():
    """Test response time consistency."""
    latencies = []
    
    for _ in range(10):
        start = time.time()
        response = client.get("/health")
        latency = (time.time() - start) * 1000
        latencies.append(latency)
        assert response.status_code == 200
    
    # Calculate standard deviation
    import statistics
    avg_latency = statistics.mean(latencies)
    std_dev = statistics.stdev(latencies)
    
    # Standard deviation should be low (consistent performance)
    assert std_dev < avg_latency * 0.5, f"High latency variance: {std_dev}ms"

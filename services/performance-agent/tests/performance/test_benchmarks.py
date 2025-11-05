"""
Performance Benchmarks

Benchmark tests for response times and throughput.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.benchmark
def test_health_endpoint_benchmark(benchmark, client: TestClient):
    """Benchmark health endpoint."""
    
    def health_check():
        response = client.get("/api/v1/health")
        return response.status_code
    
    result = benchmark(health_check)
    assert result == 200


@pytest.mark.benchmark
def test_config_endpoint_benchmark(benchmark, client: TestClient):
    """Benchmark config endpoint."""
    
    def get_config():
        response = client.get("/api/v1/config")
        return response.json()
    
    result = benchmark(get_config)
    assert "agent_id" in result


@pytest.mark.benchmark
def test_capabilities_endpoint_benchmark(benchmark, client: TestClient):
    """Benchmark capabilities endpoint."""
    
    def get_capabilities():
        response = client.get("/api/v1/capabilities")
        return response.json()
    
    result = benchmark(get_capabilities)
    assert "capabilities" in result


@pytest.mark.benchmark
def test_workflow_list_benchmark(benchmark, client: TestClient):
    """Benchmark workflow list endpoint."""
    
    def list_workflows():
        response = client.get("/api/v1/workflows")
        return response.json()
    
    result = benchmark(list_workflows)
    assert isinstance(result, list)


@pytest.mark.benchmark
def test_health_detailed_benchmark(benchmark, client: TestClient):
    """Benchmark detailed health endpoint."""
    
    def health_detailed():
        response = client.get("/api/v1/health/detailed")
        return response.json()
    
    result = benchmark(health_detailed)
    assert "status" in result

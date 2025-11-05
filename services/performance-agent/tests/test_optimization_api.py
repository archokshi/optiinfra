"""
Optimization API Tests

Tests for optimization API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
def test_optimize_endpoint_success(client: TestClient):
    """Test successful optimization."""
    from src.models.metrics import (
        VLLMMetricsSnapshot,
        VLLMRequestMetrics,
        VLLMGPUMetrics,
        VLLMThroughputMetrics
    )
    
    with patch('src.api.optimization.VLLMCollector') as mock_collector_class:
        # Setup mock collector
        mock_collector = AsyncMock()
        mock_metrics = VLLMMetricsSnapshot(
            instance_id="localhost:8000",
            endpoint="http://localhost:8000/metrics",
            request_metrics=VLLMRequestMetrics(time_to_first_token_seconds=0.15),
            gpu_metrics=VLLMGPUMetrics(num_requests_waiting=12),
            throughput_metrics=VLLMThroughputMetrics()
        )
        mock_collector.collect.return_value = mock_metrics
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/optimize",
            json={
                "instance_id": "localhost:8000",
                "instance_type": "vllm",
                "current_config": {
                    "max_batch_size": 32,
                    "quantization": "none"
                }
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["instance_id"] == "localhost:8000"
        assert data["instance_type"] == "vllm"
        assert "optimizations" in data
        assert "estimated_total_improvement" in data


@pytest.mark.unit
def test_optimize_endpoint_invalid_type(client: TestClient):
    """Test optimization with invalid instance type."""
    response = client.post(
        "/api/v1/optimize",
        json={
            "instance_id": "localhost:8000",
            "instance_type": "invalid"
        }
    )
    
    assert response.status_code == 400


@pytest.mark.unit
def test_optimize_endpoint_with_constraints(client: TestClient):
    """Test optimization with constraints."""
    from src.models.metrics import (
        VLLMMetricsSnapshot,
        VLLMRequestMetrics,
        VLLMGPUMetrics,
        VLLMThroughputMetrics
    )
    
    with patch('src.api.optimization.VLLMCollector') as mock_collector_class:
        # Setup mock
        mock_collector = AsyncMock()
        mock_metrics = VLLMMetricsSnapshot(
            instance_id="localhost:8000",
            endpoint="http://localhost:8000/metrics",
            request_metrics=VLLMRequestMetrics(time_to_first_token_seconds=0.15),
            gpu_metrics=VLLMGPUMetrics(),
            throughput_metrics=VLLMThroughputMetrics()
        )
        mock_collector.collect.return_value = mock_metrics
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request with constraints
        response = client.post(
            "/api/v1/optimize",
            json={
                "instance_id": "localhost:8000",
                "instance_type": "vllm",
                "current_config": {},
                "constraints": {
                    "max_memory_gb": 16,
                    "no_quantization": False
                }
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "optimizations" in data

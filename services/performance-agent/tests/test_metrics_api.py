"""
Metrics API Tests

Tests for metrics collection endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
def test_collect_vllm_metrics_success(client: TestClient):
    """Test successful vLLM metrics collection."""
    from src.models.metrics import (
        VLLMMetricsSnapshot,
        VLLMRequestMetrics,
        VLLMGPUMetrics,
        VLLMThroughputMetrics
    )
    
    with patch('src.api.metrics.VLLMCollector') as mock_collector_class:
        # Setup mock with proper snapshot
        mock_collector = AsyncMock()
        mock_snapshot = VLLMMetricsSnapshot(
            instance_id="vllm-001",
            endpoint="http://localhost:8000/metrics",
            request_metrics=VLLMRequestMetrics(),
            gpu_metrics=VLLMGPUMetrics(),
            throughput_metrics=VLLMThroughputMetrics()
        )
        mock_collector.collect.return_value = mock_snapshot
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/collect/vllm",
            json={
                "instance_id": "vllm-001",
                "endpoint": "http://localhost:8000/metrics",
                "timeout": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["instance_id"] == "vllm-001"


@pytest.mark.unit
def test_collect_vllm_metrics_failure(client: TestClient):
    """Test failed vLLM metrics collection."""
    with patch('src.api.metrics.VLLMCollector') as mock_collector_class:
        # Setup mock to raise error
        mock_collector = AsyncMock()
        mock_collector.collect.side_effect = Exception("Connection failed")
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/collect/vllm",
            json={
                "instance_id": "vllm-001",
                "endpoint": "http://localhost:8000/metrics",
                "timeout": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

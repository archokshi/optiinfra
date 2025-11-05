"""
Analysis API Tests

Tests for analysis API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
def test_analyze_endpoint_success(client: TestClient):
    """Test successful analysis."""
    from src.models.metrics import (
        VLLMMetricsSnapshot,
        VLLMRequestMetrics,
        VLLMGPUMetrics,
        VLLMThroughputMetrics
    )
    from src.models.analysis import AnalysisResult
    
    with patch('src.api.analysis.VLLMCollector') as mock_collector_class:
        # Setup mock collector
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
        
        # Make request
        response = client.post(
            "/api/v1/analyze",
            json={
                "instance_id": "localhost:8000",
                "instance_type": "vllm"
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["instance_id"] == "localhost:8000"
        assert data["instance_type"] == "vllm"
        assert "bottlenecks" in data
        assert "overall_health_score" in data


@pytest.mark.unit
def test_analyze_endpoint_with_slos(client: TestClient):
    """Test analysis with SLO targets."""
    from src.models.metrics import (
        VLLMMetricsSnapshot,
        VLLMRequestMetrics,
        VLLMGPUMetrics,
        VLLMThroughputMetrics
    )
    
    with patch('src.api.analysis.VLLMCollector') as mock_collector_class:
        # Setup mock
        mock_collector = AsyncMock()
        mock_metrics = VLLMMetricsSnapshot(
            instance_id="localhost:8000",
            endpoint="http://localhost:8000/metrics",
            request_metrics=VLLMRequestMetrics(time_to_first_token_seconds=0.08),
            gpu_metrics=VLLMGPUMetrics(),
            throughput_metrics=VLLMThroughputMetrics()
        )
        mock_collector.collect.return_value = mock_metrics
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request with SLO targets
        response = client.post(
            "/api/v1/analyze",
            json={
                "instance_id": "localhost:8000",
                "instance_type": "vllm",
                "slo_targets": [
                    {
                        "name": "TTFT",
                        "metric": "request_metrics.time_to_first_token_seconds",
                        "target_value": 0.1,
                        "comparison": "<"
                    }
                ]
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "slo_statuses" in data
        assert len(data["slo_statuses"]) == 1


@pytest.mark.unit
def test_analyze_endpoint_invalid_type(client: TestClient):
    """Test analysis with invalid instance type."""
    response = client.post(
        "/api/v1/analyze",
        json={
            "instance_id": "localhost:8000",
            "instance_type": "invalid"
        }
    )
    
    assert response.status_code == 400

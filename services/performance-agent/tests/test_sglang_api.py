"""
SGLang API Tests

Tests for SGLang metrics collection endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
def test_collect_sglang_metrics_success(client: TestClient):
    """Test successful SGLang metrics collection."""
    from src.models.metrics import (
        SGLangMetricsSnapshot,
        SGLangRequestMetrics,
        SGLangCacheMetrics,
        SGLangSystemMetrics
    )
    
    with patch('src.api.metrics.SGLangCollector') as mock_collector_class:
        # Setup mock with proper snapshot
        mock_collector = AsyncMock()
        mock_snapshot = SGLangMetricsSnapshot(
            instance_id="sglang-001",
            endpoint="http://localhost:30000/metrics",
            request_metrics=SGLangRequestMetrics(),
            cache_metrics=SGLangCacheMetrics(),
            system_metrics=SGLangSystemMetrics()
        )
        mock_collector.collect.return_value = mock_snapshot
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/collect/sglang",
            json={
                "instance_id": "sglang-001",
                "endpoint": "http://localhost:30000/metrics",
                "timeout": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["instance_id"] == "sglang-001"


@pytest.mark.unit
def test_collect_sglang_metrics_failure(client: TestClient):
    """Test failed SGLang metrics collection."""
    with patch('src.api.metrics.SGLangCollector') as mock_collector_class:
        # Setup mock to raise error
        mock_collector = AsyncMock()
        mock_collector.collect.side_effect = Exception("Connection failed")
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/collect/sglang",
            json={
                "instance_id": "sglang-001",
                "endpoint": "http://localhost:30000/metrics",
                "timeout": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

"""
TGI API Tests

Tests for TGI metrics collection endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
def test_collect_tgi_metrics_success(client: TestClient):
    """Test successful TGI metrics collection."""
    from src.models.metrics import (
        TGIMetricsSnapshot,
        TGIRequestMetrics,
        TGIGenerationMetrics
    )
    
    with patch('src.api.metrics.TGICollector') as mock_collector_class:
        # Setup mock with proper snapshot
        mock_collector = AsyncMock()
        mock_snapshot = TGIMetricsSnapshot(
            instance_id="tgi-001",
            endpoint="http://localhost:8080/metrics",
            request_metrics=TGIRequestMetrics(),
            generation_metrics=TGIGenerationMetrics()
        )
        mock_collector.collect.return_value = mock_snapshot
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/collect/tgi",
            json={
                "instance_id": "tgi-001",
                "endpoint": "http://localhost:8080/metrics",
                "timeout": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["instance_id"] == "tgi-001"


@pytest.mark.unit
def test_collect_tgi_metrics_failure(client: TestClient):
    """Test failed TGI metrics collection."""
    with patch('src.api.metrics.TGICollector') as mock_collector_class:
        # Setup mock to raise error
        mock_collector = AsyncMock()
        mock_collector.collect.side_effect = Exception("Connection failed")
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/collect/tgi",
            json={
                "instance_id": "tgi-001",
                "endpoint": "http://localhost:8080/metrics",
                "timeout": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

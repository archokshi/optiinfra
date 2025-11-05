"""
TGI Collector Tests

Tests for TGI metrics collector.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from src.collectors.tgi_collector import TGICollector
from src.models.metrics import TGIMetricsSnapshot


@pytest.fixture
def sample_tgi_metrics():
    """Sample TGI metrics response."""
    return """
tgi_request_success_total 250
tgi_request_failure_total 3
tgi_request_count 253
tgi_queue_size 5
tgi_request_mean_time_per_token_duration_seconds 0.015
tgi_request_validation_duration_seconds 0.002
tgi_request_queue_duration_seconds 0.050
tgi_request_inference_duration_seconds 1.2
tgi_request_input_length 128
tgi_request_generated_tokens 256
tgi_request_generated_tokens_total 64000
tgi_request_max_new_tokens 512
tgi_batch_current_size 8
tgi_batch_current_max_tokens 2048
"""


@pytest.mark.asyncio
async def test_collect_tgi_metrics(sample_tgi_metrics):
    """Test collecting metrics from TGI instance."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = sample_tgi_metrics
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Collect metrics
        async with TGICollector() as collector:
            snapshot = await collector.collect(
                instance_id="tgi-001",
                endpoint="http://localhost:8080/metrics"
            )
        
        # Verify
        assert isinstance(snapshot, TGIMetricsSnapshot)
        assert snapshot.instance_id == "tgi-001"
        assert snapshot.request_metrics.success_total == 250
        assert snapshot.request_metrics.failure_total == 3
        assert snapshot.request_metrics.queue_size == 5
        assert snapshot.generation_metrics.generated_tokens_total == 64000


@pytest.mark.asyncio
async def test_collect_tgi_metrics_error():
    """Test error handling when TGI collection fails."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Setup mock to raise error
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")
        mock_client_class.return_value = mock_client
        
        # Collect metrics
        async with TGICollector() as collector:
            with pytest.raises(httpx.HTTPError):
                await collector.collect(
                    instance_id="tgi-001",
                    endpoint="http://localhost:8080/metrics"
                )


@pytest.mark.asyncio
async def test_extract_request_metrics(sample_tgi_metrics):
    """Test extraction of request metrics."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = sample_tgi_metrics
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        async with TGICollector() as collector:
            snapshot = await collector.collect(
                instance_id="tgi-001",
                endpoint="http://localhost:8080/metrics"
            )
        
        # Verify request metrics
        assert snapshot.request_metrics.success_total == 250
        assert snapshot.request_metrics.request_count == 253
        assert snapshot.request_metrics.mean_time_per_token_seconds == 0.015


@pytest.mark.asyncio
async def test_extract_generation_metrics(sample_tgi_metrics):
    """Test extraction of generation metrics."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = sample_tgi_metrics
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        async with TGICollector() as collector:
            snapshot = await collector.collect(
                instance_id="tgi-001",
                endpoint="http://localhost:8080/metrics"
            )
        
        # Verify generation metrics
        assert snapshot.generation_metrics.input_length == 128
        assert snapshot.generation_metrics.generated_tokens == 256
        assert snapshot.generation_metrics.batch_current_size == 8

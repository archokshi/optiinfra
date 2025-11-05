"""
SGLang Collector Tests

Tests for SGLang metrics collector.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from src.collectors.sglang_collector import SGLangCollector
from src.models.metrics import SGLangMetricsSnapshot


@pytest.fixture
def sample_sglang_metrics():
    """Sample SGLang metrics response."""
    return """
sglang:request_success_total 300
sglang:request_failure_total 2
sglang:request_duration_seconds 1.8
sglang:time_to_first_token_seconds 0.020
sglang:time_per_output_token_seconds 0.008
sglang:request_input_tokens 256
sglang:request_output_tokens 512
sglang:cache_hit_rate 0.85
sglang:cache_memory_usage_bytes 4294967296
sglang:radix_cache_size 1024
sglang:prefix_cache_hit_total 255
sglang:num_requests_running 4
sglang:num_requests_waiting 1
sglang:batch_size_current 16
sglang:throughput_tokens_per_second 1250.5
"""


@pytest.mark.asyncio
async def test_collect_sglang_metrics(sample_sglang_metrics):
    """Test collecting metrics from SGLang instance."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = sample_sglang_metrics
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Collect metrics
        async with SGLangCollector() as collector:
            snapshot = await collector.collect(
                instance_id="sglang-001",
                endpoint="http://localhost:30000/metrics"
            )
        
        # Verify
        assert isinstance(snapshot, SGLangMetricsSnapshot)
        assert snapshot.instance_id == "sglang-001"
        assert snapshot.request_metrics.success_total == 300
        assert snapshot.request_metrics.failure_total == 2
        assert snapshot.cache_metrics.cache_hit_rate == 0.85
        assert snapshot.system_metrics.throughput_tokens_per_second == 1250.5


@pytest.mark.asyncio
async def test_collect_sglang_metrics_error():
    """Test error handling when SGLang collection fails."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Setup mock to raise error
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")
        mock_client_class.return_value = mock_client
        
        # Collect metrics
        async with SGLangCollector() as collector:
            with pytest.raises(httpx.HTTPError):
                await collector.collect(
                    instance_id="sglang-001",
                    endpoint="http://localhost:30000/metrics"
                )


@pytest.mark.asyncio
async def test_extract_request_metrics(sample_sglang_metrics):
    """Test extraction of request metrics."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = sample_sglang_metrics
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        async with SGLangCollector() as collector:
            snapshot = await collector.collect(
                instance_id="sglang-001",
                endpoint="http://localhost:30000/metrics"
            )
        
        # Verify request metrics
        assert snapshot.request_metrics.success_total == 300
        assert snapshot.request_metrics.time_to_first_token_seconds == 0.020
        assert snapshot.request_metrics.input_tokens == 256


@pytest.mark.asyncio
async def test_extract_cache_metrics(sample_sglang_metrics):
    """Test extraction of cache metrics."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = sample_sglang_metrics
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        async with SGLangCollector() as collector:
            snapshot = await collector.collect(
                instance_id="sglang-001",
                endpoint="http://localhost:30000/metrics"
            )
        
        # Verify cache metrics
        assert snapshot.cache_metrics.cache_hit_rate == 0.85
        assert snapshot.cache_metrics.radix_cache_size == 1024
        assert snapshot.cache_metrics.prefix_cache_hit_total == 255


@pytest.mark.asyncio
async def test_extract_system_metrics(sample_sglang_metrics):
    """Test extraction of system metrics."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = sample_sglang_metrics
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        async with SGLangCollector() as collector:
            snapshot = await collector.collect(
                instance_id="sglang-001",
                endpoint="http://localhost:30000/metrics"
            )
        
        # Verify system metrics
        assert snapshot.system_metrics.num_requests_running == 4
        assert snapshot.system_metrics.batch_size_current == 16
        assert snapshot.system_metrics.throughput_tokens_per_second == 1250.5

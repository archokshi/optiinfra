"""
vLLM Collector Tests

Tests for vLLM metrics collector.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from src.collectors.vllm_collector import VLLMCollector
from src.models.metrics import VLLMMetricsSnapshot


@pytest.fixture
def sample_vllm_metrics():
    """Sample vLLM metrics response."""
    return """
vllm:request_success_total 150
vllm:request_failure_total 5
vllm:time_to_first_token_seconds 0.025
vllm:time_per_output_token_seconds 0.010
vllm:e2e_request_latency_seconds 1.5
vllm:gpu_cache_usage_perc 75.5
vllm:gpu_memory_usage_bytes 8589934592
vllm:num_requests_running 3
vllm:num_requests_waiting 2
vllm:prompt_tokens_total 15000
vllm:generation_tokens_total 30000
"""


@pytest.mark.asyncio
async def test_collect_metrics(sample_vllm_metrics):
    """Test collecting metrics from vLLM instance."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = sample_vllm_metrics
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Collect metrics
        async with VLLMCollector() as collector:
            snapshot = await collector.collect(
                instance_id="vllm-001",
                endpoint="http://localhost:8000/metrics"
            )
        
        # Verify
        assert isinstance(snapshot, VLLMMetricsSnapshot)
        assert snapshot.instance_id == "vllm-001"
        assert snapshot.request_metrics.success_total == 150
        assert snapshot.request_metrics.failure_total == 5
        assert snapshot.gpu_metrics.cache_usage_perc == 75.5
        assert snapshot.throughput_metrics.prompt_tokens_total == 15000


@pytest.mark.asyncio
async def test_collect_metrics_error():
    """Test error handling when collection fails."""
    with patch('httpx.AsyncClient') as mock_client_class:
        # Setup mock to raise error
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")
        mock_client_class.return_value = mock_client
        
        # Collect metrics
        async with VLLMCollector() as collector:
            with pytest.raises(httpx.HTTPError):
                await collector.collect(
                    instance_id="vllm-001",
                    endpoint="http://localhost:8000/metrics"
                )

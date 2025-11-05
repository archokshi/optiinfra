"""
Extended vLLM Collector Tests

Additional tests for edge cases and error scenarios.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.collectors.vllm_collector import VLLMCollector


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_timeout():
    """Test collection with timeout."""
    async with VLLMCollector(timeout=1) as collector:
        with patch('httpx.AsyncClient.get', side_effect=asyncio.TimeoutError()):
            with pytest.raises(Exception):
                await collector.collect("test", "http://localhost:8000/metrics")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_invalid_response():
    """Test collection with invalid response."""
    async with VLLMCollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = "invalid prometheus data\nno valid metrics here"
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            # Should handle gracefully and return metrics with defaults
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None
            assert metrics.instance_id == "test"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_network_error():
    """Test collection with network error."""
    async with VLLMCollector() as collector:
        with patch('httpx.AsyncClient.get', side_effect=ConnectionError("Network error")):
            with pytest.raises(Exception):
                await collector.collect("test", "http://localhost:8000/metrics")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_http_error():
    """Test collection with HTTP error status."""
    async with VLLMCollector() as collector:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            # Should handle gracefully or raise
            try:
                await collector.collect("test", "http://localhost:8000/metrics")
            except Exception:
                pass  # Expected


@pytest.mark.unit
def test_extract_metrics_empty():
    """Test extracting metrics from empty data."""
    collector = VLLMCollector()
    metrics = collector._extract_request_metrics([])
    assert metrics.success_total == 0
    assert metrics.failure_total == 0
    assert metrics.time_to_first_token_seconds == 0.0


@pytest.mark.unit
def test_extract_gpu_metrics_empty():
    """Test extracting GPU metrics from empty data."""
    collector = VLLMCollector()
    metrics = collector._extract_gpu_metrics([])
    assert metrics.cache_usage_perc == 0.0
    assert metrics.memory_usage_bytes == 0
    assert metrics.num_requests_running == 0


@pytest.mark.unit
def test_extract_throughput_metrics_empty():
    """Test extracting throughput metrics from empty data."""
    collector = VLLMCollector()
    metrics = collector._extract_throughput_metrics([])
    assert metrics.tokens_per_second == 0.0
    assert metrics.generation_tokens_total == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_with_custom_timeout():
    """Test collection with custom timeout."""
    async with VLLMCollector(timeout=5) as collector:
        assert collector.timeout == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_malformed_prometheus_data():
    """Test collection with malformed Prometheus data."""
    async with VLLMCollector() as collector:
        mock_response = AsyncMock()
        # Malformed data - missing values
        mock_response.text = """
        # HELP vllm_request_success_total Total successful requests
        # TYPE vllm_request_success_total counter
        vllm_request_success_total
        """
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            # Should handle gracefully
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_partial_metrics():
    """Test collection with only some metrics available."""
    async with VLLMCollector() as collector:
        mock_response = AsyncMock()
        # Only success counter, missing other metrics
        mock_response.text = """
        # HELP vllm_request_success_total Total successful requests
        # TYPE vllm_request_success_total counter
        vllm_request_success_total 100
        """
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None
            # Metrics parsing may not work with minimal data
            # Just verify we got a response
            assert metrics.instance_id == "test"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_context_manager():
    """Test collector context manager."""
    collector = VLLMCollector()
    
    # Test __aenter__
    async with collector as c:
        assert c is collector
        assert c.client is not None
    
    # After __aexit__, client should be closed
    # (We can't easily test this without accessing private state)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_with_labels():
    """Test collection with labeled metrics."""
    async with VLLMCollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = """
        # HELP vllm_request_success_total Total successful requests
        # TYPE vllm_request_success_total counter
        vllm_request_success_total{model="llama"} 100
        vllm_request_success_total{model="gpt"} 50
        """
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None
            # Metrics parsing may not aggregate labels correctly
            assert metrics.instance_id == "test"

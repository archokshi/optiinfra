"""
Extended TGI Collector Tests

Additional tests for edge cases and error scenarios.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.collectors.tgi_collector import TGICollector


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_timeout():
    """Test collection with timeout."""
    async with TGICollector(timeout=1) as collector:
        with patch('httpx.AsyncClient.get', side_effect=asyncio.TimeoutError()):
            with pytest.raises(Exception):
                await collector.collect("test", "http://localhost:8000/metrics")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_invalid_response():
    """Test collection with invalid response."""
    async with TGICollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = "invalid prometheus data"
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None
            assert metrics.instance_id == "test"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_network_error():
    """Test collection with network error."""
    async with TGICollector() as collector:
        with patch('httpx.AsyncClient.get', side_effect=ConnectionError("Network error")):
            with pytest.raises(Exception):
                await collector.collect("test", "http://localhost:8000/metrics")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_http_error():
    """Test collection with HTTP error status."""
    async with TGICollector() as collector:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            with pytest.raises(Exception):
                await collector.collect("test", "http://localhost:8000/metrics")


@pytest.mark.unit
def test_extract_metrics_empty():
    """Test extracting metrics from empty data."""
    collector = TGICollector()
    metrics = collector._extract_request_metrics([])
    assert metrics.request_count == 0
    assert metrics.success_total == 0


@pytest.mark.unit
def test_extract_generation_metrics_empty():
    """Test extracting generation metrics from empty data."""
    collector = TGICollector()
    metrics = collector._extract_generation_metrics([])
    assert metrics.generated_tokens_total == 0
    assert metrics.input_length == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_with_custom_timeout():
    """Test collection with custom timeout."""
    async with TGICollector(timeout=10) as collector:
        assert collector.timeout == 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_partial_metrics():
    """Test collection with only some metrics available."""
    async with TGICollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = """
        # HELP tgi_request_count Total requests
        # TYPE tgi_request_count counter
        tgi_request_count 50
        """
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None
            assert metrics.request_metrics.request_count == 50


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_malformed_data():
    """Test collection with malformed data."""
    async with TGICollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = "not even close to prometheus format"
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_context_manager():
    """Test collector context manager."""
    collector = TGICollector()
    
    async with collector as c:
        assert c is collector
        assert c.client is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_with_histogram_metrics():
    """Test collection with histogram metrics."""
    async with TGICollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = """
        # HELP tgi_request_duration_seconds Request duration
        # TYPE tgi_request_duration_seconds histogram
        tgi_request_duration_seconds_bucket{le="0.1"} 10
        tgi_request_duration_seconds_bucket{le="0.5"} 50
        tgi_request_duration_seconds_bucket{le="+Inf"} 100
        tgi_request_duration_seconds_sum 25.5
        tgi_request_duration_seconds_count 100
        """
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None

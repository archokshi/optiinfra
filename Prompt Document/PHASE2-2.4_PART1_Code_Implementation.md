# PHASE2-2.4 PART1: SGLang Collector - Code Implementation Plan

**Phase**: PHASE2-2.4  
**Agent**: Performance Agent  
**Objective**: Implement Prometheus scraping and metrics collection for SGLang  
**Estimated Time**: 20+15m (35 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE2-2.3, 0.2c, 0.3

---

## Overview

This phase implements the SGLang metrics collector, which scrapes Prometheus metrics from SGLang inference servers. SGLang is a high-performance serving framework for LLMs with advanced features like RadixAttention and efficient memory management.

---

## SGLang Metrics Overview

### What is SGLang?
SGLang (Structured Generation Language) is a fast serving framework for LLMs and VLMs. It provides:
- RadixAttention for KV cache reuse
- Efficient memory management
- High throughput serving
- Prometheus metrics endpoint

### Key SGLang Metrics

#### Request Metrics
- `sglang:request_success_total` - Total successful requests
- `sglang:request_failure_total` - Total failed requests
- `sglang:request_duration_seconds` - Request duration
- `sglang:time_to_first_token_seconds` - TTFT
- `sglang:time_per_output_token_seconds` - TPOT
- `sglang:request_input_tokens` - Input tokens
- `sglang:request_output_tokens` - Output tokens

#### Cache Metrics
- `sglang:cache_hit_rate` - Cache hit rate
- `sglang:cache_memory_usage_bytes` - Cache memory usage
- `sglang:radix_cache_size` - RadixAttention cache size
- `sglang:prefix_cache_hit_total` - Prefix cache hits

#### System Metrics
- `sglang:num_requests_running` - Running requests
- `sglang:num_requests_waiting` - Waiting requests
- `sglang:batch_size_current` - Current batch size
- `sglang:throughput_tokens_per_second` - Token throughput

---

## Implementation Plan

### Step 1: SGLang Metrics Models (3 minutes)

#### 1.1 Update src/models/metrics.py

Add SGLang-specific models:

```python
"""
SGLang Metrics Models

Additional models for SGLang metrics.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SGLangRequestMetrics(BaseModel):
    """SGLang request-level metrics."""
    
    success_total: int = Field(default=0, description="Total successful requests")
    failure_total: int = Field(default=0, description="Total failed requests")
    request_duration_seconds: float = Field(default=0.0, description="Request duration")
    time_to_first_token_seconds: float = Field(default=0.0, description="TTFT")
    time_per_output_token_seconds: float = Field(default=0.0, description="TPOT")
    input_tokens: int = Field(default=0, description="Input tokens")
    output_tokens: int = Field(default=0, description="Output tokens")


class SGLangCacheMetrics(BaseModel):
    """SGLang cache metrics."""
    
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate")
    cache_memory_usage_bytes: int = Field(default=0, description="Cache memory usage")
    radix_cache_size: int = Field(default=0, description="RadixAttention cache size")
    prefix_cache_hit_total: int = Field(default=0, description="Prefix cache hits")


class SGLangSystemMetrics(BaseModel):
    """SGLang system metrics."""
    
    num_requests_running: int = Field(default=0, description="Running requests")
    num_requests_waiting: int = Field(default=0, description="Waiting requests")
    batch_size_current: int = Field(default=0, description="Current batch size")
    throughput_tokens_per_second: float = Field(default=0.0, description="Token throughput")


class SGLangMetricsSnapshot(BaseModel):
    """Complete snapshot of SGLang metrics."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="SGLang instance identifier")
    endpoint: str = Field(..., description="Metrics endpoint URL")
    request_metrics: SGLangRequestMetrics
    cache_metrics: SGLangCacheMetrics
    system_metrics: SGLangSystemMetrics
    raw_metrics: List[PrometheusMetric] = Field(
        default_factory=list,
        description="Raw Prometheus metrics"
    )
```

#### 1.2 Update MetricsCollectionResponse

```python
class MetricsCollectionResponse(BaseModel):
    """Response from metrics collection."""
    
    success: bool = Field(..., description="Collection success status")
    instance_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: Optional[Union[VLLMMetricsSnapshot, TGIMetricsSnapshot, "SGLangMetricsSnapshot"]] = None
    error: Optional[str] = None
```

---

### Step 2: SGLang Collector (5 minutes)

#### 2.1 Create src/collectors/sglang_collector.py

```python
"""
SGLang Metrics Collector

Collects and processes metrics from SGLang instances.
"""

import logging
from typing import Optional, List
import httpx
from datetime import datetime

from src.models.metrics import (
    SGLangMetricsSnapshot,
    SGLangRequestMetrics,
    SGLangCacheMetrics,
    SGLangSystemMetrics,
    PrometheusMetric
)
from src.collectors.prometheus_parser import PrometheusParser

logger = logging.getLogger(__name__)


class SGLangCollector:
    """Collector for SGLang Prometheus metrics."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize SGLang collector.
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self.parser = PrometheusParser()
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def collect(
        self,
        instance_id: str,
        endpoint: str
    ) -> SGLangMetricsSnapshot:
        """
        Collect metrics from SGLang instance.
        
        Args:
            instance_id: SGLang instance identifier
            endpoint: Prometheus metrics endpoint URL
            
        Returns:
            Metrics snapshot
            
        Raises:
            httpx.HTTPError: If request fails
        """
        if not self.client:
            raise RuntimeError("Collector not initialized. Use async context manager.")
        
        logger.info(f"Collecting metrics from SGLang {instance_id} at {endpoint}")
        
        # Fetch metrics
        response = await self.client.get(endpoint)
        response.raise_for_status()
        
        # Parse metrics
        raw_metrics = self.parser.parse(response.text)
        
        # Extract SGLang-specific metrics
        sglang_metrics = self.parser.filter_metrics(raw_metrics, prefix="sglang:")
        
        # Process metrics
        request_metrics = self._extract_request_metrics(sglang_metrics)
        cache_metrics = self._extract_cache_metrics(sglang_metrics)
        system_metrics = self._extract_system_metrics(sglang_metrics)
        
        return SGLangMetricsSnapshot(
            timestamp=datetime.utcnow(),
            instance_id=instance_id,
            endpoint=endpoint,
            request_metrics=request_metrics,
            cache_metrics=cache_metrics,
            system_metrics=system_metrics,
            raw_metrics=sglang_metrics
        )
    
    def _extract_request_metrics(
        self,
        metrics: List[PrometheusMetric]
    ) -> SGLangRequestMetrics:
        """Extract request-level metrics."""
        result = SGLangRequestMetrics()
        
        for metric in metrics:
            if metric.name == "sglang:request_success_total":
                result.success_total = int(metric.value)
            elif metric.name == "sglang:request_failure_total":
                result.failure_total = int(metric.value)
            elif metric.name == "sglang:request_duration_seconds":
                result.request_duration_seconds = metric.value
            elif metric.name == "sglang:time_to_first_token_seconds":
                result.time_to_first_token_seconds = metric.value
            elif metric.name == "sglang:time_per_output_token_seconds":
                result.time_per_output_token_seconds = metric.value
            elif metric.name == "sglang:request_input_tokens":
                result.input_tokens = int(metric.value)
            elif metric.name == "sglang:request_output_tokens":
                result.output_tokens = int(metric.value)
        
        return result
    
    def _extract_cache_metrics(
        self,
        metrics: List[PrometheusMetric]
    ) -> SGLangCacheMetrics:
        """Extract cache metrics."""
        result = SGLangCacheMetrics()
        
        for metric in metrics:
            if metric.name == "sglang:cache_hit_rate":
                result.cache_hit_rate = metric.value
            elif metric.name == "sglang:cache_memory_usage_bytes":
                result.cache_memory_usage_bytes = int(metric.value)
            elif metric.name == "sglang:radix_cache_size":
                result.radix_cache_size = int(metric.value)
            elif metric.name == "sglang:prefix_cache_hit_total":
                result.prefix_cache_hit_total = int(metric.value)
        
        return result
    
    def _extract_system_metrics(
        self,
        metrics: List[PrometheusMetric]
    ) -> SGLangSystemMetrics:
        """Extract system metrics."""
        result = SGLangSystemMetrics()
        
        for metric in metrics:
            if metric.name == "sglang:num_requests_running":
                result.num_requests_running = int(metric.value)
            elif metric.name == "sglang:num_requests_waiting":
                result.num_requests_waiting = int(metric.value)
            elif metric.name == "sglang:batch_size_current":
                result.batch_size_current = int(metric.value)
            elif metric.name == "sglang:throughput_tokens_per_second":
                result.throughput_tokens_per_second = metric.value
        
        return result
```

---

### Step 3: Update API Endpoints (3 minutes)

#### 3.1 Update src/api/metrics.py

Add SGLang endpoints:

```python
from src.collectors.sglang_collector import SGLangCollector
from src.models.metrics import SGLangMetricsSnapshot


@router.post(
    "/collect/sglang",
    response_model=MetricsCollectionResponse,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def collect_sglang_metrics(
    request: MetricsCollectionRequest
) -> MetricsCollectionResponse:
    """
    Collect metrics from a SGLang instance.
    
    Args:
        request: Collection request with instance details
        
    Returns:
        Collection response with metrics or error
    """
    try:
        async with SGLangCollector(timeout=request.timeout) as collector:
            metrics = await collector.collect(
                instance_id=request.instance_id,
                endpoint=request.endpoint
            )
        
        return MetricsCollectionResponse(
            success=True,
            instance_id=request.instance_id,
            metrics=metrics
        )
    
    except Exception as e:
        logger.error(
            f"Failed to collect SGLang metrics from {request.instance_id}: {e}",
            exc_info=True
        )
        
        return MetricsCollectionResponse(
            success=False,
            instance_id=request.instance_id,
            error=str(e)
        )


@router.get(
    "/metrics/sglang/{instance_id}",
    response_model=SGLangMetricsSnapshot,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def get_sglang_metrics(
    instance_id: str,
    endpoint: str
) -> SGLangMetricsSnapshot:
    """
    Get current metrics from a SGLang instance.
    
    Args:
        instance_id: SGLang instance identifier
        endpoint: Prometheus metrics endpoint URL
        
    Returns:
        Current metrics snapshot
        
    Raises:
        HTTPException: If collection fails
    """
    try:
        async with SGLangCollector() as collector:
            metrics = await collector.collect(
                instance_id=instance_id,
                endpoint=endpoint
            )
        
        return metrics
    
    except Exception as e:
        logger.error(
            f"Failed to get SGLang metrics from {instance_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect SGLang metrics: {str(e)}"
        )
```

---

### Step 4: Testing (9 minutes)

#### 4.1 Create tests/test_sglang_collector.py

```python
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
```

#### 4.2 Create tests/test_sglang_api.py

```python
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
```

---

## Success Criteria

### Functional Requirements
- ✅ SGLang collector fetches and parses metrics
- ✅ Request metrics extracted correctly
- ✅ Cache metrics extracted correctly
- ✅ System metrics extracted correctly
- ✅ API endpoints work correctly
- ✅ Error handling is robust

### Non-Functional Requirements
- ✅ Async/await for non-blocking I/O
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Tests pass with >80% coverage
- ✅ Proper error logging

---

## Dependencies

### From Previous Phases
- **PHASE2-2.3**: TGI collector (similar structure)
- **PHASE2-2.2**: vLLM collector
- **PHASE2-2.1**: FastAPI skeleton
- **0.2c**: Shared database models
- **0.3**: Shared utilities

### External Dependencies
- httpx (async HTTP client)
- Prometheus text format

---

## Next Phase

**PHASE2-2.5**: Metrics Storage - Store collected metrics in database

---

**Status**: Ready for implementation  
**Estimated Completion**: 35 minutes  
**Dependencies**: PHASE2-2.3, 0.2c, 0.3

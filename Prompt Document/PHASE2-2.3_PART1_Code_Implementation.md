# PHASE2-2.3 PART1: TGI Collector - Code Implementation Plan

**Phase**: PHASE2-2.3  
**Agent**: Performance Agent  
**Objective**: Implement Prometheus scraping and metrics collection for TGI (Text Generation Inference)  
**Estimated Time**: 20+15m (35 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE2-2.2, 0.2c, 0.3

---

## Overview

This phase implements the TGI (Text Generation Inference) metrics collector, which scrapes Prometheus metrics from Hugging Face's TGI inference servers. TGI is a high-performance text generation server optimized for LLM inference.

---

## TGI Metrics Overview

### What is TGI?
Text Generation Inference (TGI) is Hugging Face's production-ready inference server for LLMs. It provides:
- Fast inference with optimized kernels
- Dynamic batching
- Token streaming
- Multi-GPU support
- Prometheus metrics endpoint

### Key TGI Metrics

#### Request Metrics
- `tgi_request_duration_seconds` - Request duration histogram
- `tgi_request_success_total` - Total successful requests
- `tgi_request_failure_total` - Total failed requests
- `tgi_request_count` - Total request count
- `tgi_queue_size` - Current queue size
- `tgi_request_input_length` - Input token length
- `tgi_request_generated_tokens` - Generated tokens per request

#### Generation Metrics
- `tgi_request_mean_time_per_token_duration_seconds` - Mean time per token
- `tgi_request_generated_tokens_total` - Total generated tokens
- `tgi_batch_current_size` - Current batch size
- `tgi_batch_current_max_tokens` - Max tokens in current batch

#### System Metrics
- `tgi_request_max_new_tokens` - Max new tokens requested
- `tgi_request_validation_duration_seconds` - Validation time
- `tgi_request_queue_duration_seconds` - Time in queue
- `tgi_request_inference_duration_seconds` - Inference time

---

## Implementation Plan

### Step 1: TGI Metrics Models (3 minutes)

#### 1.1 Update src/models/metrics.py

Add TGI-specific models:

```python
"""
TGI Metrics Models

Additional models for TGI metrics.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TGIRequestMetrics(BaseModel):
    """TGI request-level metrics."""
    
    success_total: int = Field(default=0, description="Total successful requests")
    failure_total: int = Field(default=0, description="Total failed requests")
    request_count: int = Field(default=0, description="Total requests")
    queue_size: int = Field(default=0, description="Current queue size")
    mean_time_per_token_seconds: float = Field(default=0.0, description="Mean time per token")
    validation_duration_seconds: float = Field(default=0.0, description="Validation duration")
    queue_duration_seconds: float = Field(default=0.0, description="Queue duration")
    inference_duration_seconds: float = Field(default=0.0, description="Inference duration")


class TGIGenerationMetrics(BaseModel):
    """TGI generation metrics."""
    
    input_length: int = Field(default=0, description="Input token length")
    generated_tokens: int = Field(default=0, description="Generated tokens per request")
    generated_tokens_total: int = Field(default=0, description="Total generated tokens")
    max_new_tokens: int = Field(default=0, description="Max new tokens requested")
    batch_current_size: int = Field(default=0, description="Current batch size")
    batch_current_max_tokens: int = Field(default=0, description="Max tokens in batch")


class TGIMetricsSnapshot(BaseModel):
    """Complete snapshot of TGI metrics."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="TGI instance identifier")
    endpoint: str = Field(..., description="Metrics endpoint URL")
    request_metrics: TGIRequestMetrics
    generation_metrics: TGIGenerationMetrics
    raw_metrics: List[PrometheusMetric] = Field(
        default_factory=list,
        description="Raw Prometheus metrics"
    )
```

---

### Step 2: TGI Collector (5 minutes)

#### 2.1 Create src/collectors/tgi_collector.py

```python
"""
TGI Metrics Collector

Collects and processes metrics from TGI instances.
"""

import logging
from typing import Optional, List
import httpx
from datetime import datetime

from src.models.metrics import (
    TGIMetricsSnapshot,
    TGIRequestMetrics,
    TGIGenerationMetrics,
    PrometheusMetric
)
from src.collectors.prometheus_parser import PrometheusParser

logger = logging.getLogger(__name__)


class TGICollector:
    """Collector for TGI Prometheus metrics."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize TGI collector.
        
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
    ) -> TGIMetricsSnapshot:
        """
        Collect metrics from TGI instance.
        
        Args:
            instance_id: TGI instance identifier
            endpoint: Prometheus metrics endpoint URL
            
        Returns:
            Metrics snapshot
            
        Raises:
            httpx.HTTPError: If request fails
        """
        if not self.client:
            raise RuntimeError("Collector not initialized. Use async context manager.")
        
        logger.info(f"Collecting metrics from TGI {instance_id} at {endpoint}")
        
        # Fetch metrics
        response = await self.client.get(endpoint)
        response.raise_for_status()
        
        # Parse metrics
        raw_metrics = self.parser.parse(response.text)
        
        # Extract TGI-specific metrics
        tgi_metrics = self.parser.filter_metrics(raw_metrics, prefix="tgi_")
        
        # Process metrics
        request_metrics = self._extract_request_metrics(tgi_metrics)
        generation_metrics = self._extract_generation_metrics(tgi_metrics)
        
        return TGIMetricsSnapshot(
            timestamp=datetime.utcnow(),
            instance_id=instance_id,
            endpoint=endpoint,
            request_metrics=request_metrics,
            generation_metrics=generation_metrics,
            raw_metrics=tgi_metrics
        )
    
    def _extract_request_metrics(
        self,
        metrics: List[PrometheusMetric]
    ) -> TGIRequestMetrics:
        """Extract request-level metrics."""
        result = TGIRequestMetrics()
        
        for metric in metrics:
            if metric.name == "tgi_request_success_total":
                result.success_total = int(metric.value)
            elif metric.name == "tgi_request_failure_total":
                result.failure_total = int(metric.value)
            elif metric.name == "tgi_request_count":
                result.request_count = int(metric.value)
            elif metric.name == "tgi_queue_size":
                result.queue_size = int(metric.value)
            elif metric.name == "tgi_request_mean_time_per_token_duration_seconds":
                result.mean_time_per_token_seconds = metric.value
            elif metric.name == "tgi_request_validation_duration_seconds":
                result.validation_duration_seconds = metric.value
            elif metric.name == "tgi_request_queue_duration_seconds":
                result.queue_duration_seconds = metric.value
            elif metric.name == "tgi_request_inference_duration_seconds":
                result.inference_duration_seconds = metric.value
        
        return result
    
    def _extract_generation_metrics(
        self,
        metrics: List[PrometheusMetric]
    ) -> TGIGenerationMetrics:
        """Extract generation metrics."""
        result = TGIGenerationMetrics()
        
        for metric in metrics:
            if metric.name == "tgi_request_input_length":
                result.input_length = int(metric.value)
            elif metric.name == "tgi_request_generated_tokens":
                result.generated_tokens = int(metric.value)
            elif metric.name == "tgi_request_generated_tokens_total":
                result.generated_tokens_total = int(metric.value)
            elif metric.name == "tgi_request_max_new_tokens":
                result.max_new_tokens = int(metric.value)
            elif metric.name == "tgi_batch_current_size":
                result.batch_current_size = int(metric.value)
            elif metric.name == "tgi_batch_current_max_tokens":
                result.batch_current_max_tokens = int(metric.value)
        
        return result
```

---

### Step 3: Update API Endpoints (3 minutes)

#### 3.1 Update src/api/metrics.py

Add TGI endpoints:

```python
from src.collectors.tgi_collector import TGICollector
from src.models.metrics import TGIMetricsSnapshot


@router.post(
    "/collect/tgi",
    response_model=MetricsCollectionResponse,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def collect_tgi_metrics(
    request: MetricsCollectionRequest
) -> MetricsCollectionResponse:
    """
    Collect metrics from a TGI instance.
    
    Args:
        request: Collection request with instance details
        
    Returns:
        Collection response with metrics or error
    """
    try:
        async with TGICollector(timeout=request.timeout) as collector:
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
            f"Failed to collect TGI metrics from {request.instance_id}: {e}",
            exc_info=True
        )
        
        return MetricsCollectionResponse(
            success=False,
            instance_id=request.instance_id,
            error=str(e)
        )


@router.get(
    "/metrics/tgi/{instance_id}",
    response_model=TGIMetricsSnapshot,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def get_tgi_metrics(
    instance_id: str,
    endpoint: str
) -> TGIMetricsSnapshot:
    """
    Get current metrics from a TGI instance.
    
    Args:
        instance_id: TGI instance identifier
        endpoint: Prometheus metrics endpoint URL
        
    Returns:
        Current metrics snapshot
        
    Raises:
        HTTPException: If collection fails
    """
    try:
        async with TGICollector() as collector:
            metrics = await collector.collect(
                instance_id=instance_id,
                endpoint=endpoint
            )
        
        return metrics
    
    except Exception as e:
        logger.error(
            f"Failed to get TGI metrics from {instance_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect TGI metrics: {str(e)}"
        )
```

---

### Step 4: Testing (9 minutes)

#### 4.1 Create tests/test_tgi_collector.py

```python
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
```

#### 4.2 Create tests/test_tgi_api.py

```python
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
```

---

## Success Criteria

### Functional Requirements
- ✅ TGI collector fetches and parses metrics
- ✅ Request metrics extracted correctly
- ✅ Generation metrics extracted correctly
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
- **PHASE2-2.2**: vLLM collector (similar structure)
- **PHASE2-2.1**: FastAPI skeleton
- **0.2c**: Shared database models
- **0.3**: Shared utilities

### External Dependencies
- httpx (async HTTP client)
- Prometheus text format

---

## Next Phase

**PHASE2-2.4**: SGLang Collector - Implement metrics collection for SGLang

---

**Status**: Ready for implementation  
**Estimated Completion**: 35 minutes  
**Dependencies**: PHASE2-2.2, 0.2c, 0.3

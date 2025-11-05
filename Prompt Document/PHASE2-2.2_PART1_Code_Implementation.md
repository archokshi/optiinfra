# PHASE2-2.2 PART1: vLLM Collector - Code Implementation Plan

**Phase**: PHASE2-2.2  
**Agent**: Performance Agent  
**Objective**: Implement Prometheus scraping and metrics collection for vLLM  
**Estimated Time**: 25+20m (45 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE2-2.1, 0.2c, 0.3

---

## Overview

This phase implements the vLLM metrics collector, which scrapes Prometheus metrics from vLLM inference servers and stores them for analysis. vLLM exposes comprehensive metrics about model serving performance, GPU utilization, request latency, and throughput.

---

## vLLM Metrics Overview

### What is vLLM?
vLLM is a high-throughput and memory-efficient inference engine for Large Language Models (LLMs). It provides:
- Fast inference with PagedAttention
- Continuous batching
- Optimized CUDA kernels
- Prometheus metrics endpoint

### Key vLLM Metrics

#### Request Metrics
- `vllm:request_success_total` - Total successful requests
- `vllm:request_failure_total` - Total failed requests
- `vllm:time_to_first_token_seconds` - Time to first token (TTFT)
- `vllm:time_per_output_token_seconds` - Time per output token (TPOT)
- `vllm:e2e_request_latency_seconds` - End-to-end latency
- `vllm:request_prompt_tokens` - Prompt tokens per request
- `vllm:request_generation_tokens` - Generated tokens per request

#### GPU Metrics
- `vllm:gpu_cache_usage_perc` - KV cache usage percentage
- `vllm:gpu_memory_usage_bytes` - GPU memory usage
- `vllm:num_requests_running` - Currently running requests
- `vllm:num_requests_waiting` - Requests in queue

#### Throughput Metrics
- `vllm:prompt_tokens_total` - Total prompt tokens processed
- `vllm:generation_tokens_total` - Total tokens generated
- `vllm:num_preemptions_total` - Total preemptions

---

## Implementation Plan

### Step 1: Metrics Models (5 minutes)

#### 1.1 Create src/models/metrics.py

```python
"""
vLLM Metrics Models

Pydantic models for vLLM metrics.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class MetricType(str, Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class PrometheusMetric(BaseModel):
    """Single Prometheus metric."""
    
    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Metric type")
    value: float = Field(..., description="Metric value")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VLLMRequestMetrics(BaseModel):
    """vLLM request-level metrics."""
    
    success_total: int = Field(default=0, description="Total successful requests")
    failure_total: int = Field(default=0, description="Total failed requests")
    time_to_first_token_seconds: float = Field(default=0.0, description="TTFT in seconds")
    time_per_output_token_seconds: float = Field(default=0.0, description="TPOT in seconds")
    e2e_latency_seconds: float = Field(default=0.0, description="End-to-end latency")
    prompt_tokens: int = Field(default=0, description="Prompt tokens")
    generation_tokens: int = Field(default=0, description="Generated tokens")


class VLLMGPUMetrics(BaseModel):
    """vLLM GPU metrics."""
    
    cache_usage_perc: float = Field(default=0.0, description="KV cache usage %")
    memory_usage_bytes: int = Field(default=0, description="GPU memory in bytes")
    num_requests_running: int = Field(default=0, description="Running requests")
    num_requests_waiting: int = Field(default=0, description="Waiting requests")


class VLLMThroughputMetrics(BaseModel):
    """vLLM throughput metrics."""
    
    prompt_tokens_total: int = Field(default=0, description="Total prompt tokens")
    generation_tokens_total: int = Field(default=0, description="Total generated tokens")
    num_preemptions_total: int = Field(default=0, description="Total preemptions")
    requests_per_second: float = Field(default=0.0, description="Requests per second")
    tokens_per_second: float = Field(default=0.0, description="Tokens per second")


class VLLMMetricsSnapshot(BaseModel):
    """Complete snapshot of vLLM metrics."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="vLLM instance identifier")
    endpoint: str = Field(..., description="Metrics endpoint URL")
    request_metrics: VLLMRequestMetrics
    gpu_metrics: VLLMGPUMetrics
    throughput_metrics: VLLMThroughputMetrics
    raw_metrics: List[PrometheusMetric] = Field(
        default_factory=list,
        description="Raw Prometheus metrics"
    )


class MetricsCollectionRequest(BaseModel):
    """Request to collect metrics from vLLM instance."""
    
    instance_id: str = Field(..., description="vLLM instance identifier")
    endpoint: str = Field(..., description="Prometheus metrics endpoint URL")
    timeout: int = Field(default=10, description="Request timeout in seconds")


class MetricsCollectionResponse(BaseModel):
    """Response from metrics collection."""
    
    success: bool = Field(..., description="Collection success status")
    instance_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: Optional[VLLMMetricsSnapshot] = None
    error: Optional[str] = None
```

---

### Step 2: Prometheus Parser (7 minutes)

#### 2.1 Create src/collectors/__init__.py

```python
"""Metrics collectors for Performance Agent."""
```

#### 2.2 Create src/collectors/prometheus_parser.py

```python
"""
Prometheus Metrics Parser

Parses Prometheus text format metrics.
"""

import re
from typing import List, Dict, Tuple, Optional
import logging

from src.models.metrics import PrometheusMetric, MetricType

logger = logging.getLogger(__name__)


class PrometheusParser:
    """Parser for Prometheus text format metrics."""
    
    # Regex patterns
    METRIC_LINE_PATTERN = re.compile(
        r'^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)'
        r'(?:\{(?P<labels>[^}]+)\})?\s+'
        r'(?P<value>[^\s]+)'
        r'(?:\s+(?P<timestamp>\d+))?$'
    )
    
    TYPE_PATTERN = re.compile(r'^#\s+TYPE\s+(?P<name>\S+)\s+(?P<type>\S+)')
    HELP_PATTERN = re.compile(r'^#\s+HELP\s+(?P<name>\S+)\s+(?P<help>.+)')
    
    def __init__(self):
        self.metric_types: Dict[str, str] = {}
        self.metric_help: Dict[str, str] = {}
    
    def parse(self, text: str) -> List[PrometheusMetric]:
        """
        Parse Prometheus text format metrics.
        
        Args:
            text: Prometheus metrics in text format
            
        Returns:
            List of parsed metrics
        """
        metrics: List[PrometheusMetric] = []
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Parse TYPE comments
            type_match = self.TYPE_PATTERN.match(line)
            if type_match:
                self.metric_types[type_match.group('name')] = type_match.group('type')
                continue
            
            # Parse HELP comments
            help_match = self.HELP_PATTERN.match(line)
            if help_match:
                self.metric_help[help_match.group('name')] = help_match.group('help')
                continue
            
            # Skip other comments
            if line.startswith('#'):
                continue
            
            # Parse metric line
            metric = self._parse_metric_line(line)
            if metric:
                metrics.append(metric)
        
        return metrics
    
    def _parse_metric_line(self, line: str) -> Optional[PrometheusMetric]:
        """Parse a single metric line."""
        match = self.METRIC_LINE_PATTERN.match(line)
        if not match:
            logger.warning(f"Failed to parse metric line: {line}")
            return None
        
        name = match.group('name')
        value_str = match.group('value')
        labels_str = match.group('labels')
        
        # Parse value
        try:
            value = float(value_str)
        except ValueError:
            logger.warning(f"Invalid metric value: {value_str}")
            return None
        
        # Parse labels
        labels = self._parse_labels(labels_str) if labels_str else {}
        
        # Get metric type
        metric_type = self._get_metric_type(name)
        
        return PrometheusMetric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels
        )
    
    def _parse_labels(self, labels_str: str) -> Dict[str, str]:
        """Parse label string into dictionary."""
        labels = {}
        
        # Split by comma, but respect quoted values
        parts = re.findall(r'(\w+)="([^"]*)"', labels_str)
        
        for key, value in parts:
            labels[key] = value
        
        return labels
    
    def _get_metric_type(self, name: str) -> MetricType:
        """Get metric type from name."""
        # Check if we have explicit type
        if name in self.metric_types:
            type_str = self.metric_types[name]
            try:
                return MetricType(type_str.lower())
            except ValueError:
                pass
        
        # Infer from name
        if name.endswith('_total'):
            return MetricType.COUNTER
        elif name.endswith('_seconds') or name.endswith('_bytes'):
            return MetricType.HISTOGRAM
        else:
            return MetricType.GAUGE
    
    def filter_metrics(
        self,
        metrics: List[PrometheusMetric],
        prefix: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[PrometheusMetric]:
        """
        Filter metrics by prefix and labels.
        
        Args:
            metrics: List of metrics to filter
            prefix: Metric name prefix filter
            labels: Label filters
            
        Returns:
            Filtered metrics
        """
        filtered = metrics
        
        # Filter by prefix
        if prefix:
            filtered = [m for m in filtered if m.name.startswith(prefix)]
        
        # Filter by labels
        if labels:
            filtered = [
                m for m in filtered
                if all(m.labels.get(k) == v for k, v in labels.items())
            ]
        
        return filtered
```

---

### Step 3: vLLM Collector (8 minutes)

#### 3.1 Create src/collectors/vllm_collector.py

```python
"""
vLLM Metrics Collector

Collects and processes metrics from vLLM instances.
"""

import logging
from typing import Optional, List
import httpx
from datetime import datetime

from src.models.metrics import (
    VLLMMetricsSnapshot,
    VLLMRequestMetrics,
    VLLMGPUMetrics,
    VLLMThroughputMetrics,
    PrometheusMetric
)
from src.collectors.prometheus_parser import PrometheusParser

logger = logging.getLogger(__name__)


class VLLMCollector:
    """Collector for vLLM Prometheus metrics."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize vLLM collector.
        
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
    ) -> VLLMMetricsSnapshot:
        """
        Collect metrics from vLLM instance.
        
        Args:
            instance_id: vLLM instance identifier
            endpoint: Prometheus metrics endpoint URL
            
        Returns:
            Metrics snapshot
            
        Raises:
            httpx.HTTPError: If request fails
        """
        if not self.client:
            raise RuntimeError("Collector not initialized. Use async context manager.")
        
        logger.info(f"Collecting metrics from {instance_id} at {endpoint}")
        
        # Fetch metrics
        response = await self.client.get(endpoint)
        response.raise_for_status()
        
        # Parse metrics
        raw_metrics = self.parser.parse(response.text)
        
        # Extract vLLM-specific metrics
        vllm_metrics = self.parser.filter_metrics(raw_metrics, prefix="vllm:")
        
        # Process metrics
        request_metrics = self._extract_request_metrics(vllm_metrics)
        gpu_metrics = self._extract_gpu_metrics(vllm_metrics)
        throughput_metrics = self._extract_throughput_metrics(vllm_metrics)
        
        return VLLMMetricsSnapshot(
            timestamp=datetime.utcnow(),
            instance_id=instance_id,
            endpoint=endpoint,
            request_metrics=request_metrics,
            gpu_metrics=gpu_metrics,
            throughput_metrics=throughput_metrics,
            raw_metrics=vllm_metrics
        )
    
    def _extract_request_metrics(
        self,
        metrics: List[PrometheusMetric]
    ) -> VLLMRequestMetrics:
        """Extract request-level metrics."""
        result = VLLMRequestMetrics()
        
        for metric in metrics:
            if metric.name == "vllm:request_success_total":
                result.success_total = int(metric.value)
            elif metric.name == "vllm:request_failure_total":
                result.failure_total = int(metric.value)
            elif metric.name == "vllm:time_to_first_token_seconds":
                result.time_to_first_token_seconds = metric.value
            elif metric.name == "vllm:time_per_output_token_seconds":
                result.time_per_output_token_seconds = metric.value
            elif metric.name == "vllm:e2e_request_latency_seconds":
                result.e2e_latency_seconds = metric.value
            elif metric.name == "vllm:request_prompt_tokens":
                result.prompt_tokens = int(metric.value)
            elif metric.name == "vllm:request_generation_tokens":
                result.generation_tokens = int(metric.value)
        
        return result
    
    def _extract_gpu_metrics(
        self,
        metrics: List[PrometheusMetric]
    ) -> VLLMGPUMetrics:
        """Extract GPU metrics."""
        result = VLLMGPUMetrics()
        
        for metric in metrics:
            if metric.name == "vllm:gpu_cache_usage_perc":
                result.cache_usage_perc = metric.value
            elif metric.name == "vllm:gpu_memory_usage_bytes":
                result.memory_usage_bytes = int(metric.value)
            elif metric.name == "vllm:num_requests_running":
                result.num_requests_running = int(metric.value)
            elif metric.name == "vllm:num_requests_waiting":
                result.num_requests_waiting = int(metric.value)
        
        return result
    
    def _extract_throughput_metrics(
        self,
        metrics: List[PrometheusMetric]
    ) -> VLLMThroughputMetrics:
        """Extract throughput metrics."""
        result = VLLMThroughputMetrics()
        
        for metric in metrics:
            if metric.name == "vllm:prompt_tokens_total":
                result.prompt_tokens_total = int(metric.value)
            elif metric.name == "vllm:generation_tokens_total":
                result.generation_tokens_total = int(metric.value)
            elif metric.name == "vllm:num_preemptions_total":
                result.num_preemptions_total = int(metric.value)
        
        # Calculate derived metrics
        # Note: These would need time-series data for accurate calculation
        # For now, we'll set them to 0 and calculate in the analysis phase
        result.requests_per_second = 0.0
        result.tokens_per_second = 0.0
        
        return result
```

---

### Step 4: API Endpoints (5 minutes)

#### 4.1 Create src/api/metrics.py

```python
"""
Metrics Collection Endpoints

API endpoints for collecting metrics from vLLM instances.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List
import logging

from src.models.metrics import (
    MetricsCollectionRequest,
    MetricsCollectionResponse,
    VLLMMetricsSnapshot
)
from src.collectors.vllm_collector import VLLMCollector

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/collect/vllm",
    response_model=MetricsCollectionResponse,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def collect_vllm_metrics(
    request: MetricsCollectionRequest
) -> MetricsCollectionResponse:
    """
    Collect metrics from a vLLM instance.
    
    Args:
        request: Collection request with instance details
        
    Returns:
        Collection response with metrics or error
    """
    try:
        async with VLLMCollector(timeout=request.timeout) as collector:
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
            f"Failed to collect metrics from {request.instance_id}: {e}",
            exc_info=True
        )
        
        return MetricsCollectionResponse(
            success=False,
            instance_id=request.instance_id,
            error=str(e)
        )


@router.get(
    "/metrics/vllm/{instance_id}",
    response_model=VLLMMetricsSnapshot,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def get_vllm_metrics(
    instance_id: str,
    endpoint: str
) -> VLLMMetricsSnapshot:
    """
    Get current metrics from a vLLM instance.
    
    Args:
        instance_id: vLLM instance identifier
        endpoint: Prometheus metrics endpoint URL
        
    Returns:
        Current metrics snapshot
        
    Raises:
        HTTPException: If collection fails
    """
    try:
        async with VLLMCollector() as collector:
            metrics = await collector.collect(
                instance_id=instance_id,
                endpoint=endpoint
            )
        
        return metrics
    
    except Exception as e:
        logger.error(
            f"Failed to get metrics from {instance_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}"
        )
```

---

### Step 5: Update Main Application (2 minutes)

#### 5.1 Update src/main.py

Add the metrics router:

```python
# Add import
from src.api import health, metrics

# Add router
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
```

---

### Step 6: Testing (8 minutes)

#### 6.1 Create tests/test_prometheus_parser.py

```python
"""
Prometheus Parser Tests

Tests for Prometheus metrics parser.
"""

import pytest
from src.collectors.prometheus_parser import PrometheusParser
from src.models.metrics import MetricType


@pytest.fixture
def parser():
    """Parser fixture."""
    return PrometheusParser()


@pytest.fixture
def sample_metrics():
    """Sample Prometheus metrics."""
    return """
# HELP vllm:request_success_total Total successful requests
# TYPE vllm:request_success_total counter
vllm:request_success_total{model="llama-2-7b"} 150

# HELP vllm:time_to_first_token_seconds Time to first token
# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds{model="llama-2-7b",quantile="0.5"} 0.025
vllm:time_to_first_token_seconds{model="llama-2-7b",quantile="0.95"} 0.050

# HELP vllm:gpu_cache_usage_perc GPU cache usage percentage
# TYPE vllm:gpu_cache_usage_perc gauge
vllm:gpu_cache_usage_perc 75.5
"""


@pytest.mark.unit
def test_parse_metrics(parser, sample_metrics):
    """Test parsing Prometheus metrics."""
    metrics = parser.parse(sample_metrics)
    
    assert len(metrics) == 4
    assert all(m.name.startswith("vllm:") for m in metrics)


@pytest.mark.unit
def test_parse_counter(parser):
    """Test parsing counter metric."""
    text = 'vllm:request_success_total{model="test"} 100'
    metrics = parser.parse(text)
    
    assert len(metrics) == 1
    metric = metrics[0]
    assert metric.name == "vllm:request_success_total"
    assert metric.value == 100
    assert metric.labels == {"model": "test"}


@pytest.mark.unit
def test_parse_gauge(parser):
    """Test parsing gauge metric."""
    text = 'vllm:gpu_cache_usage_perc 75.5'
    metrics = parser.parse(text)
    
    assert len(metrics) == 1
    metric = metrics[0]
    assert metric.name == "vllm:gpu_cache_usage_perc"
    assert metric.value == 75.5
    assert metric.labels == {}


@pytest.mark.unit
def test_filter_by_prefix(parser, sample_metrics):
    """Test filtering metrics by prefix."""
    metrics = parser.parse(sample_metrics)
    filtered = parser.filter_metrics(metrics, prefix="vllm:time")
    
    assert len(filtered) == 2
    assert all(m.name.startswith("vllm:time") for m in filtered)


@pytest.mark.unit
def test_filter_by_labels(parser, sample_metrics):
    """Test filtering metrics by labels."""
    metrics = parser.parse(sample_metrics)
    filtered = parser.filter_metrics(
        metrics,
        labels={"model": "llama-2-7b"}
    )
    
    assert len(filtered) == 3
    assert all(m.labels.get("model") == "llama-2-7b" for m in filtered)
```

#### 6.2 Create tests/test_vllm_collector.py

```python
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
```

#### 6.3 Create tests/test_metrics_api.py

```python
"""
Metrics API Tests

Tests for metrics collection endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
def test_collect_vllm_metrics_success(client: TestClient):
    """Test successful vLLM metrics collection."""
    with patch('src.api.metrics.VLLMCollector') as mock_collector_class:
        # Setup mock
        mock_collector = AsyncMock()
        mock_snapshot = AsyncMock()
        mock_snapshot.instance_id = "vllm-001"
        mock_collector.collect.return_value = mock_snapshot
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/collect/vllm",
            json={
                "instance_id": "vllm-001",
                "endpoint": "http://localhost:8000/metrics",
                "timeout": 10
            }
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["instance_id"] == "vllm-001"


@pytest.mark.unit
def test_collect_vllm_metrics_failure(client: TestClient):
    """Test failed vLLM metrics collection."""
    with patch('src.api.metrics.VLLMCollector') as mock_collector_class:
        # Setup mock to raise error
        mock_collector = AsyncMock()
        mock_collector.collect.side_effect = Exception("Connection failed")
        mock_collector_class.return_value.__aenter__.return_value = mock_collector
        
        # Make request
        response = client.post(
            "/api/v1/collect/vllm",
            json={
                "instance_id": "vllm-001",
                "endpoint": "http://localhost:8000/metrics",
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
- ✅ Prometheus metrics parser works correctly
- ✅ vLLM collector fetches and parses metrics
- ✅ API endpoints accept collection requests
- ✅ Metrics are properly structured
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
- **PHASE2-2.1**: FastAPI skeleton, configuration, logging
- **0.2c**: Shared database models (for storing metrics)
- **0.3**: Shared utilities

### External Dependencies
- httpx (async HTTP client)
- Prometheus text format

---

## Next Phase

**PHASE2-2.3**: TGI Collector - Implement metrics collection for Text Generation Inference

---

**Status**: Ready for implementation  
**Estimated Completion**: 45 minutes  
**Dependencies**: PHASE2-2.1, 0.2c, 0.3

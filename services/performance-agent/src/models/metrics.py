"""
vLLM Metrics Models

Pydantic models for vLLM metrics.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
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


from typing import Union


class MetricsCollectionResponse(BaseModel):
    """Response from metrics collection."""
    
    success: bool = Field(..., description="Collection success status")
    instance_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: Optional[Union[VLLMMetricsSnapshot, "TGIMetricsSnapshot", "SGLangMetricsSnapshot"]] = None
    error: Optional[str] = None


# TGI Metrics Models

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


# SGLang Metrics Models

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


class MetricsCollectionRequest(BaseModel):
    """Request to collect metrics from an instance."""
    
    instance_id: str = Field(..., description="Instance identifier")
    endpoint: str = Field(..., description="Metrics endpoint URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class MetricsCollectionResponse(BaseModel):
    """Response from metrics collection."""
    
    success: bool = Field(..., description="Whether collection was successful")
    instance_id: str = Field(..., description="Instance identifier")
    metrics: Optional[Union[VLLMMetricsSnapshot, TGIMetricsSnapshot, SGLangMetricsSnapshot]] = None
    error: Optional[str] = Field(None, description="Error message if failed")

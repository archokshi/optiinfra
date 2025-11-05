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

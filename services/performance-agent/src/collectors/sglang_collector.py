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

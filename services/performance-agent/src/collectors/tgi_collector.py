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

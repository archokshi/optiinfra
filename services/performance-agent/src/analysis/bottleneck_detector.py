"""
Bottleneck Detector

Detects performance bottlenecks from metrics.
"""

import logging
from typing import List, Optional
from datetime import datetime

from src.models.analysis import Bottleneck, BottleneckType, Severity
from src.models.metrics import (
    VLLMMetricsSnapshot,
    TGIMetricsSnapshot,
    SGLangMetricsSnapshot
)

logger = logging.getLogger(__name__)


class BottleneckDetector:
    """Detects performance bottlenecks."""
    
    # Default thresholds
    DEFAULT_THRESHOLDS = {
        "ttft_seconds": 0.1,  # 100ms
        "tpot_seconds": 0.05,  # 50ms
        "queue_size": 10,
        "cache_hit_rate": 0.7,  # 70%
        "memory_usage_percent": 0.85,  # 85%
        "throughput_tokens_per_second": 100,
    }
    
    def __init__(self, thresholds: Optional[dict] = None):
        """
        Initialize detector.
        
        Args:
            thresholds: Custom threshold values
        """
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
    
    def detect_vllm_bottlenecks(
        self,
        metrics: VLLMMetricsSnapshot
    ) -> List[Bottleneck]:
        """Detect bottlenecks in vLLM metrics."""
        bottlenecks = []
        
        # Check TTFT
        if metrics.request_metrics.time_to_first_token_seconds > self.thresholds["ttft_seconds"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=self._calculate_severity(
                    metrics.request_metrics.time_to_first_token_seconds,
                    self.thresholds["ttft_seconds"],
                    higher_is_worse=True
                ),
                description="Time to First Token exceeds threshold",
                metric_name="time_to_first_token_seconds",
                current_value=metrics.request_metrics.time_to_first_token_seconds,
                threshold_value=self.thresholds["ttft_seconds"],
                recommendation="Consider reducing batch size or enabling prefix caching"
            ))
        
        # Check TPOT
        if metrics.request_metrics.time_per_output_token_seconds > self.thresholds["tpot_seconds"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=self._calculate_severity(
                    metrics.request_metrics.time_per_output_token_seconds,
                    self.thresholds["tpot_seconds"],
                    higher_is_worse=True
                ),
                description="Time per Output Token exceeds threshold",
                metric_name="time_per_output_token_seconds",
                current_value=metrics.request_metrics.time_per_output_token_seconds,
                threshold_value=self.thresholds["tpot_seconds"],
                recommendation="Check GPU utilization and consider quantization"
            ))
        
        # Check queue size
        if metrics.gpu_metrics.num_requests_waiting > self.thresholds["queue_size"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.QUEUE_BUILDUP,
                severity=self._calculate_severity(
                    metrics.gpu_metrics.num_requests_waiting,
                    self.thresholds["queue_size"],
                    higher_is_worse=True
                ),
                description="Request queue is building up",
                metric_name="num_requests_waiting",
                current_value=float(metrics.gpu_metrics.num_requests_waiting),
                threshold_value=float(self.thresholds["queue_size"]),
                recommendation="Scale horizontally or increase batch size"
            ))
        
        # Check cache usage
        if metrics.gpu_metrics.cache_usage_perc > self.thresholds["memory_usage_percent"] * 100:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.MEMORY_PRESSURE,
                severity=Severity.HIGH,
                description="GPU cache usage is high",
                metric_name="cache_usage_perc",
                current_value=metrics.gpu_metrics.cache_usage_perc,
                threshold_value=self.thresholds["memory_usage_percent"] * 100,
                recommendation="Reduce max sequence length or enable KV cache eviction"
            ))
        
        return bottlenecks
    
    def detect_tgi_bottlenecks(
        self,
        metrics: TGIMetricsSnapshot
    ) -> List[Bottleneck]:
        """Detect bottlenecks in TGI metrics."""
        bottlenecks = []
        
        # Check mean time per token
        if metrics.request_metrics.mean_time_per_token_seconds > self.thresholds["tpot_seconds"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=self._calculate_severity(
                    metrics.request_metrics.mean_time_per_token_seconds,
                    self.thresholds["tpot_seconds"],
                    higher_is_worse=True
                ),
                description="Mean time per token exceeds threshold",
                metric_name="mean_time_per_token_seconds",
                current_value=metrics.request_metrics.mean_time_per_token_seconds,
                threshold_value=self.thresholds["tpot_seconds"],
                recommendation="Enable tensor parallelism or use Flash Attention"
            ))
        
        # Check queue size
        if metrics.request_metrics.queue_size > self.thresholds["queue_size"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.QUEUE_BUILDUP,
                severity=self._calculate_severity(
                    metrics.request_metrics.queue_size,
                    self.thresholds["queue_size"],
                    higher_is_worse=True
                ),
                description="Request queue is building up",
                metric_name="queue_size",
                current_value=float(metrics.request_metrics.queue_size),
                threshold_value=float(self.thresholds["queue_size"]),
                recommendation="Increase max batch size or scale horizontally"
            ))
        
        # Check batch size efficiency
        if metrics.generation_metrics.batch_current_size < 4:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.BATCH_SIZE_SUBOPTIMAL,
                severity=Severity.MEDIUM,
                description="Batch size is suboptimal",
                metric_name="batch_current_size",
                current_value=float(metrics.generation_metrics.batch_current_size),
                threshold_value=4.0,
                recommendation="Increase max batch size for better GPU utilization"
            ))
        
        return bottlenecks
    
    def detect_sglang_bottlenecks(
        self,
        metrics: SGLangMetricsSnapshot
    ) -> List[Bottleneck]:
        """Detect bottlenecks in SGLang metrics."""
        bottlenecks = []
        
        # Check TTFT
        if metrics.request_metrics.time_to_first_token_seconds > self.thresholds["ttft_seconds"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=self._calculate_severity(
                    metrics.request_metrics.time_to_first_token_seconds,
                    self.thresholds["ttft_seconds"],
                    higher_is_worse=True
                ),
                description="Time to First Token exceeds threshold",
                metric_name="time_to_first_token_seconds",
                current_value=metrics.request_metrics.time_to_first_token_seconds,
                threshold_value=self.thresholds["ttft_seconds"],
                recommendation="Optimize RadixAttention cache configuration"
            ))
        
        # Check cache hit rate
        if metrics.cache_metrics.cache_hit_rate < self.thresholds["cache_hit_rate"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.CACHE_INEFFICIENCY,
                severity=self._calculate_severity(
                    metrics.cache_metrics.cache_hit_rate,
                    self.thresholds["cache_hit_rate"],
                    higher_is_worse=False
                ),
                description="Cache hit rate is below threshold",
                metric_name="cache_hit_rate",
                current_value=metrics.cache_metrics.cache_hit_rate,
                threshold_value=self.thresholds["cache_hit_rate"],
                recommendation="Increase RadixAttention cache size or review prompt patterns"
            ))
        
        # Check throughput
        if metrics.system_metrics.throughput_tokens_per_second < self.thresholds["throughput_tokens_per_second"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.LOW_THROUGHPUT,
                severity=self._calculate_severity(
                    metrics.system_metrics.throughput_tokens_per_second,
                    self.thresholds["throughput_tokens_per_second"],
                    higher_is_worse=False
                ),
                description="Token throughput is below threshold",
                metric_name="throughput_tokens_per_second",
                current_value=metrics.system_metrics.throughput_tokens_per_second,
                threshold_value=self.thresholds["throughput_tokens_per_second"],
                recommendation="Increase batch size or enable continuous batching"
            ))
        
        # Check queue
        if metrics.system_metrics.num_requests_waiting > self.thresholds["queue_size"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.QUEUE_BUILDUP,
                severity=self._calculate_severity(
                    metrics.system_metrics.num_requests_waiting,
                    self.thresholds["queue_size"],
                    higher_is_worse=True
                ),
                description="Request queue is building up",
                metric_name="num_requests_waiting",
                current_value=float(metrics.system_metrics.num_requests_waiting),
                threshold_value=float(self.thresholds["queue_size"]),
                recommendation="Scale horizontally or optimize batch scheduling"
            ))
        
        return bottlenecks
    
    def _calculate_severity(
        self,
        current: float,
        threshold: float,
        higher_is_worse: bool = True
    ) -> Severity:
        """Calculate severity based on deviation from threshold."""
        if higher_is_worse:
            ratio = current / threshold if threshold > 0 else float('inf')
            if ratio >= 2.0:
                return Severity.CRITICAL
            elif ratio >= 1.5:
                return Severity.HIGH
            elif ratio >= 1.2:
                return Severity.MEDIUM
            else:
                return Severity.LOW
        else:
            ratio = threshold / current if current > 0 else float('inf')
            if ratio >= 2.0:
                return Severity.CRITICAL
            elif ratio >= 1.5:
                return Severity.HIGH
            elif ratio >= 1.2:
                return Severity.MEDIUM
            else:
                return Severity.LOW

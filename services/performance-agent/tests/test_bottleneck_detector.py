"""
Bottleneck Detector Tests

Tests for bottleneck detection.
"""

import pytest
from src.analysis.bottleneck_detector import BottleneckDetector
from src.models.analysis import BottleneckType, Severity
from src.models.metrics import (
    VLLMMetricsSnapshot,
    VLLMRequestMetrics,
    VLLMGPUMetrics,
    VLLMThroughputMetrics,
    TGIMetricsSnapshot,
    TGIRequestMetrics,
    TGIGenerationMetrics,
    SGLangMetricsSnapshot,
    SGLangRequestMetrics,
    SGLangCacheMetrics,
    SGLangSystemMetrics
)


@pytest.fixture
def detector():
    """Bottleneck detector fixture."""
    return BottleneckDetector()


@pytest.mark.unit
def test_detect_vllm_high_ttft(detector):
    """Test detection of high TTFT in vLLM."""
    metrics = VLLMMetricsSnapshot(
        instance_id="test",
        endpoint="http://test",
        request_metrics=VLLMRequestMetrics(time_to_first_token_seconds=0.15),
        gpu_metrics=VLLMGPUMetrics(),
        throughput_metrics=VLLMThroughputMetrics()
    )
    
    bottlenecks = detector.detect_vllm_bottlenecks(metrics)
    
    assert len(bottlenecks) > 0
    assert any(b.type == BottleneckType.HIGH_LATENCY for b in bottlenecks)
    assert any(b.metric_name == "time_to_first_token_seconds" for b in bottlenecks)


@pytest.mark.unit
def test_detect_vllm_queue_buildup(detector):
    """Test detection of queue buildup in vLLM."""
    metrics = VLLMMetricsSnapshot(
        instance_id="test",
        endpoint="http://test",
        request_metrics=VLLMRequestMetrics(),
        gpu_metrics=VLLMGPUMetrics(num_requests_waiting=15),
        throughput_metrics=VLLMThroughputMetrics()
    )
    
    bottlenecks = detector.detect_vllm_bottlenecks(metrics)
    
    assert len(bottlenecks) > 0
    assert any(b.type == BottleneckType.QUEUE_BUILDUP for b in bottlenecks)


@pytest.mark.unit
def test_detect_tgi_high_latency(detector):
    """Test detection of high latency in TGI."""
    metrics = TGIMetricsSnapshot(
        instance_id="test",
        endpoint="http://test",
        request_metrics=TGIRequestMetrics(mean_time_per_token_seconds=0.08),
        generation_metrics=TGIGenerationMetrics()
    )
    
    bottlenecks = detector.detect_tgi_bottlenecks(metrics)
    
    assert len(bottlenecks) > 0
    assert any(b.type == BottleneckType.HIGH_LATENCY for b in bottlenecks)


@pytest.mark.unit
def test_detect_sglang_cache_inefficiency(detector):
    """Test detection of cache inefficiency in SGLang."""
    metrics = SGLangMetricsSnapshot(
        instance_id="test",
        endpoint="http://test",
        request_metrics=SGLangRequestMetrics(),
        cache_metrics=SGLangCacheMetrics(cache_hit_rate=0.5),
        system_metrics=SGLangSystemMetrics()
    )
    
    bottlenecks = detector.detect_sglang_bottlenecks(metrics)
    
    assert len(bottlenecks) > 0
    assert any(b.type == BottleneckType.CACHE_INEFFICIENCY for b in bottlenecks)


@pytest.mark.unit
def test_severity_calculation(detector):
    """Test severity calculation."""
    # Critical severity (2x threshold)
    severity = detector._calculate_severity(0.2, 0.1, higher_is_worse=True)
    assert severity == Severity.CRITICAL
    
    # High severity (1.6x threshold - need >= 1.5)
    severity = detector._calculate_severity(0.16, 0.1, higher_is_worse=True)
    assert severity == Severity.HIGH
    
    # Medium severity (1.3x threshold - need >= 1.2)
    severity = detector._calculate_severity(0.13, 0.1, higher_is_worse=True)
    assert severity == Severity.MEDIUM

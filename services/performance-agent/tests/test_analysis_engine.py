"""
Analysis Engine Tests

Tests for analysis engine.
"""

import pytest
from src.analysis.engine import AnalysisEngine
from src.models.analysis import SLOTarget
from src.models.metrics import (
    VLLMMetricsSnapshot,
    VLLMRequestMetrics,
    VLLMGPUMetrics,
    VLLMThroughputMetrics
)


@pytest.fixture
def engine():
    """Analysis engine fixture."""
    return AnalysisEngine()


@pytest.fixture
def sample_metrics():
    """Sample metrics with bottlenecks."""
    return VLLMMetricsSnapshot(
        instance_id="test",
        endpoint="http://test",
        request_metrics=VLLMRequestMetrics(
            time_to_first_token_seconds=0.15,  # High
            time_per_output_token_seconds=0.03
        ),
        gpu_metrics=VLLMGPUMetrics(
            num_requests_waiting=12,  # High
            cache_usage_perc=75.0
        ),
        throughput_metrics=VLLMThroughputMetrics()
    )


@pytest.mark.unit
def test_analyze_with_bottlenecks(engine, sample_metrics):
    """Test analysis with bottlenecks."""
    result = engine.analyze(sample_metrics, "vllm")
    
    assert result.instance_id == "test"
    assert result.instance_type == "vllm"
    assert len(result.bottlenecks) > 0
    assert result.overall_health_score < 100.0
    assert len(result.recommendations) > 0


@pytest.mark.unit
def test_analyze_with_slos(engine, sample_metrics):
    """Test analysis with SLO targets."""
    slo_targets = [
        SLOTarget(
            name="TTFT",
            metric="request_metrics.time_to_first_token_seconds",
            target_value=0.1,
            comparison="<"
        )
    ]
    
    result = engine.analyze(sample_metrics, "vllm", slo_targets)
    
    assert len(result.slo_statuses) == 1
    assert result.slo_statuses[0].is_compliant is False


@pytest.mark.unit
def test_health_score_calculation(engine):
    """Test health score calculation."""
    # Perfect metrics
    perfect_metrics = VLLMMetricsSnapshot(
        instance_id="test",
        endpoint="http://test",
        request_metrics=VLLMRequestMetrics(
            time_to_first_token_seconds=0.05,
            time_per_output_token_seconds=0.02
        ),
        gpu_metrics=VLLMGPUMetrics(
            num_requests_waiting=2,
            cache_usage_perc=50.0
        ),
        throughput_metrics=VLLMThroughputMetrics()
    )
    
    result = engine.analyze(perfect_metrics, "vllm")
    
    assert result.overall_health_score == 100.0
    assert len(result.bottlenecks) == 0

"""
SLO Monitor Tests

Tests for SLO monitoring.
"""

import pytest
from src.analysis.slo_monitor import SLOMonitor
from src.models.analysis import SLOTarget
from src.models.metrics import (
    VLLMMetricsSnapshot,
    VLLMRequestMetrics,
    VLLMGPUMetrics,
    VLLMThroughputMetrics
)


@pytest.fixture
def monitor():
    """SLO monitor fixture."""
    return SLOMonitor()


@pytest.fixture
def sample_metrics():
    """Sample metrics fixture."""
    return VLLMMetricsSnapshot(
        instance_id="test",
        endpoint="http://test",
        request_metrics=VLLMRequestMetrics(
            time_to_first_token_seconds=0.08,
            time_per_output_token_seconds=0.03
        ),
        gpu_metrics=VLLMGPUMetrics(cache_usage_perc=75.0),
        throughput_metrics=VLLMThroughputMetrics()
    )


@pytest.mark.unit
def test_slo_compliant(monitor, sample_metrics):
    """Test SLO compliance check - compliant."""
    targets = [
        SLOTarget(
            name="TTFT",
            metric="request_metrics.time_to_first_token_seconds",
            target_value=0.1,
            comparison="<"
        )
    ]
    
    statuses = monitor.check_slos(sample_metrics, targets)
    
    assert len(statuses) == 1
    assert statuses[0].is_compliant is True
    assert statuses[0].current_value == 0.08


@pytest.mark.unit
def test_slo_violation(monitor, sample_metrics):
    """Test SLO compliance check - violation."""
    targets = [
        SLOTarget(
            name="TTFT",
            metric="request_metrics.time_to_first_token_seconds",
            target_value=0.05,
            comparison="<"
        )
    ]
    
    statuses = monitor.check_slos(sample_metrics, targets)
    
    assert len(statuses) == 1
    assert statuses[0].is_compliant is False
    assert statuses[0].deviation_percent > 0


@pytest.mark.unit
def test_multiple_slos(monitor, sample_metrics):
    """Test multiple SLO targets."""
    targets = [
        SLOTarget(
            name="TTFT",
            metric="request_metrics.time_to_first_token_seconds",
            target_value=0.1,
            comparison="<"
        ),
        SLOTarget(
            name="Cache Usage",
            metric="gpu_metrics.cache_usage_perc",
            target_value=80.0,
            comparison="<"
        )
    ]
    
    statuses = monitor.check_slos(sample_metrics, targets)
    
    assert len(statuses) == 2
    assert all(s.is_compliant for s in statuses)

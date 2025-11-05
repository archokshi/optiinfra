"""
Quantization Optimizer Tests

Tests for quantization optimization.
"""

import pytest
from src.optimization.quantization_optimizer import QuantizationOptimizer
from src.models.analysis import Bottleneck, BottleneckType, Severity
from src.models.optimization import QuantizationMethod


@pytest.fixture
def optimizer():
    """Quantization optimizer fixture."""
    return QuantizationOptimizer()


@pytest.mark.unit
def test_quantization_for_memory_pressure(optimizer):
    """Test quantization recommendation for memory pressure."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.MEMORY_PRESSURE,
            severity=Severity.CRITICAL,
            description="Critical memory usage",
            metric_name="memory_usage",
            current_value=95.0,
            threshold_value=85.0,
            recommendation="Reduce memory usage"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"quantization": "none"}
    )
    
    assert len(optimizations) > 0
    assert config is not None
    assert config.method == QuantizationMethod.INT4
    assert config.target_bits == 4


@pytest.mark.unit
def test_quantization_for_latency(optimizer):
    """Test quantization recommendation for latency issues."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.HIGH_LATENCY,
            severity=Severity.HIGH,
            description="High latency",
            metric_name="ttft",
            current_value=0.2,
            threshold_value=0.1,
            recommendation="Reduce latency"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"quantization": "none"}
    )
    
    assert len(optimizations) > 0
    assert config is not None
    assert config.method == QuantizationMethod.INT8
    assert config.target_bits == 8


@pytest.mark.unit
def test_no_quantization_if_already_enabled(optimizer):
    """Test no recommendation if quantization already enabled."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.HIGH_LATENCY,
            severity=Severity.HIGH,
            description="High latency",
            metric_name="ttft",
            current_value=0.2,
            threshold_value=0.1,
            recommendation="Reduce latency"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"quantization": "int8"}
    )
    
    assert len(optimizations) == 0
    assert config is None

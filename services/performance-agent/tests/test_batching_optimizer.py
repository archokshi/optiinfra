"""
Batching Optimizer Tests

Tests for batching optimization.
"""

import pytest
from src.optimization.batching_optimizer import BatchingOptimizer
from src.models.analysis import Bottleneck, BottleneckType, Severity


@pytest.fixture
def optimizer():
    """Batching optimizer fixture."""
    return BatchingOptimizer()


@pytest.mark.unit
def test_batching_for_queue_buildup(optimizer):
    """Test batching optimization for queue buildup."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.QUEUE_BUILDUP,
            severity=Severity.HIGH,
            description="Queue building up",
            metric_name="queue_size",
            current_value=15.0,
            threshold_value=10.0,
            recommendation="Increase batch size"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"max_batch_size": 32}
    )
    
    assert len(optimizations) > 0
    assert config is not None
    assert config.max_batch_size == 64  # 32 * 2


@pytest.mark.unit
def test_batching_for_low_throughput(optimizer):
    """Test batching optimization for low throughput."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.LOW_THROUGHPUT,
            severity=Severity.MEDIUM,
            description="Low throughput",
            metric_name="throughput",
            current_value=50.0,
            threshold_value=100.0,
            recommendation="Increase batch size"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"max_batch_size": 32}
    )
    
    assert len(optimizations) > 0
    assert config is not None
    assert config.max_batch_size == 64


@pytest.mark.unit
def test_batching_for_suboptimal_batch_size(optimizer):
    """Test batching optimization for suboptimal batch size."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.BATCH_SIZE_SUBOPTIMAL,
            severity=Severity.MEDIUM,
            description="Batch size too small",
            metric_name="batch_size",
            current_value=2.0,
            threshold_value=4.0,
            recommendation="Increase batch size"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "tgi",
        {"max_batch_size": 16}
    )
    
    assert len(optimizations) > 0
    assert config is not None
    assert config.max_batch_size == 32  # 16 + 16


@pytest.mark.unit
def test_batch_size_cap(optimizer):
    """Test batch size doesn't exceed maximum."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.QUEUE_BUILDUP,
            severity=Severity.HIGH,
            description="Queue building up",
            metric_name="queue_size",
            current_value=15.0,
            threshold_value=10.0,
            recommendation="Increase batch size"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"max_batch_size": 200}
    )
    
    assert len(optimizations) > 0
    assert config is not None
    assert config.max_batch_size <= 256  # Cap at 256

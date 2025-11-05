"""
KV Cache Optimizer Tests

Tests for KV cache optimization.
"""

import pytest
from src.optimization.kv_cache_optimizer import KVCacheOptimizer
from src.models.analysis import Bottleneck, BottleneckType, Severity


@pytest.fixture
def optimizer():
    """KV cache optimizer fixture."""
    return KVCacheOptimizer()


@pytest.mark.unit
def test_memory_pressure_optimization(optimizer):
    """Test optimization for memory pressure."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.MEMORY_PRESSURE,
            severity=Severity.HIGH,
            description="High memory usage",
            metric_name="cache_usage_perc",
            current_value=90.0,
            threshold_value=85.0,
            recommendation="Reduce cache size"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"max_model_len": 4096}
    )
    
    assert len(optimizations) > 0
    assert any(opt.type.value == "kv_cache" for opt in optimizations)
    assert any("max_model_len" in change.parameter for opt in optimizations for change in opt.config_changes)


@pytest.mark.unit
def test_cache_inefficiency_optimization_sglang(optimizer):
    """Test cache efficiency optimization for SGLang."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.CACHE_INEFFICIENCY,
            severity=Severity.MEDIUM,
            description="Low cache hit rate",
            metric_name="cache_hit_rate",
            current_value=0.5,
            threshold_value=0.7,
            recommendation="Increase cache size"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "sglang",
        {"radix_cache_size_gb": 4}
    )
    
    assert len(optimizations) > 0
    assert config is not None
    assert config.enable_prefix_caching is True
    assert config.cache_size_gb == 8.0


@pytest.mark.unit
def test_cache_inefficiency_optimization_vllm(optimizer):
    """Test cache efficiency optimization for vLLM."""
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.CACHE_INEFFICIENCY,
            severity=Severity.MEDIUM,
            description="Low cache hit rate",
            metric_name="cache_hit_rate",
            current_value=0.5,
            threshold_value=0.7,
            recommendation="Enable prefix caching"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"enable_prefix_caching": False}
    )
    
    assert len(optimizations) > 0
    assert config is not None
    assert config.enable_prefix_caching is True


@pytest.mark.unit
def test_no_optimizations_needed(optimizer):
    """Test when no optimizations are needed."""
    bottlenecks = []
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {}
    )
    
    assert len(optimizations) == 0
    assert config is None

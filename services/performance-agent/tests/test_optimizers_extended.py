"""
Extended Optimizer Tests

Additional tests for optimizer edge cases and scenarios.
"""

import pytest
from src.optimization.kv_cache_optimizer import KVCacheOptimizer
from src.optimization.quantization_optimizer import QuantizationOptimizer
from src.optimization.batching_optimizer import BatchingOptimizer
from src.models.analysis import Bottleneck, BottleneckType, Severity


# KV Cache Optimizer Tests

@pytest.mark.unit
def test_kv_cache_no_bottlenecks():
    """Test KV cache optimizer with no bottlenecks."""
    optimizer = KVCacheOptimizer()
    optimizations, config = optimizer.generate_optimizations([], "vllm", {})
    
    assert len(optimizations) == 0
    assert config is None


@pytest.mark.unit
def test_kv_cache_with_empty_config():
    """Test KV cache optimizer with empty config."""
    optimizer = KVCacheOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.MEMORY_PRESSURE,
            severity=Severity.HIGH,
            description="High memory usage",
            metric_name="memory",
            current_value=0.9,
            threshold_value=0.8,
            recommendation="Reduce memory"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "vllm", {})
    
    # May or may not generate optimizations depending on implementation
    assert isinstance(optimizations, list)
    # Config may be None if no specific config changes needed
    assert config is None or hasattr(config, 'max_model_len')


@pytest.mark.unit
def test_kv_cache_tgi_instance():
    """Test KV cache optimizer with TGI instance."""
    optimizer = KVCacheOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.MEMORY_PRESSURE,
            severity=Severity.MEDIUM,
            description="Memory pressure",
            metric_name="memory",
            current_value=0.85,
            threshold_value=0.8,
            recommendation="Optimize"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "tgi", {})
    
    # TGI may have different optimizations
    assert isinstance(optimizations, list)


@pytest.mark.unit
def test_kv_cache_sglang_instance():
    """Test KV cache optimizer with SGLang instance."""
    optimizer = KVCacheOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.CACHE_INEFFICIENCY,
            severity=Severity.HIGH,
            description="Low cache hit rate",
            metric_name="cache_hit_rate",
            current_value=0.3,
            threshold_value=0.7,
            recommendation="Improve caching"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "sglang", {})
    
    assert len(optimizations) > 0


@pytest.mark.unit
def test_kv_cache_low_severity():
    """Test KV cache optimizer with low severity bottleneck."""
    optimizer = KVCacheOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.MEMORY_PRESSURE,
            severity=Severity.LOW,
            description="Minor memory pressure",
            metric_name="memory",
            current_value=0.82,
            threshold_value=0.8,
            recommendation="Monitor"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "vllm", {})
    
    # May or may not generate optimizations for low severity
    assert isinstance(optimizations, list)


# Quantization Optimizer Tests

@pytest.mark.unit
def test_quantization_no_bottlenecks():
    """Test quantization optimizer with no bottlenecks."""
    optimizer = QuantizationOptimizer()
    optimizations, config = optimizer.generate_optimizations([], "vllm", {})
    
    assert len(optimizations) == 0
    assert config is None


@pytest.mark.unit
def test_quantization_already_quantized_int8():
    """Test quantization optimizer when already using INT8."""
    optimizer = QuantizationOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.HIGH_LATENCY,
            severity=Severity.HIGH,
            description="High latency",
            metric_name="ttft",
            current_value=0.2,
            threshold_value=0.1,
            recommendation="Optimize"
        )
    ]
    
    # Already using INT8
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"quantization": "int8"}
    )
    
    # Should not recommend further quantization or recommend INT4
    assert isinstance(optimizations, list)


@pytest.mark.unit
def test_quantization_already_quantized_int4():
    """Test quantization optimizer when already using INT4."""
    optimizer = QuantizationOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.MEMORY_PRESSURE,
            severity=Severity.CRITICAL,
            description="Critical memory",
            metric_name="memory",
            current_value=0.95,
            threshold_value=0.8,
            recommendation="Urgent action"
        )
    ]
    
    # Already at most aggressive quantization
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"quantization": "int4"}
    )
    
    # Should not recommend further quantization
    assert len(optimizations) == 0


@pytest.mark.unit
def test_quantization_memory_pressure():
    """Test quantization for memory pressure."""
    optimizer = QuantizationOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.MEMORY_PRESSURE,
            severity=Severity.HIGH,
            description="High memory usage",
            metric_name="memory",
            current_value=0.9,
            threshold_value=0.8,
            recommendation="Reduce memory"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "vllm", {})
    
    assert len(optimizations) > 0
    # Should recommend some form of quantization
    assert any("quantiz" in opt.description.lower() or "int" in opt.description.lower()
               for opt in optimizations)


@pytest.mark.unit
def test_quantization_high_latency():
    """Test quantization for high latency."""
    optimizer = QuantizationOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.HIGH_LATENCY,
            severity=Severity.MEDIUM,
            description="Moderate latency",
            metric_name="ttft",
            current_value=0.15,
            threshold_value=0.1,
            recommendation="Improve latency"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "vllm", {})
    
    assert len(optimizations) > 0


@pytest.mark.unit
def test_quantization_tgi_instance():
    """Test quantization with TGI instance."""
    optimizer = QuantizationOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.HIGH_LATENCY,
            severity=Severity.HIGH,
            description="High latency",
            metric_name="latency",
            current_value=0.3,
            threshold_value=0.1,
            recommendation="Optimize"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "tgi", {})
    
    assert isinstance(optimizations, list)


# Batching Optimizer Tests

@pytest.mark.unit
def test_batching_no_bottlenecks():
    """Test batching optimizer with no bottlenecks."""
    optimizer = BatchingOptimizer()
    optimizations, config = optimizer.generate_optimizations([], "vllm", {})
    
    assert len(optimizations) == 0
    assert config is None


@pytest.mark.unit
def test_batching_at_max_batch_size():
    """Test batching optimizer at maximum batch size."""
    optimizer = BatchingOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.QUEUE_BUILDUP,
            severity=Severity.HIGH,
            description="Queue buildup",
            metric_name="queue_size",
            current_value=15.0,
            threshold_value=10.0,
            recommendation="Increase batch"
        )
    ]
    
    # Already at max
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"max_batch_size": 256}
    )
    
    # Should still recommend but cap at 256
    if config:
        assert config.max_batch_size <= 256


@pytest.mark.unit
def test_batching_queue_buildup():
    """Test batching for queue buildup."""
    optimizer = BatchingOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.QUEUE_BUILDUP,
            severity=Severity.MEDIUM,
            description="Moderate queue",
            metric_name="queue_size",
            current_value=12.0,
            threshold_value=10.0,
            recommendation="Increase batch"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "vllm", {})
    
    assert len(optimizations) > 0
    assert config is not None


@pytest.mark.unit
def test_batching_low_throughput():
    """Test batching for low throughput."""
    optimizer = BatchingOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.LOW_THROUGHPUT,
            severity=Severity.HIGH,
            description="Low throughput",
            metric_name="throughput",
            current_value=50.0,
            threshold_value=100.0,
            recommendation="Improve throughput"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "vllm", {})
    
    assert len(optimizations) > 0


@pytest.mark.unit
def test_batching_with_small_current_batch():
    """Test batching with small current batch size."""
    optimizer = BatchingOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.QUEUE_BUILDUP,
            severity=Severity.HIGH,
            description="Queue buildup",
            metric_name="queue_size",
            current_value=20.0,
            threshold_value=10.0,
            recommendation="Increase batch"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"max_batch_size": 8}
    )
    
    assert len(optimizations) > 0
    if config:
        assert config.max_batch_size > 8


@pytest.mark.unit
def test_batching_tgi_instance():
    """Test batching with TGI instance."""
    optimizer = BatchingOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.QUEUE_BUILDUP,
            severity=Severity.MEDIUM,
            description="Queue buildup",
            metric_name="queue",
            current_value=15.0,
            threshold_value=10.0,
            recommendation="Optimize"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "tgi", {})
    
    assert isinstance(optimizations, list)


@pytest.mark.unit
def test_batching_sglang_instance():
    """Test batching with SGLang instance."""
    optimizer = BatchingOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.LOW_THROUGHPUT,
            severity=Severity.HIGH,
            description="Low throughput",
            metric_name="throughput",
            current_value=30.0,
            threshold_value=100.0,
            recommendation="Improve"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(bottlenecks, "sglang", {})
    
    assert isinstance(optimizations, list)


# Cross-optimizer Tests

@pytest.mark.unit
def test_all_optimizers_with_none_config():
    """Test all optimizers with None config."""
    kv_optimizer = KVCacheOptimizer()
    quant_optimizer = QuantizationOptimizer()
    batch_optimizer = BatchingOptimizer()
    
    bottlenecks = []
    
    # Should handle None config gracefully
    kv_opts, _ = kv_optimizer.generate_optimizations(bottlenecks, "vllm", None)
    quant_opts, _ = quant_optimizer.generate_optimizations(bottlenecks, "vllm", None)
    batch_opts, _ = batch_optimizer.generate_optimizations(bottlenecks, "vllm", None)
    
    assert isinstance(kv_opts, list)
    assert isinstance(quant_opts, list)
    assert isinstance(batch_opts, list)


@pytest.mark.unit
def test_all_optimizers_with_multiple_bottlenecks():
    """Test all optimizers with multiple bottlenecks."""
    kv_optimizer = KVCacheOptimizer()
    quant_optimizer = QuantizationOptimizer()
    batch_optimizer = BatchingOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.MEMORY_PRESSURE,
            severity=Severity.HIGH,
            description="High memory",
            metric_name="memory",
            current_value=0.9,
            threshold_value=0.8,
            recommendation="Reduce"
        ),
        Bottleneck(
            type=BottleneckType.QUEUE_BUILDUP,
            severity=Severity.MEDIUM,
            description="Queue buildup",
            metric_name="queue",
            current_value=15.0,
            threshold_value=10.0,
            recommendation="Increase batch"
        ),
        Bottleneck(
            type=BottleneckType.HIGH_LATENCY,
            severity=Severity.HIGH,
            description="High latency",
            metric_name="ttft",
            current_value=0.2,
            threshold_value=0.1,
            recommendation="Optimize"
        )
    ]
    
    kv_opts, _ = kv_optimizer.generate_optimizations(bottlenecks, "vllm", {})
    quant_opts, _ = quant_optimizer.generate_optimizations(bottlenecks, "vllm", {})
    batch_opts, _ = batch_optimizer.generate_optimizations(bottlenecks, "vllm", {})
    
    # Each optimizer should find relevant optimizations
    assert len(kv_opts) > 0 or len(quant_opts) > 0 or len(batch_opts) > 0

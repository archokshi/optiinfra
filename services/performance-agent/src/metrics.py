"""
Performance Agent Specific Metrics

Metrics for tracking performance optimization.
"""

from prometheus_client import Counter, Gauge, Histogram, REGISTRY
from shared.utils.prometheus_metrics import BaseMetrics


class PerformanceAgentMetrics(BaseMetrics):
    """Metrics specific to the Performance Agent"""
    
    def __init__(self):
        super().__init__('performance-agent', REGISTRY)
        
        # Latency metrics
        self.latency_improvement_ratio = Gauge(
            'latency_improvement_ratio',
            'Ratio of latency improvement (before/after)',
            ['optimization_type'],
            registry=self.registry
        )
        
        self.latency_before_ms = Histogram(
            'latency_before_ms',
            'Latency before optimization (milliseconds)',
            ['model'],
            buckets=(10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
            registry=self.registry
        )
        
        self.latency_after_ms = Histogram(
            'latency_after_ms',
            'Latency after optimization (milliseconds)',
            ['model'],
            buckets=(10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
            registry=self.registry
        )
        
        # Throughput metrics
        self.throughput_qps = Gauge(
            'throughput_qps',
            'Current throughput in queries per second',
            ['model'],
            registry=self.registry
        )
        
        self.throughput_tokens_per_second = Gauge(
            'throughput_tokens_per_second',
            'Throughput in tokens per second',
            ['model'],
            registry=self.registry
        )
        
        # KV cache metrics
        self.kv_cache_hit_rate = Gauge(
            'kv_cache_hit_rate',
            'KV cache hit rate (0-1)',
            ['model'],
            registry=self.registry
        )
        
        self.kv_cache_size_bytes = Gauge(
            'kv_cache_size_bytes',
            'KV cache size in bytes',
            ['model'],
            registry=self.registry
        )
        
        self.kv_cache_evictions_total = Counter(
            'kv_cache_evictions_total',
            'Total KV cache evictions',
            ['model'],
            registry=self.registry
        )
        
        # Quantization metrics
        self.quantization_speedup = Gauge(
            'quantization_speedup',
            'Speedup from quantization (ratio)',
            ['model', 'quantization_level'],  # FP16, FP8, INT8
            registry=self.registry
        )
        
        self.quantization_accuracy_impact = Gauge(
            'quantization_accuracy_impact',
            'Accuracy impact from quantization (0-1)',
            ['model', 'quantization_level'],
            registry=self.registry
        )
        
        # Batch processing metrics
        self.batch_size = Gauge(
            'batch_size',
            'Current batch size',
            ['model'],
            registry=self.registry
        )
        
        self.batch_processing_time_seconds = Histogram(
            'batch_processing_time_seconds',
            'Batch processing time in seconds',
            ['model'],
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
            registry=self.registry
        )
        
        # Model loading metrics
        self.model_load_time_seconds = Histogram(
            'model_load_time_seconds',
            'Model loading time in seconds',
            ['model', 'engine'],  # vLLM, TGI, SGLang
            buckets=(1, 5, 10, 30, 60, 120, 300),
            registry=self.registry
        )
        
        self.model_memory_usage_bytes = Gauge(
            'model_memory_usage_bytes',
            'Model memory usage in bytes',
            ['model'],
            registry=self.registry
        )
        
        # Optimization results
        self.performance_optimizations_total = Counter(
            'performance_optimizations_total',
            'Total performance optimizations applied',
            ['optimization_type', 'outcome'],
            registry=self.registry
        )
    
    def record_latency_improvement(self, opt_type: str, before_ms: float, after_ms: float, model: str):
        """Record latency improvement from optimization"""
        self.latency_before_ms.labels(model=model).observe(before_ms)
        self.latency_after_ms.labels(model=model).observe(after_ms)
        
        if before_ms > 0:
            improvement_ratio = before_ms / after_ms
            self.latency_improvement_ratio.labels(
                optimization_type=opt_type
            ).set(improvement_ratio)
    
    def update_throughput(self, model: str, qps: float, tokens_per_sec: float):
        """Update throughput metrics"""
        self.throughput_qps.labels(model=model).set(qps)
        self.throughput_tokens_per_second.labels(model=model).set(tokens_per_sec)
    
    def update_kv_cache(self, model: str, hit_rate: float, size_bytes: int):
        """Update KV cache metrics"""
        self.kv_cache_hit_rate.labels(model=model).set(hit_rate)
        self.kv_cache_size_bytes.labels(model=model).set(size_bytes)
    
    def record_kv_cache_eviction(self, model: str):
        """Record a KV cache eviction"""
        self.kv_cache_evictions_total.labels(model=model).inc()
    
    def record_quantization(self, model: str, level: str, speedup: float, accuracy_impact: float):
        """Record quantization metrics"""
        self.quantization_speedup.labels(
            model=model,
            quantization_level=level
        ).set(speedup)
        
        self.quantization_accuracy_impact.labels(
            model=model,
            quantization_level=level
        ).set(accuracy_impact)
    
    def update_batch_metrics(self, model: str, batch_size: int, processing_time: float):
        """Update batch processing metrics"""
        self.batch_size.labels(model=model).set(batch_size)
        self.batch_processing_time_seconds.labels(model=model).observe(processing_time)
    
    def record_model_load(self, model: str, engine: str, load_time: float, memory_bytes: int):
        """Record model loading metrics"""
        self.model_load_time_seconds.labels(
            model=model,
            engine=engine
        ).observe(load_time)
        
        self.model_memory_usage_bytes.labels(model=model).set(memory_bytes)
    
    def record_optimization(self, opt_type: str, outcome: str):
        """Record a performance optimization"""
        self.performance_optimizations_total.labels(
            optimization_type=opt_type,
            outcome=outcome
        ).inc()

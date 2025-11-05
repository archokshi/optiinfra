"""
KV Cache Optimizer

Optimizes KV cache configuration.
"""

import logging
from typing import List, Optional

from src.models.optimization import (
    Optimization,
    OptimizationType,
    ImpactLevel,
    ConfigChange,
    KVCacheOptimization
)
from src.models.analysis import Bottleneck, BottleneckType

logger = logging.getLogger(__name__)


class KVCacheOptimizer:
    """Optimizes KV cache settings."""
    
    def generate_optimizations(
        self,
        bottlenecks: List[Bottleneck],
        instance_type: str,
        current_config: Optional[dict] = None
    ) -> tuple[List[Optimization], Optional[KVCacheOptimization]]:
        """
        Generate KV cache optimizations.
        
        Args:
            bottlenecks: Detected bottlenecks
            instance_type: Type of instance
            current_config: Current configuration
            
        Returns:
            Tuple of (optimizations list, KV cache config)
        """
        optimizations = []
        kv_config = None
        
        # Check for memory pressure
        memory_bottlenecks = [
            b for b in bottlenecks 
            if b.type == BottleneckType.MEMORY_PRESSURE
        ]
        
        if memory_bottlenecks:
            opt = self._optimize_memory_pressure(
                memory_bottlenecks[0],
                instance_type,
                current_config
            )
            if opt:
                optimizations.append(opt)
        
        # Check for cache inefficiency
        cache_bottlenecks = [
            b for b in bottlenecks 
            if b.type == BottleneckType.CACHE_INEFFICIENCY
        ]
        
        if cache_bottlenecks:
            opt, config = self._optimize_cache_efficiency(
                cache_bottlenecks[0],
                instance_type,
                current_config
            )
            if opt:
                optimizations.append(opt)
                kv_config = config
        
        return optimizations, kv_config
    
    def _optimize_memory_pressure(
        self,
        bottleneck: Bottleneck,
        instance_type: str,
        current_config: Optional[dict]
    ) -> Optional[Optimization]:
        """Optimize for memory pressure."""
        config_changes = []
        
        # Reduce max sequence length
        config_changes.append(ConfigChange(
            parameter="max_model_len",
            current_value=current_config.get("max_model_len", 4096) if current_config else 4096,
            recommended_value=2048,
            reason="Reduce memory footprint by limiting sequence length"
        ))
        
        # Enable KV cache eviction
        config_changes.append(ConfigChange(
            parameter="enable_chunked_prefill",
            current_value=current_config.get("enable_chunked_prefill", False) if current_config else False,
            recommended_value=True,
            reason="Enable chunked prefill to reduce memory spikes"
        ))
        
        return Optimization(
            type=OptimizationType.KV_CACHE,
            title="Reduce KV Cache Memory Pressure",
            description="Optimize KV cache settings to reduce memory usage",
            config_changes=config_changes,
            expected_impact=ImpactLevel.HIGH,
            estimated_improvement="30-40% memory reduction",
            implementation_effort="Low - config change only",
            risks=[
                "May reduce maximum supported sequence length",
                "Could impact throughput for long sequences"
            ],
            prerequisites=[]
        )
    
    def _optimize_cache_efficiency(
        self,
        bottleneck: Bottleneck,
        instance_type: str,
        current_config: Optional[dict]
    ) -> tuple[Optional[Optimization], Optional[KVCacheOptimization]]:
        """Optimize cache efficiency."""
        config_changes = []
        
        if instance_type == "sglang":
            # Enable RadixAttention optimizations
            config_changes.append(ConfigChange(
                parameter="enable_radix_cache",
                current_value=current_config.get("enable_radix_cache", True) if current_config else True,
                recommended_value=True,
                reason="Ensure RadixAttention cache is enabled"
            ))
            
            config_changes.append(ConfigChange(
                parameter="radix_cache_size_gb",
                current_value=current_config.get("radix_cache_size_gb", 4) if current_config else 4,
                recommended_value=8,
                reason="Increase cache size to improve hit rate"
            ))
            
            kv_config = KVCacheOptimization(
                enable_prefix_caching=True,
                cache_size_gb=8.0,
                eviction_policy="lru",
                block_size=16
            )
        else:
            # vLLM or TGI prefix caching
            config_changes.append(ConfigChange(
                parameter="enable_prefix_caching",
                current_value=current_config.get("enable_prefix_caching", False) if current_config else False,
                recommended_value=True,
                reason="Enable prefix caching to improve cache hit rate"
            ))
            
            kv_config = KVCacheOptimization(
                enable_prefix_caching=True,
                cache_size_gb=None,
                eviction_policy="lru"
            )
        
        optimization = Optimization(
            type=OptimizationType.KV_CACHE,
            title="Improve KV Cache Hit Rate",
            description="Enable and optimize prefix caching for better cache efficiency",
            config_changes=config_changes,
            expected_impact=ImpactLevel.HIGH,
            estimated_improvement="40-60% TTFT reduction for repeated prefixes",
            implementation_effort="Low - config change only",
            risks=["Increased memory usage for cache"],
            prerequisites=[]
        )
        
        return optimization, kv_config

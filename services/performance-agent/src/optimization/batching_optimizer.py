"""
Batching Optimizer

Optimizes batching configuration.
"""

import logging
from typing import List, Optional

from src.models.optimization import (
    Optimization,
    OptimizationType,
    ImpactLevel,
    ConfigChange,
    BatchingOptimization
)
from src.models.analysis import Bottleneck, BottleneckType

logger = logging.getLogger(__name__)


class BatchingOptimizer:
    """Optimizes batching settings."""
    
    def generate_optimizations(
        self,
        bottlenecks: List[Bottleneck],
        instance_type: str,
        current_config: Optional[dict] = None
    ) -> tuple[List[Optimization], Optional[BatchingOptimization]]:
        """
        Generate batching optimizations.
        
        Args:
            bottlenecks: Detected bottlenecks
            instance_type: Type of instance
            current_config: Current configuration
            
        Returns:
            Tuple of (optimizations list, batching config)
        """
        optimizations = []
        batch_config = None
        
        # Check for suboptimal batch size
        batch_bottlenecks = [
            b for b in bottlenecks 
            if b.type == BottleneckType.BATCH_SIZE_SUBOPTIMAL
        ]
        
        # Check for queue buildup
        queue_bottlenecks = [
            b for b in bottlenecks 
            if b.type == BottleneckType.QUEUE_BUILDUP
        ]
        
        # Check for low throughput
        throughput_bottlenecks = [
            b for b in bottlenecks 
            if b.type == BottleneckType.LOW_THROUGHPUT
        ]
        
        if batch_bottlenecks or queue_bottlenecks or throughput_bottlenecks:
            opt, config = self._optimize_batching(
                bottlenecks,
                instance_type,
                current_config
            )
            if opt:
                optimizations.append(opt)
                batch_config = config
        
        return optimizations, batch_config
    
    def _optimize_batching(
        self,
        bottlenecks: List[Bottleneck],
        instance_type: str,
        current_config: Optional[dict]
    ) -> tuple[Optional[Optimization], Optional[BatchingOptimization]]:
        """Optimize batching configuration."""
        config_changes = []
        
        current_batch_size = current_config.get("max_batch_size", 32) if current_config else 32
        
        # Determine optimal batch size
        has_queue = any(b.type == BottleneckType.QUEUE_BUILDUP for b in bottlenecks)
        has_low_throughput = any(b.type == BottleneckType.LOW_THROUGHPUT for b in bottlenecks)
        
        if has_queue or has_low_throughput:
            # Increase batch size
            recommended_batch_size = min(current_batch_size * 2, 256)
            improvement = "30-50% throughput increase"
            impact = ImpactLevel.HIGH
        else:
            # Moderate increase
            recommended_batch_size = min(current_batch_size + 16, 128)
            improvement = "15-25% throughput increase"
            impact = ImpactLevel.MEDIUM
        
        config_changes.append(ConfigChange(
            parameter="max_batch_size",
            current_value=current_batch_size,
            recommended_value=recommended_batch_size,
            reason="Increase batch size for better GPU utilization"
        ))
        
        # Enable continuous batching if not enabled
        if instance_type in ["vllm", "sglang"]:
            config_changes.append(ConfigChange(
                parameter="enable_continuous_batching",
                current_value=current_config.get("enable_continuous_batching", True) if current_config else True,
                recommended_value=True,
                reason="Ensure continuous batching is enabled for optimal throughput"
            ))
        
        batch_config = BatchingOptimization(
            max_batch_size=recommended_batch_size,
            enable_continuous_batching=True,
            enable_dynamic_batching=True,
            max_waiting_tokens=recommended_batch_size * 2048,
            scheduling_policy="fcfs"
        )
        
        optimization = Optimization(
            type=OptimizationType.BATCHING,
            title="Optimize Batch Size and Scheduling",
            description="Increase batch size and enable continuous batching",
            config_changes=config_changes,
            expected_impact=impact,
            estimated_improvement=improvement,
            implementation_effort="Low - config change only",
            risks=[
                "Increased memory usage",
                "Slightly higher latency for individual requests"
            ],
            prerequisites=["Sufficient GPU memory available"]
        )
        
        return optimization, batch_config

"""
Optimization Engine

Main engine for generating optimization recommendations.
"""

import logging
from typing import Optional, Dict, Any

from src.models.optimization import OptimizationPlan, OptimizationRequest
from src.models.analysis import AnalysisResult
from src.optimization.kv_cache_optimizer import KVCacheOptimizer
from src.optimization.quantization_optimizer import QuantizationOptimizer
from src.optimization.batching_optimizer import BatchingOptimizer

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """Main optimization engine."""
    
    def __init__(self):
        """Initialize engine."""
        self.kv_cache_optimizer = KVCacheOptimizer()
        self.quantization_optimizer = QuantizationOptimizer()
        self.batching_optimizer = BatchingOptimizer()
    
    def generate_plan(
        self,
        analysis_result: AnalysisResult,
        current_config: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> OptimizationPlan:
        """
        Generate optimization plan from analysis result.
        
        Args:
            analysis_result: Analysis result with bottlenecks
            current_config: Current instance configuration
            constraints: Optimization constraints
            
        Returns:
            Optimization plan
        """
        logger.info(f"Generating optimization plan for {analysis_result.instance_id}")
        
        all_optimizations = []
        
        # Generate KV cache optimizations
        kv_opts, kv_config = self.kv_cache_optimizer.generate_optimizations(
            analysis_result.bottlenecks,
            analysis_result.instance_type,
            current_config
        )
        all_optimizations.extend(kv_opts)
        
        # Generate quantization optimizations
        quant_opts, quant_config = self.quantization_optimizer.generate_optimizations(
            analysis_result.bottlenecks,
            analysis_result.instance_type,
            current_config
        )
        all_optimizations.extend(quant_opts)
        
        # Generate batching optimizations
        batch_opts, batch_config = self.batching_optimizer.generate_optimizations(
            analysis_result.bottlenecks,
            analysis_result.instance_type,
            current_config
        )
        all_optimizations.extend(batch_opts)
        
        # Prioritize optimizations
        priority_order = self._prioritize_optimizations(all_optimizations)
        
        # Estimate total improvement
        total_improvement = self._estimate_total_improvement(all_optimizations)
        
        return OptimizationPlan(
            instance_id=analysis_result.instance_id,
            instance_type=analysis_result.instance_type,
            optimizations=all_optimizations,
            kv_cache_config=kv_config,
            quantization_config=quant_config,
            batching_config=batch_config,
            priority_order=priority_order,
            estimated_total_improvement=total_improvement
        )
    
    def _prioritize_optimizations(self, optimizations) -> list:
        """Prioritize optimizations by impact."""
        impact_order = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        sorted_opts = sorted(
            optimizations,
            key=lambda x: impact_order.get(x.expected_impact.value, 0),
            reverse=True
        )
        
        return [f"{opt.type.value}_{i}" for i, opt in enumerate(sorted_opts)]
    
    def _estimate_total_improvement(self, optimizations) -> str:
        """Estimate total improvement."""
        if not optimizations:
            return "No optimizations recommended"
        
        impact_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for opt in optimizations:
            impact_counts[opt.expected_impact.value] += 1
        
        if impact_counts["critical"] > 0:
            return "50-70% overall performance improvement expected"
        elif impact_counts["high"] > 0:
            return "30-50% overall performance improvement expected"
        elif impact_counts["medium"] > 0:
            return "15-30% overall performance improvement expected"
        else:
            return "5-15% overall performance improvement expected"

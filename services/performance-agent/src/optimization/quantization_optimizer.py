"""
Quantization Optimizer

Optimizes model quantization strategy.
"""

import logging
from typing import List, Optional

from src.models.optimization import (
    Optimization,
    OptimizationType,
    ImpactLevel,
    ConfigChange,
    QuantizationOptimization,
    QuantizationMethod
)
from src.models.analysis import Bottleneck, BottleneckType

logger = logging.getLogger(__name__)


class QuantizationOptimizer:
    """Optimizes quantization settings."""
    
    def generate_optimizations(
        self,
        bottlenecks: List[Bottleneck],
        instance_type: str,
        current_config: Optional[dict] = None
    ) -> tuple[List[Optimization], Optional[QuantizationOptimization]]:
        """
        Generate quantization optimizations.
        
        Args:
            bottlenecks: Detected bottlenecks
            instance_type: Type of instance
            current_config: Current configuration
            
        Returns:
            Tuple of (optimizations list, quantization config)
        """
        optimizations = []
        quant_config = None
        
        # Check for high latency
        latency_bottlenecks = [
            b for b in bottlenecks 
            if b.type == BottleneckType.HIGH_LATENCY
        ]
        
        # Check for memory pressure
        memory_bottlenecks = [
            b for b in bottlenecks 
            if b.type == BottleneckType.MEMORY_PRESSURE
        ]
        
        if latency_bottlenecks or memory_bottlenecks:
            current_quant = current_config.get("quantization") if current_config else None
            
            if not current_quant or current_quant == "none":
                # Recommend quantization
                opt, config = self._recommend_quantization(
                    instance_type,
                    has_memory_pressure=bool(memory_bottlenecks),
                    has_latency_issues=bool(latency_bottlenecks)
                )
                if opt:
                    optimizations.append(opt)
                    quant_config = config
        
        return optimizations, quant_config
    
    def _recommend_quantization(
        self,
        instance_type: str,
        has_memory_pressure: bool,
        has_latency_issues: bool
    ) -> tuple[Optional[Optimization], Optional[QuantizationOptimization]]:
        """Recommend quantization method."""
        
        # Determine best quantization method
        if has_memory_pressure:
            # Aggressive quantization for memory
            method = QuantizationMethod.INT4
            target_bits = 4
            improvement = "50-60% memory reduction, 30-40% latency reduction"
            impact = ImpactLevel.CRITICAL
        else:
            # Balanced quantization for latency
            method = QuantizationMethod.INT8
            target_bits = 8
            improvement = "30-40% memory reduction, 20-30% latency reduction"
            impact = ImpactLevel.HIGH
        
        config_changes = [
            ConfigChange(
                parameter="quantization",
                current_value="none",
                recommended_value=method.value,
                reason=f"Apply {method.value.upper()} quantization to reduce memory and improve latency"
            ),
            ConfigChange(
                parameter="dtype",
                current_value="float16",
                recommended_value=method.value,
                reason="Set data type to match quantization method"
            )
        ]
        
        quant_config = QuantizationOptimization(
            method=method,
            target_bits=target_bits,
            quantize_weights=True,
            quantize_activations=False,
            calibration_samples=512
        )
        
        optimization = Optimization(
            type=OptimizationType.QUANTIZATION,
            title=f"Apply {method.value.upper()} Quantization",
            description=f"Quantize model to {target_bits}-bit for better performance",
            config_changes=config_changes,
            expected_impact=impact,
            estimated_improvement=improvement,
            implementation_effort="Medium - requires model reload",
            risks=[
                "Slight accuracy degradation (typically <1%)",
                "Requires model re-loading",
                "May need calibration dataset"
            ],
            prerequisites=[
                "Model supports quantization",
                "Calibration dataset available (for AWQ/GPTQ)"
            ]
        )
        
        return optimization, quant_config

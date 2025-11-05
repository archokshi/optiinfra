# PHASE2-2.6 PART1: Optimization Engine - Code Implementation Plan

**Phase**: PHASE2-2.6  
**Agent**: Performance Agent  
**Objective**: Implement optimization recommendations for KV cache, quantization, and batching  
**Estimated Time**: 30+25m (55 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE2-2.5, 2.4, 2.3, 2.2, 1.8

---

## Overview

This phase implements the Optimization Engine that generates actionable optimization recommendations based on detected bottlenecks. The engine provides specific configuration changes for KV cache management, quantization strategies, and batching optimizations.

---

## Optimization Engine Overview

### What is the Optimization Engine?
The Optimization Engine is the recommendation layer that:
- Analyzes bottlenecks from the Analysis Engine
- Generates specific configuration recommendations
- Provides quantization strategies
- Optimizes KV cache settings
- Tunes batching parameters
- Estimates performance impact

### Key Optimization Areas

#### 1. KV Cache Optimization
- **Cache Size**: Adjust based on memory pressure
- **Eviction Policy**: Configure cache eviction strategies
- **Prefix Caching**: Enable/disable prefix caching
- **RadixAttention**: Optimize for SGLang

#### 2. Quantization Strategies
- **INT8**: 8-bit integer quantization
- **INT4**: 4-bit integer quantization
- **FP8**: 8-bit floating point
- **AWQ**: Activation-aware Weight Quantization
- **GPTQ**: Post-training quantization

#### 3. Batching Optimization
- **Batch Size**: Optimal batch size calculation
- **Continuous Batching**: Enable/disable
- **Dynamic Batching**: Configure dynamic batching
- **Scheduling**: Optimize request scheduling

---

## Implementation Plan

### Step 1: Optimization Models (5 minutes)

#### 1.1 Create src/models/optimization.py

```python
"""
Optimization Models

Models for optimization recommendations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OptimizationType(str, Enum):
    """Types of optimizations."""
    KV_CACHE = "kv_cache"
    QUANTIZATION = "quantization"
    BATCHING = "batching"
    MEMORY = "memory"
    PARALLELISM = "parallelism"


class ImpactLevel(str, Enum):
    """Expected impact level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QuantizationMethod(str, Enum):
    """Quantization methods."""
    INT8 = "int8"
    INT4 = "int4"
    FP8 = "fp8"
    AWQ = "awq"
    GPTQ = "gptq"
    NONE = "none"


class ConfigChange(BaseModel):
    """Configuration change recommendation."""
    
    parameter: str = Field(..., description="Configuration parameter name")
    current_value: Any = Field(..., description="Current value")
    recommended_value: Any = Field(..., description="Recommended value")
    reason: str = Field(..., description="Reason for change")


class Optimization(BaseModel):
    """Single optimization recommendation."""
    
    type: OptimizationType
    title: str
    description: str
    config_changes: List[ConfigChange]
    expected_impact: ImpactLevel
    estimated_improvement: str = Field(..., description="e.g., '20-30% latency reduction'")
    implementation_effort: str = Field(..., description="e.g., 'Low - config change only'")
    risks: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)


class KVCacheOptimization(BaseModel):
    """KV cache specific optimization."""
    
    enable_prefix_caching: bool
    cache_size_gb: Optional[float] = None
    eviction_policy: Optional[str] = None
    block_size: Optional[int] = None
    swap_space_gb: Optional[float] = None


class QuantizationOptimization(BaseModel):
    """Quantization specific optimization."""
    
    method: QuantizationMethod
    target_bits: int = Field(..., description="Target bit width")
    quantize_weights: bool = True
    quantize_activations: bool = False
    calibration_samples: Optional[int] = None


class BatchingOptimization(BaseModel):
    """Batching specific optimization."""
    
    max_batch_size: int
    enable_continuous_batching: bool
    enable_dynamic_batching: bool
    max_waiting_tokens: Optional[int] = None
    scheduling_policy: Optional[str] = None


class OptimizationPlan(BaseModel):
    """Complete optimization plan."""
    
    instance_id: str
    instance_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    optimizations: List[Optimization]
    kv_cache_config: Optional[KVCacheOptimization] = None
    quantization_config: Optional[QuantizationOptimization] = None
    batching_config: Optional[BatchingOptimization] = None
    priority_order: List[str] = Field(
        default_factory=list,
        description="Ordered list of optimization IDs by priority"
    )
    estimated_total_improvement: str


class OptimizationRequest(BaseModel):
    """Request for optimization recommendations."""
    
    instance_id: str
    instance_type: str
    current_config: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
```

---

### Step 2: KV Cache Optimizer (7 minutes)

#### 2.1 Create src/optimization/kv_cache_optimizer.py

```python
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
```

---

### Step 3: Quantization Optimizer (7 minutes)

#### 3.1 Create src/optimization/quantization_optimizer.py

```python
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
```

---

### Step 4: Batching Optimizer (7 minutes)

#### 4.1 Create src/optimization/batching_optimizer.py

```python
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
```

---

### Step 5: Optimization Engine (4 minutes)

#### 5.1 Create src/optimization/engine.py

```python
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
```

---

## Success Criteria

### Functional Requirements
- ✅ KV cache optimization recommendations
- ✅ Quantization strategy recommendations
- ✅ Batching optimization recommendations
- ✅ Configuration change tracking
- ✅ Impact estimation
- ✅ Priority ordering

### Non-Functional Requirements
- ✅ Recommendations complete in < 1 second
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Tests pass with >80% coverage

---

## Dependencies

### From Previous Phases
- **PHASE2-2.5**: Analysis Engine (bottleneck detection)
- **PHASE2-2.4**: SGLang collector
- **PHASE2-2.3**: TGI collector
- **PHASE2-2.2**: vLLM collector

---

## Next Phase

**PHASE2-2.7**: Integration Testing - End-to-end testing of Performance Agent

---

**Status**: Ready for implementation  
**Estimated Completion**: 55 minutes  
**Dependencies**: PHASE2-2.5, 2.4, 2.3, 2.2

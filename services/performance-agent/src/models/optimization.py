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

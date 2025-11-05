"""
Configuration Models

Data models for configuration tracking and optimization.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class OptimizationStrategy(str, Enum):
    """Optimization strategy types."""
    QUALITY_FIRST = "quality_first"
    COST_FIRST = "cost_first"
    BALANCED = "balanced"
    CUSTOM = "custom"


class ConfigurationSnapshot(BaseModel):
    """Snapshot of LLM configuration at a point in time."""
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    timestamp: datetime = Field(..., description="Snapshot timestamp")
    model: str = Field(..., description="LLM model name")
    temperature: float = Field(..., description="Sampling temperature")
    max_tokens: int = Field(..., description="Maximum tokens")
    timeout: int = Field(..., description="Request timeout in seconds")
    max_retries: int = Field(..., description="Maximum retry attempts")
    enabled: bool = Field(..., description="Whether LLM is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConfigurationChange(BaseModel):
    """Configuration change event."""
    change_id: str = Field(..., description="Unique change identifier")
    timestamp: datetime = Field(..., description="Change timestamp")
    parameter: str = Field(..., description="Parameter that changed")
    old_value: Any = Field(..., description="Previous value")
    new_value: Any = Field(..., description="New value")
    reason: str = Field(..., description="Reason for change")
    changed_by: str = Field(default="system", description="Who made the change")
    impact: Optional[Dict[str, Any]] = Field(default=None, description="Expected impact")


class ConfigurationMetrics(BaseModel):
    """Performance metrics for a configuration."""
    config_id: str = Field(..., description="Configuration identifier")
    avg_quality: float = Field(..., description="Average quality score")
    avg_latency: float = Field(..., description="Average latency in ms")
    avg_tokens: int = Field(..., description="Average tokens used")
    success_rate: float = Field(..., description="Success rate (0-1)")
    cost_per_request: float = Field(..., description="Average cost per request")
    sample_size: int = Field(..., description="Number of samples")
    timestamp: datetime = Field(..., description="Metrics timestamp")


class ParameterImpact(BaseModel):
    """Impact analysis for a parameter."""
    parameter: str = Field(..., description="Parameter name")
    current_value: Any = Field(..., description="Current value")
    quality_correlation: float = Field(..., description="Correlation with quality (-1 to 1)")
    cost_correlation: float = Field(..., description="Correlation with cost (-1 to 1)")
    latency_correlation: float = Field(..., description="Correlation with latency (-1 to 1)")
    optimal_range: Optional[Dict[str, Any]] = Field(default=None, description="Optimal value range")


class ConfigurationRecommendation(BaseModel):
    """Optimization recommendation."""
    recommendation_id: str = Field(..., description="Unique recommendation identifier")
    parameter: str = Field(..., description="Parameter to optimize")
    current_value: Any = Field(..., description="Current value")
    recommended_value: Any = Field(..., description="Recommended value")
    expected_improvement: Dict[str, str] = Field(..., description="Expected improvements")
    confidence: float = Field(..., description="Confidence score (0-1)")
    reason: str = Field(..., description="Reason for recommendation")
    priority: str = Field(default="medium", description="Priority level")


class OptimizationRequest(BaseModel):
    """Request for configuration optimization."""
    strategy: OptimizationStrategy = Field(..., description="Optimization strategy")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Optimization constraints")
    target_metrics: Optional[Dict[str, float]] = Field(default=None, description="Target metric values")


class OptimizationResult(BaseModel):
    """Result of configuration optimization."""
    original_config: ConfigurationSnapshot = Field(..., description="Original configuration")
    optimized_config: ConfigurationSnapshot = Field(..., description="Optimized configuration")
    changes: List[ConfigurationChange] = Field(..., description="List of changes made")
    expected_improvements: Dict[str, str] = Field(..., description="Expected improvements")
    recommendations: List[ConfigurationRecommendation] = Field(..., description="Additional recommendations")


class ConfigurationDrift(BaseModel):
    """Configuration drift detection result."""
    drift_detected: bool = Field(..., description="Whether drift was detected")
    drifted_parameters: List[str] = Field(..., description="Parameters that drifted")
    drift_magnitude: float = Field(..., description="Overall drift magnitude")
    recommendations: List[ConfigurationRecommendation] = Field(..., description="Recommendations to fix drift")
    timestamp: datetime = Field(..., description="Detection timestamp")

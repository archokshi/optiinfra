"""
Analysis Models

Models for bottleneck detection and SLO monitoring.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class BottleneckType(str, Enum):
    """Types of bottlenecks."""
    HIGH_LATENCY = "high_latency"
    LOW_THROUGHPUT = "low_throughput"
    QUEUE_BUILDUP = "queue_buildup"
    CACHE_INEFFICIENCY = "cache_inefficiency"
    MEMORY_PRESSURE = "memory_pressure"
    BATCH_SIZE_SUBOPTIMAL = "batch_size_suboptimal"


class Severity(str, Enum):
    """Severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Bottleneck(BaseModel):
    """Detected bottleneck."""
    
    type: BottleneckType
    severity: Severity
    description: str
    metric_name: str
    current_value: float
    threshold_value: float
    recommendation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SLOTarget(BaseModel):
    """SLO target definition."""
    
    name: str = Field(..., description="SLO name")
    metric: str = Field(..., description="Metric to monitor")
    target_value: float = Field(..., description="Target value")
    comparison: str = Field(..., description="Comparison operator: <, >, <=, >=")
    description: Optional[str] = None


class SLOStatus(BaseModel):
    """SLO compliance status."""
    
    target: SLOTarget
    current_value: float
    is_compliant: bool
    deviation_percent: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    
    instance_id: str
    instance_type: str = Field(..., description="vllm, tgi, or sglang")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    bottlenecks: List[Bottleneck] = Field(default_factory=list)
    slo_statuses: List[SLOStatus] = Field(default_factory=list)
    overall_health_score: float = Field(..., ge=0.0, le=100.0)
    recommendations: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    """Request to analyze metrics."""
    
    instance_id: str
    instance_type: str = Field(..., description="vllm, tgi, or sglang")
    slo_targets: Optional[List[SLOTarget]] = None

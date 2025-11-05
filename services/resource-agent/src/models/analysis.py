"""
Analysis Models

Pydantic models for resource analysis results.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class BottleneckType(str, Enum):
    """Types of resource bottlenecks."""
    
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK = "network"
    NONE = "none"


class UtilizationLevel(str, Enum):
    """Resource utilization levels."""
    
    IDLE = "idle"  # < 20%
    LOW = "low"  # 20-50%
    MODERATE = "moderate"  # 50-70%
    HIGH = "high"  # 70-90%
    CRITICAL = "critical"  # > 90%


class Severity(str, Enum):
    """Issue severity levels."""
    
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Bottleneck(BaseModel):
    """Bottleneck detection result."""
    
    type: BottleneckType = Field(..., description="Type of bottleneck")
    severity: Severity = Field(..., description="Severity level")
    utilization_percent: float = Field(..., ge=0, le=100, description="Current utilization %")
    threshold_percent: float = Field(..., description="Threshold that triggered detection")
    message: str = Field(..., description="Human-readable message")
    recommendations: List[str] = Field(default_factory=list, description="Optimization recommendations")


class ResourceUtilization(BaseModel):
    """Resource utilization summary."""
    
    resource_type: str = Field(..., description="Type of resource (cpu, gpu, memory, etc.)")
    current_percent: float = Field(..., ge=0, le=100, description="Current utilization %")
    level: UtilizationLevel = Field(..., description="Utilization level")
    is_bottleneck: bool = Field(default=False, description="Whether this is a bottleneck")


class EfficiencyScore(BaseModel):
    """Efficiency scoring."""
    
    overall_score: float = Field(..., ge=0, le=100, description="Overall efficiency score (0-100)")
    gpu_efficiency: Optional[float] = Field(None, ge=0, le=100, description="GPU efficiency score")
    cpu_efficiency: float = Field(..., ge=0, le=100, description="CPU efficiency score")
    memory_efficiency: float = Field(..., ge=0, le=100, description="Memory efficiency score")
    
    # Efficiency breakdown
    gpu_utilization_score: Optional[float] = Field(None, description="GPU utilization component")
    gpu_power_efficiency: Optional[float] = Field(None, description="GPU power efficiency component")
    cpu_balance_score: float = Field(..., description="CPU core balance score")
    memory_availability_score: float = Field(..., description="Memory availability score")


class OptimizationRecommendation(BaseModel):
    """Optimization recommendation."""
    
    priority: Severity = Field(..., description="Recommendation priority")
    category: str = Field(..., description="Category (scaling, optimization, etc.)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    expected_impact: str = Field(..., description="Expected impact")
    implementation_effort: str = Field(..., description="Implementation effort (low, medium, high)")


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="Instance identifier")
    
    # Bottleneck detection
    primary_bottleneck: BottleneckType = Field(..., description="Primary bottleneck")
    bottlenecks: List[Bottleneck] = Field(default_factory=list, description="All detected bottlenecks")
    
    # Utilization summary
    utilization_summary: List[ResourceUtilization] = Field(
        default_factory=list,
        description="Resource utilization summary"
    )
    
    # Efficiency scoring
    efficiency: EfficiencyScore = Field(..., description="Efficiency scores")
    
    # Recommendations
    recommendations: List[OptimizationRecommendation] = Field(
        default_factory=list,
        description="Optimization recommendations"
    )
    
    # Overall assessment
    overall_health: str = Field(..., description="Overall system health (healthy, degraded, critical)")
    health_score: float = Field(..., ge=0, le=100, description="Overall health score (0-100)")

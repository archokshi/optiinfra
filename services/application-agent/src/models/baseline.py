"""
Baseline Models

Pydantic models for baseline tracking and regression detection.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class BaselineType(str, Enum):
    """Baseline type."""
    ROLLING = "rolling"
    FIXED = "fixed"
    ADAPTIVE = "adaptive"


class BaselineStatus(str, Enum):
    """Baseline status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class RegressionSeverity(str, Enum):
    """Regression severity levels."""
    NONE = "none"
    MINOR = "minor"  # 5-10% drop
    MODERATE = "moderate"  # 10-20% drop
    SEVERE = "severe"  # 20-30% drop
    CRITICAL = "critical"  # >30% drop


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class BaselineConfig(BaseModel):
    """Configuration for baseline establishment."""
    
    model_name: str = Field(..., description="Model name")
    config_hash: str = Field(default="default", description="Configuration hash")
    baseline_type: BaselineType = Field(default=BaselineType.ROLLING, description="Baseline type")
    sample_size: int = Field(default=100, description="Sample size for baseline")
    threshold_percentage: float = Field(default=5.0, description="Regression threshold (%)")


class BaselineMetrics(BaseModel):
    """Baseline quality metrics."""
    
    average_quality: float = Field(..., description="Average quality score")
    average_relevance: float = Field(..., description="Average relevance score")
    average_coherence: float = Field(..., description="Average coherence score")
    average_hallucination: float = Field(..., description="Average hallucination rate")
    std_dev_quality: Optional[float] = Field(None, description="Standard deviation of quality")
    min_quality: Optional[float] = Field(None, description="Minimum quality")
    max_quality: Optional[float] = Field(None, description="Maximum quality")


class Baseline(BaseModel):
    """Complete baseline with metadata."""
    
    baseline_id: str = Field(..., description="Unique baseline ID")
    model_name: str = Field(..., description="Model name")
    config_hash: str = Field(..., description="Configuration hash")
    baseline_type: BaselineType = Field(..., description="Baseline type")
    metrics: BaselineMetrics = Field(..., description="Baseline metrics")
    sample_size: int = Field(..., description="Number of samples")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: BaselineStatus = Field(default=BaselineStatus.ACTIVE)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RegressionAlert(BaseModel):
    """Regression alert."""
    
    alert_id: str = Field(..., description="Unique alert ID")
    level: AlertLevel = Field(..., description="Alert level")
    message: str = Field(..., description="Alert message")
    severity: RegressionSeverity = Field(..., description="Regression severity")
    quality_drop: float = Field(..., description="Quality drop percentage")
    baseline_quality: float = Field(..., description="Baseline quality")
    current_quality: float = Field(..., description="Current quality")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RegressionResult(BaseModel):
    """Regression detection result."""
    
    regression_detected: bool = Field(..., description="Whether regression was detected")
    regression_score: float = Field(..., ge=0, le=100, description="Regression score (0-100)")
    severity: RegressionSeverity = Field(..., description="Regression severity")
    quality_drop: float = Field(..., description="Quality drop amount")
    quality_drop_percentage: float = Field(..., description="Quality drop percentage")
    baseline_quality: float = Field(..., description="Baseline quality")
    current_quality: float = Field(..., description="Current quality")
    z_score: Optional[float] = Field(None, description="Z-score for anomaly detection")
    alert: Optional[RegressionAlert] = Field(None, description="Generated alert if regression detected")
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RegressionDetectionRequest(BaseModel):
    """Request for regression detection."""
    
    model_name: str = Field(..., description="Model name")
    config_hash: str = Field(default="default", description="Configuration hash")
    current_quality: float = Field(..., ge=0, le=100, description="Current quality score")
    current_relevance: Optional[float] = Field(None, description="Current relevance score")
    current_coherence: Optional[float] = Field(None, description="Current coherence score")
    current_hallucination: Optional[float] = Field(None, description="Current hallucination rate")

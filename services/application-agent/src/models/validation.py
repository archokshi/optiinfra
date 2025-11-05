"""
Validation Models

Pydantic models for validation engine and A/B testing.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ValidationDecision(str, Enum):
    """Validation decision types."""
    APPROVE = "approve"
    REJECT = "reject"
    MANUAL_REVIEW = "manual_review"
    PENDING = "pending"


class ABTestGroup(str, Enum):
    """A/B test group types."""
    CONTROL = "control"
    TREATMENT = "treatment"


class ABTestConfig(BaseModel):
    """Configuration for A/B test."""
    
    test_id: str = Field(..., description="Unique test ID")
    name: str = Field(..., description="Test name")
    control_group: str = Field(..., description="Control group identifier")
    treatment_group: str = Field(..., description="Treatment group identifier")
    metric: str = Field(default="overall_quality", description="Metric to compare")
    sample_size: int = Field(default=100, description="Target sample size per group")
    significance_level: float = Field(default=0.05, description="Significance level (alpha)")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ABTestObservation(BaseModel):
    """Single observation in A/B test."""
    
    test_id: str = Field(..., description="Test ID")
    group: ABTestGroup = Field(..., description="Test group")
    value: float = Field(..., description="Observed value")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ABTestResult(BaseModel):
    """Result of A/B test analysis."""
    
    test_id: str = Field(..., description="Test ID")
    control_mean: float = Field(..., description="Control group mean")
    treatment_mean: float = Field(..., description="Treatment group mean")
    control_std: float = Field(..., description="Control group std dev")
    treatment_std: float = Field(..., description="Treatment group std dev")
    control_size: int = Field(..., description="Control group sample size")
    treatment_size: int = Field(..., description="Treatment group sample size")
    
    # Statistical test results
    t_statistic: float = Field(..., description="T-test statistic")
    p_value: float = Field(..., description="P-value")
    degrees_of_freedom: int = Field(..., description="Degrees of freedom")
    statistically_significant: bool = Field(..., description="Is result significant")
    
    # Effect size
    effect_size: float = Field(..., description="Cohen's d effect size")
    
    # Confidence intervals
    ci_95_lower: float = Field(..., description="95% CI lower bound")
    ci_95_upper: float = Field(..., description="95% CI upper bound")
    ci_99_lower: float = Field(..., description="99% CI lower bound")
    ci_99_upper: float = Field(..., description="99% CI upper bound")
    
    # Winner determination
    winner: Optional[ABTestGroup] = Field(None, description="Winning group")
    improvement_percentage: float = Field(..., description="Improvement percentage")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationRequest(BaseModel):
    """Request for validation."""
    
    name: str = Field(..., description="Validation name")
    model_name: str = Field(..., description="Model name")
    config_hash: str = Field(default="default", description="Configuration hash")
    baseline_quality: float = Field(..., description="Baseline quality score")
    new_quality: float = Field(..., description="New quality score")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Complete validation result."""
    
    validation_id: str = Field(..., description="Unique validation ID")
    name: str = Field(..., description="Validation name")
    
    # Decision
    decision: ValidationDecision = Field(..., description="Validation decision")
    confidence: float = Field(..., ge=0, le=1, description="Decision confidence (0-1)")
    
    # Quality metrics
    baseline_quality: float = Field(..., description="Baseline quality")
    new_quality: float = Field(..., description="New quality")
    quality_change: float = Field(..., description="Quality change amount")
    quality_change_percentage: float = Field(..., description="Quality change percentage")
    
    # Statistical analysis
    statistically_significant: bool = Field(..., description="Is change significant")
    p_value: Optional[float] = Field(None, description="P-value if test performed")
    effect_size: Optional[float] = Field(None, description="Effect size if calculated")
    
    # Recommendation
    recommendation: str = Field(..., description="Human-readable recommendation")
    reasoning: List[str] = Field(default_factory=list, description="Decision reasoning")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationHistory(BaseModel):
    """Validation history record."""
    
    validation_id: str = Field(..., description="Validation ID")
    decision: ValidationDecision = Field(..., description="Decision made")
    quality_change: float = Field(..., description="Quality change")
    confidence: float = Field(..., description="Confidence score")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

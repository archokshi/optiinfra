"""
Pydantic models for Learning Loop.

Type-safe models for outcome tracking, feedback analysis, and continuous improvement.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class OutcomeRecord(BaseModel):
    """Record of an execution outcome."""
    outcome_id: str = Field(..., description="Unique outcome identifier")
    execution_id: str = Field(..., description="Execution ID")
    recommendation_id: str = Field(..., description="Recommendation ID")
    recommendation_type: str = Field(..., description="Type of recommendation")
    success: bool = Field(..., description="Whether execution succeeded")
    actual_savings: Optional[float] = Field(None, description="Actual savings achieved")
    predicted_savings: float = Field(..., description="Predicted savings")
    savings_accuracy: float = Field(..., description="Actual / Predicted ratio")
    execution_duration_seconds: float = Field(..., description="Execution duration")
    issues_encountered: List[str] = Field(default_factory=list, description="Issues during execution")
    post_execution_metrics: Dict[str, Any] = Field(default_factory=dict, description="Post-execution metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Outcome timestamp")


class SavingsMeasurement(BaseModel):
    """Measurement of actual savings over time."""
    execution_id: str
    recommendation_id: str
    measurement_period_days: int
    actual_savings: float
    predicted_savings: float
    savings_accuracy: float
    cost_before: float
    cost_after: float
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class ComparisonResult(BaseModel):
    """Comparison of predicted vs actual outcomes."""
    recommendation_id: str
    predicted_savings: float
    actual_savings: float
    savings_accuracy: float
    prediction_error: float
    execution_success: bool
    notes: List[str] = Field(default_factory=list)


class ExecutionMetrics(BaseModel):
    """Metrics from an execution."""
    execution_id: str
    duration_seconds: float
    success: bool
    resources_affected: int
    issues_count: int
    rollback_required: bool
    user_satisfaction: Optional[float] = None


class SimilarCase(BaseModel):
    """A similar historical case."""
    recommendation_id: str = Field(..., description="Historical recommendation ID")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    outcome: OutcomeRecord = Field(..., description="Historical outcome")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class SuccessPatterns(BaseModel):
    """Patterns found in successful executions."""
    recommendation_type: str
    success_rate: float
    total_cases: int
    common_characteristics: List[str] = Field(default_factory=list)
    optimal_conditions: Dict[str, Any] = Field(default_factory=dict)
    best_practices: List[str] = Field(default_factory=list)
    avg_savings_accuracy: float
    confidence: float


class FailurePatterns(BaseModel):
    """Patterns found in failed executions."""
    recommendation_type: str
    failure_rate: float
    total_cases: int
    common_causes: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    avoidance_strategies: List[str] = Field(default_factory=list)
    avg_execution_duration: float
    confidence: float


class AccuracyMetrics(BaseModel):
    """Accuracy metrics for recommendations."""
    recommendation_type: Optional[str] = None
    total_executions: int
    successful_executions: int
    success_rate: float
    avg_savings_accuracy: float
    avg_prediction_error: float
    roi_accuracy: float
    improvement_over_baseline: float
    measurement_period_days: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class LearningInsight(BaseModel):
    """An insight learned from outcomes."""
    insight_id: str
    insight_type: str = Field(..., description="Type: success_pattern, failure_pattern, improvement")
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    impact: str = Field(..., description="Impact level: low, medium, high")
    actionable_recommendations: List[str] = Field(default_factory=list)
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImprovementOpportunity(BaseModel):
    """An opportunity for improvement."""
    opportunity_id: str
    area: str = Field(..., description="Area: scoring, prediction, risk_assessment")
    current_performance: float
    potential_improvement: float
    suggested_actions: List[str] = Field(default_factory=list)
    estimated_impact: str = Field(..., description="Impact: low, medium, high")
    priority: int = Field(..., ge=1, le=5)
    status: str = Field(default="pending", description="Status: pending, in_progress, completed")


class ScoringWeights(BaseModel):
    """Weights for recommendation scoring."""
    roi_weight: float = 0.4
    risk_weight: float = 0.3
    urgency_weight: float = 0.2
    confidence_weight: float = 0.1
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    performance_history: Dict[str, float] = Field(default_factory=dict)


class PredictionModel(BaseModel):
    """Model for cost predictions."""
    recommendation_type: str
    base_accuracy: float
    adjustment_factors: Dict[str, float] = Field(default_factory=dict)
    seasonal_factors: Dict[str, float] = Field(default_factory=dict)
    confidence_interval: float
    last_trained: datetime = Field(default_factory=datetime.utcnow)
    training_samples: int


class RiskModel(BaseModel):
    """Model for risk assessment."""
    recommendation_type: str
    base_risk_score: float
    risk_factors: Dict[str, float] = Field(default_factory=dict)
    failure_indicators: List[str] = Field(default_factory=list)
    mitigation_strategies: Dict[str, str] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ImprovementResult(BaseModel):
    """Result of applying improvements."""
    improvement_id: str
    area: str
    changes_applied: List[str] = Field(default_factory=list)
    expected_impact: float
    actual_impact: Optional[float] = None
    success: bool
    applied_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessingResult(BaseModel):
    """Result of processing an execution outcome."""
    outcome_id: str
    stored_in_qdrant: bool
    vector_id: Optional[str] = None
    insights_generated: int
    improvements_identified: int
    processing_time_seconds: float
    success: bool
    message: str


class LearningCycleResult(BaseModel):
    """Result of a learning cycle."""
    cycle_id: str
    started_at: datetime
    completed_at: datetime
    outcomes_processed: int
    insights_generated: int
    improvements_applied: int
    accuracy_improvement: float
    duration_seconds: float
    success: bool
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class LearningMetrics(BaseModel):
    """Overall learning metrics."""
    total_outcomes_tracked: int
    success_rate: float
    avg_savings_accuracy: float
    avg_prediction_error: float
    improvement_over_baseline: float
    learning_cycles_completed: int
    last_learning_cycle: Optional[datetime] = None
    active_improvements: int
    insights_generated: int
    measurement_period_days: int = 30


class OutcomeData(BaseModel):
    """Data for tracking an outcome."""
    execution_id: str
    recommendation_id: str
    success: bool
    actual_savings: Optional[float] = None
    predicted_savings: float
    execution_duration_seconds: float
    issues_encountered: List[str] = Field(default_factory=list)
    post_execution_metrics: Dict[str, Any] = Field(default_factory=dict)


class FeedbackData(BaseModel):
    """Aggregated feedback data."""
    recommendation_type: str
    total_executions: int
    success_patterns: SuccessPatterns
    failure_patterns: FailurePatterns
    accuracy_metrics: AccuracyMetrics
    insights: List[LearningInsight] = Field(default_factory=list)

"""
Application Schema Models (FOUNDATION-0.2e)
Tracks LLM quality metrics, baselines, and regressions
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Boolean, Text,
    Enum as SQLEnum, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from shared.database.models.core import Base


# ==========================================
# ENUMS
# ==========================================

class BaselineType(str, enum.Enum):
    """Types of quality baselines"""
    INITIAL = "initial"
    UPDATED = "updated"
    ROLLBACK = "rollback"


class RegressionType(str, enum.Enum):
    """Types of quality regressions"""
    QUALITY_DROP = "quality_drop"
    LATENCY_INCREASE = "latency_increase"
    HALLUCINATION_SPIKE = "hallucination_spike"
    TOXICITY_INCREASE = "toxicity_increase"


class RegressionSeverity(str, enum.Enum):
    """Severity levels for regressions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegressionAction(str, enum.Enum):
    """Actions taken for regressions"""
    ALERT_ONLY = "alert_only"
    ROLLBACK_TRIGGERED = "rollback_triggered"
    MANUAL_REVIEW = "manual_review"
    AUTO_FIXED = "auto_fixed"


# ==========================================
# MODELS
# ==========================================

class QualityMetric(Base):
    """
    Tracks per-request quality metrics for LLM outputs
    
    Stores detailed quality scores for each LLM request to enable
    quality monitoring, regression detection, and A/B testing.
    """
    __tablename__ = "quality_metrics"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Request Details
    request_id = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique identifier for the LLM request"
    )
    model_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Model name: gpt-4, claude-3-opus, llama-3-70b, etc."
    )
    model_version = Column(
        String(50),
        nullable=False,
        comment="Model version: 0314, 20240229, etc."
    )
    
    # Token Usage
    prompt_tokens = Column(
        Integer,
        nullable=True,
        comment="Number of tokens in prompt"
    )
    completion_tokens = Column(
        Integer,
        nullable=True,
        comment="Number of tokens in completion"
    )
    
    # Performance
    latency_ms = Column(
        Float,
        nullable=True,
        comment="Request latency in milliseconds"
    )
    
    # Quality Scores (0.0 to 1.0)
    relevance_score = Column(
        Float,
        nullable=True,
        comment="How relevant is the response to the prompt (0-1)"
    )
    coherence_score = Column(
        Float,
        nullable=True,
        comment="How coherent and logical is the response (0-1)"
    )
    factuality_score = Column(
        Float,
        nullable=True,
        comment="How factually accurate is the response (0-1)"
    )
    hallucination_detected = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether hallucination was detected"
    )
    toxicity_score = Column(
        Float,
        nullable=True,
        comment="Toxicity level of the response (0-1, lower is better)"
    )
    overall_quality_score = Column(
        Float,
        nullable=False,
        index=True,
        comment="Aggregated quality score (0-1)"
    )
    
    # Timing
    timestamp = Column(
        DateTime,
        nullable=False,
        index=True,
        comment="When the request was made"
    )
    
    # Additional Data
    quality_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional context: user_id, session_id, etc."
    )
    
    # Audit
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="quality_metrics")
    customer = relationship("Customer", back_populates="quality_metrics")
    
    # Indexes
    __table_args__ = (
        Index(
            "ix_quality_metrics_agent_model",
            "agent_id", "model_name"
        ),
        Index(
            "ix_quality_metrics_customer_model",
            "customer_id", "model_name"
        ),
        Index(
            "ix_quality_metrics_timestamp",
            "timestamp"
        ),
        Index(
            "ix_quality_metrics_overall_score",
            "overall_quality_score"
        ),
        Index(
            "ix_quality_metrics_model_timestamp",
            "model_name", "timestamp"
        ),
    )
    
    def __repr__(self):
        return (
            f"<QualityMetric(id={self.id}, "
            f"model={self.model_name}, score={self.overall_quality_score:.2f})>"
        )


class QualityBaseline(Base):
    """
    Stores quality baselines for comparison and regression detection
    
    Baselines are established from sample sets and used to detect
    when quality degrades after changes.
    """
    __tablename__ = "quality_baselines"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Model Details
    model_name = Column(
        String(100),
        nullable=False,
        index=True
    )
    model_version = Column(
        String(50),
        nullable=False
    )
    
    # Baseline Type
    baseline_type = Column(
        SQLEnum(BaselineType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BaselineType.INITIAL,
        index=True
    )
    
    # Sample Info
    sample_size = Column(
        Integer,
        nullable=False,
        comment="Number of requests used to establish baseline"
    )
    
    # Average Scores
    avg_relevance_score = Column(
        Float,
        nullable=True,
        comment="Average relevance score from samples"
    )
    avg_coherence_score = Column(
        Float,
        nullable=True,
        comment="Average coherence score from samples"
    )
    avg_factuality_score = Column(
        Float,
        nullable=True,
        comment="Average factuality score from samples"
    )
    avg_overall_score = Column(
        Float,
        nullable=False,
        comment="Average overall quality score"
    )
    
    # Performance Baseline
    p95_latency_ms = Column(
        Float,
        nullable=True,
        comment="P95 latency from samples"
    )
    
    # Validity
    established_at = Column(
        DateTime,
        nullable=False,
        index=True,
        comment="When the baseline was established"
    )
    valid_until = Column(
        DateTime,
        nullable=True,
        comment="When the baseline expires (null = indefinite)"
    )
    
    # Additional Data
    baseline_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional context: confidence_interval, std_dev, etc."
    )
    
    # Audit
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="quality_baselines")
    customer = relationship("Customer", back_populates="quality_baselines")
    regressions = relationship(
        "QualityRegression",
        back_populates="baseline",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index(
            "ix_quality_baselines_agent_model",
            "agent_id", "model_name"
        ),
        Index(
            "ix_quality_baselines_customer_model",
            "customer_id", "model_name"
        ),
        Index(
            "ix_quality_baselines_established_at",
            "established_at"
        ),
        Index(
            "ix_quality_baselines_type",
            "baseline_type"
        ),
    )
    
    def __repr__(self):
        return (
            f"<QualityBaseline(id={self.id}, "
            f"model={self.model_name}, type={self.baseline_type}, "
            f"score={self.avg_overall_score:.2f})>"
        )


class QualityRegression(Base):
    """
    Tracks detected quality regressions
    
    Records when quality drops below acceptable thresholds,
    enabling automated rollbacks and alerts.
    """
    __tablename__ = "quality_regressions"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    baseline_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quality_baselines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Baseline used for comparison"
    )
    workflow_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Workflow that caused the regression (if known)"
    )
    
    # Regression Details
    regression_type = Column(
        SQLEnum(RegressionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    severity = Column(
        SQLEnum(RegressionSeverity, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    
    # Detection Time
    detected_at = Column(
        DateTime,
        nullable=False,
        index=True
    )
    
    # Metric Details
    metric_name = Column(
        String(100),
        nullable=False,
        comment="Which metric regressed: overall_score, relevance, latency, etc."
    )
    baseline_value = Column(
        Float,
        nullable=False,
        comment="Expected value from baseline"
    )
    current_value = Column(
        Float,
        nullable=False,
        comment="Actual value that triggered regression"
    )
    delta_percent = Column(
        Float,
        nullable=False,
        comment="Percentage change from baseline (negative = worse)"
    )
    sample_size = Column(
        Integer,
        nullable=False,
        comment="Number of samples used to detect regression"
    )
    
    # Action & Resolution
    action_taken = Column(
        SQLEnum(RegressionAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RegressionAction.ALERT_ONLY,
        index=True
    )
    resolved_at = Column(
        DateTime,
        nullable=True,
        comment="When the regression was resolved"
    )
    resolution_notes = Column(
        Text,
        nullable=True,
        comment="How the regression was resolved"
    )
    
    # Additional Data
    regression_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional context: affected_requests, p_value, etc."
    )
    
    # Audit
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    
    # Relationships
    agent = relationship("Agent", back_populates="quality_regressions")
    customer = relationship("Customer", back_populates="quality_regressions")
    baseline = relationship("QualityBaseline", back_populates="regressions")
    workflow = relationship(
        "WorkflowExecution",
        foreign_keys=[workflow_execution_id],
        backref="quality_regressions"
    )
    
    # Indexes
    __table_args__ = (
        Index(
            "ix_quality_regressions_agent_severity",
            "agent_id", "severity"
        ),
        Index(
            "ix_quality_regressions_customer_type",
            "customer_id", "regression_type"
        ),
        Index(
            "ix_quality_regressions_detected_at",
            "detected_at"
        ),
        Index(
            "ix_quality_regressions_baseline",
            "baseline_id"
        ),
        Index(
            "ix_quality_regressions_workflow",
            "workflow_execution_id"
        ),
        Index(
            "ix_quality_regressions_unresolved",
            "resolved_at"
        ),
    )
    
    def __repr__(self):
        return (
            f"<QualityRegression(id={self.id}, "
            f"type={self.regression_type}, severity={self.severity}, "
            f"resolved={self.resolved_at is not None})>"
        )
    
    @property
    def is_resolved(self):
        """Check if regression has been resolved"""
        return self.resolved_at is not None
    
    @property
    def time_to_resolve_minutes(self):
        """Calculate time to resolution in minutes"""
        if self.resolved_at and self.detected_at:
            return (self.resolved_at - self.detected_at).total_seconds() / 60
        return None

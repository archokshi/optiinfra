"""
Workflow History Models (FOUNDATION-0.2c)
Tracks workflow executions, steps, and artifacts
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Integer, BigInteger, Text, Enum as SQLEnum,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from shared.database.models.core import Base


# ==========================================
# ENUMS
# ==========================================

class WorkflowType(str, enum.Enum):
    """Types of workflows that can be executed"""
    COST_ANALYSIS = "cost_analysis"
    PERFORMANCE_TUNING = "performance_tuning"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    QUALITY_CHECK = "quality_check"
    SCALING_DECISION = "scaling_decision"
    CONFIGURATION_UPDATE = "configuration_update"
    HEALTH_CHECK = "health_check"
    ANOMALY_DETECTION = "anomaly_detection"


class WorkflowStatus(str, enum.Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class StepStatus(str, enum.Enum):
    """Status of individual workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ArtifactType(str, enum.Enum):
    """Types of artifacts generated during workflows"""
    REPORT = "report"
    CONFIG = "config"
    LOG = "log"
    RECOMMENDATION = "recommendation"
    CHART = "chart"
    METRICS = "metrics"
    ALERT = "alert"
    DIAGNOSTIC = "diagnostic"


# ==========================================
# MODELS
# ==========================================

class WorkflowExecution(Base):
    """
    Tracks high-level workflow executions
    
    A workflow execution represents a complete run of a workflow
    (e.g., a cost analysis, performance tuning session)
    """
    __tablename__ = "workflow_executions"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique workflow execution identifier"
    )
    
    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent that executed this workflow"
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Customer this workflow was executed for"
    )
    
    # Workflow Details
    workflow_type = Column(
        SQLEnum(WorkflowType, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Type of workflow executed"
    )
    status = Column(
        SQLEnum(WorkflowStatus, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=WorkflowStatus.PENDING,
        index=True,
        comment="Current status of workflow execution"
    )
    
    # Timing
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When workflow execution started"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When workflow execution completed"
    )
    
    # Data
    input_data = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Input parameters for workflow"
    )
    output_data = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Output results from workflow"
    )
    error_details = Column(
        JSONB,
        nullable=True,
        comment="Error details if workflow failed"
    )
    
    # Metadata
    workflow_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional workflow metadata"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Workflow creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    
    # Relationships
    agent = relationship("Agent", back_populates="workflow_executions")
    customer = relationship("Customer", back_populates="workflow_executions")
    steps = relationship(
        "WorkflowStep",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order"
    )
    artifacts = relationship(
        "WorkflowArtifact",
        back_populates="execution",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index(
            "ix_workflow_executions_agent_status",
            "agent_id", "status"
        ),
        Index(
            "ix_workflow_executions_customer_type",
            "customer_id", "workflow_type"
        ),
        Index(
            "ix_workflow_executions_started_at",
            "started_at"
        ),
    )
    
    def __repr__(self):
        return (
            f"<WorkflowExecution(id={self.id}, "
            f"type={self.workflow_type}, status={self.status})>"
        )


class WorkflowStep(Base):
    """
    Tracks individual steps within a workflow execution
    
    Each workflow consists of multiple steps that execute in order
    """
    __tablename__ = "workflow_steps"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique workflow step identifier"
    )
    
    # Foreign Key
    workflow_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent workflow execution"
    )
    
    # Step Details
    step_name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Name of this step"
    )
    step_order = Column(
        Integer,
        nullable=False,
        comment="Order of execution (1, 2, 3...)"
    )
    status = Column(
        SQLEnum(StepStatus, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=StepStatus.PENDING,
        index=True,
        comment="Current status of this step"
    )
    
    # Timing
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When step execution started"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When step execution completed"
    )
    
    # Data
    input_data = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Input data for this step"
    )
    output_data = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Output data from this step"
    )
    error_details = Column(
        JSONB,
        nullable=True,
        comment="Error details if step failed"
    )
    
    # Retry Logic
    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times this step has been retried"
    )
    max_retries = Column(
        Integer,
        nullable=False,
        default=3,
        comment="Maximum number of retries allowed"
    )
    
    # Metadata
    step_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional step metadata"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Step creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="steps")
    artifacts = relationship(
        "WorkflowArtifact",
        back_populates="step",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index(
            "ix_workflow_steps_execution_order",
            "workflow_execution_id", "step_order"
        ),
        Index(
            "ix_workflow_steps_execution_status",
            "workflow_execution_id", "status"
        ),
        Index(
            "ix_workflow_steps_name_status",
            "step_name", "status"
        ),
    )
    
    def __repr__(self):
        return (
            f"<WorkflowStep(id={self.id}, name={self.step_name}, "
            f"order={self.step_order}, status={self.status})>"
        )


class WorkflowArtifact(Base):
    """
    Stores artifacts generated during workflow execution
    
    Artifacts include reports, configs, logs, charts, etc.
    """
    __tablename__ = "workflow_artifacts"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique artifact identifier"
    )
    
    # Foreign Keys
    workflow_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent workflow execution"
    )
    workflow_step_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_steps.id", ondelete="CASCADE"),
        nullable=True,  # Can be null for execution-level artifacts
        index=True,
        comment="Step that generated this artifact (optional)"
    )
    
    # Artifact Details
    artifact_type = Column(
        SQLEnum(ArtifactType, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Type of artifact"
    )
    artifact_name = Column(
        String(255),
        nullable=False,
        comment="Human-readable artifact name"
    )
    artifact_path = Column(
        Text,
        nullable=False,
        comment="Storage path (S3, file system, etc.)"
    )
    
    # Size & Type
    artifact_size_bytes = Column(
        BigInteger,
        nullable=True,
        comment="Size of artifact in bytes"
    )
    content_type = Column(
        String(100),
        nullable=True,
        comment="MIME type of artifact"
    )
    
    # Metadata
    artifact_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional artifact metadata"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Artifact creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="artifacts")
    step = relationship("WorkflowStep", back_populates="artifacts")
    
    # Indexes
    __table_args__ = (
        Index(
            "ix_workflow_artifacts_execution_type",
            "workflow_execution_id", "artifact_type"
        ),
        Index(
            "ix_workflow_artifacts_step_type",
            "workflow_step_id", "artifact_type"
        ),
    )
    
    def __repr__(self):
        return (
            f"<WorkflowArtifact(id={self.id}, name={self.artifact_name}, "
            f"type={self.artifact_type})>"
        )

"""
Resource Schema Models (FOUNDATION-0.2d)
Tracks resource metrics and auto-scaling events
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Float, Boolean, Enum as SQLEnum,
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

class ResourceType(str, enum.Enum):
    """Types of resources being monitored"""
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"


class ScalingEventType(str, enum.Enum):
    """Types of scaling events"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    AUTO_SCALE_TRIGGERED = "auto_scale_triggered"
    MANUAL_SCALE = "manual_scale"
    SCALE_CANCELLED = "scale_cancelled"


# ==========================================
# MODELS
# ==========================================

class ResourceMetric(Base):
    """
    Tracks resource utilization metrics
    
    Stores GPU utilization, CPU usage, memory, disk I/O, network bandwidth
    for each instance. Supports time-series analysis of resource usage.
    """
    __tablename__ = "resource_metrics"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique metric identifier"
    )
    
    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent collecting this metric"
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Customer this metric belongs to"
    )
    
    # Instance Identification
    instance_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Cloud instance ID (e.g., i-0abc123, instance-xyz)"
    )
    
    # Resource Details
    resource_type = Column(
        SQLEnum(ResourceType, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Type of resource being measured"
    )
    metric_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Metric name: utilization, temperature, memory_used, etc."
    )
    metric_value = Column(
        Float,
        nullable=False,
        comment="Numeric value of the metric"
    )
    unit = Column(
        String(50),
        nullable=False,
        comment="Unit: percent, celsius, MB, GB, etc."
    )
    
    # Timing
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When the metric was collected"
    )
    
    # Additional Data
    resource_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional context: gpu_model, instance_type, etc."
    )
    
    # Audit
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp"
    )
    
    # Relationships
    agent = relationship("Agent", back_populates="resource_metrics")
    customer = relationship("Customer", back_populates="resource_metrics")
    
    # Indexes
    __table_args__ = (
        Index(
            "ix_resource_metrics_agent_instance",
            "agent_id", "instance_id"
        ),
        Index(
            "ix_resource_metrics_customer_type",
            "customer_id", "resource_type"
        ),
        Index(
            "ix_resource_metrics_instance_timestamp",
            "instance_id", "timestamp"
        ),
        Index(
            "ix_resource_metrics_type_name",
            "resource_type", "metric_name"
        ),
    )
    
    def __repr__(self):
        return (
            f"<ResourceMetric(id={self.id}, "
            f"instance={self.instance_id}, type={self.resource_type}, "
            f"metric={self.metric_name}, value={self.metric_value})>"
        )


class ScalingEvent(Base):
    """
    Tracks auto-scaling events
    
    Records all scaling decisions (up/down), their triggers, outcomes,
    and effects on the system.
    """
    __tablename__ = "scaling_events"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique scaling event identifier"
    )
    
    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent that executed scaling"
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Customer this scaling event belongs to"
    )
    workflow_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Link to workflow that triggered scaling"
    )
    
    # Event Details
    event_type = Column(
        SQLEnum(ScalingEventType, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Type of scaling event"
    )
    trigger_reason = Column(
        String(500),
        nullable=False,
        comment="Why scaling was triggered: high_gpu_util, low_cpu_util, etc."
    )
    
    # State Changes
    before_state = Column(
        JSONB,
        nullable=False,
        comment="State before scaling: instance_count, avg_utilization, etc."
    )
    after_state = Column(
        JSONB,
        nullable=False,
        comment="State after scaling: new_instance_count, new_utilization, etc."
    )
    
    # Outcome
    success = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether scaling succeeded"
    )
    error_details = Column(
        JSONB,
        nullable=True,
        comment="Error details if scaling failed"
    )
    
    # Timing
    executed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When scaling was initiated"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When scaling completed (or failed)"
    )
    
    # Additional Data
    scaling_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional context: cost_impact, performance_impact, etc."
    )
    
    # Audit
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    
    # Relationships
    agent = relationship("Agent", back_populates="scaling_events")
    customer = relationship("Customer", back_populates="scaling_events")
    workflow = relationship(
        "WorkflowExecution",
        foreign_keys=[workflow_execution_id],
        backref="scaling_events"
    )
    
    # Indexes
    __table_args__ = (
        Index(
            "ix_scaling_events_agent_type",
            "agent_id", "event_type"
        ),
        Index(
            "ix_scaling_events_customer_success",
            "customer_id", "success"
        ),
        Index(
            "ix_scaling_events_workflow",
            "workflow_execution_id"
        ),
    )
    
    def __repr__(self):
        return (
            f"<ScalingEvent(id={self.id}, type={self.event_type}, "
            f"success={self.success}, executed_at={self.executed_at})>"
        )
    
    @property
    def duration_seconds(self):
        """Calculate scaling duration in seconds"""
        if self.completed_at and self.executed_at:
            return (self.completed_at - self.executed_at).total_seconds()
        return None

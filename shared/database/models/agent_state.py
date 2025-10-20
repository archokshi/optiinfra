"""
Agent state and configuration models.
Extends the core schema with agent-specific data.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database.models.core import Base


# ============================================================================
# ENUMS
# ============================================================================

class ConfigType(str, PyEnum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"


class AgentStatusDetail(str, PyEnum):
    """Detailed agent status"""
    IDLE = "idle"
    BUSY = "busy"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"


class MetricType(str, PyEnum):
    """Metric value types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


# ============================================================================
# MODELS
# ============================================================================

class AgentConfig(Base):
    """
    Agent configuration storage.
    
    Stores key-value configuration for each agent.
    Examples: thresholds, timeouts, feature flags, optimization parameters.
    """
    __tablename__ = "agent_configs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique config entry identifier"
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent this config belongs to"
    )
    config_key = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Configuration key (e.g., 'kv_cache_size')"
    )
    config_value = Column(
        Text,
        nullable=False,
        comment="Configuration value (stored as string)"
    )
    config_type = Column(
        Enum(ConfigType, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ConfigType.STRING,
        comment="Type of configuration value"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of this config"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Config creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )

    # Relationships
    agent = relationship("Agent", back_populates="configs")

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_agent_config_agent", "agent_id"),
        Index("idx_agent_config_key", "config_key"),
        Index("idx_agent_config_agent_key", "agent_id", "config_key"),
        UniqueConstraint("agent_id", "config_key", name="uq_agent_config"),
    )

    def __repr__(self):
        return f"<AgentConfig(agent_id={self.agent_id}, key='{self.config_key}', type={self.config_type.value})>"


class AgentState(Base):
    """
    Real-time agent state.
    
    Tracks the current operational state of each agent:
    - Active workflows
    - Resource locks
    - Current status
    - Resource usage
    """
    __tablename__ = "agent_states"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique state identifier"
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Agent this state belongs to (one-to-one)"
    )
    current_status = Column(
        Enum(AgentStatusDetail, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AgentStatusDetail.IDLE,
        index=True,
        comment="Current detailed status"
    )
    active_workflows = Column(
        JSONB,
        nullable=False,
        default=[],
        comment="List of currently active workflow IDs"
    )
    locks = Column(
        JSONB,
        nullable=False,
        default={},
        comment="Resource locks held by this agent"
    )
    last_activity = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Last activity timestamp"
    )
    resource_usage = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Current resource usage (CPU, memory, etc.)"
    )
    state_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        default={},
        comment="Additional state metadata"
    )
    
    # Workflow Tracking (FOUNDATION-0.2c)
    current_workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Currently executing workflow (if any)"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="State creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )

    # Relationships
    agent = relationship("Agent", back_populates="state", uselist=False)
    current_workflow = relationship("WorkflowExecution", foreign_keys=[current_workflow_id])

    # Indexes
    __table_args__ = (
        Index("idx_agent_state_agent", "agent_id"),
        Index("idx_agent_state_status", "current_status"),
        Index("idx_agent_state_activity", "last_activity"),
    )

    def __repr__(self):
        return f"<AgentState(agent_id={self.agent_id}, status={self.current_status.value})>"


class AgentCapability(Base):
    """
    Agent capability definitions.
    
    Tracks what each agent can do, with version information.
    Example: Cost Agent can do "spot_migration" v1.2.0
    """
    __tablename__ = "agent_capabilities"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique capability identifier"
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent this capability belongs to"
    )
    capability_name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Capability name (e.g., 'spot_migration')"
    )
    capability_version = Column(
        String(50),
        nullable=False,
        default="1.0.0",
        comment="Capability version (semver)"
    )
    enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this capability is currently enabled"
    )
    config = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Capability-specific configuration"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Capability registration timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )

    # Relationships
    agent = relationship("Agent", back_populates="capability_details")

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_agent_cap_agent", "agent_id"),
        Index("idx_agent_cap_name", "capability_name"),
        Index("idx_agent_cap_enabled", "enabled"),
        Index("idx_agent_cap_agent_name", "agent_id", "capability_name"),
        UniqueConstraint("agent_id", "capability_name", name="uq_agent_capability"),
    )

    def __repr__(self):
        return f"<AgentCapability(agent_id={self.agent_id}, name='{self.capability_name}', version='{self.capability_version}')>"


class AgentMetric(Base):
    """
    Agent-level performance metrics.
    
    Time-series metrics for agent performance:
    - Request counts
    - Success rates
    - Processing times
    - Resource usage
    """
    __tablename__ = "agent_metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique metric identifier"
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent this metric belongs to"
    )
    metric_name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Metric name (e.g., 'requests_total')"
    )
    metric_value = Column(
        Float,
        nullable=False,
        comment="Metric value"
    )
    metric_type = Column(
        Enum(MetricType, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=MetricType.GAUGE,
        comment="Type of metric"
    )
    tags = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Metric tags/labels"
    )
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Metric recording timestamp"
    )

    # Relationships
    agent = relationship("Agent", back_populates="metrics")

    # Indexes
    __table_args__ = (
        Index("idx_agent_metric_agent", "agent_id"),
        Index("idx_agent_metric_name", "metric_name"),
        Index("idx_agent_metric_recorded", "recorded_at"),
        Index("idx_agent_metric_agent_name", "agent_id", "metric_name"),
        Index("idx_agent_metric_agent_recorded", "agent_id", "recorded_at"),
    )

    def __repr__(self):
        return f"<AgentMetric(agent_id={self.agent_id}, name='{self.metric_name}', value={self.metric_value})>"

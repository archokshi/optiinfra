"""
Database models package.
"""
from shared.database.models.core import (
    Base,
    # Enums
    CustomerPlan,
    CustomerStatus,
    AgentType,
    AgentStatus,
    EventSeverity,
    RecommendationPriority,
    RecommendationStatus,
    ApprovalStatus,
    OptimizationStatus,
    # Models
    Customer,
    Agent,
    Event,
    Recommendation,
    Approval,
    Optimization,
)

# Agent State Models (FOUNDATION-0.2b)
from shared.database.models.agent_state import (
    # Enums
    ConfigType,
    AgentStatusDetail,
    MetricType,
    # Models
    AgentConfig,
    AgentState,
    AgentCapability,
    AgentMetric,
)

# Workflow history models (0.2c)
from shared.database.models.workflow_history import (
    WorkflowExecution,
    WorkflowStep,
    WorkflowArtifact,
    # Enums
    WorkflowType,
    WorkflowStatus,
    StepStatus,
    ArtifactType,
)

__all__ = [
    "Base",
    # Core Enums
    "CustomerPlan",
    "CustomerStatus",
    "AgentType",
    "AgentStatus",
    "EventSeverity",
    "RecommendationPriority",
    "RecommendationStatus",
    "ApprovalStatus",
    "OptimizationStatus",
    # Agent State Enums
    "ConfigType",
    "AgentStatusDetail",
    "MetricType",
    # Workflow History Enums
    "WorkflowType",
    "WorkflowStatus",
    "StepStatus",
    "ArtifactType",
    # Core Models
    "Customer",
    "Agent",
    "Event",
    "Recommendation",
    "Approval",
    "Optimization",
    # Agent State Models
    "AgentConfig",
    "AgentState",
    "AgentCapability",
    "AgentMetric",
    # Workflow History Models
    "WorkflowExecution",
    "WorkflowStep",
    "WorkflowArtifact",
]

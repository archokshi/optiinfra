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
]

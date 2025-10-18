"""
Workflow state definitions for LangGraph.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class ResourceInfo(TypedDict):
    """Information about a cloud resource"""

    resource_id: str
    resource_type: str
    provider: str
    region: str
    cost_per_month: float
    utilization: float
    tags: Dict[str, str]


class AnalysisResult(TypedDict):
    """Results from resource analysis"""

    waste_detected: bool
    waste_amount: float
    waste_percentage: float
    inefficiency_reasons: List[str]
    metrics: Dict[str, Any]


class Recommendation(TypedDict):
    """Cost optimization recommendation"""

    recommendation_id: str
    recommendation_type: str  # "spot_migration", "right_sizing", "reserved_instance"
    resource_id: str
    description: str
    estimated_savings: float
    confidence_score: float
    implementation_steps: List[str]


class CostOptimizationState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    This is the shared state between all nodes.
    """

    # Input
    resources: List[ResourceInfo]
    request_id: str
    timestamp: datetime

    # Analysis results
    analysis_results: Optional[List[AnalysisResult]]
    total_waste_detected: float

    # Recommendations
    recommendations: Optional[List[Recommendation]]
    total_potential_savings: float

    # Summary
    summary: Optional[str]

    # Metadata
    workflow_status: str  # "pending", "analyzing", "recommending", "complete", "failed"
    error_message: Optional[str]


# NEW - Spot Migration State Definitions


class MigrationPhase(str, Enum):
    """Migration phases for gradual rollout"""

    PENDING = "pending"
    ANALYZING = "analyzing"
    COORDINATING = "coordinating"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING_10 = "executing_10_percent"
    EXECUTING_50 = "executing_50_percent"
    EXECUTING_100 = "executing_100_percent"
    MONITORING = "monitoring"
    COMPLETE = "complete"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class EC2Instance(TypedDict):
    """EC2 instance information"""

    instance_id: str
    instance_type: str
    region: str
    availability_zone: str
    state: str  # running, stopped, etc.
    launch_time: datetime
    cost_per_month: float
    spot_eligible: bool
    workload_type: str  # stable, variable, burst
    utilization_metrics: Dict[str, float]


class SpotOpportunity(TypedDict):
    """Identified spot migration opportunity"""

    instance_id: str
    current_cost: float
    spot_cost: float
    savings_amount: float
    savings_percentage: float
    risk_level: str  # low, medium, high
    interruption_rate: float
    recommended_capacity: int
    migration_strategy: str


class AgentApproval(TypedDict):
    """Approval from other agents"""

    agent_type: str  # performance, resource, application
    approved: bool
    confidence: float
    concerns: List[str]
    recommendations: List[str]


class MigrationExecution(TypedDict):
    """Migration execution status"""

    phase: str  # 10%, 50%, 100%
    started_at: datetime
    completed_at: Optional[datetime]
    instances_migrated: int
    instances_total: int
    success_rate: float
    errors: List[str]


class QualityMetrics(TypedDict):
    """Quality metrics during migration"""

    baseline_latency: float
    current_latency: float
    baseline_error_rate: float
    current_error_rate: float
    quality_score: float
    degradation_percentage: float
    acceptable: bool


class SpotMigrationState(TypedDict):
    """
    Complete state for spot migration workflow.
    This extends the basic cost optimization state.
    """

    # Request info
    request_id: str
    customer_id: str
    timestamp: datetime

    # Analysis phase
    ec2_instances: List[EC2Instance]
    spot_opportunities: Optional[List[SpotOpportunity]]
    total_savings: float

    # Coordination phase
    performance_approval: Optional[AgentApproval]
    resource_approval: Optional[AgentApproval]
    application_approval: Optional[AgentApproval]
    coordination_complete: bool

    # Approval phase
    customer_approved: bool
    approval_timestamp: Optional[datetime]

    # Execution phase
    migration_phase: str
    execution_10: Optional[MigrationExecution]
    execution_50: Optional[MigrationExecution]
    execution_100: Optional[MigrationExecution]

    # Monitoring phase
    quality_baseline: Optional[QualityMetrics]
    quality_current: Optional[QualityMetrics]
    rollback_triggered: bool

    # Result
    workflow_status: str
    final_savings: float
    migration_duration: Optional[float]
    success: bool
    error_message: Optional[str]

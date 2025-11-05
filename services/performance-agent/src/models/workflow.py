"""
Workflow State Models

Models for LangGraph workflow state.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models.analysis import AnalysisResult
from src.models.optimization import OptimizationPlan


class WorkflowStatus(str, Enum):
    """Workflow status."""
    PENDING = "pending"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    OPTIMIZING = "optimizing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROLLING_OUT = "rolling_out"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RolloutStage(str, Enum):
    """Rollout stage."""
    STAGE_10 = "10%"
    STAGE_50 = "50%"
    STAGE_100 = "100%"


class RolloutStatus(BaseModel):
    """Status of a rollout stage."""
    
    stage: RolloutStage
    status: str = Field(..., description="success, failed, in_progress")
    started_at: datetime
    completed_at: Optional[datetime] = None
    health_score_before: float
    health_score_after: Optional[float] = None
    metrics_snapshot: Optional[Dict[str, Any]] = None
    issues: List[str] = Field(default_factory=list)


class WorkflowState(BaseModel):
    """Complete workflow state."""
    
    # Workflow metadata
    workflow_id: str
    instance_id: str
    instance_type: str
    status: WorkflowStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Analysis results
    analysis_result: Optional[AnalysisResult] = None
    
    # Optimization plan
    optimization_plan: Optional[OptimizationPlan] = None
    
    # Approval
    requires_approval: bool = True
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Rollout tracking
    current_stage: Optional[RolloutStage] = None
    rollout_history: List[RolloutStatus] = Field(default_factory=list)
    
    # Configuration
    original_config: Optional[Dict[str, Any]] = None
    applied_config: Optional[Dict[str, Any]] = None
    
    # Monitoring
    health_threshold: float = 0.9  # Rollback if health drops below 90%
    monitoring_duration_seconds: int = 300  # 5 minutes per stage
    
    # Results
    final_health_score: Optional[float] = None
    total_improvement: Optional[str] = None
    error_message: Optional[str] = None


class WorkflowRequest(BaseModel):
    """Request to start a workflow."""
    
    instance_id: str
    instance_type: str
    requires_approval: bool = True
    auto_rollout: bool = False  # If True, skip approval
    monitoring_duration_seconds: int = 300
    health_threshold: float = 0.9

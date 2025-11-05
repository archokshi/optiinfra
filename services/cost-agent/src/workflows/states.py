"""
State definitions for Cost Agent workflows using LangGraph.

Each workflow has its own state schema that extends the base OptimizationState.
These states are used by LangGraph for state management and persistence.
"""

from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime


class OptimizationState(TypedDict):
    """Base state for all optimization workflows"""
    
    # Identification
    customer_id: str
    workflow_id: str
    workflow_type: str
    
    # Input data
    infrastructure: Dict[str, Any]
    current_costs: Dict[str, float]
    constraints: Dict[str, Any]
    
    # Analysis phase
    analysis_results: Optional[Dict[str, Any]]
    
    # Recommendation phase
    recommendations: Optional[List[Dict[str, Any]]]
    estimated_savings: Optional[float]
    confidence_score: Optional[float]
    
    # Approval phase
    requires_approval: bool
    approval_status: Optional[str]  # "pending", "approved", "rejected"
    approval_reason: Optional[str]
    
    # Execution phase
    execution_results: Optional[Dict[str, Any]]
    execution_status: Optional[str]  # "running", "success", "failed"
    
    # Success tracking
    success: bool
    
    # Learning phase
    outcome: Optional[Dict[str, Any]]
    learned: bool
    
    # Error handling
    errors: List[str]
    rollback_needed: bool
    rollback_completed: bool
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class SpotMigrationState(OptimizationState):
    """State for spot instance migration workflow"""
    
    # Spot-specific fields
    instances_to_migrate: Optional[List[Dict[str, Any]]]
    spot_availability: Optional[Dict[str, Any]]
    migration_plan: Optional[Dict[str, Any]]
    fallback_strategy: Optional[str]
    
    # Migration execution
    migrated_instances: List[str]
    failed_instances: List[str]
    interruption_rate: Optional[float]


class ReservedInstanceState(OptimizationState):
    """State for reserved instance optimization workflow"""
    
    # RI-specific fields
    usage_patterns: Optional[Dict[str, Any]]
    ri_recommendations: Optional[List[Dict[str, Any]]]
    commitment_period: Optional[str]  # "1-year", "3-year"
    payment_option: Optional[str]  # "all-upfront", "partial", "no-upfront"
    
    # Purchase tracking
    purchased_ris: List[Dict[str, Any]]
    total_upfront_cost: Optional[float]


class RightSizingState(OptimizationState):
    """State for instance right-sizing workflow"""
    
    # Right-sizing specific fields
    utilization_data: Optional[Dict[str, Any]]
    resize_recommendations: Optional[List[Dict[str, Any]]]
    
    # Resize execution
    resized_instances: List[Dict[str, Any]]
    performance_impact: Optional[Dict[str, Any]]


def create_initial_state(
    customer_id: str,
    workflow_type: str,
    infrastructure: Dict[str, Any],
    current_costs: Dict[str, float],
    constraints: Optional[Dict[str, Any]] = None
) -> OptimizationState:
    """
    Create initial state for a workflow
    
    Args:
        customer_id: Customer identifier
        workflow_type: Type of workflow (spot_migration, reserved_instance, right_sizing)
        infrastructure: Infrastructure data
        current_costs: Current cost data
        constraints: Optional constraints
        
    Returns:
        Initial OptimizationState
    """
    import uuid
    
    return OptimizationState(
        customer_id=customer_id,
        workflow_id=str(uuid.uuid4()),
        workflow_type=workflow_type,
        infrastructure=infrastructure,
        current_costs=current_costs,
        constraints=constraints or {},
        analysis_results=None,
        recommendations=None,
        estimated_savings=None,
        confidence_score=None,
        requires_approval=True,
        approval_status=None,
        approval_reason=None,
        execution_results=None,
        execution_status=None,
        success=False,
        outcome=None,
        learned=False,
        errors=[],
        rollback_needed=False,
        rollback_completed=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={}
    )

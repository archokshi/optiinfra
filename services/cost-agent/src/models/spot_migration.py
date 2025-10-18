"""
Request/response models for spot migration API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SpotMigrationRequest(BaseModel):
    """Request to start spot migration"""

    customer_id: str = Field(..., description="Customer identifier")
    instance_ids: Optional[List[str]] = Field(
        None,
        description="Specific instances to migrate (optional, will analyze all if not provided)",
    )
    auto_approve: bool = Field(
        False,
        description="Auto-approve migration (for demo purposes)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "customer-123",
                "instance_ids": None,
                "auto_approve": True,
            }
        }


class SpotOpportunityResponse(BaseModel):
    """Single spot opportunity"""

    instance_id: str
    current_cost: float
    spot_cost: float
    savings_amount: float
    savings_percentage: float
    risk_level: str


class AgentApprovalResponse(BaseModel):
    """Agent approval response"""

    agent_type: str
    approved: bool
    confidence: float
    concerns: List[str]
    recommendations: List[str]


class MigrationPhaseResponse(BaseModel):
    """Migration phase execution"""

    phase: str
    started_at: datetime
    completed_at: Optional[datetime]
    instances_migrated: int
    instances_total: int
    success_rate: float
    errors: List[str]


class SpotMigrationResponse(BaseModel):
    """Response from spot migration"""

    request_id: str
    customer_id: str
    timestamp: datetime

    # Analysis
    instances_analyzed: int
    opportunities_found: int
    total_savings: float
    opportunities: List[SpotOpportunityResponse]

    # Coordination
    performance_approval: Optional[AgentApprovalResponse]
    resource_approval: Optional[AgentApprovalResponse]
    application_approval: Optional[AgentApprovalResponse]

    # Execution
    execution_10_percent: Optional[MigrationPhaseResponse]
    execution_50_percent: Optional[MigrationPhaseResponse]
    execution_100_percent: Optional[MigrationPhaseResponse]

    # Results
    workflow_status: str
    final_savings: float
    success: bool
    error_message: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "spot-20251018120000",
                "customer_id": "customer-123",
                "timestamp": "2025-10-18T12:00:00Z",
                "instances_analyzed": 10,
                "opportunities_found": 6,
                "total_savings": 2450.00,
                "workflow_status": "complete",
                "final_savings": 2450.00,
                "success": True,
            }
        }

"""
Request/response models for spot migration API.
Extended with security validation for PHASE1-1.6.
"""

from datetime import datetime
from typing import List, Optional
import re

from pydantic import BaseModel, Field, field_validator, ConfigDict


class SpotMigrationRequest(BaseModel):
    """
    Request to start spot migration.
    Includes production security validation.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_id": "customer-123",
                "cloud_provider": "aws",
                "instance_ids": ["i-1234567890abcdef0"],
                "auto_approve": False,
            }
        }
    )

    customer_id: str = Field(
        ...,
        description="Customer identifier (alphanumeric, dash, underscore only)",
        min_length=1,
        max_length=64,
        pattern=r'^[a-zA-Z0-9_-]+$'
    )
    
    cloud_provider: str = Field(
        default="aws",
        description="Cloud provider (aws, gcp, or azure)",
        pattern=r'^(aws|gcp|azure)$'
    )
    
    instance_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific instances to migrate (optional, will analyze all if not provided)",
        max_length=1000
    )
    
    auto_approve: bool = Field(
        default=False,
        description="Auto-approve migration (for demo purposes only)",
    )

    @field_validator('customer_id')
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        """Validate customer ID format"""
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', v):
            raise ValueError(
                "Customer ID must be 1-64 characters, alphanumeric with dash/underscore only"
            )
        return v
    
    @field_validator('instance_ids')
    @classmethod
    def validate_instance_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate instance ID formats"""
        if v is None:
            return v
        
        if len(v) > 1000:
            raise ValueError("Maximum 1000 instance IDs allowed")
        
        for instance_id in v:
            # AWS: i-xxxxxxxxxxxxxxxxx (8-17 hex chars)
            # GCP: instance-name (alphanumeric with dash)
            # Azure: vm-name (alphanumeric with dash/underscore)
            if not re.match(r'^[a-zA-Z0-9_-]{1,255}$', instance_id):
                raise ValueError(
                    f"Invalid instance ID format: {instance_id}. "
                    "Must be 1-255 alphanumeric characters with dash/underscore"
                )
        
        return v


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

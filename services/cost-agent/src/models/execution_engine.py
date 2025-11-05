"""
Pydantic models for Execution Engine.

Type-safe models for execution requests, responses, and data structures.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    """Execution status values."""
    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    """Risk level values."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionRequest(BaseModel):
    """Request to execute a recommendation."""
    recommendation_id: str = Field(..., description="Recommendation to execute")
    dry_run: bool = Field(default=False, description="Simulate without making changes")
    auto_approve: bool = Field(default=False, description="Skip approval step")
    scheduled_time: Optional[datetime] = Field(None, description="Schedule for later")
    force: bool = Field(default=False, description="Force execution despite warnings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_id": "rec-123",
                "dry_run": False,
                "auto_approve": True
            }
        }


class ExecutionResult(BaseModel):
    """Result of an execution."""
    execution_id: str
    recommendation_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    success: bool
    error_message: Optional[str] = None
    rollback_available: bool = True
    actual_savings: Optional[float] = None
    execution_log: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec-abc123",
                "recommendation_id": "rec-123",
                "status": "completed",
                "started_at": "2025-10-22T20:00:00Z",
                "completed_at": "2025-10-22T20:05:00Z",
                "duration_seconds": 300,
                "success": True,
                "rollback_available": True,
                "execution_log": ["Started execution", "Validated", "Executed", "Completed"]
            }
        }


class ValidationResult(BaseModel):
    """Result of pre-execution validation."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    risk_level: RiskLevel
    estimated_duration_minutes: int = Field(ge=0)
    requires_approval: bool = True
    blocking_issues: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "errors": [],
                "warnings": ["Resource will be terminated"],
                "risk_level": "low",
                "estimated_duration_minutes": 5,
                "requires_approval": True
            }
        }


class ExecutionStatusResponse(BaseModel):
    """Detailed execution status."""
    execution_id: str
    recommendation_id: str
    status: ExecutionStatus
    progress_percent: int = Field(ge=0, le=100)
    current_step: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    execution_log: List[str] = []
    can_cancel: bool = True
    can_rollback: bool = False


class RollbackPlan(BaseModel):
    """Plan for rolling back an execution."""
    execution_id: str
    rollback_steps: List[str]
    estimated_duration_minutes: int = Field(ge=0)
    risk_level: RiskLevel
    requires_approval: bool = False
    warnings: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec-abc123",
                "rollback_steps": [
                    "Stop new instance",
                    "Restore from backup",
                    "Verify restoration"
                ],
                "estimated_duration_minutes": 10,
                "risk_level": "low",
                "requires_approval": False
            }
        }


class RollbackResult(BaseModel):
    """Result of a rollback operation."""
    execution_id: str
    success: bool
    message: str
    rollback_started_at: datetime
    rollback_completed_at: Optional[datetime] = None
    rollback_log: List[str] = []


class ExecutionListResponse(BaseModel):
    """List of executions."""
    total: int
    executions: List[ExecutionStatusResponse]
    page: int = 1
    page_size: int = 50


class ExecutorResult(BaseModel):
    """Result from an individual executor."""
    success: bool
    message: str
    details: Dict[str, Any] = {}
    changes_made: List[str] = []
    rollback_info: Dict[str, Any] = {}

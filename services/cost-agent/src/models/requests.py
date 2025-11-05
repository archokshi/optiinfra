"""
API Request Models.

Pydantic models for API request validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# Enums
class CloudProvider(str, Enum):
    """Cloud provider types."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class RecommendationType(str, Enum):
    """Recommendation types."""
    SPOT_MIGRATION = "spot_migration"
    RIGHTSIZING = "rightsizing"
    RESERVED_INSTANCE = "reserved_instance"
    STORAGE_OPTIMIZATION = "storage_optimization"


# Cost Collection Requests
class GetCostsRequest(BaseModel):
    """Request to get costs."""
    customer_id: str = Field(..., description="Customer ID")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    granularity: Optional[str] = Field("daily", description="Granularity (daily, weekly, monthly)")
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "start_date": "2025-10-01",
                "end_date": "2025-10-23",
                "granularity": "daily"
            }
        }


class ExportCostsRequest(BaseModel):
    """Request to export costs."""
    customer_id: str = Field(..., description="Customer ID")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    format: str = Field("csv", description="Export format (csv, json, excel)")
    include_details: bool = Field(True, description="Include detailed breakdown")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "start_date": "2025-10-01",
                "end_date": "2025-10-23",
                "format": "csv",
                "include_details": True
            }
        }


# Analysis Requests
class AnalyzeCostsRequest(BaseModel):
    """Request to analyze costs."""
    customer_id: str = Field(..., description="Customer ID")
    lookback_days: int = Field(30, description="Days to look back", ge=1, le=365)
    detect_anomalies: bool = Field(True, description="Detect anomalies")
    forecast_days: int = Field(30, description="Days to forecast", ge=1, le=90)
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "lookback_days": 30,
                "detect_anomalies": True,
                "forecast_days": 30
            }
        }


class GetAnomaliesRequest(BaseModel):
    """Request to get anomalies."""
    customer_id: str = Field(..., description="Customer ID")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    severity: Optional[str] = Field(None, description="Filter by severity (low, medium, high)")
    limit: int = Field(50, description="Maximum results", ge=1, le=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "severity": "high",
                "limit": 50
            }
        }


# Recommendation Requests
class GenerateRecommendationsRequest(BaseModel):
    """Request to generate recommendations."""
    customer_id: str = Field(..., description="Customer ID")
    lookback_days: int = Field(30, description="Days to analyze", ge=7, le=365)
    recommendation_types: Optional[List[RecommendationType]] = Field(
        None, 
        description="Types of recommendations to generate"
    )
    min_savings: Optional[float] = Field(
        None, 
        description="Minimum monthly savings threshold",
        ge=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "lookback_days": 30,
                "recommendation_types": ["spot_migration", "rightsizing"],
                "min_savings": 100.0
            }
        }


class ApproveRecommendationRequest(BaseModel):
    """Request to approve a recommendation."""
    approved_by: str = Field(..., description="User who approved")
    notes: Optional[str] = Field(None, description="Approval notes")
    scheduled_execution: Optional[datetime] = Field(
        None,
        description="Schedule execution for later"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "approved_by": "admin@example.com",
                "notes": "Approved for production deployment",
                "scheduled_execution": "2025-10-24T10:00:00Z"
            }
        }


class RejectRecommendationRequest(BaseModel):
    """Request to reject a recommendation."""
    rejected_by: str = Field(..., description="User who rejected")
    reason: str = Field(..., description="Rejection reason")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rejected_by": "admin@example.com",
                "reason": "Risk too high for production environment"
            }
        }


# Execution Requests
class ExecuteRecommendationRequest(BaseModel):
    """Request to execute a recommendation."""
    recommendation_id: str = Field(..., description="Recommendation ID")
    dry_run: bool = Field(False, description="Perform dry run without actual changes")
    execute_immediately: bool = Field(True, description="Execute immediately or schedule")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled execution time")
    notification_emails: Optional[List[str]] = Field(
        None,
        description="Email addresses for notifications"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_id": "rec-123",
                "dry_run": False,
                "execute_immediately": True,
                "notification_emails": ["admin@example.com"]
            }
        }


class RollbackExecutionRequest(BaseModel):
    """Request to rollback an execution."""
    reason: str = Field(..., description="Rollback reason")
    rollback_by: str = Field(..., description="User initiating rollback")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Unexpected performance degradation",
                "rollback_by": "admin@example.com"
            }
        }


# Learning Loop Requests
class TrackOutcomeRequest(BaseModel):
    """Request to track execution outcome."""
    recommendation_id: str = Field(..., description="Recommendation ID")
    execution_id: str = Field(..., description="Execution ID")
    actual_savings: float = Field(..., description="Actual savings achieved")
    execution_success: bool = Field(..., description="Whether execution succeeded")
    metrics: Optional[dict] = Field(None, description="Additional metrics")
    feedback: Optional[str] = Field(None, description="User feedback")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_id": "rec-123",
                "execution_id": "exec-456",
                "actual_savings": 1250.50,
                "execution_success": True,
                "metrics": {
                    "downtime_minutes": 0,
                    "performance_impact": "none"
                },
                "feedback": "Execution went smoothly"
            }
        }


# Bulk Operations Requests
class BulkGenerateRequest(BaseModel):
    """Request to generate recommendations in bulk."""
    customer_ids: List[str] = Field(..., description="List of customer IDs")
    lookback_days: int = Field(30, description="Days to look back for analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_ids": ["cust-123", "cust-456", "cust-789"],
                "lookback_days": 30
            }
        }


class BulkExecuteRequest(BaseModel):
    """Request to execute recommendations in bulk."""
    recommendation_ids: List[str] = Field(..., description="List of recommendation IDs")
    dry_run: bool = Field(False, description="Perform dry run without actual execution")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_ids": ["rec-123", "rec-456", "rec-789"],
                "dry_run": False
            }
        }


# Webhook Requests
class RegisterWebhookRequest(BaseModel):
    """Request to register a webhook."""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret for verification")
    description: Optional[str] = Field(None, description="Webhook description")
    
    @validator('url')
    def url_must_be_https(cls, v):
        if not v.startswith('https://'):
            raise ValueError('Webhook URL must use HTTPS')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/webhooks/optiinfra",
                "events": ["recommendation.created", "execution.completed"],
                "secret": "whsec_1234567890abcdef",
                "description": "Production webhook"
            }
        }

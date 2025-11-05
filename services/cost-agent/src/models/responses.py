"""
API Response Models.

Pydantic models for API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class ExecutionStatus(str, Enum):
    """Execution status types."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RecommendationStatus(str, Enum):
    """Recommendation status types."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


# Base Response
class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = Field(..., description="Whether request succeeded")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


# Cost Responses
class CostBreakdown(BaseModel):
    """Cost breakdown by service/resource."""
    service: str = Field(..., description="Service name")
    cost: float = Field(..., description="Cost amount")
    percentage: float = Field(..., description="Percentage of total")
    trend: Optional[str] = Field(None, description="Trend (increasing, decreasing, stable)")


class CostResponse(BaseModel):
    """Cost data response."""
    customer_id: str = Field(..., description="Customer ID")
    provider: str = Field(..., description="Cloud provider")
    total_cost: float = Field(..., description="Total cost")
    currency: str = Field("USD", description="Currency")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    breakdown: List[CostBreakdown] = Field(..., description="Cost breakdown")
    daily_costs: Optional[List[Dict[str, Any]]] = Field(None, description="Daily cost data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "provider": "aws",
                "total_cost": 15420.50,
                "currency": "USD",
                "start_date": "2025-10-01T00:00:00Z",
                "end_date": "2025-10-23T23:59:59Z",
                "breakdown": [
                    {"service": "EC2", "cost": 8500.00, "percentage": 55.1, "trend": "stable"},
                    {"service": "RDS", "cost": 4200.00, "percentage": 27.2, "trend": "increasing"}
                ]
            }
        }


# Analysis Responses
class AnomalyResponse(BaseModel):
    """Anomaly detection response."""
    id: str = Field(..., description="Anomaly ID")
    customer_id: str = Field(..., description="Customer ID")
    detected_at: datetime = Field(..., description="Detection timestamp")
    service: str = Field(..., description="Affected service")
    severity: str = Field(..., description="Severity (low, medium, high)")
    expected_cost: float = Field(..., description="Expected cost")
    actual_cost: float = Field(..., description="Actual cost")
    deviation_percentage: float = Field(..., description="Deviation percentage")
    description: str = Field(..., description="Anomaly description")
    recommended_actions: List[str] = Field(..., description="Recommended actions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "anom-123",
                "customer_id": "cust-123",
                "detected_at": "2025-10-23T10:00:00Z",
                "service": "EC2",
                "severity": "high",
                "expected_cost": 5000.00,
                "actual_cost": 7250.00,
                "deviation_percentage": 45.0,
                "description": "Unexpected spike in EC2 costs",
                "recommended_actions": ["Review instance usage", "Check for runaway processes"]
            }
        }


class ForecastResponse(BaseModel):
    """Cost forecast response."""
    customer_id: str = Field(..., description="Customer ID")
    forecast_period: str = Field(..., description="Forecast period")
    predicted_cost: float = Field(..., description="Predicted cost")
    confidence_interval: Dict[str, float] = Field(..., description="Confidence interval")
    daily_forecast: List[Dict[str, Any]] = Field(..., description="Daily forecast data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "forecast_period": "30_days",
                "predicted_cost": 16500.00,
                "confidence_interval": {"lower": 15000.00, "upper": 18000.00},
                "daily_forecast": [
                    {"date": "2025-10-24", "cost": 550.00}
                ]
            }
        }


# Recommendation Responses
class RecommendationResponse(BaseModel):
    """Recommendation response."""
    id: str = Field(..., description="Recommendation ID")
    customer_id: str = Field(..., description="Customer ID")
    type: str = Field(..., description="Recommendation type")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    status: RecommendationStatus = Field(..., description="Recommendation status")
    priority: str = Field(..., description="Priority (low, medium, high)")
    estimated_monthly_savings: float = Field(..., description="Estimated monthly savings")
    implementation_effort: str = Field(..., description="Implementation effort")
    risk_level: str = Field(..., description="Risk level")
    affected_resources: List[str] = Field(..., description="Affected resources")
    created_at: datetime = Field(..., description="Creation timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rec-123",
                "customer_id": "cust-123",
                "type": "spot_migration",
                "title": "Migrate 10 EC2 instances to Spot",
                "description": "Migrate non-critical workloads to Spot instances",
                "status": "pending",
                "priority": "high",
                "estimated_monthly_savings": 1200.00,
                "implementation_effort": "medium",
                "risk_level": "low",
                "affected_resources": ["i-123", "i-456"],
                "created_at": "2025-10-23T10:00:00Z"
            }
        }


# Execution Responses
class ExecutionResponse(BaseModel):
    """Execution response."""
    id: str = Field(..., description="Execution ID")
    recommendation_id: str = Field(..., description="Recommendation ID")
    customer_id: str = Field(..., description="Customer ID")
    status: ExecutionStatus = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds")
    success: bool = Field(..., description="Whether execution succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    changes_applied: List[Dict[str, Any]] = Field(..., description="Changes applied")
    rollback_available: bool = Field(..., description="Whether rollback is available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "exec-123",
                "recommendation_id": "rec-123",
                "customer_id": "cust-123",
                "status": "completed",
                "started_at": "2025-10-23T10:00:00Z",
                "completed_at": "2025-10-23T10:05:00Z",
                "duration_seconds": 300,
                "success": True,
                "changes_applied": [
                    {"resource": "i-123", "action": "migrated_to_spot"}
                ],
                "rollback_available": True
            }
        }


# Learning Loop Responses
class LearningMetricsResponse(BaseModel):
    """Learning metrics response."""
    customer_id: str = Field(..., description="Customer ID")
    total_recommendations: int = Field(..., description="Total recommendations")
    executed_recommendations: int = Field(..., description="Executed recommendations")
    success_rate: float = Field(..., description="Success rate percentage")
    average_savings_accuracy: float = Field(..., description="Average savings accuracy")
    total_actual_savings: float = Field(..., description="Total actual savings")
    total_predicted_savings: float = Field(..., description="Total predicted savings")
    top_performing_types: List[Dict[str, Any]] = Field(..., description="Top performing recommendation types")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "total_recommendations": 150,
                "executed_recommendations": 120,
                "success_rate": 95.5,
                "average_savings_accuracy": 87.3,
                "total_actual_savings": 45000.00,
                "total_predicted_savings": 51500.00,
                "top_performing_types": [
                    {"type": "spot_migration", "success_rate": 98.0}
                ]
            }
        }


class InsightResponse(BaseModel):
    """Learning insight response."""
    id: str = Field(..., description="Insight ID")
    type: str = Field(..., description="Insight type")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    confidence: float = Field(..., description="Confidence score (0-1)")
    impact: str = Field(..., description="Impact level (low, medium, high)")
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    supporting_data: Dict[str, Any] = Field(..., description="Supporting data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "insight-123",
                "type": "pattern",
                "title": "Spot migrations highly successful for batch workloads",
                "description": "Analysis shows 98% success rate for spot migrations on batch processing instances",
                "confidence": 0.95,
                "impact": "high",
                "recommendations": ["Prioritize spot migration for batch workloads"],
                "supporting_data": {"sample_size": 50, "success_count": 49}
            }
        }


# Bulk Operation Responses
class BulkOperationResponse(BaseModel):
    """Bulk operation response."""
    operation_id: str = Field(..., description="Bulk operation ID")
    status: str = Field(..., description="Operation status")
    total_items: int = Field(..., description="Total items to process")
    processed_items: int = Field(0, description="Items processed so far")
    successful_items: int = Field(0, description="Successfully processed items")
    failed_items: int = Field(0, description="Failed items")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    started_at: datetime = Field(..., description="Operation start time")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_id": "bulk-op-123",
                "status": "in_progress",
                "total_items": 100,
                "processed_items": 45,
                "successful_items": 43,
                "failed_items": 2,
                "errors": ["Failed to process rec-789: timeout"],
                "started_at": "2025-10-23T10:00:00Z",
                "estimated_completion": "2025-10-23T10:15:00Z"
            }
        }


# Webhook Responses
class WebhookResponse(BaseModel):
    """Webhook response."""
    id: str = Field(..., description="Webhook ID")
    customer_id: str = Field(..., description="Customer ID")
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Subscribed events")
    is_active: bool = Field(..., description="Whether webhook is active")
    description: Optional[str] = Field(None, description="Webhook description")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger timestamp")
    total_deliveries: int = Field(0, description="Total deliveries")
    failed_deliveries: int = Field(0, description="Failed deliveries")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "webhook-123",
                "customer_id": "cust-123",
                "url": "https://example.com/webhooks/optiinfra",
                "events": ["recommendation.created", "execution.completed"],
                "is_active": True,
                "description": "Production webhook",
                "created_at": "2025-10-23T10:00:00Z",
                "last_triggered_at": "2025-10-23T12:00:00Z",
                "total_deliveries": 150,
                "failed_deliveries": 2
            }
        }


# Notification Responses
class NotificationResponse(BaseModel):
    """Notification response."""
    id: str = Field(..., description="Notification ID")
    customer_id: str = Field(..., description="Customer ID")
    type: str = Field(..., description="Notification type")
    category: str = Field(..., description="Notification category")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    is_read: bool = Field(False, description="Whether notification is read")
    created_at: datetime = Field(..., description="Creation timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    action_url: Optional[str] = Field(None, description="Action URL")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "notif-123",
                "customer_id": "cust-123",
                "type": "warning",
                "category": "cost_alert",
                "title": "Cost Spike Detected",
                "message": "Your AWS costs increased by 45% in the last 24 hours",
                "is_read": False,
                "created_at": "2025-10-23T10:00:00Z",
                "action_url": "/analysis/anomalies",
                "metadata": {"cost_increase": 45.2}
            }
        }


# Error Response
class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "details": {"field": "start_date", "issue": "must be before end_date"},
                "timestamp": "2025-10-23T10:00:00Z",
                "request_id": "req-123"
            }
        }

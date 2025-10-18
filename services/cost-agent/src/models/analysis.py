"""
Request/response models for analysis endpoint.
"""

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class ResourceRequest(BaseModel):
    """Single resource to analyze"""

    resource_id: str = Field(..., description="Unique resource identifier")
    resource_type: str = Field(..., description="Type of resource (e.g., 'ec2', 'rds')")
    provider: str = Field(
        ..., description="Cloud provider (e.g., 'aws', 'gcp', 'azure')"
    )
    region: str = Field(..., description="Cloud region")
    cost_per_month: float = Field(..., ge=0, description="Monthly cost in USD")
    utilization: float = Field(
        ..., ge=0, le=1, description="Utilization percentage (0-1)"
    )
    tags: Dict[str, str] = Field(default_factory=dict, description="Resource tags")

    class Config:
        json_schema_extra = {
            "example": {
                "resource_id": "i-1234567890abcdef0",
                "resource_type": "ec2",
                "provider": "aws",
                "region": "us-east-1",
                "cost_per_month": 150.00,
                "utilization": 0.25,
                "tags": {"environment": "production", "team": "backend"},
            }
        }


class AnalysisRequest(BaseModel):
    """Request to analyze resources for cost optimization"""

    resources: List[ResourceRequest] = Field(
        ..., min_length=1, description="Resources to analyze"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resources": [
                    {
                        "resource_id": "i-1234567890abcdef0",
                        "resource_type": "ec2",
                        "provider": "aws",
                        "region": "us-east-1",
                        "cost_per_month": 150.00,
                        "utilization": 0.25,
                        "tags": {"environment": "production"},
                    }
                ]
            }
        }


class RecommendationResponse(BaseModel):
    """Single optimization recommendation"""

    recommendation_id: str
    recommendation_type: str
    resource_id: str
    description: str
    estimated_savings: float
    confidence_score: float
    implementation_steps: List[str]


class AnalysisResponse(BaseModel):
    """Response from cost optimization analysis"""

    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    resources_analyzed: int = Field(..., description="Number of resources analyzed")
    total_waste_detected: float = Field(..., description="Total waste in USD/month")
    total_potential_savings: float = Field(
        ..., description="Total potential savings in USD/month"
    )
    recommendations: List[RecommendationResponse] = Field(
        ..., description="Optimization recommendations"
    )
    summary: str = Field(..., description="Executive summary")
    workflow_status: str = Field(..., description="Workflow status")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req-abc123",
                "timestamp": "2025-10-18T10:00:00Z",
                "resources_analyzed": 5,
                "total_waste_detected": 375.00,
                "total_potential_savings": 375.00,
                "recommendations": [
                    {
                        "recommendation_id": "rec-xyz789",
                        "recommendation_type": "right_sizing",
                        "resource_id": "i-1234567890abcdef0",
                        "description": "Right-size instance to match utilization",
                        "estimated_savings": 75.00,
                        "confidence_score": 0.85,
                        "implementation_steps": [
                            "1. Analyze workload",
                            "2. Resize instance",
                        ],
                    }
                ],
                "summary": "Found 3 optimization opportunities...",
                "workflow_status": "complete",
            }
        }

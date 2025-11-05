"""
Pydantic schemas for input validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class CostAnalysisRequest(BaseModel):
    """Cost analysis request schema."""
    
    cloud_provider: str = Field(..., regex="^(aws|gcp|azure)$")
    time_range: str = Field(..., regex="^(1h|6h|12h|24h|7d|30d)$")
    resource_types: Optional[List[str]] = Field(default=None, max_items=50)
    filters: Optional[Dict[str, Any]] = Field(default=None)
    
    @validator("resource_types")
    def validate_resource_types(cls, v):
        """Validate resource types."""
        if v:
            allowed_types = ["compute", "storage", "network", "database", "other"]
            for rt in v:
                if rt not in allowed_types:
                    raise ValueError(f"Invalid resource type: {rt}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "cloud_provider": "aws",
                "time_range": "24h",
                "resource_types": ["compute", "storage"],
                "filters": {"region": "us-east-1"}
            }
        }


class PerformanceAnalysisRequest(BaseModel):
    """Performance analysis request schema."""
    
    application_id: str = Field(..., min_length=1, max_length=100)
    metric_types: List[str] = Field(..., min_items=1, max_items=20)
    time_range: str = Field(..., regex="^(1h|6h|12h|24h|7d|30d)$")
    
    @validator("metric_types")
    def validate_metric_types(cls, v):
        """Validate metric types."""
        allowed_metrics = [
            "latency", "throughput", "error_rate", "cpu", "memory",
            "disk_io", "network_io", "response_time"
        ]
        for metric in v:
            if metric not in allowed_metrics:
                raise ValueError(f"Invalid metric type: {metric}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "application_id": "app-123",
                "metric_types": ["latency", "throughput"],
                "time_range": "24h"
            }
        }


class RecommendationRequest(BaseModel):
    """Recommendation request schema."""
    
    context: str = Field(..., min_length=10, max_length=5000)
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")
    categories: Optional[List[str]] = Field(default=None, max_items=10)
    
    @validator("context")
    def validate_context(cls, v):
        """Validate context doesn't contain suspicious content."""
        from shared.middleware.request_validator import validator
        error = validator.validate_string(v, "context")
        if error:
            raise ValueError(error)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "context": "High CPU usage detected on production servers",
                "priority": "high",
                "categories": ["performance", "cost"]
            }
        }

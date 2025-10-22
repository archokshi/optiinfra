"""
Pydantic models for AWS cost collection API.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AWSCollectionRequest(BaseModel):
    """Request model for AWS cost collection"""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    services: Optional[List[str]] = Field(
        default=None,
        description="Services to collect (EC2, RDS, Lambda, S3)"
    )
    analyze: bool = Field(default=True, description="Run analysis after collection")
    dry_run: bool = Field(default=False, description="Dry run without storing data")


class AWSCollectionResponse(BaseModel):
    """Response model for AWS cost collection"""
    status: str = Field(..., description="Status: started, completed, failed")
    job_id: str = Field(..., description="Job ID for tracking")
    estimated_duration_seconds: Optional[int] = Field(
        default=None,
        description="Estimated duration"
    )
    services_to_collect: Optional[int] = None
    regions_to_scan: Optional[int] = None
    results: Optional[Dict[str, Any]] = None


class AWSCostQueryParams(BaseModel):
    """Query parameters for cost data"""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    service: Optional[str] = Field(default=None, description="Filter by service")
    region: Optional[str] = Field(default=None, description="Filter by region")
    include_instances: bool = Field(default=False, description="Include instance details")


class AWSCostResponse(BaseModel):
    """Response model for cost data"""
    time_period: Dict[str, str]
    total_cost: float
    by_service: Dict[str, float]
    by_region: Dict[str, float]
    daily_breakdown: List[Dict[str, Any]]


class AWSOpportunityQueryParams(BaseModel):
    """Query parameters for optimization opportunities"""
    min_savings: float = Field(default=0.0, description="Minimum savings threshold")
    service: Optional[str] = Field(default=None, description="Filter by service")
    opportunity_type: Optional[str] = Field(default=None, description="Filter by type")
    priority: Optional[str] = Field(default=None, description="Filter by priority")


class AWSOpportunity(BaseModel):
    """Model for optimization opportunity"""
    id: str
    type: str
    service: str
    resource_ids: List[str]
    description: str
    estimated_savings: float
    confidence: float
    priority: str
    effort: str
    risk: str


class AWSOpportunitiesResponse(BaseModel):
    """Response model for optimization opportunities"""
    total_opportunities: int
    total_potential_savings: float
    opportunities: List[AWSOpportunity]


class AWSAnalysisRequest(BaseModel):
    """Request model for comprehensive analysis"""
    analyze_trends: bool = Field(default=True, description="Analyze cost trends")
    detect_anomalies: bool = Field(default=True, description="Detect anomalies")
    forecast_30d: bool = Field(default=True, description="Generate 30-day forecast")


class AWSAnalysisResponse(BaseModel):
    """Response model for comprehensive analysis"""
    analysis_id: str
    timestamp: str
    summary: Dict[str, Any]
    trends: Optional[Dict[str, Any]] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    forecast: Optional[Dict[str, Any]] = None
    recommendations_summary: Dict[str, Any]


class AWSConnectionTestResponse(BaseModel):
    """Response model for connection test"""
    status: str
    account_id: Optional[str] = None
    regions: Optional[List[str]] = None
    cost_explorer_available: bool
    permissions_valid: bool
    error: Optional[str] = None


class AWSJobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str  # running, completed, failed
    progress: float
    current_service: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    estimated_completion: Optional[str] = None
    duration_seconds: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

"""
GCP Cost Collection Models

Pydantic models for GCP cost collection API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class GCPCollectionRequest(BaseModel):
    """Request model for GCP cost collection"""
    project_id: str = Field(..., description="GCP project ID")
    credentials_path: Optional[str] = Field(None, description="Path to service account credentials")
    billing_account_id: Optional[str] = Field(None, description="Billing account ID")
    billing_dataset: Optional[str] = Field(None, description="BigQuery billing dataset")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    lookback_days: int = Field(30, description="Days to analyze for utilization")
    include_utilization: bool = Field(True, description="Include utilization metrics")


class GCPTestConnectionRequest(BaseModel):
    """Request model for testing GCP connection"""
    project_id: str = Field(..., description="GCP project ID")
    credentials_path: Optional[str] = Field(None, description="Path to service account credentials")


class GCPCostBreakdown(BaseModel):
    """GCP cost breakdown"""
    by_service: Dict[str, float] = Field(default_factory=dict)
    by_project: Dict[str, float] = Field(default_factory=dict)
    daily: List[Dict[str, Any]] = Field(default_factory=list)


class GCPServiceMetrics(BaseModel):
    """Metrics for a GCP service"""
    total_instances: int = 0
    total_monthly_cost: float = 0.0
    instances: List[Dict[str, Any]] = Field(default_factory=list)


class GCPComputeMetrics(GCPServiceMetrics):
    """Compute Engine specific metrics"""
    idle_instances: int = 0
    underutilized_instances: int = 0
    preemptible_opportunities: int = 0
    disk_costs: Dict[str, Any] = Field(default_factory=dict)


class GCPSQLMetrics(GCPServiceMetrics):
    """Cloud SQL specific metrics"""
    idle_databases: int = 0
    ha_conversion_opportunities: int = 0
    storage_costs: Dict[str, Any] = Field(default_factory=dict)


class GCPFunctionsMetrics(GCPServiceMetrics):
    """Cloud Functions specific metrics"""
    total_functions: int = 0
    over_provisioned_functions: int = 0


class GCPStorageMetrics(BaseModel):
    """Cloud Storage metrics"""
    total_buckets: int = 0
    total_monthly_cost: float = 0.0
    storage_class_distribution: Dict[str, float] = Field(default_factory=dict)
    lifecycle_opportunities: int = 0
    buckets: List[Dict[str, Any]] = Field(default_factory=list)


class GCPOpportunity(BaseModel):
    """Optimization opportunity"""
    service: str
    type: str
    resource_id: str
    estimated_savings: float
    recommendation: str
    details: Dict[str, Any] = Field(default_factory=dict)


class GCPOptimization(BaseModel):
    """Optimization summary"""
    total_opportunities: int = 0
    total_potential_savings: float = 0.0
    opportunities: List[GCPOpportunity] = Field(default_factory=list)


class GCPAnomaly(BaseModel):
    """Cost anomaly"""
    date: str
    cost: float
    baseline: float
    deviation: float
    severity: str


class GCPCostResponse(BaseModel):
    """Response model for GCP cost analysis"""
    project_id: str
    time_period: Dict[str, str]
    total_cost: float
    cost_breakdown: GCPCostBreakdown
    services: Dict[str, Any] = Field(default_factory=dict)
    optimization: GCPOptimization
    anomalies: List[GCPAnomaly] = Field(default_factory=list)
    analyzed_at: str


class GCPConnectionTestResponse(BaseModel):
    """Response for connection test"""
    success: bool
    project_id: str
    billing_info: Dict[str, Any] = Field(default_factory=dict)
    accessible_services: List[str] = Field(default_factory=list)
    message: str


class GCPCostQueryRequest(BaseModel):
    """Request for querying GCP costs"""
    project_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    service: Optional[str] = None
    group_by: Optional[List[str]] = None


class GCPOpportunitiesRequest(BaseModel):
    """Request for GCP optimization opportunities"""
    project_id: str
    service: Optional[str] = None
    min_savings: float = Field(0.0, description="Minimum monthly savings")
    limit: int = Field(20, description="Max results")

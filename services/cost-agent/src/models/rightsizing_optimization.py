"""
Right-Sizing Optimization Pydantic Models

This module defines the data models for right-sizing optimization requests,
recommendations, and responses with comprehensive validation.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import re


class RightSizingRequest(BaseModel):
    """Request model for right-sizing optimization."""
    
    customer_id: str = Field(
        ...,
        description="Customer identifier",
        min_length=1,
        max_length=64
    )
    
    cloud_provider: str = Field(
        default="aws",
        description="Cloud provider (aws, gcp, azure)"
    )
    
    service_types: List[str] = Field(
        default=["ec2"],
        description="Service types to analyze"
    )
    
    analysis_period_days: int = Field(
        default=30,
        ge=7,
        le=90,
        description="Analysis period in days (7-90)"
    )
    
    min_utilization_threshold: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Minimum utilization threshold for over-provisioning detection"
    )
    
    max_utilization_threshold: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Maximum utilization threshold for under-provisioning detection"
    )
    
    include_burstable: bool = Field(
        default=True,
        description="Include burstable instance types in recommendations"
    )
    
    include_arm: bool = Field(
        default=True,
        description="Include ARM/Graviton instances in recommendations"
    )
    
    min_savings_threshold: float = Field(
        default=10.0,
        ge=0.0,
        description="Minimum monthly savings to generate recommendation"
    )
    
    customer_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Customer-specific preferences"
    )
    
    @field_validator('customer_id')
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        """Validate customer ID format."""
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', v):
            raise ValueError('customer_id must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @field_validator('cloud_provider')
    @classmethod
    def validate_cloud_provider(cls, v: str) -> str:
        """Validate cloud provider."""
        valid_providers = ['aws', 'gcp', 'azure']
        if v.lower() not in valid_providers:
            raise ValueError(f'cloud_provider must be one of: {", ".join(valid_providers)}')
        return v.lower()
    
    @field_validator('service_types')
    @classmethod
    def validate_service_types(cls, v: List[str]) -> List[str]:
        """Validate service types."""
        valid_services = ['ec2', 'rds', 'elasticache', 'redshift']
        for service in v:
            if service.lower() not in valid_services:
                raise ValueError(f'Invalid service_type: {service}. Must be one of: {", ".join(valid_services)}')
        return [s.lower() for s in v]
    
    @model_validator(mode='after')
    def validate_thresholds(self):
        """Validate that min threshold is less than max threshold."""
        if self.min_utilization_threshold >= self.max_utilization_threshold:
            raise ValueError('min_utilization_threshold must be less than max_utilization_threshold')
        return self


class ResourceMetrics(BaseModel):
    """Resource utilization metrics for an instance."""
    
    cpu_p50: float = Field(ge=0.0, le=100.0, description="CPU 50th percentile")
    cpu_p95: float = Field(ge=0.0, le=100.0, description="CPU 95th percentile")
    cpu_p99: float = Field(ge=0.0, le=100.0, description="CPU 99th percentile")
    cpu_max: float = Field(ge=0.0, le=100.0, description="CPU maximum")
    cpu_avg: float = Field(ge=0.0, le=100.0, description="CPU average")
    cpu_std: float = Field(ge=0.0, description="CPU standard deviation")
    
    memory_p50: float = Field(ge=0.0, le=100.0, description="Memory 50th percentile")
    memory_p95: float = Field(ge=0.0, le=100.0, description="Memory 95th percentile")
    memory_p99: float = Field(ge=0.0, le=100.0, description="Memory 99th percentile")
    memory_max: float = Field(ge=0.0, le=100.0, description="Memory maximum")
    memory_avg: float = Field(ge=0.0, le=100.0, description="Memory average")
    memory_std: float = Field(ge=0.0, description="Memory standard deviation")
    
    network_in_p95: float = Field(ge=0.0, description="Network in 95th percentile (Mbps)")
    network_out_p95: float = Field(ge=0.0, description="Network out 95th percentile (Mbps)")
    
    disk_read_iops_p95: Optional[float] = Field(default=None, ge=0.0, description="Disk read IOPS 95th percentile")
    disk_write_iops_p95: Optional[float] = Field(default=None, ge=0.0, description="Disk write IOPS 95th percentile")
    
    throttling_events: int = Field(default=0, ge=0, description="Number of throttling events")
    burstable_credit_balance: Optional[float] = Field(default=None, ge=0.0, description="Burstable credit balance")
    
    data_points: int = Field(ge=1, description="Number of data points analyzed")


class RightSizingRecommendation(BaseModel):
    """Right-sizing recommendation for a single instance."""
    
    instance_id: str = Field(..., description="Instance identifier")
    current_instance_type: str = Field(..., description="Current instance type")
    recommended_instance_type: str = Field(..., description="Recommended instance type")
    service_type: str = Field(default="ec2", description="Service type")
    region: str = Field(..., description="AWS region")
    
    # Current metrics
    current_metrics: ResourceMetrics = Field(..., description="Current resource metrics")
    
    # Cost analysis
    current_hourly_cost: float = Field(ge=0.0, description="Current hourly cost")
    recommended_hourly_cost: float = Field(ge=0.0, description="Recommended hourly cost")
    hourly_savings: float = Field(description="Hourly savings (can be negative for upsizing)")
    monthly_savings: float = Field(description="Monthly savings")
    annual_savings: float = Field(description="Annual savings")
    savings_percent: float = Field(description="Savings percentage")
    
    # Capacity comparison
    current_vcpus: int = Field(ge=0, description="Current vCPUs")
    recommended_vcpus: int = Field(ge=0, description="Recommended vCPUs")
    current_memory_gb: float = Field(ge=0.0, description="Current memory in GB")
    recommended_memory_gb: float = Field(ge=0.0, description="Recommended memory in GB")
    
    # Risk assessment
    performance_risk: str = Field(..., description="Performance risk level (low, medium, high)")
    risk_factors: List[str] = Field(default=[], description="List of risk factors")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")
    
    # Migration
    migration_complexity: str = Field(..., description="Migration complexity (simple, moderate, complex)")
    estimated_downtime_minutes: int = Field(ge=0, description="Estimated downtime in minutes")
    requires_testing: bool = Field(default=False, description="Whether testing is required")
    
    # Metadata
    optimization_type: str = Field(..., description="Optimization type (downsize, upsize, family_change)")
    provisioning_issue: str = Field(..., description="Provisioning issue (over_provisioned, under_provisioned)")
    recommendation_reason: str = Field(default="", description="Reason for recommendation")
    
    @field_validator('performance_risk')
    @classmethod
    def validate_performance_risk(cls, v: str) -> str:
        """Validate performance risk level."""
        valid_risks = ['low', 'medium', 'high']
        if v.lower() not in valid_risks:
            raise ValueError(f'performance_risk must be one of: {", ".join(valid_risks)}')
        return v.lower()
    
    @field_validator('migration_complexity')
    @classmethod
    def validate_migration_complexity(cls, v: str) -> str:
        """Validate migration complexity."""
        valid_complexity = ['simple', 'moderate', 'complex']
        if v.lower() not in valid_complexity:
            raise ValueError(f'migration_complexity must be one of: {", ".join(valid_complexity)}')
        return v.lower()
    
    @field_validator('optimization_type')
    @classmethod
    def validate_optimization_type(cls, v: str) -> str:
        """Validate optimization type."""
        valid_types = ['downsize', 'upsize', 'family_change', 'same_size']
        if v.lower() not in valid_types:
            raise ValueError(f'optimization_type must be one of: {", ".join(valid_types)}')
        return v.lower()


class ImpactAnalysis(BaseModel):
    """Impact analysis for all recommendations."""
    
    total_instances_analyzed: int = Field(ge=0, description="Total instances analyzed")
    optimization_candidates: int = Field(ge=0, description="Number of optimization candidates")
    
    # Cost impact
    total_current_monthly_cost: float = Field(ge=0.0, description="Total current monthly cost")
    total_recommended_monthly_cost: float = Field(ge=0.0, description="Total recommended monthly cost")
    total_monthly_savings: float = Field(description="Total monthly savings")
    total_annual_savings: float = Field(description="Total annual savings")
    average_savings_percent: float = Field(description="Average savings percentage")
    
    # Performance impact
    low_risk_count: int = Field(ge=0, description="Number of low-risk recommendations")
    medium_risk_count: int = Field(ge=0, description="Number of medium-risk recommendations")
    high_risk_count: int = Field(ge=0, description="Number of high-risk recommendations")
    requires_testing_count: int = Field(ge=0, description="Number requiring testing")
    
    # Migration complexity
    simple_migrations: int = Field(ge=0, description="Number of simple migrations")
    moderate_migrations: int = Field(ge=0, description="Number of moderate migrations")
    complex_migrations: int = Field(ge=0, description="Number of complex migrations")
    total_estimated_downtime_minutes: int = Field(ge=0, description="Total estimated downtime")
    
    # Breakdown
    downsize_migrations_count: int = Field(ge=0, description="Number of downsize migrations")
    upsize_migrations_count: int = Field(ge=0, description="Number of upsize migrations")
    family_change_migrations_count: int = Field(ge=0, description="Number of family change migrations")
    
    # Summary
    quick_wins_count: int = Field(ge=0, description="Number of quick wins")
    quick_wins: List[Dict[str, Any]] = Field(default=[], description="Quick win recommendations")
    
    # Executive summary
    executive_summary: Dict[str, Any] = Field(default={}, description="Executive summary")
    implementation_roadmap: Dict[str, Any] = Field(default={}, description="Implementation roadmap")


class RightSizingResponse(BaseModel):
    """Response model for right-sizing optimization."""
    
    request_id: str = Field(..., description="Request identifier")
    customer_id: str = Field(..., description="Customer identifier")
    cloud_provider: str = Field(..., description="Cloud provider")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    # Analysis results
    instances_analyzed: int = Field(ge=0, description="Number of instances analyzed")
    optimization_candidates: int = Field(ge=0, description="Number of optimization candidates")
    over_provisioned_count: int = Field(ge=0, description="Number of over-provisioned instances")
    under_provisioned_count: int = Field(ge=0, description="Number of under-provisioned instances")
    optimal_count: int = Field(ge=0, description="Number of optimally-sized instances")
    
    # Recommendations
    recommendations: List[RightSizingRecommendation] = Field(default=[], description="List of recommendations")
    
    # Financial summary
    total_monthly_savings: float = Field(default=0.0, description="Total monthly savings")
    total_annual_savings: float = Field(default=0.0, description="Total annual savings")
    average_savings_percent: float = Field(default=0.0, description="Average savings percentage")
    
    # Impact analysis
    impact_analysis: Optional[ImpactAnalysis] = Field(default=None, description="Impact analysis")
    
    # Workflow status
    workflow_status: str = Field(..., description="Workflow status")
    success: bool = Field(default=True, description="Whether the workflow succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    @field_validator('workflow_status')
    @classmethod
    def validate_workflow_status(cls, v: str) -> str:
        """Validate workflow status."""
        valid_statuses = [
            'initialized', 'collecting_metrics', 'analyzed', 
            'recommendations_generated', 'impact_calculated', 
            'complete', 'failed'
        ]
        if v not in valid_statuses:
            raise ValueError(f'workflow_status must be one of: {", ".join(valid_statuses)}')
        return v

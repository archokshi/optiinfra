"""
Pydantic models for Reserved Instance optimization.

Provides request/response validation and data structures for RI workflows.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import re


class RIOptimizationRequest(BaseModel):
    """Request model for RI optimization with input validation."""
    
    customer_id: str = Field(
        ...,
        description="Customer identifier",
        min_length=1,
        max_length=64
    )
    
    cloud_provider: str = Field(
        ...,
        description="Cloud provider (aws, gcp, azure)"
    )
    
    service_types: List[str] = Field(
        default=["ec2"],
        description="Service types to analyze (ec2, rds, elasticache, etc.)"
    )
    
    analysis_period_days: int = Field(
        default=30,
        ge=7,
        le=90,
        description="Analysis period in days (7-90)"
    )
    
    min_uptime_percent: float = Field(
        default=80.0,
        ge=50.0,
        le=100.0,
        description="Minimum uptime percentage for RI candidates (50-100)"
    )
    
    min_monthly_cost: float = Field(
        default=50.0,
        ge=0.0,
        description="Minimum monthly cost threshold for RI candidates"
    )
    
    customer_preferences: Optional[Dict[str, str]] = Field(
        default=None,
        description="Customer preferences (payment_preference, term_preference)"
    )
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @field_validator('customer_id')
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        """Validate customer ID format."""
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', v):
            raise ValueError(
                'customer_id must be 1-64 characters, alphanumeric with dash/underscore only'
            )
        return v
    
    @field_validator('cloud_provider')
    @classmethod
    def validate_cloud_provider(cls, v: str) -> str:
        """Validate cloud provider."""
        if v not in ['aws', 'gcp', 'azure']:
            raise ValueError('cloud_provider must be one of: aws, gcp, azure')
        return v
    
    @field_validator('service_types')
    @classmethod
    def validate_service_types(cls, v: List[str]) -> List[str]:
        """Validate service types."""
        valid_services = {
            'ec2', 'rds', 'elasticache', 'redshift',  # AWS
            'compute', 'sql',  # GCP
            'vm', 'sql-db'  # Azure
        }
        
        if not v:
            raise ValueError('service_types cannot be empty')
        
        for service in v:
            if service not in valid_services:
                raise ValueError(
                    f'Invalid service type: {service}. '
                    f'Valid options: {", ".join(sorted(valid_services))}'
                )
        
        return v


class RIRecommendation(BaseModel):
    """Single RI recommendation with all details."""
    
    instance_id: str = Field(..., description="Instance identifier")
    instance_type: str = Field(..., description="Instance type")
    service_type: str = Field(..., description="Service type (ec2, rds, etc.)")
    region: str = Field(..., description="Cloud region")
    
    term: str = Field(..., description="RI term (1year or 3year)")
    payment_option: str = Field(
        ...,
        description="Payment option (all_upfront, partial_upfront, no_upfront, committed, reserved)"
    )
    quantity: int = Field(default=1, ge=1, description="Number of RIs to purchase")
    
    # Cost details
    on_demand_cost_monthly: float = Field(..., ge=0, description="Current on-demand monthly cost")
    ri_cost_upfront: float = Field(..., ge=0, description="RI upfront cost")
    ri_cost_monthly: float = Field(..., ge=0, description="RI monthly cost")
    
    # Savings details
    monthly_savings: float = Field(..., ge=0, description="Monthly savings")
    annual_savings: float = Field(..., ge=0, description="Annual savings")
    total_savings: float = Field(..., description="Total savings over term")
    savings_percent: float = Field(..., ge=0, le=100, description="Savings percentage")
    breakeven_months: int = Field(..., ge=0, description="Months to break even")
    
    # Risk assessment
    risk_level: str = Field(..., description="Risk level (low, medium, high)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    usage_pattern: str = Field(
        ...,
        description="Usage pattern (steady, growing, seasonal, declining)"
    )
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @field_validator('term')
    @classmethod
    def validate_term(cls, v: str) -> str:
        """Validate RI term."""
        if v not in ['1year', '3year']:
            raise ValueError('term must be either "1year" or "3year"')
        return v
    
    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level."""
        if v not in ['low', 'medium', 'high']:
            raise ValueError('risk_level must be one of: low, medium, high')
        return v


class ROIAnalysis(BaseModel):
    """ROI analysis results."""
    
    average_breakeven_months: float = Field(..., description="Average break-even period in months")
    total_investment: float = Field(..., ge=0, description="Total upfront investment")
    total_monthly_savings: float = Field(..., ge=0, description="Total monthly savings")
    total_annual_savings: float = Field(..., ge=0, description="Total annual savings")
    
    total_return_1yr: float = Field(..., description="Total return over 1 year")
    total_return_3yr: float = Field(..., description="Total return over 3 years")
    
    roi_percent_1yr: float = Field(..., description="ROI percentage for 1 year")
    roi_percent_3yr: float = Field(..., description="ROI percentage for 3 years")
    risk_adjusted_roi: float = Field(..., description="Risk-adjusted ROI percentage")
    
    npv_1yr: float = Field(..., description="Net Present Value for 1 year")
    npv_3yr: float = Field(..., description="Net Present Value for 3 years")
    
    one_year_ris: int = Field(..., ge=0, description="Count of 1-year RI recommendations")
    three_year_ris: int = Field(..., ge=0, description="Count of 3-year RI recommendations")
    
    low_risk_count: int = Field(..., ge=0, description="Count of low-risk recommendations")
    medium_risk_count: int = Field(..., ge=0, description="Count of medium-risk recommendations")
    high_risk_count: int = Field(..., ge=0, description="Count of high-risk recommendations")
    
    recommendation_summary: Dict[str, Any] = Field(
        ...,
        description="Detailed breakdown of recommendations"
    )
    
    model_config = ConfigDict(str_strip_whitespace=True)


class RIOptimizationResponse(BaseModel):
    """Response model for RI optimization with complete results."""
    
    request_id: str = Field(..., description="Request identifier")
    customer_id: str = Field(..., description="Customer identifier")
    cloud_provider: str = Field(..., description="Cloud provider")
    
    # Analysis results
    instances_analyzed: int = Field(..., ge=0, description="Number of instances analyzed")
    stable_workloads_found: int = Field(..., ge=0, description="Number of stable workloads found")
    
    # Recommendations
    recommendations: List[RIRecommendation] = Field(
        default=[],
        description="List of RI recommendations"
    )
    
    # Financial summary
    total_upfront_cost: float = Field(..., ge=0, description="Total upfront cost for all RIs")
    total_monthly_savings: float = Field(..., ge=0, description="Total monthly savings")
    total_annual_savings: float = Field(..., ge=0, description="Total annual savings")
    total_three_year_savings: float = Field(..., ge=0, description="Total 3-year savings")
    
    # ROI analysis
    roi_analysis: Optional[ROIAnalysis] = Field(None, description="Comprehensive ROI analysis")
    
    # Workflow status
    workflow_status: str = Field(..., description="Workflow status")
    success: bool = Field(..., description="Whether optimization succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    timestamp: str = Field(..., description="Response timestamp")
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @field_validator('workflow_status')
    @classmethod
    def validate_workflow_status(cls, v: str) -> str:
        """Validate workflow status."""
        valid_statuses = [
            'initialized', 'collecting_data', 'analyzed',
            'recommendations_generated', 'roi_calculated',
            'complete', 'failed'
        ]
        if v not in valid_statuses:
            raise ValueError(f'Invalid workflow_status: {v}')
        return v

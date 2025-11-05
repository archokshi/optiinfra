"""
Analysis Engine Pydantic Models

This module defines the data models for analysis engine requests, idle resources,
anomalies, and analysis reports with comprehensive validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import re


class AnalysisRequest(BaseModel):
    """Request model for analysis engine."""
    
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
    
    analysis_types: List[str] = Field(
        default=["idle", "anomaly"],
        description="Types of analysis to perform"
    )
    
    lookback_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Lookback period in days (1-30)"
    )
    
    idle_threshold_cpu: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="CPU idle threshold percentage"
    )
    
    idle_threshold_memory: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Memory idle threshold percentage"
    )
    
    anomaly_sensitivity: str = Field(
        default="medium",
        description="Anomaly detection sensitivity (low, medium, high)"
    )
    
    include_recommendations: bool = Field(
        default=True,
        description="Include recommendations in report"
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
    
    @field_validator('analysis_types')
    @classmethod
    def validate_analysis_types(cls, v: List[str]) -> List[str]:
        """Validate analysis types."""
        valid_types = ['idle', 'anomaly', 'both']
        for analysis_type in v:
            if analysis_type.lower() not in valid_types:
                raise ValueError(f'Invalid analysis_type: {analysis_type}. Must be one of: {", ".join(valid_types)}')
        return [t.lower() for t in v]
    
    @field_validator('anomaly_sensitivity')
    @classmethod
    def validate_anomaly_sensitivity(cls, v: str) -> str:
        """Validate anomaly sensitivity."""
        valid_sensitivities = ['low', 'medium', 'high']
        if v.lower() not in valid_sensitivities:
            raise ValueError(f'anomaly_sensitivity must be one of: {", ".join(valid_sensitivities)}')
        return v.lower()


class IdleResource(BaseModel):
    """Model for an idle resource."""
    
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="Resource type (ec2, rds, ebs, etc.)")
    resource_name: Optional[str] = Field(default=None, description="Resource name")
    region: str = Field(..., description="AWS region")
    
    # Utilization metrics
    cpu_avg: float = Field(ge=0.0, le=100.0, description="Average CPU utilization")
    memory_avg: float = Field(ge=0.0, le=100.0, description="Average memory utilization")
    network_in_avg: float = Field(ge=0.0, description="Average network in (KB/s)")
    network_out_avg: float = Field(ge=0.0, description="Average network out (KB/s)")
    disk_read_ops: float = Field(ge=0.0, description="Disk read operations")
    disk_write_ops: float = Field(ge=0.0, description="Disk write operations")
    
    # Idle analysis
    idle_severity: str = Field(..., description="Idle severity (critical, high, medium, low)")
    idle_duration_days: int = Field(ge=0, description="Days resource has been idle")
    last_active_timestamp: Optional[str] = Field(default=None, description="Last active timestamp")
    
    # Cost analysis
    hourly_cost: float = Field(ge=0.0, description="Hourly cost")
    daily_waste: float = Field(ge=0.0, description="Daily waste cost")
    monthly_waste: float = Field(ge=0.0, description="Monthly waste cost")
    annual_waste: float = Field(ge=0.0, description="Annual waste cost")
    
    # Recommendations
    recommendation: str = Field(..., description="Recommended action")
    recommendation_reason: str = Field(..., description="Reason for recommendation")
    estimated_savings: Optional[float] = Field(default=None, ge=0.0, description="Estimated savings")
    
    @field_validator('idle_severity')
    @classmethod
    def validate_idle_severity(cls, v: str) -> str:
        """Validate idle severity."""
        valid_severities = ['critical', 'high', 'medium', 'low']
        if v.lower() not in valid_severities:
            raise ValueError(f'idle_severity must be one of: {", ".join(valid_severities)}')
        return v.lower()
    
    @field_validator('recommendation')
    @classmethod
    def validate_recommendation(cls, v: str) -> str:
        """Validate recommendation."""
        valid_recommendations = ['terminate', 'hibernate', 'review', 'monitor', 'none']
        if v.lower() not in valid_recommendations:
            raise ValueError(f'recommendation must be one of: {", ".join(valid_recommendations)}')
        return v.lower()


class Anomaly(BaseModel):
    """Model for a detected anomaly."""
    
    anomaly_id: str = Field(..., description="Anomaly identifier")
    anomaly_type: str = Field(..., description="Anomaly type")
    resource_id: Optional[str] = Field(default=None, description="Resource identifier")
    resource_type: Optional[str] = Field(default=None, description="Resource type")
    region: str = Field(..., description="Region")
    
    # Detection details
    detected_at: str = Field(..., description="Detection timestamp")
    anomaly_score: float = Field(ge=0.0, le=1.0, description="Anomaly score (0-1)")
    severity: str = Field(..., description="Severity level")
    
    # Anomaly specifics
    metric_name: str = Field(..., description="Metric name")
    expected_value: float = Field(description="Expected value")
    actual_value: float = Field(description="Actual value")
    deviation_percent: float = Field(description="Deviation percentage")
    
    # Context
    description: str = Field(..., description="Anomaly description")
    potential_causes: List[str] = Field(default=[], description="Potential causes")
    recommended_actions: List[str] = Field(default=[], description="Recommended actions")
    
    # Impact
    cost_impact: Optional[float] = Field(default=None, description="Cost impact")
    security_impact: Optional[str] = Field(default=None, description="Security impact level")
    
    @field_validator('anomaly_type')
    @classmethod
    def validate_anomaly_type(cls, v: str) -> str:
        """Validate anomaly type."""
        valid_types = ['cost_spike', 'cost_drop', 'cost_trend', 'usage_spike', 
                       'memory_leak', 'configuration_drift', 'security_risk']
        if v.lower() not in valid_types:
            # Allow other types but log warning
            pass
        return v.lower()
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity."""
        valid_severities = ['critical', 'high', 'medium', 'low']
        if v.lower() not in valid_severities:
            raise ValueError(f'severity must be one of: {", ".join(valid_severities)}')
        return v.lower()


class AnalysisReport(BaseModel):
    """Model for analysis report."""
    
    report_id: str = Field(..., description="Report identifier")
    customer_id: str = Field(..., description="Customer identifier")
    cloud_provider: str = Field(..., description="Cloud provider")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")
    lookback_days: int = Field(ge=1, le=30, description="Lookback period")
    
    # Idle resources
    total_idle_resources: int = Field(ge=0, description="Total idle resources")
    idle_resources: List[Dict[str, Any]] = Field(default=[], description="List of idle resources")
    idle_by_severity: Dict[str, int] = Field(default={}, description="Idle resources by severity")
    total_monthly_waste: float = Field(ge=0.0, description="Total monthly waste")
    total_annual_waste: float = Field(ge=0.0, description="Total annual waste")
    
    # Anomalies
    total_anomalies: int = Field(ge=0, description="Total anomalies")
    anomalies: List[Dict[str, Any]] = Field(default=[], description="List of anomalies")
    anomalies_by_type: Dict[str, int] = Field(default={}, description="Anomalies by type")
    anomalies_by_severity: Dict[str, int] = Field(default={}, description="Anomalies by severity")
    
    # Summary
    executive_summary: Dict[str, Any] = Field(default={}, description="Executive summary")
    top_findings: List[Dict[str, Any]] = Field(default=[], description="Top findings")
    recommended_actions: List[Dict[str, Any]] = Field(default=[], description="Recommended actions")
    
    # Metadata
    analysis_duration_seconds: float = Field(ge=0.0, description="Analysis duration")
    success: bool = Field(default=True, description="Success status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class AnalysisResponse(BaseModel):
    """Response model for analysis engine."""
    
    request_id: str = Field(..., description="Request identifier")
    customer_id: str = Field(..., description="Customer identifier")
    cloud_provider: str = Field(..., description="Cloud provider")
    timestamp: str = Field(..., description="Response timestamp")
    
    # Results
    analysis_report: AnalysisReport = Field(..., description="Analysis report")
    
    # Status
    workflow_status: str = Field(..., description="Workflow status")
    success: bool = Field(default=True, description="Success status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    @field_validator('workflow_status')
    @classmethod
    def validate_workflow_status(cls, v: str) -> str:
        """Validate workflow status."""
        valid_statuses = [
            'initialized', 'collecting_data', 'idle_detected', 
            'anomalies_detected', 'report_generated', 'complete', 'failed'
        ]
        if v not in valid_statuses:
            raise ValueError(f'workflow_status must be one of: {", ".join(valid_statuses)}')
        return v

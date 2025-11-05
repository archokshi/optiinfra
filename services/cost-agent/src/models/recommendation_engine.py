"""
Pydantic models for Recommendation Engine.

Type-safe models for requests, responses, and data structures.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from enum import Enum


class RecommendationType(str, Enum):
    """Recommendation types."""
    TERMINATE = "terminate"
    HIBERNATE = "hibernate"
    RIGHT_SIZE = "right_size"
    SPOT = "spot"
    RI = "ri"
    AUTO_SCALE = "auto_scale"
    STORAGE_OPTIMIZE = "storage_optimize"
    CONFIG_FIX = "config_fix"
    SECURITY_FIX = "security_fix"
    INVESTIGATE = "investigate"


class RiskLevel(str, Enum):
    """Risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TrendDirection(str, Enum):
    """Trend directions."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class RecommendationCategory(str, Enum):
    """Recommendation categories."""
    QUICK_WIN = "quick_win"
    STRATEGIC = "strategic"
    LONG_TERM = "long_term"


class Recommendation(BaseModel):
    """Individual recommendation."""
    recommendation_id: str
    customer_id: str
    recommendation_type: str
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    region: str
    
    # Description
    title: str
    description: str
    rationale: str
    
    # Savings
    monthly_savings: float = Field(ge=0)
    annual_savings: float = Field(ge=0)
    implementation_cost: float = Field(ge=0)
    payback_period_days: int = Field(ge=0)
    
    # Risk assessment
    risk_level: str
    risk_factors: List[str] = []
    rollback_plan: Optional[str] = None
    
    # Implementation
    implementation_steps: List[str]
    estimated_time_minutes: int = Field(ge=0)
    requires_approval: bool
    
    # Metadata
    created_at: datetime
    expires_at: Optional[datetime] = None
    source: str  # idle_detection, anomaly, trend_analysis
    confidence: float = Field(ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_id": "rec-123",
                "customer_id": "cust-456",
                "recommendation_type": "terminate",
                "resource_id": "i-1234567890",
                "resource_type": "ec2",
                "region": "us-east-1",
                "title": "Terminate idle EC2 instance",
                "description": "Instance has been idle for 30 days",
                "rationale": "0% CPU, 0% memory utilization",
                "monthly_savings": 52.00,
                "annual_savings": 624.00,
                "implementation_cost": 0.0,
                "payback_period_days": 0,
                "risk_level": "low",
                "risk_factors": ["Verify no dependencies"],
                "rollback_plan": "Launch new instance if needed",
                "implementation_steps": ["Verify", "Backup", "Terminate"],
                "estimated_time_minutes": 15,
                "requires_approval": True,
                "created_at": "2025-10-22T20:00:00Z",
                "source": "idle_detection",
                "confidence": 0.95
            }
        }


class ScoredRecommendation(BaseModel):
    """Recommendation with scores."""
    recommendation: Recommendation
    
    # Scores (0-100)
    roi_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    urgency_score: float = Field(ge=0, le=100)
    business_impact_score: float = Field(ge=0, le=100)
    priority_score: float = Field(ge=0, le=100)
    
    # Ranking
    rank: int = Field(ge=1)
    category: str
    
    # Context
    scoring_context: Dict[str, Any] = {}
    scored_at: Optional[datetime] = None


class CostForecast(BaseModel):
    """Cost forecast with confidence intervals."""
    customer_id: str
    forecast_start_date: date
    forecast_end_date: date
    
    # Forecast data
    daily_forecast: List[float]
    weekly_forecast: List[float]
    monthly_forecast: List[float]
    
    # Confidence intervals
    daily_lower_bound: List[float]
    daily_upper_bound: List[float]
    confidence_level: float = Field(ge=0.0, le=1.0)
    
    # Trends
    trend_direction: str
    growth_rate_percent: float
    
    # Metadata
    model_used: str
    forecast_accuracy: Optional[float] = None
    generated_at: datetime


class SavingsForecast(BaseModel):
    """Savings forecast for a recommendation."""
    recommendation_id: str
    
    # Savings forecast
    monthly_savings: float
    annual_savings: float
    three_year_savings: float
    
    # Timeline
    savings_start_date: date
    full_savings_date: date
    
    # Confidence
    confidence_level: float = Field(ge=0.0, le=1.0)
    confidence_interval: Tuple[float, float]
    
    # Assumptions
    assumptions: List[str]
    risk_factors: List[str]


class TrendAnalysis(BaseModel):
    """Historical trend analysis."""
    customer_id: str
    analysis_period_days: int
    analysis_date: datetime
    
    # Cost trends
    total_cost_trend: str
    cost_growth_rate: float
    cost_volatility: float
    
    # By resource type
    cost_by_resource_type: Dict[str, float]
    fastest_growing_resource: str
    largest_cost_driver: str
    
    # Patterns
    daily_pattern: Optional[Dict[str, float]] = None
    weekly_pattern: Optional[Dict[str, float]] = None
    monthly_pattern: Optional[Dict[str, float]] = None
    
    # Insights
    key_findings: List[str]
    recommendations: List[str]


class RecommendationEngineRequest(BaseModel):
    """Request to generate recommendations."""
    customer_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    analysis_report: Dict[str, Any]
    
    # Options
    include_predictions: bool = True
    include_trends: bool = True
    forecast_days: int = Field(default=30, ge=1, le=365)
    max_recommendations: int = Field(default=50, ge=1, le=200)
    min_monthly_savings: float = Field(default=10.0, ge=0.0)
    
    # Scoring weights (must sum to 1.0)
    roi_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    risk_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    urgency_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    impact_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    
    # Filters
    excluded_resource_types: List[str] = []
    excluded_regions: List[str] = []
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    
    @validator('roi_weight', 'risk_weight', 'urgency_weight', 'impact_weight')
    def validate_weights_sum(cls, v, values):
        """Validate that weights sum to 1.0."""
        if 'roi_weight' in values and 'risk_weight' in values and 'urgency_weight' in values:
            total = (
                values.get('roi_weight', 0) +
                values.get('risk_weight', 0) +
                values.get('urgency_weight', 0) +
                v
            )
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "customer-123",
                "analysis_report": {
                    "idle_resources": [],
                    "anomalies": []
                },
                "include_predictions": True,
                "include_trends": True,
                "forecast_days": 30,
                "max_recommendations": 50,
                "min_monthly_savings": 10.0
            }
        }


class RecommendationEngineResponse(BaseModel):
    """Response from recommendation engine."""
    request_id: str
    customer_id: str
    timestamp: datetime
    
    # Recommendations
    total_recommendations: int = Field(ge=0)
    scored_recommendations: List[ScoredRecommendation]
    
    # Forecasts
    cost_forecast: Optional[CostForecast] = None
    total_potential_savings: float = Field(ge=0)
    
    # Trends
    trend_analysis: Optional[TrendAnalysis] = None
    
    # Summary
    quick_wins: List[ScoredRecommendation]
    strategic_initiatives: List[ScoredRecommendation]
    long_term_opportunities: List[ScoredRecommendation]
    
    # Metadata
    processing_time_seconds: float = Field(ge=0)
    success: bool
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req-789",
                "customer_id": "customer-123",
                "timestamp": "2025-10-22T20:00:00Z",
                "total_recommendations": 10,
                "scored_recommendations": [],
                "total_potential_savings": 500.00,
                "quick_wins": [],
                "strategic_initiatives": [],
                "long_term_opportunities": [],
                "processing_time_seconds": 2.5,
                "success": True
            }
        }

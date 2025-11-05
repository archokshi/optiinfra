"""
Pydantic models for LLM integration.

Type-safe models for LLM requests, responses, and operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime


class LLMRequest(BaseModel):
    """LLM request model."""
    
    prompt: str = Field(..., min_length=1, description="User prompt")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    max_tokens: int = Field(default=2000, ge=1, le=8000, description="Maximum tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    
    @validator("prompt")
    def validate_prompt(cls, v):
        """Validate prompt is not empty."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v


class LLMResponse(BaseModel):
    """LLM response model."""
    
    content: str = Field(..., description="Generated content")
    tokens_used: int = Field(default=0, ge=0, description="Tokens used")
    model: str = Field(..., description="Model used")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Latency in milliseconds")
    cached: bool = Field(default=False, description="Whether response was cached")


class InsightGenerationRequest(BaseModel):
    """Request for insight generation."""
    
    analysis_report: Dict[str, Any] = Field(..., description="Analysis report data")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    
    @validator("analysis_report")
    def validate_report(cls, v):
        """Validate analysis report has required fields."""
        if not v:
            raise ValueError("Analysis report cannot be empty")
        return v


class InsightGenerationResponse(BaseModel):
    """Response with generated insights."""
    
    insights: str = Field(..., description="Generated insights")
    enhanced_recommendations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Enhanced recommendations"
    )
    executive_summary: str = Field(..., description="Executive summary")
    tokens_used: int = Field(default=0, ge=0, description="Total tokens used")
    cache_hit: bool = Field(default=False, description="Whether cache was hit")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class RecommendationEnhancementRequest(BaseModel):
    """Request for recommendation enhancement."""
    
    recommendation: Dict[str, Any] = Field(..., description="Recommendation to enhance")
    max_tokens: int = Field(default=1500, ge=100, le=4000, description="Maximum tokens")
    
    @validator("recommendation")
    def validate_recommendation(cls, v):
        """Validate recommendation has required fields."""
        required_fields = ["optimization_type"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Recommendation missing required field: {field}")
        return v


class RecommendationEnhancementResponse(BaseModel):
    """Response with enhanced recommendation."""
    
    original_recommendation: Dict[str, Any] = Field(..., description="Original recommendation")
    enhancement: str = Field(..., description="LLM enhancement")
    enhanced_recommendation: Dict[str, Any] = Field(..., description="Combined recommendation")
    tokens_used: int = Field(default=0, ge=0, description="Tokens used")


class ExecutiveSummaryRequest(BaseModel):
    """Request for executive summary generation."""
    
    analysis_report: Dict[str, Any] = Field(..., description="Analysis report")
    insights: str = Field(..., min_length=10, description="Generated insights")
    max_tokens: int = Field(default=2000, ge=200, le=4000, description="Maximum tokens")


class ExecutiveSummaryResponse(BaseModel):
    """Response with executive summary."""
    
    summary: str = Field(..., description="Executive summary")
    tokens_used: int = Field(default=0, ge=0, description="Tokens used")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class BottleneckExplanationRequest(BaseModel):
    """Request for bottleneck explanation."""
    
    bottleneck: Dict[str, Any] = Field(..., description="Bottleneck details")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    max_tokens: int = Field(default=1000, ge=100, le=2000, description="Maximum tokens")
    
    @validator("bottleneck")
    def validate_bottleneck(cls, v):
        """Validate bottleneck has required fields."""
        if "bottleneck_type" not in v:
            raise ValueError("Bottleneck missing required field: bottleneck_type")
        return v


class BottleneckExplanationResponse(BaseModel):
    """Response with bottleneck explanation."""
    
    bottleneck_type: str = Field(..., description="Type of bottleneck")
    explanation: str = Field(..., description="Explanation")
    tokens_used: int = Field(default=0, ge=0, description="Tokens used")


class ROIAnalysisRequest(BaseModel):
    """Request for ROI analysis."""
    
    optimization_description: str = Field(..., min_length=10, description="Description of optimization")
    current_metrics: Dict[str, Any] = Field(..., description="Current performance metrics")
    expected_improvement: Dict[str, Any] = Field(..., description="Expected improvement")
    max_tokens: int = Field(default=1500, ge=200, le=3000, description="Maximum tokens")


class ROIAnalysisResponse(BaseModel):
    """Response with ROI analysis."""
    
    roi_summary: str = Field(..., description="ROI summary")
    business_impact: str = Field(..., description="Business impact explanation")
    implementation_effort: str = Field(..., description="Implementation effort assessment")
    tokens_used: int = Field(default=0, ge=0, description="Tokens used")


class LLMMetadata(BaseModel):
    """Metadata for LLM operations."""
    
    model: str = Field(..., description="Model used")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    tokens_used: int = Field(default=0, ge=0, description="Total tokens used")
    cache_hit: bool = Field(default=False, description="Whether cache was hit")
    error: Optional[str] = Field(None, description="Error message if any")


class EnhancedAnalysisReport(BaseModel):
    """Enhanced analysis report with LLM insights."""
    
    # Original technical data
    bottlenecks: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    optimizations: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    
    # LLM enhancements
    llm_insights: Optional[str] = Field(None, description="Natural language insights")
    enhanced_recommendations: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Recommendations with LLM enhancement"
    )
    executive_summary: Optional[str] = Field(None, description="Executive summary")
    llm_metadata: Optional[LLMMetadata] = Field(None, description="LLM operation metadata")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LLMCacheStats(BaseModel):
    """LLM cache statistics."""
    
    cache_size: int = Field(default=0, ge=0, description="Number of cached items")
    cache_enabled: bool = Field(default=True, description="Whether caching is enabled")
    cache_hit_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Cache hit rate")
    total_requests: int = Field(default=0, ge=0, description="Total requests")
    cache_hits: int = Field(default=0, ge=0, description="Cache hits")
    cache_misses: int = Field(default=0, ge=0, description="Cache misses")


class LLMHealthCheck(BaseModel):
    """LLM health check response."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    model: str = Field(..., description="Model being used")
    api_available: bool = Field(..., description="Whether API is available")
    last_request_latency_ms: Optional[float] = Field(None, description="Last request latency")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

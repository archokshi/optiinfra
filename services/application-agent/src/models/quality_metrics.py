"""
Quality Metrics Models

Pydantic models for quality monitoring.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class QualityRequest(BaseModel):
    """Request for quality analysis."""
    
    prompt: str = Field(..., description="User prompt")
    response: str = Field(..., description="LLM response")
    model_name: Optional[str] = Field(None, description="Model used")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RelevanceScore(BaseModel):
    """Relevance scoring result."""
    
    score: float = Field(..., ge=0, le=100, description="Relevance score (0-100)")
    keyword_overlap: float = Field(..., description="Keyword overlap ratio")
    length_appropriate: bool = Field(..., description="Response length is appropriate")
    question_type_match: bool = Field(..., description="Response matches question type")
    details: Dict[str, Any] = Field(default_factory=dict)


class CoherenceScore(BaseModel):
    """Coherence scoring result."""
    
    score: float = Field(..., ge=0, le=100, description="Coherence score (0-100)")
    sentence_quality: float = Field(..., description="Sentence structure quality")
    logical_flow: float = Field(..., description="Logical flow score")
    contradictions: int = Field(default=0, description="Number of contradictions detected")
    readability: float = Field(..., description="Readability score")
    details: Dict[str, Any] = Field(default_factory=dict)


class HallucinationResult(BaseModel):
    """Hallucination detection result."""
    
    hallucination_rate: float = Field(..., ge=0, le=100, description="Hallucination rate (%)")
    confidence_markers: int = Field(default=0, description="Uncertain language markers")
    unsupported_claims: int = Field(default=0, description="Unsupported factual claims")
    numeric_precision: int = Field(default=0, description="Overly specific numbers")
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH")
    details: Dict[str, Any] = Field(default_factory=dict)


class QualityMetrics(BaseModel):
    """Complete quality metrics for a response."""
    
    # Identifiers
    request_id: str = Field(..., description="Unique request ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Input
    prompt: str = Field(..., description="User prompt")
    response: str = Field(..., description="LLM response")
    model_name: Optional[str] = None
    
    # Quality Scores
    relevance: RelevanceScore
    coherence: CoherenceScore
    hallucination: HallucinationResult
    
    # Overall
    overall_quality: float = Field(..., ge=0, le=100, description="Overall quality score")
    quality_grade: str = Field(..., description="Quality grade: A, B, C, D, F")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_grade(self) -> str:
        """Calculate quality grade."""
        if self.overall_quality >= 90:
            return "A"
        elif self.overall_quality >= 80:
            return "B"
        elif self.overall_quality >= 70:
            return "C"
        elif self.overall_quality >= 60:
            return "D"
        else:
            return "F"


class QualityTrend(BaseModel):
    """Quality trend over time."""
    
    time_period: str = Field(..., description="Time period (e.g., '1h', '24h')")
    average_quality: float = Field(..., description="Average quality score")
    min_quality: float = Field(..., description="Minimum quality score")
    max_quality: float = Field(..., description="Maximum quality score")
    total_requests: int = Field(..., description="Total requests analyzed")
    quality_distribution: Dict[str, int] = Field(..., description="Distribution by grade")

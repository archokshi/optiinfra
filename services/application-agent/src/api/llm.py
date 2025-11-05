"""
LLM API Endpoints

Provides endpoints for LLM-based quality analysis.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ..analyzers.llm_quality_analyzer import llm_quality_analyzer
from ..core.logger import logger

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMAnalysisRequest(BaseModel):
    """Request for LLM analysis."""
    prompt: str = Field(..., description="Input prompt")
    response: str = Field(..., description="Model response")


class LLMAnalysisResponse(BaseModel):
    """Response from LLM analysis."""
    relevance_score: Optional[float] = None
    coherence_score: Optional[float] = None
    hallucination_score: Optional[float] = None
    overall_quality: Optional[float] = None
    llm_enabled: bool


@router.post("/analyze", response_model=LLMAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_with_llm(request: LLMAnalysisRequest) -> LLMAnalysisResponse:
    """
    Analyze quality using LLM.
    
    Args:
        request: Analysis request
        
    Returns:
        LLM-based quality scores
    """
    try:
        logger.info(f"LLM analysis requested for prompt: {request.prompt[:50]}...")
        
        scores = await llm_quality_analyzer.analyze_all(
            request.prompt,
            request.response
        )
        
        return LLMAnalysisResponse(
            relevance_score=scores.get("relevance"),
            coherence_score=scores.get("coherence"),
            hallucination_score=scores.get("hallucination"),
            overall_quality=scores.get("overall"),
            llm_enabled=True
        )
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM analysis failed: {str(e)}"
        )


@router.post("/score", status_code=status.HTTP_200_OK)
async def get_llm_score(request: LLMAnalysisRequest) -> Dict[str, Any]:
    """
    Get LLM quality score.
    
    Args:
        request: Analysis request
        
    Returns:
        Overall quality score
    """
    try:
        score = await llm_quality_analyzer.analyze_overall_quality(
            request.prompt,
            request.response
        )
        
        return {
            "overall_quality": score,
            "llm_enabled": score is not None
        }
        
    except Exception as e:
        logger.error(f"LLM scoring failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM scoring failed: {str(e)}"
        )


@router.post("/suggest", status_code=status.HTTP_200_OK)
async def get_improvement_suggestions(request: LLMAnalysisRequest) -> Dict[str, Any]:
    """
    Get improvement suggestions from LLM.
    
    Args:
        request: Analysis request
        
    Returns:
        Improvement suggestions
    """
    try:
        suggestions = await llm_quality_analyzer.suggest_improvements(
            request.prompt,
            request.response
        )
        
        return {
            "suggestions": suggestions,
            "llm_enabled": suggestions is not None
        }
        
    except Exception as e:
        logger.error(f"LLM suggestions failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM suggestions failed: {str(e)}"
        )

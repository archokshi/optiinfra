"""
Quality Monitoring API Endpoints

Provides endpoints for quality analysis and monitoring.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from ..models.quality_metrics import QualityRequest, QualityMetrics, QualityTrend
from ..collectors.quality_collector import quality_collector
from ..analyzers.quality_analyzer import quality_analyzer
from ..core.logger import logger

router = APIRouter(prefix="/quality", tags=["quality"])


@router.post("/analyze", response_model=QualityMetrics, status_code=status.HTTP_200_OK)
async def analyze_quality(request: QualityRequest) -> QualityMetrics:
    """
    Analyze quality of an LLM response.
    
    Args:
        request: Quality analysis request
        
    Returns:
        Quality metrics
    """
    try:
        logger.info(f"Analyzing quality for prompt: {request.prompt[:50]}...")
        
        metrics = await quality_collector.collect_quality_metrics(request)
        
        # Add to analyzer history
        quality_analyzer.add_metrics(metrics)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Quality analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality analysis failed: {str(e)}"
        )


@router.get("/trend", response_model=QualityTrend, status_code=status.HTTP_200_OK)
async def get_quality_trend(time_period: str = "1h") -> QualityTrend:
    """
    Get quality trend for a time period.
    
    Args:
        time_period: Time period (e.g., '1h', '24h', '7d')
        
    Returns:
        Quality trend
    """
    try:
        trend = quality_analyzer.get_quality_trend(time_period)
        return trend
        
    except Exception as e:
        logger.error(f"Failed to get quality trend: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality trend: {str(e)}"
        )


@router.get("/insights", status_code=status.HTTP_200_OK)
async def get_quality_insights() -> Dict[str, Any]:
    """
    Get quality insights and recommendations.
    
    Returns:
        Quality insights
    """
    try:
        insights = quality_analyzer.get_quality_insights()
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get quality insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality insights: {str(e)}"
        )


@router.get("/metrics/latest", response_model=QualityMetrics, status_code=status.HTTP_200_OK)
async def get_latest_metrics() -> QualityMetrics:
    """
    Get latest quality metrics.
    
    Returns:
        Latest quality metrics
    """
    if not quality_analyzer.metrics_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quality metrics available"
        )
    
    return quality_analyzer.metrics_history[-1]


@router.get("/metrics/history", status_code=status.HTTP_200_OK)
async def get_metrics_history(limit: int = 100) -> Dict[str, Any]:
    """
    Get quality metrics history.
    
    Args:
        limit: Maximum number of metrics to return
        
    Returns:
        Metrics history
    """
    history = quality_analyzer.metrics_history[-limit:]
    
    return {
        "total": len(quality_analyzer.metrics_history),
        "returned": len(history),
        "metrics": [
            {
                "request_id": m.request_id,
                "timestamp": m.timestamp.isoformat(),
                "overall_quality": m.overall_quality,
                "quality_grade": m.quality_grade,
                "relevance": m.relevance.score,
                "coherence": m.coherence.score,
                "hallucination_rate": m.hallucination.hallucination_rate
            }
            for m in history
        ]
    }

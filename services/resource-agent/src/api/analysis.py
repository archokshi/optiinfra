"""
Analysis API

Endpoints for resource analysis and recommendations.
"""

from fastapi import APIRouter, HTTPException, status

from src.models.analysis import AnalysisResult
from src.collectors.system_collector import SystemCollector
from src.collectors.gpu_collector import GPUCollector
from src.analysis.analyzer import ResourceAnalyzer
from src.config import settings

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get(
    "/",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Get resource analysis"
)
async def get_analysis() -> AnalysisResult:
    """
    Analyze current resource utilization and generate recommendations.
    
    Returns:
        AnalysisResult: Analysis results with bottlenecks and recommendations
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Collect metrics
        system_collector = SystemCollector()
        system_metrics = system_collector.collect(instance_id=settings.agent_id)
        
        # Collect GPU metrics if available
        gpu_metrics = None
        with GPUCollector() as gpu_collector:
            if gpu_collector.is_available():
                gpu_metrics = gpu_collector.collect(instance_id=settings.agent_id)
        
        # Analyze
        analyzer = ResourceAnalyzer()
        analysis = analyzer.analyze(system_metrics, gpu_metrics)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resources: {str(e)}"
        )


@router.get(
    "/health-score",
    status_code=status.HTTP_200_OK,
    summary="Get health score only"
)
async def get_health_score() -> dict:
    """
    Get overall health score.
    
    Returns:
        dict: Health score and status
    """
    try:
        system_collector = SystemCollector()
        system_metrics = system_collector.collect(instance_id=settings.agent_id)
        
        gpu_metrics = None
        with GPUCollector() as gpu_collector:
            if gpu_collector.is_available():
                gpu_metrics = gpu_collector.collect(instance_id=settings.agent_id)
        
        analyzer = ResourceAnalyzer()
        analysis = analyzer.analyze(system_metrics, gpu_metrics)
        
        return {
            "health_score": analysis.health_score,
            "overall_health": analysis.overall_health,
            "primary_bottleneck": analysis.primary_bottleneck.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health score: {str(e)}"
        )

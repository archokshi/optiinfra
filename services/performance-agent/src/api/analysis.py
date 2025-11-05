"""
Analysis Endpoints

API endpoints for analysis engine.
"""

from fastapi import APIRouter, HTTPException, status
import logging

from src.models.analysis import AnalysisRequest, AnalysisResult
from src.analysis.engine import AnalysisEngine
from src.collectors.vllm_collector import VLLMCollector
from src.collectors.tgi_collector import TGICollector
from src.collectors.sglang_collector import SGLangCollector

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize engine
analysis_engine = AnalysisEngine()


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["analysis"]
)
async def analyze_instance(request: AnalysisRequest) -> AnalysisResult:
    """
    Analyze instance metrics and detect bottlenecks.
    
    Args:
        request: Analysis request
        
    Returns:
        Analysis result with bottlenecks and SLO status
    """
    try:
        # Collect metrics based on instance type
        if request.instance_type == "vllm":
            async with VLLMCollector() as collector:
                metrics = await collector.collect(
                    instance_id=request.instance_id,
                    endpoint=f"http://{request.instance_id}/metrics"
                )
        elif request.instance_type == "tgi":
            async with TGICollector() as collector:
                metrics = await collector.collect(
                    instance_id=request.instance_id,
                    endpoint=f"http://{request.instance_id}/metrics"
                )
        elif request.instance_type == "sglang":
            async with SGLangCollector() as collector:
                metrics = await collector.collect(
                    instance_id=request.instance_id,
                    endpoint=f"http://{request.instance_id}/metrics"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown instance type: {request.instance_type}"
            )
        
        # Analyze metrics
        result = analysis_engine.analyze(
            metrics=metrics,
            instance_type=request.instance_type,
            slo_targets=request.slo_targets
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

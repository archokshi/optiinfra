"""
Optimization Endpoints

API endpoints for optimization engine.
"""

from fastapi import APIRouter, HTTPException, status
import logging

from src.models.optimization import OptimizationRequest, OptimizationPlan
from src.optimization.engine import OptimizationEngine
from src.analysis.engine import AnalysisEngine
from src.collectors.vllm_collector import VLLMCollector
from src.collectors.tgi_collector import TGICollector
from src.collectors.sglang_collector import SGLangCollector

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize engines
analysis_engine = AnalysisEngine()
optimization_engine = OptimizationEngine()


@router.post(
    "/optimize",
    response_model=OptimizationPlan,
    status_code=status.HTTP_200_OK,
    tags=["optimization"]
)
async def optimize_instance(request: OptimizationRequest) -> OptimizationPlan:
    """
    Generate optimization plan for instance.
    
    Args:
        request: Optimization request
        
    Returns:
        Optimization plan with recommendations
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
        analysis_result = analysis_engine.analyze(
            metrics=metrics,
            instance_type=request.instance_type
        )
        
        # Generate optimization plan
        plan = optimization_engine.generate_plan(
            analysis_result=analysis_result,
            current_config=request.current_config,
            constraints=request.constraints
        )
        
        return plan
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )

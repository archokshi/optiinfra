"""
Optimization API

Endpoints for running optimization workflows.
"""

from fastapi import APIRouter, HTTPException, status

from src.models.workflow import WorkflowResult
from src.workflow.optimizer import OptimizationWorkflow
from src.config import settings

router = APIRouter(prefix="/optimize", tags=["optimize"])


@router.post(
    "/run",
    response_model=WorkflowResult,
    status_code=status.HTTP_200_OK,
    summary="Run optimization workflow"
)
async def run_optimization() -> WorkflowResult:
    """
    Run complete optimization workflow.
    
    Collects metrics, analyzes resources, generates LLM insights,
    and provides actionable optimization recommendations.
    
    Returns:
        WorkflowResult: Workflow execution result with recommendations
    """
    try:
        workflow = OptimizationWorkflow()
        result = await workflow.run(instance_id=settings.agent_id)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization workflow failed: {str(e)}"
        )

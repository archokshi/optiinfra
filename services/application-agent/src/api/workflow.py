"""
Workflow API Endpoints

Provides endpoints for LangGraph workflows.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from ..workflows.quality_validation_workflow import run_validation_workflow
from ..core.logger import logger

router = APIRouter(prefix="/workflow", tags=["workflow"])

# Store workflow results in memory
workflow_results: Dict[str, Dict[str, Any]] = {}


class WorkflowRequest(BaseModel):
    """Request to run validation workflow."""
    model_name: str = Field(..., description="Model name")
    prompt: str = Field(..., description="Input prompt")
    response: str = Field(..., description="Model response")
    config_hash: str = Field(default="default", description="Configuration hash")


class WorkflowResponse(BaseModel):
    """Response from workflow execution."""
    request_id: str
    status: str
    decision: Optional[str] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    errors: List[str] = []


@router.post("/validate", response_model=WorkflowResponse, status_code=status.HTTP_200_OK)
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """
    Run quality validation workflow.
    
    Args:
        request: Workflow request
        
    Returns:
        Workflow result
    """
    try:
        logger.info(f"Running workflow for model {request.model_name}")
        
        # Run the workflow
        result = run_validation_workflow(
            model_name=request.model_name,
            prompt=request.prompt,
            response=request.response,
            config_hash=request.config_hash
        )
        
        # Store result
        workflow_results[result["request_id"]] = result
        
        # Build response
        response = WorkflowResponse(
            request_id=result["request_id"],
            status=result["status"],
            decision=result.get("decision"),
            quality_metrics=result.get("quality_metrics"),
            validation_result=result.get("validation_result"),
            errors=result.get("errors", [])
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/status/{request_id}", status_code=status.HTTP_200_OK)
async def get_workflow_status(request_id: str) -> Dict[str, Any]:
    """
    Get workflow status.
    
    Args:
        request_id: Workflow request ID
        
    Returns:
        Workflow status
    """
    if request_id not in workflow_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {request_id} not found"
        )
    
    result = workflow_results[request_id]
    
    return {
        "request_id": result["request_id"],
        "status": result["status"],
        "current_step": result.get("current_step"),
        "decision": result.get("decision"),
        "errors": result.get("errors", [])
    }


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_workflow_history(limit: int = 100) -> Dict[str, Any]:
    """
    Get workflow execution history.
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        Workflow history
    """
    try:
        # Get recent workflows
        workflows = list(workflow_results.values())[-limit:]
        
        history = [
            {
                "request_id": w["request_id"],
                "model_name": w["model_name"],
                "status": w["status"],
                "decision": w.get("decision"),
                "quality": w.get("quality_metrics", {}).get("overall_quality") if w.get("quality_metrics") else None
            }
            for w in workflows
        ]
        
        return {
            "total": len(history),
            "workflows": history
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow history: {str(e)}"
        )

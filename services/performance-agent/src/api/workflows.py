"""
Workflow Endpoints

API endpoints for LangGraph workflows.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
import logging

from src.models.workflow import WorkflowRequest, WorkflowState
from src.workflows.manager import WorkflowManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize manager
workflow_manager = WorkflowManager()


@router.post(
    "/workflows",
    response_model=WorkflowState,
    status_code=status.HTTP_201_CREATED,
    tags=["workflows"]
)
async def start_workflow(request: WorkflowRequest) -> WorkflowState:
    """
    Start a new optimization workflow.
    
    Args:
        request: Workflow request
        
    Returns:
        Workflow state
    """
    try:
        state = await workflow_manager.start_workflow(request)
        return state
    
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowState,
    tags=["workflows"]
)
def get_workflow(workflow_id: str) -> WorkflowState:
    """Get workflow state by ID."""
    state = workflow_manager.get_workflow(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return state


@router.post(
    "/workflows/{workflow_id}/approve",
    response_model=WorkflowState,
    tags=["workflows"]
)
def approve_workflow(workflow_id: str, approved_by: str = "user") -> WorkflowState:
    """Approve a workflow."""
    state = workflow_manager.approve_workflow(workflow_id, approved_by)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return state


@router.post(
    "/workflows/{workflow_id}/reject",
    response_model=WorkflowState,
    tags=["workflows"]
)
def reject_workflow(workflow_id: str) -> WorkflowState:
    """Reject a workflow."""
    state = workflow_manager.reject_workflow(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return state


@router.get(
    "/workflows",
    response_model=List[WorkflowState],
    tags=["workflows"]
)
def list_workflows(
    status: Optional[str] = None,
    limit: int = 50
) -> List[WorkflowState]:
    """
    List all workflows.
    
    Args:
        status: Filter by status (optional)
        limit: Maximum number of workflows to return
        
    Returns:
        List of workflows
    """
    workflows = []
    
    for workflow_id in workflow_manager.workflows.keys():
        state = workflow_manager.get_workflow(workflow_id)
        if state:
            if status is None or state.status.value == status:
                workflows.append(state)
    
    # Sort by created_at descending
    workflows.sort(key=lambda w: w.created_at, reverse=True)
    
    return workflows[:limit]

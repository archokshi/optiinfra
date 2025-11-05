"""
Execution Engine API Routes.

FastAPI endpoints for execution management.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.execution.engine import ExecutionEngine
from src.models.execution_engine import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatusResponse,
    ExecutionListResponse,
    RollbackResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["execution"])

# Initialize execution engine
execution_engine = ExecutionEngine()


@router.post("/executions/execute", response_model=dict)
async def execute_recommendation(request: ExecutionRequest):
    """
    Execute a recommendation.
    
    Args:
        request: Execution request
    
    Returns:
        Execution result
    """
    try:
        logger.info(f"Executing recommendation {request.recommendation_id}")
        
        result = await execution_engine.execute_recommendation(
            recommendation_id=request.recommendation_id,
            dry_run=request.dry_run,
            auto_approve=request.auto_approve,
            force=request.force
        )
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Error executing recommendation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}", response_model=dict)
async def get_execution_status(execution_id: str):
    """
    Get execution status.
    
    Args:
        execution_id: Execution ID
    
    Returns:
        Execution status
    """
    try:
        status = await execution_engine.get_execution_status(execution_id)
        return status.dict()
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting execution status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """
    Cancel an execution.
    
    Args:
        execution_id: Execution ID
    
    Returns:
        Success message
    """
    try:
        success = await execution_engine.cancel_execution(execution_id)
        
        if success:
            return {"success": True, "message": f"Execution {execution_id} cancelled"}
        else:
            return {"success": False, "message": "Cannot cancel execution in current state"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/rollback", response_model=dict)
async def rollback_execution(execution_id: str):
    """
    Rollback an execution.
    
    Args:
        execution_id: Execution ID
    
    Returns:
        Rollback result
    """
    try:
        result = await execution_engine.rollback_execution(execution_id)
        return result.dict()
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error rolling back execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}/logs")
async def get_execution_logs(execution_id: str):
    """
    Get execution logs.
    
    Args:
        execution_id: Execution ID
    
    Returns:
        Execution logs
    """
    try:
        status = await execution_engine.get_execution_status(execution_id)
        
        return {
            "execution_id": execution_id,
            "logs": status.execution_log
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting execution logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
async def list_executions(
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
):
    """
    List executions.
    
    Args:
        customer_id: Filter by customer ID
        status: Filter by status
        limit: Maximum number of results
    
    Returns:
        List of executions
    """
    try:
        # In production, would query database
        # For now, return executions from memory
        executions = []
        
        for exec_id, exec_data in execution_engine.executions.items():
            # Apply filters
            if customer_id and exec_data.get("customer_id") != customer_id:
                continue
            if status and exec_data.get("status") != status:
                continue
            
            # Get full status
            exec_status = await execution_engine.get_execution_status(exec_id)
            executions.append(exec_status.dict())
            
            if len(executions) >= limit:
                break
        
        return {
            "total": len(executions),
            "executions": executions,
            "page": 1,
            "page_size": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

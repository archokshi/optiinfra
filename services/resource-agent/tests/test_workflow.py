"""
Workflow Tests

Tests for optimization workflow.
"""

import pytest
from src.workflow.optimizer import OptimizationWorkflow
from src.models.workflow import WorkflowStatus


@pytest.mark.asyncio
async def test_workflow_initialization():
    """Test workflow initialization."""
    workflow = OptimizationWorkflow()
    assert workflow is not None


@pytest.mark.asyncio
async def test_workflow_run():
    """Test workflow execution."""
    workflow = OptimizationWorkflow()
    result = await workflow.run(instance_id="test")
    
    assert result is not None
    assert result.workflow_id is not None
    assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
    assert result.execution_time_ms >= 0


@pytest.mark.asyncio
async def test_workflow_result_structure():
    """Test workflow result structure."""
    workflow = OptimizationWorkflow()
    result = await workflow.run(instance_id="test")
    
    assert hasattr(result, 'workflow_id')
    assert hasattr(result, 'status')
    assert hasattr(result, 'actions')
    assert hasattr(result, 'execution_time_ms')

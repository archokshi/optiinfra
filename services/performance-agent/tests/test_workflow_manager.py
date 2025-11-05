"""
Workflow Manager Tests

Tests for workflow manager.
"""

import pytest
from src.workflows.manager import WorkflowManager
from src.models.workflow import WorkflowRequest, WorkflowStatus


@pytest.fixture
def manager():
    """Workflow manager fixture."""
    return WorkflowManager()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_workflow(manager):
    """Test starting a workflow."""
    request = WorkflowRequest(
        instance_id="localhost:8000",
        instance_type="vllm",
        requires_approval=False,
        auto_rollout=True,
        monitoring_duration_seconds=1  # Short for testing
    )
    
    state = await manager.start_workflow(request)
    
    assert state.workflow_id is not None
    assert state.instance_id == "localhost:8000"
    assert state.instance_type == "vllm"
    assert state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.ROLLED_BACK]


@pytest.mark.unit
def test_get_workflow(manager):
    """Test getting workflow by ID."""
    # Non-existent workflow
    state = manager.get_workflow("non-existent")
    assert state is None


@pytest.mark.unit
def test_approve_workflow(manager):
    """Test approving a workflow."""
    # Create a workflow state manually
    workflow_id = "test-123"
    manager.workflows[workflow_id] = {
        "workflow_id": workflow_id,
        "instance_id": "localhost:8000",
        "instance_type": "vllm",
        "status": WorkflowStatus.AWAITING_APPROVAL.value,
        "created_at": "2025-01-24T00:00:00",
        "updated_at": "2025-01-24T00:00:00",
        "requires_approval": True,
        "approved": None,
        "approved_by": None,
        "approved_at": None,
        "rollout_history": []
    }
    
    # Approve it
    state = manager.approve_workflow(workflow_id, "admin")
    
    assert state is not None
    assert state.approved is True
    assert state.approved_by == "admin"
    assert state.status == WorkflowStatus.APPROVED


@pytest.mark.unit
def test_reject_workflow(manager):
    """Test rejecting a workflow."""
    # Create a workflow state manually
    workflow_id = "test-456"
    manager.workflows[workflow_id] = {
        "workflow_id": workflow_id,
        "instance_id": "localhost:8000",
        "instance_type": "vllm",
        "status": WorkflowStatus.AWAITING_APPROVAL.value,
        "created_at": "2025-01-24T00:00:00",
        "updated_at": "2025-01-24T00:00:00",
        "requires_approval": True,
        "approved": None,
        "rollout_history": []
    }
    
    # Reject it
    state = manager.reject_workflow(workflow_id)
    
    assert state is not None
    assert state.approved is False
    assert state.status == WorkflowStatus.REJECTED

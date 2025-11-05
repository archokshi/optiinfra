"""
Workflow Models Tests

Tests for workflow state models.
"""

import pytest
from datetime import datetime
from src.models.workflow import (
    WorkflowStatus,
    RolloutStage,
    RolloutStatus,
    WorkflowState,
    WorkflowRequest
)


@pytest.mark.unit
def test_workflow_status_enum():
    """Test workflow status enum."""
    assert WorkflowStatus.PENDING.value == "pending"
    assert WorkflowStatus.COMPLETED.value == "completed"
    assert WorkflowStatus.ROLLED_BACK.value == "rolled_back"


@pytest.mark.unit
def test_rollout_stage_enum():
    """Test rollout stage enum."""
    assert RolloutStage.STAGE_10.value == "10%"
    assert RolloutStage.STAGE_50.value == "50%"
    assert RolloutStage.STAGE_100.value == "100%"


@pytest.mark.unit
def test_rollout_status_model():
    """Test rollout status model."""
    status = RolloutStatus(
        stage=RolloutStage.STAGE_10,
        status="success",
        started_at=datetime.utcnow(),
        health_score_before=75.0,
        health_score_after=85.0
    )
    
    assert status.stage == RolloutStage.STAGE_10
    assert status.status == "success"
    assert status.health_score_before == 75.0
    assert status.health_score_after == 85.0


@pytest.mark.unit
def test_workflow_state_model():
    """Test workflow state model."""
    state = WorkflowState(
        workflow_id="test-123",
        instance_id="localhost:8000",
        instance_type="vllm",
        status=WorkflowStatus.PENDING
    )
    
    assert state.workflow_id == "test-123"
    assert state.instance_id == "localhost:8000"
    assert state.instance_type == "vllm"
    assert state.status == WorkflowStatus.PENDING
    assert state.requires_approval is True
    assert state.health_threshold == 0.9


@pytest.mark.unit
def test_workflow_request_model():
    """Test workflow request model."""
    request = WorkflowRequest(
        instance_id="localhost:8000",
        instance_type="vllm",
        requires_approval=False,
        auto_rollout=True
    )
    
    assert request.instance_id == "localhost:8000"
    assert request.instance_type == "vllm"
    assert request.requires_approval is False
    assert request.auto_rollout is True

"""
Workflow API Tests

Tests for workflow API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
def test_start_workflow_endpoint(client: TestClient):
    """Test starting a workflow via API."""
    with patch('src.api.workflows.workflow_manager.start_workflow') as mock_start:
        # Setup mock
        from src.models.workflow import WorkflowState, WorkflowStatus
        mock_state = WorkflowState(
            workflow_id="test-123",
            instance_id="localhost:8000",
            instance_type="vllm",
            status=WorkflowStatus.COMPLETED
        )
        mock_start.return_value = mock_state
        
        # Make request
        response = client.post(
            "/api/v1/workflows",
            json={
                "instance_id": "localhost:8000",
                "instance_type": "vllm",
                "requires_approval": False,
                "auto_rollout": True
            }
        )
        
        # Verify
        assert response.status_code == 201
        data = response.json()
        assert data["workflow_id"] == "test-123"
        assert data["status"] == "completed"


@pytest.mark.unit
def test_get_workflow_endpoint(client: TestClient):
    """Test getting workflow status via API."""
    with patch('src.api.workflows.workflow_manager.get_workflow') as mock_get:
        # Setup mock
        from src.models.workflow import WorkflowState, WorkflowStatus
        mock_state = WorkflowState(
            workflow_id="test-123",
            instance_id="localhost:8000",
            instance_type="vllm",
            status=WorkflowStatus.ROLLING_OUT
        )
        mock_get.return_value = mock_state
        
        # Make request
        response = client.get("/api/v1/workflows/test-123")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == "test-123"
        assert data["status"] == "rolling_out"


@pytest.mark.unit
def test_get_workflow_not_found(client: TestClient):
    """Test getting non-existent workflow."""
    with patch('src.api.workflows.workflow_manager.get_workflow') as mock_get:
        mock_get.return_value = None
        
        response = client.get("/api/v1/workflows/non-existent")
        
        assert response.status_code == 404


@pytest.mark.unit
def test_approve_workflow_endpoint(client: TestClient):
    """Test approving a workflow via API."""
    with patch('src.api.workflows.workflow_manager.approve_workflow') as mock_approve:
        # Setup mock
        from src.models.workflow import WorkflowState, WorkflowStatus
        mock_state = WorkflowState(
            workflow_id="test-123",
            instance_id="localhost:8000",
            instance_type="vllm",
            status=WorkflowStatus.APPROVED,
            approved=True,
            approved_by="admin"
        )
        mock_approve.return_value = mock_state
        
        # Make request
        response = client.post("/api/v1/workflows/test-123/approve?approved_by=admin")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] is True
        assert data["approved_by"] == "admin"


@pytest.mark.unit
def test_reject_workflow_endpoint(client: TestClient):
    """Test rejecting a workflow via API."""
    with patch('src.api.workflows.workflow_manager.reject_workflow') as mock_reject:
        # Setup mock
        from src.models.workflow import WorkflowState, WorkflowStatus
        mock_state = WorkflowState(
            workflow_id="test-123",
            instance_id="localhost:8000",
            instance_type="vllm",
            status=WorkflowStatus.REJECTED,
            approved=False
        )
        mock_reject.return_value = mock_state
        
        # Make request
        response = client.post("/api/v1/workflows/test-123/reject")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] is False
        assert data["status"] == "rejected"

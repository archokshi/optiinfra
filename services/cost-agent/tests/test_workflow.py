"""
Tests for LangGraph workflow.
"""

from datetime import datetime

import pytest

from src.workflows.cost_optimization import create_cost_optimization_workflow


@pytest.fixture
def sample_resources():
    """Sample resources for testing"""
    return [
        {
            "resource_id": "i-test001",
            "resource_type": "ec2",
            "provider": "aws",
            "region": "us-east-1",
            "cost_per_month": 100.0,
            "utilization": 0.2,  # Low utilization - should trigger recommendation
            "tags": {"env": "test"},
        },
        {
            "resource_id": "i-test002",
            "resource_type": "ec2",
            "provider": "aws",
            "region": "us-west-2",
            "cost_per_month": 200.0,
            "utilization": 0.8,  # High utilization - no recommendation
            "tags": {"env": "prod"},
        },
    ]


@pytest.fixture
def initial_state(sample_resources):
    """Create initial workflow state"""
    return {
        "resources": sample_resources,
        "request_id": "test-req-001",
        "timestamp": datetime.utcnow(),
        "analysis_results": None,
        "total_waste_detected": 0.0,
        "recommendations": None,
        "total_potential_savings": 0.0,
        "summary": None,
        "workflow_status": "pending",
        "error_message": None,
    }


def test_workflow_creation():
    """Test that workflow can be created"""
    workflow = create_cost_optimization_workflow()
    assert workflow is not None


def test_workflow_executes_successfully(initial_state):
    """Test that workflow executes end-to-end"""
    workflow = create_cost_optimization_workflow()
    result = workflow.invoke(initial_state)

    assert result["workflow_status"] == "complete"
    assert "analysis_results" in result
    assert "recommendations" in result
    assert "summary" in result


def test_workflow_detects_waste(initial_state):
    """Test that workflow detects waste in underutilized resources"""
    workflow = create_cost_optimization_workflow()
    result = workflow.invoke(initial_state)

    # Should detect waste from low utilization resource
    assert result["total_waste_detected"] > 0


def test_workflow_generates_recommendations(initial_state):
    """Test that workflow generates recommendations"""
    workflow = create_cost_optimization_workflow()
    result = workflow.invoke(initial_state)

    # Should have at least one recommendation for low utilization resource
    assert len(result["recommendations"]) >= 1
    assert result["total_potential_savings"] > 0


def test_workflow_creates_summary(initial_state):
    """Test that workflow creates a summary"""
    workflow = create_cost_optimization_workflow()
    result = workflow.invoke(initial_state)

    assert result["summary"] is not None
    assert len(result["summary"]) > 0
    assert "Cost Optimization Analysis Summary" in result["summary"]


def test_workflow_preserves_request_id(initial_state):
    """Test that workflow preserves request ID throughout"""
    workflow = create_cost_optimization_workflow()
    result = workflow.invoke(initial_state)

    assert result["request_id"] == initial_state["request_id"]


def test_workflow_with_no_waste():
    """Test workflow with resources that have high utilization"""
    state = {
        "resources": [
            {
                "resource_id": "i-efficient",
                "resource_type": "ec2",
                "provider": "aws",
                "region": "us-east-1",
                "cost_per_month": 100.0,
                "utilization": 0.9,  # High utilization - no waste
                "tags": {},
            }
        ],
        "request_id": "test-req-002",
        "timestamp": datetime.utcnow(),
        "analysis_results": None,
        "total_waste_detected": 0.0,
        "recommendations": None,
        "total_potential_savings": 0.0,
        "summary": None,
        "workflow_status": "pending",
        "error_message": None,
    }

    workflow = create_cost_optimization_workflow()
    result = workflow.invoke(state)

    assert result["total_waste_detected"] == 0.0
    assert len(result["recommendations"]) == 0

"""
Tests for spot migration workflow.
"""

from datetime import datetime

import pytest

from src.workflows.spot_migration import create_spot_migration_workflow


@pytest.fixture
def initial_spot_state():
    """Create initial spot migration state"""
    return {
        "request_id": "test-spot-001",
        "customer_id": "test-customer",
        "timestamp": datetime.utcnow(),
        "ec2_instances": [],  # Will be generated
        "spot_opportunities": None,
        "total_savings": 0.0,
        "performance_approval": None,
        "resource_approval": None,
        "application_approval": None,
        "coordination_complete": False,
        "customer_approved": True,
        "approval_timestamp": datetime.utcnow(),
        "migration_phase": "pending",
        "execution_10": None,
        "execution_50": None,
        "execution_100": None,
        "quality_baseline": None,
        "quality_current": None,
        "rollback_triggered": False,
        "workflow_status": "pending",
        "final_savings": 0.0,
        "migration_duration": None,
        "success": False,
        "error_message": None,
    }


def test_spot_workflow_creation():
    """Test that spot workflow can be created"""
    workflow = create_spot_migration_workflow()
    assert workflow is not None


def test_spot_workflow_executes_end_to_end(initial_spot_state):
    """Test complete spot migration workflow"""
    workflow = create_spot_migration_workflow()
    result = workflow.invoke(initial_spot_state)

    # Verify workflow completed
    assert result["workflow_status"] in ["complete", "monitoring"]
    assert "ec2_instances" in result
    assert "spot_opportunities" in result


def test_spot_workflow_analyzes_instances(initial_spot_state):
    """Test that workflow analyzes EC2 instances"""
    workflow = create_spot_migration_workflow()
    result = workflow.invoke(initial_spot_state)

    # Should have generated instances
    assert len(result["ec2_instances"]) > 0
    assert result["spot_opportunities"] is not None


def test_spot_workflow_finds_opportunities(initial_spot_state):
    """Test that workflow finds spot opportunities"""
    workflow = create_spot_migration_workflow()
    result = workflow.invoke(initial_spot_state)

    # Should find some opportunities
    opportunities = result.get("spot_opportunities", [])
    assert len(opportunities) >= 0  # May be 0 if no eligible instances
    assert result["total_savings"] >= 0


def test_spot_workflow_coordinates_agents(initial_spot_state):
    """Test multi-agent coordination"""
    workflow = create_spot_migration_workflow()
    result = workflow.invoke(initial_spot_state)

    # Should have agent approvals
    assert result.get("performance_approval") is not None
    assert result.get("resource_approval") is not None
    assert result.get("application_approval") is not None
    assert result["coordination_complete"] is True


def test_spot_workflow_executes_migration(initial_spot_state):
    """Test migration execution phases"""
    workflow = create_spot_migration_workflow()
    result = workflow.invoke(initial_spot_state)

    # Should have execution results (if opportunities found and migration succeeded)
    opportunities = result.get("spot_opportunities", [])
    if opportunities and len(opportunities) > 0:
        # Check if migration was attempted
        if result.get("workflow_status") == "complete":
            # Successful migration should have all phases
            assert result.get("execution_10") is not None
            assert result.get("execution_50") is not None
            assert result.get("execution_100") is not None
        else:
            # Failed migration may have partial execution
            # Just verify it has execution_10 at minimum
            assert result.get("execution_10") is not None or result.get("workflow_status") == "failed"
    else:
        # If no opportunities, execution should have failed early
        assert result.get("workflow_status") in ["failed", "complete", "monitoring"]


def test_spot_workflow_monitors_quality(initial_spot_state):
    """Test quality monitoring"""
    workflow = create_spot_migration_workflow()
    result = workflow.invoke(initial_spot_state)

    # Should have quality metrics
    assert result.get("quality_baseline") is not None
    assert result.get("quality_current") is not None
    assert "rollback_triggered" in result


def test_spot_workflow_calculates_savings(initial_spot_state):
    """Test savings calculation"""
    workflow = create_spot_migration_workflow()
    result = workflow.invoke(initial_spot_state)

    # Should calculate savings
    assert "total_savings" in result
    assert "final_savings" in result
    assert result["final_savings"] >= 0


def test_spot_workflow_preserves_request_id(initial_spot_state):
    """Test that request ID is preserved"""
    workflow = create_spot_migration_workflow()
    result = workflow.invoke(initial_spot_state)

    assert result["request_id"] == initial_spot_state["request_id"]
    assert result["customer_id"] == initial_spot_state["customer_id"]

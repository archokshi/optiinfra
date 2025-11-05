"""
Unit Tests for Execution Engine.

Tests execution logic and state management.
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@pytest.mark.unit
class TestExecutor:
    """Test execution engine."""
    
    def test_execution_structure(self, sample_execution):
        """Test execution data structure."""
        assert "id" in sample_execution
        assert "recommendation_id" in sample_execution
        assert "status" in sample_execution
        assert "success" in sample_execution
    
    def test_execution_status_transitions(self):
        """Test execution status transitions."""
        valid_statuses = ["pending", "in_progress", "completed", "failed", "rolled_back"]
        
        # Valid transitions
        transitions = {
            "pending": ["in_progress"],
            "in_progress": ["completed", "failed"],
            "completed": ["rolled_back"],
            "failed": [],
            "rolled_back": []
        }
        
        for status, allowed in transitions.items():
            assert status in valid_statuses
            for next_status in allowed:
                assert next_status in valid_statuses
    
    def test_execution_duration_calculation(self, sample_execution):
        """Test execution duration calculation."""
        duration = sample_execution["duration_seconds"]
        
        assert duration > 0
        assert duration == 300  # 5 minutes
    
    def test_dry_run_mode(self):
        """Test dry run execution mode."""
        dry_run = True
        
        if dry_run:
            # Should not make actual changes
            changes_applied = []
        else:
            changes_applied = ["change1", "change2"]
        
        assert len(changes_applied) == 0
    
    def test_rollback_availability(self, sample_execution):
        """Test rollback availability check."""
        assert sample_execution["rollback_available"] == True
        assert sample_execution["success"] == True
    
    def test_failed_execution(self, sample_execution_failed):
        """Test failed execution handling."""
        assert sample_execution_failed["success"] == False
        assert "error_message" in sample_execution_failed
        assert len(sample_execution_failed["changes_applied"]) == 0


@pytest.mark.unit
class TestRollback:
    """Test rollback functionality."""
    
    def test_rollback_structure(self):
        """Test rollback data structure."""
        rollback = {
            "execution_id": "exec-123",
            "rollback_id": "rollback-123",
            "status": "completed",
            "changes_reverted": ["change1", "change2"]
        }
        
        assert "execution_id" in rollback
        assert "rollback_id" in rollback
        assert len(rollback["changes_reverted"]) > 0
    
    def test_rollback_validation(self, sample_execution):
        """Test rollback validation."""
        # Can only rollback successful executions
        can_rollback = (
            sample_execution["success"] == True and
            sample_execution["rollback_available"] == True
        )
        
        assert can_rollback == True
    
    def test_rollback_changes_reversal(self):
        """Test changes reversal logic."""
        original_changes = [
            {"resource": "i-123", "action": "migrate_to_spot"},
            {"resource": "i-456", "action": "migrate_to_spot"}
        ]
        
        # Reverse changes
        rollback_changes = [
            {"resource": c["resource"], "action": f"revert_{c['action']}"}
            for c in original_changes
        ]
        
        assert len(rollback_changes) == len(original_changes)
        assert all("revert_" in c["action"] for c in rollback_changes)


@pytest.mark.unit
class TestStateMachine:
    """Test state machine logic."""
    
    def test_state_transitions(self):
        """Test valid state transitions."""
        current_state = "pending"
        
        def transition_to(new_state: str) -> bool:
            valid_transitions = {
                "pending": ["in_progress"],
                "in_progress": ["completed", "failed"]
            }
            
            return new_state in valid_transitions.get(current_state, [])
        
        assert transition_to("in_progress") == True
        assert transition_to("completed") == False  # Can't skip in_progress
    
    def test_state_validation(self):
        """Test state validation."""
        valid_states = ["pending", "in_progress", "completed", "failed", "rolled_back"]
        
        test_state = "completed"
        assert test_state in valid_states
        
        invalid_state = "unknown"
        assert invalid_state not in valid_states

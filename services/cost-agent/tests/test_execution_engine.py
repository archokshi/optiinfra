"""
Comprehensive tests for Execution Engine.

Tests cover:
- Execution Engine Core (8 tests)
- Validation (6 tests)
- Executors (8 tests)
- Rollback (4 tests)
- Integration (4 tests)

Total: 30+ tests
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from src.execution.engine import ExecutionEngine
from src.execution.validator import ExecutionValidator
from src.execution.rollback import RollbackManager
from src.execution.executors.terminate import TerminateExecutor
from src.execution.executors.rightsize import RightSizeExecutor
from src.models.execution_engine import (
    ExecutionStatus,
    RiskLevel,
    ExecutionRequest
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_recommendation():
    """Sample recommendation for testing."""
    return {
        "recommendation_id": "rec-test-123",
        "recommendation_type": "terminate",
        "resource_id": "i-test123",
        "resource_type": "ec2",
        "region": "us-east-1",
        "monthly_savings": 52.00,
        "requires_approval": True
    }


@pytest.fixture
def sample_rightsize_recommendation():
    """Sample right-size recommendation."""
    return {
        "recommendation_id": "rec-test-456",
        "recommendation_type": "right_size",
        "resource_id": "i-test456",
        "resource_type": "ec2",
        "region": "us-east-1",
        "current_type": "t3.large",
        "target_type": "t3.medium",
        "monthly_savings": 30.00
    }


@pytest.fixture
def execution_engine():
    """Execution engine instance."""
    return ExecutionEngine()


@pytest.fixture
def validator():
    """Validator instance."""
    return ExecutionValidator()


@pytest.fixture
def rollback_manager():
    """Rollback manager instance."""
    return RollbackManager()


# ============================================================================
# EXECUTION ENGINE CORE TESTS (8 tests)
# ============================================================================

class TestExecutionEngine:
    """Test execution engine core functionality."""
    
    @pytest.mark.asyncio
    async def test_execute_recommendation_dry_run(self, execution_engine, sample_recommendation):
        """Test dry-run execution."""
        result = await execution_engine.execute_recommendation(
            recommendation_id=sample_recommendation["recommendation_id"],
            dry_run=True,
            auto_approve=True
        )
        
        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED
        assert result.execution_id is not None
        assert result.duration_seconds is not None
        assert len(result.execution_log) > 0
    
    @pytest.mark.asyncio
    async def test_execute_recommendation_live(self, execution_engine, sample_recommendation):
        """Test live execution."""
        result = await execution_engine.execute_recommendation(
            recommendation_id=sample_recommendation["recommendation_id"],
            dry_run=False,
            auto_approve=True
        )
        
        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED
        assert result.actual_savings is not None
    
    @pytest.mark.asyncio
    async def test_get_execution_status(self, execution_engine, sample_recommendation):
        """Test getting execution status."""
        # Execute first
        result = await execution_engine.execute_recommendation(
            recommendation_id=sample_recommendation["recommendation_id"],
            dry_run=True,
            auto_approve=True
        )
        
        # Get status
        status = await execution_engine.get_execution_status(result.execution_id)
        
        assert status.execution_id == result.execution_id
        assert status.status == ExecutionStatus.COMPLETED
        assert status.progress_percent == 100
        assert status.current_step == "Completed"
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self, execution_engine):
        """Test cancelling an execution."""
        # Create a pending execution
        execution_id = "test-exec-123"
        execution_engine.executions[execution_id] = {
            "execution_id": execution_id,
            "recommendation_id": "rec-123",
            "status": ExecutionStatus.PENDING,
            "started_at": datetime.utcnow(),
            "execution_log": []
        }
        
        # Cancel it
        success = await execution_engine.cancel_execution(execution_id)
        
        assert success is True
        assert execution_engine.executions[execution_id]["status"] == ExecutionStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_cannot_cancel_completed_execution(self, execution_engine, sample_recommendation):
        """Test that completed executions cannot be cancelled."""
        # Execute first
        result = await execution_engine.execute_recommendation(
            recommendation_id=sample_recommendation["recommendation_id"],
            dry_run=True,
            auto_approve=True
        )
        
        # Try to cancel
        success = await execution_engine.cancel_execution(result.execution_id)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_execution_with_invalid_recommendation(self, execution_engine):
        """Test execution with non-existent recommendation."""
        result = await execution_engine.execute_recommendation(
            recommendation_id="non-existent",
            dry_run=True,
            auto_approve=True
        )
        
        # Should complete (mock recommendation is returned)
        assert result.execution_id is not None
    
    @pytest.mark.asyncio
    async def test_execution_state_transitions(self, execution_engine, sample_recommendation):
        """Test execution state machine transitions."""
        result = await execution_engine.execute_recommendation(
            recommendation_id=sample_recommendation["recommendation_id"],
            dry_run=True,
            auto_approve=True
        )
        
        # Verify final state
        status = await execution_engine.get_execution_status(result.execution_id)
        assert status.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]
    
    @pytest.mark.asyncio
    async def test_execution_logging(self, execution_engine, sample_recommendation):
        """Test that execution logs are captured."""
        result = await execution_engine.execute_recommendation(
            recommendation_id=sample_recommendation["recommendation_id"],
            dry_run=True,
            auto_approve=True
        )
        
        assert len(result.execution_log) > 0
        assert any("Started execution" in log for log in result.execution_log)
        assert any("completed" in log.lower() for log in result.execution_log)


# ============================================================================
# VALIDATION TESTS (6 tests)
# ============================================================================

class TestExecutionValidator:
    """Test execution validation functionality."""
    
    @pytest.mark.asyncio
    async def test_validate_valid_recommendation(self, validator, sample_recommendation):
        """Test validation of valid recommendation."""
        result = await validator.validate_execution(sample_recommendation)
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert result.estimated_duration_minutes > 0
    
    @pytest.mark.asyncio
    async def test_validate_missing_fields(self, validator):
        """Test validation with missing required fields."""
        incomplete_rec = {
            "recommendation_id": "rec-123"
            # Missing recommendation_type and resource_id
        }
        
        result = await validator.validate_execution(incomplete_rec)
        
        assert result.valid is False
        assert len(result.errors) > 0
        assert len(result.blocking_issues) > 0
    
    @pytest.mark.asyncio
    async def test_check_permissions(self, validator, sample_recommendation):
        """Test permission checking."""
        has_permission = await validator.check_permissions(sample_recommendation)
        
        # Mock always returns True
        assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_check_dependencies(self, validator, sample_recommendation):
        """Test dependency checking."""
        dependencies = await validator.check_dependencies(sample_recommendation)
        
        # Mock returns empty list
        assert isinstance(dependencies, list)
    
    @pytest.mark.asyncio
    async def test_assess_risk(self, validator, sample_recommendation):
        """Test risk assessment."""
        assessment = await validator.assess_risk(sample_recommendation)
        
        assert "risk_level" in assessment
        assert "warnings" in assessment
        assert assessment["risk_level"] in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_risk_levels_by_type(self, validator):
        """Test that different recommendation types have appropriate risk levels."""
        # Terminate should be high risk
        terminate_rec = {
            "recommendation_id": "rec-1",
            "recommendation_type": "terminate",
            "resource_id": "i-123",
            "resource_type": "ec2"
        }
        
        result = await validator.validate_execution(terminate_rec)
        assert result.risk_level == RiskLevel.HIGH
        
        # Hibernate should be low risk
        hibernate_rec = {
            "recommendation_id": "rec-2",
            "recommendation_type": "hibernate",
            "resource_id": "i-456",
            "resource_type": "ec2"
        }
        
        result = await validator.validate_execution(hibernate_rec)
        assert result.risk_level == RiskLevel.LOW


# ============================================================================
# EXECUTOR TESTS (8 tests)
# ============================================================================

class TestExecutors:
    """Test executor implementations."""
    
    @pytest.mark.asyncio
    async def test_terminate_executor_dry_run(self, sample_recommendation):
        """Test terminate executor in dry-run mode."""
        executor = TerminateExecutor()
        
        result = await executor.execute(sample_recommendation, dry_run=True)
        
        assert result.success is True
        assert "Would terminate" in result.message
        assert len(result.changes_made) > 0
    
    @pytest.mark.asyncio
    async def test_terminate_executor_live(self, sample_recommendation):
        """Test terminate executor in live mode."""
        executor = TerminateExecutor()
        
        result = await executor.execute(sample_recommendation, dry_run=False)
        
        assert result.success is True
        assert "Successfully terminated" in result.message
        assert "backup_id" in result.details
    
    @pytest.mark.asyncio
    async def test_terminate_executor_rollback(self):
        """Test terminate executor rollback."""
        executor = TerminateExecutor()
        
        execution_record = {
            "backup_id": "backup-123",
            "resource_type": "ec2"
        }
        
        result = await executor.rollback(execution_record)
        
        assert result.success is True
        assert "Restored" in result.message
    
    @pytest.mark.asyncio
    async def test_terminate_executor_verify(self):
        """Test terminate executor verification."""
        executor = TerminateExecutor()
        
        execution_record = {
            "resource_id": "i-123",
            "resource_type": "ec2"
        }
        
        verified = await executor.verify(execution_record)
        
        assert verified is True
    
    @pytest.mark.asyncio
    async def test_rightsize_executor_dry_run(self, sample_rightsize_recommendation):
        """Test right-size executor in dry-run mode."""
        executor = RightSizeExecutor()
        
        result = await executor.execute(sample_rightsize_recommendation, dry_run=True)
        
        assert result.success is True
        assert "Would right-size" in result.message
        assert result.rollback_info.get("original_type") is not None
    
    @pytest.mark.asyncio
    async def test_rightsize_executor_live(self, sample_rightsize_recommendation):
        """Test right-size executor in live mode."""
        executor = RightSizeExecutor()
        
        result = await executor.execute(sample_rightsize_recommendation, dry_run=False)
        
        assert result.success is True
        assert "Successfully right-sized" in result.message
    
    @pytest.mark.asyncio
    async def test_rightsize_executor_rollback(self):
        """Test right-size executor rollback."""
        executor = RightSizeExecutor()
        
        execution_record = {
            "original_type": "t3.large"
        }
        
        result = await executor.rollback(execution_record)
        
        assert result.success is True
        assert "t3.large" in result.message
    
    @pytest.mark.asyncio
    async def test_executor_registry(self, execution_engine):
        """Test that all executors are registered."""
        expected_executors = [
            "terminate", "right_size", "hibernate", "spot",
            "ri", "auto_scale", "storage_optimize", "config_fix"
        ]
        
        for executor_type in expected_executors:
            assert executor_type in execution_engine.executors


# ============================================================================
# ROLLBACK TESTS (4 tests)
# ============================================================================

class TestRollbackManager:
    """Test rollback management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_rollback_plan(self, rollback_manager, sample_recommendation):
        """Test rollback plan creation."""
        plan = await rollback_manager.create_rollback_plan(sample_recommendation)
        
        assert plan.execution_id is not None
        assert len(plan.rollback_steps) > 0
        assert plan.estimated_duration_minutes > 0
        assert plan.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_execute_rollback(self, rollback_manager, sample_recommendation):
        """Test rollback execution."""
        result = await rollback_manager.execute_rollback(
            execution_id="exec-123",
            recommendation=sample_recommendation,
            rollback_info={}
        )
        
        assert result.success is True
        assert len(result.rollback_log) > 0
        assert result.rollback_started_at is not None
    
    @pytest.mark.asyncio
    async def test_verify_rollback(self, rollback_manager, sample_recommendation):
        """Test rollback verification."""
        verified = await rollback_manager.verify_rollback(
            execution_id="exec-123",
            recommendation=sample_recommendation
        )
        
        assert verified is True
    
    @pytest.mark.asyncio
    async def test_rollback_plan_by_type(self, rollback_manager):
        """Test that different types have appropriate rollback plans."""
        # Terminate should have complex rollback
        terminate_rec = {
            "recommendation_type": "terminate",
            "resource_id": "i-123"
        }
        
        plan = await rollback_manager.create_rollback_plan(terminate_rec)
        assert len(plan.rollback_steps) >= 3
        assert plan.risk_level == RiskLevel.HIGH
        
        # Hibernate should have simple rollback
        hibernate_rec = {
            "recommendation_type": "hibernate",
            "resource_id": "i-456"
        }
        
        plan = await rollback_manager.create_rollback_plan(hibernate_rec)
        assert plan.risk_level == RiskLevel.LOW


# ============================================================================
# INTEGRATION TESTS (4 tests)
# ============================================================================

class TestIntegration:
    """Test end-to-end integration."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_execution_flow(self, execution_engine, sample_recommendation):
        """Test complete execution flow."""
        # Execute
        result = await execution_engine.execute_recommendation(
            recommendation_id=sample_recommendation["recommendation_id"],
            dry_run=True,
            auto_approve=True
        )
        
        assert result.success is True
        
        # Get status
        status = await execution_engine.get_execution_status(result.execution_id)
        assert status.status == ExecutionStatus.COMPLETED
        
        # Verify logs
        assert len(status.execution_log) > 0
    
    @pytest.mark.asyncio
    async def test_execution_with_rollback(self, execution_engine, sample_recommendation):
        """Test execution followed by rollback."""
        # Execute
        result = await execution_engine.execute_recommendation(
            recommendation_id=sample_recommendation["recommendation_id"],
            dry_run=True,
            auto_approve=True
        )
        
        assert result.success is True
        
        # Rollback
        rollback_result = await execution_engine.rollback_execution(result.execution_id)
        assert rollback_result.success is True
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_executions(self, execution_engine):
        """Test multiple executions running concurrently."""
        recommendations = [
            {"recommendation_id": f"rec-{i}", "recommendation_type": "terminate", 
             "resource_id": f"i-{i}", "resource_type": "ec2"}
            for i in range(3)
        ]
        
        # Execute all concurrently
        tasks = [
            execution_engine.execute_recommendation(
                recommendation_id=rec["recommendation_id"],
                dry_run=True,
                auto_approve=True
            )
            for rec in recommendations
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.success for r in results)
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_execution_error_handling(self, execution_engine):
        """Test error handling in execution flow."""
        # This should handle gracefully even with invalid data
        result = await execution_engine.execute_recommendation(
            recommendation_id="invalid-rec",
            dry_run=True,
            auto_approve=True
        )
        
        # Should complete (mock returns valid recommendation)
        assert result.execution_id is not None


# ============================================================================
# PYDANTIC MODEL TESTS (2 tests)
# ============================================================================

class TestPydanticModels:
    """Test Pydantic model validation."""
    
    def test_execution_request_validation(self):
        """Test ExecutionRequest model validation."""
        # Valid request
        request = ExecutionRequest(
            recommendation_id="rec-123",
            dry_run=True,
            auto_approve=False
        )
        
        assert request.recommendation_id == "rec-123"
        assert request.dry_run is True
    
    def test_execution_request_defaults(self):
        """Test ExecutionRequest default values."""
        request = ExecutionRequest(recommendation_id="rec-123")
        
        assert request.dry_run is False
        assert request.auto_approve is False
        assert request.force is False
        assert request.scheduled_time is None


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

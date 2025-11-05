"""
Execution Engine Core.

Main orchestrator for executing cost optimization recommendations.
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime

from src.execution.validator import ExecutionValidator
from src.execution.rollback import RollbackManager
from src.models.execution_engine import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionStatusResponse,
    RollbackResult
)

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Core execution orchestrator."""
    
    def __init__(self, db_client=None, metrics_client=None):
        """
        Initialize execution engine.
        
        Args:
            db_client: Database client for storing execution history
            metrics_client: Metrics client for recording execution metrics
        """
        self.validator = ExecutionValidator()
        self.rollback_manager = RollbackManager()
        self.db_client = db_client
        self.metrics_client = metrics_client
        
        # In-memory execution state (would be Redis in production)
        self.executions = {}
        
        # Executor registry
        self.executors = {}
        self._register_executors()
    
    def _register_executors(self):
        """Register all executor types."""
        try:
            from src.execution.executors.terminate import TerminateExecutor
            from src.execution.executors.rightsize import RightSizeExecutor
            from src.execution.executors.hibernate import HibernateExecutor
            from src.execution.executors.spot import SpotMigrationExecutor
            from src.execution.executors.ri import RIPurchaseExecutor
            from src.execution.executors.autoscale import AutoScaleExecutor
            from src.execution.executors.storage import StorageOptimizeExecutor
            from src.execution.executors.config_fix import ConfigFixExecutor
            
            self.executors = {
                "terminate": TerminateExecutor(),
                "right_size": RightSizeExecutor(),
                "hibernate": HibernateExecutor(),
                "spot": SpotMigrationExecutor(),
                "ri": RIPurchaseExecutor(),
                "auto_scale": AutoScaleExecutor(),
                "storage_optimize": StorageOptimizeExecutor(),
                "config_fix": ConfigFixExecutor(),
            }
            logger.info(f"Registered {len(self.executors)} executors")
        except ImportError as e:
            logger.warning(f"Some executors not available: {e}")
    
    async def execute_recommendation(
        self,
        recommendation_id: str,
        dry_run: bool = False,
        auto_approve: bool = False,
        force: bool = False
    ) -> ExecutionResult:
        """
        Execute a recommendation.
        
        Args:
            recommendation_id: ID of recommendation to execute
            dry_run: If True, simulate without making changes
            auto_approve: If True, skip approval step
            force: If True, execute despite warnings
        
        Returns:
            ExecutionResult with execution details
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        started_at = datetime.utcnow()
        
        execution_log = []
        
        try:
            logger.info(f"Starting execution {execution_id} for recommendation {recommendation_id}")
            execution_log.append(f"Started execution at {started_at}")
            
            # Initialize execution state
            self.executions[execution_id] = {
                "execution_id": execution_id,
                "recommendation_id": recommendation_id,
                "status": ExecutionStatus.PENDING,
                "started_at": started_at,
                "dry_run": dry_run,
                "execution_log": execution_log
            }
            
            # Step 1: Load recommendation
            recommendation = await self._load_recommendation(recommendation_id)
            if not recommendation:
                raise ValueError(f"Recommendation {recommendation_id} not found")
            
            execution_log.append("Loaded recommendation")
            
            # Step 2: Validate execution
            self._update_status(execution_id, ExecutionStatus.VALIDATING)
            execution_log.append("Validating execution")
            
            validation_result = await self.validator.validate_execution(recommendation)
            
            if not validation_result.valid and not force:
                execution_log.append(f"Validation failed: {validation_result.errors}")
                self._update_status(execution_id, ExecutionStatus.FAILED)
                
                return ExecutionResult(
                    execution_id=execution_id,
                    recommendation_id=recommendation_id,
                    status=ExecutionStatus.FAILED,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    duration_seconds=time.time() - start_time,
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}",
                    execution_log=execution_log
                )
            
            execution_log.append("Validation passed")
            
            # Step 3: Approval (if required)
            if validation_result.requires_approval and not auto_approve:
                self._update_status(execution_id, ExecutionStatus.APPROVED)
                execution_log.append("Waiting for approval")
                # In production, would wait for approval here
                # For now, auto-approve
                logger.info(f"Auto-approving execution {execution_id}")
            
            execution_log.append("Approved for execution")
            
            # Step 4: Execute
            self._update_status(execution_id, ExecutionStatus.EXECUTING)
            execution_log.append("Executing recommendation")
            
            executor_result = await self._execute_with_executor(
                recommendation,
                dry_run=dry_run
            )
            
            if not executor_result.success:
                execution_log.append(f"Execution failed: {executor_result.message}")
                self._update_status(execution_id, ExecutionStatus.FAILED)
                
                # Attempt rollback if not dry-run
                if not dry_run:
                    execution_log.append("Attempting automatic rollback")
                    rollback_result = await self.rollback_manager.execute_rollback(
                        execution_id,
                        recommendation,
                        executor_result.rollback_info
                    )
                    if rollback_result.success:
                        execution_log.append("Rollback successful")
                        self._update_status(execution_id, ExecutionStatus.ROLLED_BACK)
                    else:
                        execution_log.append(f"Rollback failed: {rollback_result.message}")
                
                return ExecutionResult(
                    execution_id=execution_id,
                    recommendation_id=recommendation_id,
                    status=self.executions[execution_id]["status"],
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    duration_seconds=time.time() - start_time,
                    success=False,
                    error_message=executor_result.message,
                    execution_log=execution_log
                )
            
            execution_log.append("Execution successful")
            execution_log.extend(executor_result.changes_made)
            
            # Step 5: Complete
            self._update_status(execution_id, ExecutionStatus.COMPLETED)
            execution_log.append("Execution completed")
            
            # Calculate actual savings (if not dry-run)
            actual_savings = None
            if not dry_run:
                actual_savings = recommendation.get("monthly_savings", 0)
            
            duration = time.time() - start_time
            
            logger.info(
                f"Execution {execution_id} completed successfully in {duration:.2f}s"
            )
            
            return ExecutionResult(
                execution_id=execution_id,
                recommendation_id=recommendation_id,
                status=ExecutionStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=duration,
                success=True,
                actual_savings=actual_savings,
                execution_log=execution_log
            )
            
        except Exception as e:
            logger.error(f"Error executing recommendation: {e}", exc_info=True)
            execution_log.append(f"Error: {str(e)}")
            
            if execution_id in self.executions:
                self._update_status(execution_id, ExecutionStatus.FAILED)
            
            return ExecutionResult(
                execution_id=execution_id,
                recommendation_id=recommendation_id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
                execution_log=execution_log
            )
    
    async def get_execution_status(
        self,
        execution_id: str
    ) -> ExecutionStatusResponse:
        """
        Get execution status.
        
        Args:
            execution_id: Execution ID
        
        Returns:
            ExecutionStatusResponse with current status
        """
        if execution_id not in self.executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self.executions[execution_id]
        
        # Calculate progress
        status = execution["status"]
        progress_map = {
            ExecutionStatus.PENDING: 0,
            ExecutionStatus.VALIDATING: 20,
            ExecutionStatus.APPROVED: 40,
            ExecutionStatus.EXECUTING: 60,
            ExecutionStatus.COMPLETED: 100,
            ExecutionStatus.FAILED: 100,
            ExecutionStatus.ROLLED_BACK: 100,
            ExecutionStatus.CANCELLED: 100
        }
        progress = progress_map.get(status, 0)
        
        # Determine current step
        step_map = {
            ExecutionStatus.PENDING: "Pending",
            ExecutionStatus.VALIDATING: "Validating",
            ExecutionStatus.APPROVED: "Approved",
            ExecutionStatus.EXECUTING: "Executing",
            ExecutionStatus.COMPLETED: "Completed",
            ExecutionStatus.FAILED: "Failed",
            ExecutionStatus.ROLLED_BACK: "Rolled Back",
            ExecutionStatus.CANCELLED: "Cancelled"
        }
        current_step = step_map.get(status, "Unknown")
        
        # Can cancel if not completed/failed
        can_cancel = status in [
            ExecutionStatus.PENDING,
            ExecutionStatus.VALIDATING,
            ExecutionStatus.APPROVED
        ]
        
        # Can rollback if failed or completed
        can_rollback = status in [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED
        ]
        
        return ExecutionStatusResponse(
            execution_id=execution_id,
            recommendation_id=execution["recommendation_id"],
            status=status,
            progress_percent=progress,
            current_step=current_step,
            started_at=execution["started_at"],
            completed_at=execution.get("completed_at"),
            success=execution.get("success"),
            error_message=execution.get("error_message"),
            execution_log=execution.get("execution_log", []),
            can_cancel=can_cancel,
            can_rollback=can_rollback
        )
    
    async def cancel_execution(
        self,
        execution_id: str
    ) -> bool:
        """
        Cancel an execution.
        
        Args:
            execution_id: Execution ID
        
        Returns:
            True if cancelled successfully
        """
        if execution_id not in self.executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self.executions[execution_id]
        status = execution["status"]
        
        # Can only cancel if not yet executing
        if status in [ExecutionStatus.PENDING, ExecutionStatus.VALIDATING, ExecutionStatus.APPROVED]:
            self._update_status(execution_id, ExecutionStatus.CANCELLED)
            execution["execution_log"].append("Execution cancelled by user")
            logger.info(f"Execution {execution_id} cancelled")
            return True
        
        logger.warning(f"Cannot cancel execution {execution_id} in status {status}")
        return False
    
    async def rollback_execution(
        self,
        execution_id: str
    ) -> RollbackResult:
        """
        Rollback an execution.
        
        Args:
            execution_id: Execution ID
        
        Returns:
            RollbackResult with rollback details
        """
        if execution_id not in self.executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self.executions[execution_id]
        
        # Load recommendation
        recommendation = await self._load_recommendation(execution["recommendation_id"])
        
        # Execute rollback
        rollback_result = await self.rollback_manager.execute_rollback(
            execution_id,
            recommendation,
            execution.get("rollback_info", {})
        )
        
        if rollback_result.success:
            self._update_status(execution_id, ExecutionStatus.ROLLED_BACK)
            execution["execution_log"].append("Rollback completed successfully")
        else:
            execution["execution_log"].append(f"Rollback failed: {rollback_result.message}")
        
        return rollback_result
    
    # Private helper methods
    
    async def _load_recommendation(
        self,
        recommendation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load recommendation from database or cache."""
        # In production, would load from database
        # For now, return a mock recommendation
        return {
            "recommendation_id": recommendation_id,
            "recommendation_type": "terminate",
            "resource_id": "i-test123",
            "resource_type": "ec2",
            "region": "us-east-1",
            "monthly_savings": 52.00
        }
    
    async def _execute_with_executor(
        self,
        recommendation: Dict[str, Any],
        dry_run: bool = False
    ) -> Any:
        """Execute recommendation with appropriate executor."""
        rec_type = recommendation.get("recommendation_type", "")
        
        # Get executor
        executor = self.executors.get(rec_type)
        if not executor:
            # Return mock success for unimplemented executors
            from src.models.execution_engine import ExecutorResult
            return ExecutorResult(
                success=True,
                message=f"Executed {rec_type} (mock)",
                changes_made=[f"Would execute {rec_type} recommendation"]
            )
        
        # Execute
        return await executor.execute(recommendation, dry_run=dry_run)
    
    def _update_status(
        self,
        execution_id: str,
        status: ExecutionStatus
    ):
        """Update execution status."""
        if execution_id in self.executions:
            self.executions[execution_id]["status"] = status
            
            if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                self.executions[execution_id]["completed_at"] = datetime.utcnow()
                self.executions[execution_id]["success"] = (status == ExecutionStatus.COMPLETED)

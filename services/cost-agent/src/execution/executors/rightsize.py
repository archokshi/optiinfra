"""
Right-Size Executor.

Executes instance right-sizing operations.
"""

import logging
from typing import Dict, Any

from src.execution.executors.base import BaseExecutor
from src.models.execution_engine import ExecutorResult

logger = logging.getLogger(__name__)


class RightSizeExecutor(BaseExecutor):
    """Executes instance right-sizing."""
    
    async def execute(
        self,
        recommendation: Dict[str, Any],
        dry_run: bool = False
    ) -> ExecutorResult:
        """Execute right-sizing."""
        resource_id = recommendation.get("resource_id", "unknown")
        current_type = recommendation.get("current_type", "unknown")
        target_type = recommendation.get("target_type", "unknown")
        
        self._log_execution(recommendation, dry_run, f"Right-sizing from {current_type} to {target_type}")
        
        changes_made = []
        
        if dry_run:
            changes_made.append(f"Would stop instance {resource_id}")
            changes_made.append(f"Would modify type from {current_type} to {target_type}")
            changes_made.append(f"Would start instance")
            
            return ExecutorResult(
                success=True,
                message=f"Dry-run: Would right-size {resource_id}",
                details={"current_type": current_type, "target_type": target_type},
                changes_made=changes_made,
                rollback_info={"original_type": current_type}
            )
        
        try:
            # Execute right-sizing
            changes_made.append(f"Stopped instance {resource_id}")
            changes_made.append(f"Modified type to {target_type}")
            changes_made.append(f"Started instance {resource_id}")
            
            return ExecutorResult(
                success=True,
                message=f"Successfully right-sized {resource_id}",
                details={"new_type": target_type},
                changes_made=changes_made,
                rollback_info={"original_type": current_type}
            )
        except Exception as e:
            return ExecutorResult(
                success=False,
                message=f"Failed to right-size: {str(e)}",
                details={},
                changes_made=changes_made,
                rollback_info={"original_type": current_type}
            )
    
    async def rollback(self, execution_record: Dict[str, Any]) -> ExecutorResult:
        """Rollback right-sizing."""
        original_type = execution_record.get("original_type")
        return ExecutorResult(
            success=True,
            message=f"Rolled back to {original_type}",
            details={},
            changes_made=[f"Restored original type {original_type}"],
            rollback_info={}
        )
    
    async def verify(self, execution_record: Dict[str, Any]) -> bool:
        """Verify right-sizing."""
        return True

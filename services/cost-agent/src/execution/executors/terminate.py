"""
Terminate Executor.

Executes termination of idle resources.
"""

import logging
from typing import Dict, Any

from src.execution.executors.base import BaseExecutor
from src.models.execution_engine import ExecutorResult

logger = logging.getLogger(__name__)


class TerminateExecutor(BaseExecutor):
    """Executes resource termination."""
    
    async def execute(
        self,
        recommendation: Dict[str, Any],
        dry_run: bool = False
    ) -> ExecutorResult:
        """Execute termination."""
        resource_id = recommendation.get("resource_id", "unknown")
        resource_type = recommendation.get("resource_type", "unknown")
        region = recommendation.get("region", "us-east-1")
        
        self._log_execution(recommendation, dry_run, "Starting termination")
        
        changes_made = []
        rollback_info = {}
        
        try:
            if dry_run:
                changes_made.append(f"Would terminate {resource_type} {resource_id}")
                changes_made.append(f"Would create final backup")
                changes_made.append(f"Would verify termination")
                
                return ExecutorResult(
                    success=True,
                    message=f"Dry-run: Would terminate {resource_id}",
                    details={
                        "resource_id": resource_id,
                        "resource_type": resource_type,
                        "region": region
                    },
                    changes_made=changes_made,
                    rollback_info={}
                )
            
            # Step 1: Create backup
            self._log_execution(recommendation, dry_run, "Creating final backup")
            backup_id = await self._create_backup(resource_id, resource_type, region)
            changes_made.append(f"Created backup: {backup_id}")
            rollback_info["backup_id"] = backup_id
            
            # Step 2: Stop resource
            self._log_execution(recommendation, dry_run, "Stopping resource")
            await self._stop_resource(resource_id, resource_type, region)
            changes_made.append(f"Stopped {resource_type} {resource_id}")
            
            # Step 3: Wait and verify
            self._log_execution(recommendation, dry_run, "Waiting for stop confirmation")
            await self._wait_for_stop(resource_id, resource_type, region)
            changes_made.append("Verified resource stopped")
            
            # Step 4: Terminate
            self._log_execution(recommendation, dry_run, "Terminating resource")
            await self._terminate_resource(resource_id, resource_type, region)
            changes_made.append(f"Terminated {resource_type} {resource_id}")
            
            self._log_execution(recommendation, dry_run, "Termination completed")
            
            return ExecutorResult(
                success=True,
                message=f"Successfully terminated {resource_id}",
                details={
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "region": region,
                    "backup_id": backup_id
                },
                changes_made=changes_made,
                rollback_info=rollback_info
            )
            
        except Exception as e:
            logger.error(f"Error terminating {resource_id}: {e}", exc_info=True)
            return ExecutorResult(
                success=False,
                message=f"Failed to terminate {resource_id}: {str(e)}",
                details={},
                changes_made=changes_made,
                rollback_info=rollback_info
            )
    
    async def rollback(
        self,
        execution_record: Dict[str, Any]
    ) -> ExecutorResult:
        """Rollback termination by restoring from backup."""
        backup_id = execution_record.get("backup_id")
        resource_type = execution_record.get("resource_type", "unknown")
        
        if not backup_id:
            return ExecutorResult(
                success=False,
                message="No backup ID found for rollback",
                details={},
                changes_made=[],
                rollback_info={}
            )
        
        try:
            # Restore from backup
            new_resource_id = await self._restore_from_backup(backup_id, resource_type)
            
            return ExecutorResult(
                success=True,
                message=f"Restored resource from backup: {new_resource_id}",
                details={"new_resource_id": new_resource_id},
                changes_made=[f"Restored from backup {backup_id}"],
                rollback_info={}
            )
            
        except Exception as e:
            return ExecutorResult(
                success=False,
                message=f"Failed to rollback: {str(e)}",
                details={},
                changes_made=[],
                rollback_info={}
            )
    
    async def verify(
        self,
        execution_record: Dict[str, Any]
    ) -> bool:
        """Verify termination was successful."""
        resource_id = execution_record.get("resource_id")
        resource_type = execution_record.get("resource_type")
        
        # In production, would check if resource is actually terminated
        logger.info(f"Verifying termination of {resource_type} {resource_id}")
        return True
    
    # Private helper methods
    
    async def _create_backup(
        self,
        resource_id: str,
        resource_type: str,
        region: str
    ) -> str:
        """Create backup of resource."""
        # In production, would create actual backup
        backup_id = f"backup-{resource_id}"
        logger.info(f"Created backup {backup_id}")
        return backup_id
    
    async def _stop_resource(
        self,
        resource_id: str,
        resource_type: str,
        region: str
    ):
        """Stop resource."""
        # In production, would call AWS API
        logger.info(f"Stopped {resource_type} {resource_id}")
    
    async def _wait_for_stop(
        self,
        resource_id: str,
        resource_type: str,
        region: str
    ):
        """Wait for resource to stop."""
        # In production, would poll until stopped
        logger.info(f"Waiting for {resource_type} {resource_id} to stop")
    
    async def _terminate_resource(
        self,
        resource_id: str,
        resource_type: str,
        region: str
    ):
        """Terminate resource."""
        # In production, would call AWS API
        logger.info(f"Terminated {resource_type} {resource_id}")
    
    async def _restore_from_backup(
        self,
        backup_id: str,
        resource_type: str
    ) -> str:
        """Restore resource from backup."""
        # In production, would restore from actual backup
        new_resource_id = f"i-restored-{backup_id}"
        logger.info(f"Restored {resource_type} from {backup_id}: {new_resource_id}")
        return new_resource_id

"""Spot Migration Executor - Stub implementation."""
import logging
from typing import Dict, Any
from src.execution.executors.base import BaseExecutor
from src.models.execution_engine import ExecutorResult

logger = logging.getLogger(__name__)

class SpotMigrationExecutor(BaseExecutor):
    async def execute(self, recommendation: Dict[str, Any], dry_run: bool = False) -> ExecutorResult:
        return ExecutorResult(success=True, message="Spot migration executed (stub)", details={}, changes_made=["Migrated to spot instance"], rollback_info={})
    
    async def rollback(self, execution_record: Dict[str, Any]) -> ExecutorResult:
        return ExecutorResult(success=True, message="Spot rollback (stub)", details={}, changes_made=[], rollback_info={})
    
    async def verify(self, execution_record: Dict[str, Any]) -> bool:
        return True

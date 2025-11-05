"""
Base Executor.

Abstract base class for all executor implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

from src.models.execution_engine import ExecutorResult

logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """Base class for all executors."""
    
    def __init__(self):
        """Initialize executor."""
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def execute(
        self,
        recommendation: Dict[str, Any],
        dry_run: bool = False
    ) -> ExecutorResult:
        """
        Execute a recommendation.
        
        Args:
            recommendation: Recommendation to execute
            dry_run: If True, simulate without making changes
        
        Returns:
            ExecutorResult with execution details
        """
        pass
    
    @abstractmethod
    async def rollback(
        self,
        execution_record: Dict[str, Any]
    ) -> ExecutorResult:
        """
        Rollback an execution.
        
        Args:
            execution_record: Record of the execution to rollback
        
        Returns:
            ExecutorResult with rollback details
        """
        pass
    
    @abstractmethod
    async def verify(
        self,
        execution_record: Dict[str, Any]
    ) -> bool:
        """
        Verify execution was successful.
        
        Args:
            execution_record: Record of the execution to verify
        
        Returns:
            True if execution verified
        """
        pass
    
    def _log_execution(
        self,
        recommendation: Dict[str, Any],
        dry_run: bool,
        message: str
    ):
        """Log execution details."""
        rec_id = recommendation.get("recommendation_id", "unknown")
        resource_id = recommendation.get("resource_id", "unknown")
        
        mode = "DRY-RUN" if dry_run else "LIVE"
        logger.info(f"[{mode}] {self.name} - {resource_id}: {message}")

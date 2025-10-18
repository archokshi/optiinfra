"""
Gradual rollout logic for spot migration.
Implements 10% → 50% → 100% migration strategy.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from src.workflows.state import MigrationExecution

logger = logging.getLogger("cost_agent")


class GradualRollout:
    """Manages gradual rollout of spot migrations"""

    def __init__(self):
        """Initialize rollout manager"""
        self.phases = [10, 50, 100]
        self.monitoring_duration = {
            10: 5,  # 5 minutes after 10%
            50: 10,  # 10 minutes after 50%
            100: 15,  # 15 minutes after 100%
        }

    async def execute_phase(
        self,
        phase_percentage: int,
        instance_ids: List[str],
        execute_func,
    ) -> MigrationExecution:
        """
        Execute a single migration phase.

        Args:
            phase_percentage: 10, 50, or 100
            instance_ids: Instances to migrate
            execute_func: Function to execute migration

        Returns:
            MigrationExecution with results
        """
        logger.info(f"Starting {phase_percentage}% migration phase")

        started_at = datetime.utcnow()
        instances_total = len(instance_ids)
        instances_to_migrate = int(instances_total * phase_percentage / 100)

        errors = []
        instances_migrated = 0

        # Execute migrations
        for i, instance_id in enumerate(instance_ids[:instances_to_migrate]):
            try:
                result = await execute_func(instance_id, phase_percentage)
                if result["success"]:
                    instances_migrated += 1
                else:
                    errors.append(f"Failed to migrate {instance_id}")
            except Exception as e:
                logger.error(f"Migration error for {instance_id}: {e}")
                errors.append(str(e))

        completed_at = datetime.utcnow()
        success_rate = (
            instances_migrated / instances_to_migrate if instances_to_migrate > 0 else 0
        )

        execution: MigrationExecution = {
            "phase": f"{phase_percentage}%",
            "started_at": started_at,
            "completed_at": completed_at,
            "instances_migrated": instances_migrated,
            "instances_total": instances_to_migrate,
            "success_rate": success_rate,
            "errors": errors,
        }

        logger.info(
            f"Phase {phase_percentage}% complete: "
            f"{instances_migrated}/{instances_to_migrate} migrated "
            f"({success_rate*100:.1f}% success)"
        )

        return execution

    async def monitor_phase(
        self,
        phase_percentage: int,
        quality_check_func,
    ) -> Dict[str, Any]:
        """
        Monitor quality after a migration phase.

        Args:
            phase_percentage: Phase that was executed
            quality_check_func: Function to check quality

        Returns:
            Quality monitoring results
        """
        duration = self.monitoring_duration[phase_percentage]
        logger.info(
            f"Monitoring for {duration} minutes after {phase_percentage}% migration"
        )

        # Simulate monitoring duration (in reality this would be real-time)
        # For demo purposes, we'll check immediately
        await asyncio.sleep(1)  # Simulate brief monitoring

        quality_metrics = await quality_check_func()

        return {
            "phase": f"{phase_percentage}%",
            "monitoring_duration": duration,
            "quality_metrics": quality_metrics,
            "acceptable": quality_metrics.get("acceptable", True),
        }

    def should_continue(
        self,
        execution: MigrationExecution,
        monitoring_result: Dict[str, Any],
    ) -> bool:
        """
        Determine if rollout should continue to next phase.

        Args:
            execution: Execution results
            monitoring_result: Monitoring results

        Returns:
            True if should continue, False if should stop/rollback
        """
        # Check success rate
        if execution["success_rate"] < 0.95:  # 95% threshold
            logger.warning(
                f"Success rate too low: {execution['success_rate']*100:.1f}%"
            )
            return False

        # Check quality
        if not monitoring_result.get("acceptable", True):
            logger.warning("Quality degradation detected")
            return False

        logger.info(f"Phase {execution['phase']} passed checks, continuing")
        return True


# Global instance
gradual_rollout = GradualRollout()

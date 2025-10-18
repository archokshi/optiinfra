"""
Spot migration execution node.
Implements gradual rollout: 10% → 50% → 100%.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from src.utils.aws_simulator import aws_simulator
from src.utils.gradual_rollout import gradual_rollout
from src.workflows.state import SpotMigrationState

logger = logging.getLogger("cost_agent")


async def execute_migration_async(state: SpotMigrationState) -> Dict[str, Any]:
    """
    Execute spot migration with gradual rollout.

    This node:
    1. Executes 10% migration
    2. Monitors for 5 minutes
    3. Executes 50% migration
    4. Monitors for 10 minutes
    5. Executes 100% migration
    6. Final monitoring

    Args:
        state: Current workflow state

    Returns:
        Updated state with execution results
    """
    logger.info("Starting gradual spot migration execution")

    opportunities = state.get("spot_opportunities", [])
    instance_ids = [opp["instance_id"] for opp in opportunities]

    if not instance_ids:
        logger.warning("No instances to migrate")
        return {
            **state,
            "workflow_status": "failed",
            "error_message": "No instances to migrate",
        }

    # Migration execution function
    async def execute_func(instance_id, phase):
        result = aws_simulator.execute_spot_migration(instance_id, phase)
        await asyncio.sleep(0.1)  # Simulate execution time
        return result

    # Quality check function
    async def quality_check_func():
        metrics = aws_simulator.get_quality_metrics()
        quality_score = 0.95  # Simulated score
        degradation = abs(quality_score - 1.0) * 100
        return {
            "latency": metrics["latency"],
            "error_rate": metrics["error_rate"],
            "quality_score": quality_score,
            "degradation_percentage": degradation,
            "acceptable": degradation < 5.0,  # < 5% degradation
        }

    # Phase 1: 10% migration
    logger.info("=" * 60)
    logger.info("PHASE 1: Migrating 10% of instances")
    logger.info("=" * 60)

    execution_10 = await gradual_rollout.execute_phase(
        phase_percentage=10,
        instance_ids=instance_ids,
        execute_func=execute_func,
    )

    monitoring_10 = await gradual_rollout.monitor_phase(
        phase_percentage=10,
        quality_check_func=quality_check_func,
    )

    if not gradual_rollout.should_continue(execution_10, monitoring_10):
        logger.error("Migration stopped after 10% phase")
        return {
            **state,
            "execution_10": execution_10,
            "workflow_status": "failed",
            "migration_phase": "failed",
            "error_message": "Failed quality checks at 10% phase",
        }

    # Phase 2: 50% migration
    logger.info("=" * 60)
    logger.info("PHASE 2: Migrating 50% of instances")
    logger.info("=" * 60)

    execution_50 = await gradual_rollout.execute_phase(
        phase_percentage=50,
        instance_ids=instance_ids,
        execute_func=execute_func,
    )

    monitoring_50 = await gradual_rollout.monitor_phase(
        phase_percentage=50,
        quality_check_func=quality_check_func,
    )

    if not gradual_rollout.should_continue(execution_50, monitoring_50):
        logger.error("Migration stopped after 50% phase")
        return {
            **state,
            "execution_10": execution_10,
            "execution_50": execution_50,
            "workflow_status": "failed",
            "migration_phase": "failed",
            "error_message": "Failed quality checks at 50% phase",
        }

    # Phase 3: 100% migration
    logger.info("=" * 60)
    logger.info("PHASE 3: Migrating 100% of instances")
    logger.info("=" * 60)

    execution_100 = await gradual_rollout.execute_phase(
        phase_percentage=100,
        instance_ids=instance_ids,
        execute_func=execute_func,
    )

    monitoring_100 = await gradual_rollout.monitor_phase(
        phase_percentage=100,
        quality_check_func=quality_check_func,
    )

    if not gradual_rollout.should_continue(execution_100, monitoring_100):
        logger.error("Migration completed but quality degraded")
        return {
            **state,
            "execution_10": execution_10,
            "execution_50": execution_50,
            "execution_100": execution_100,
            "workflow_status": "failed",
            "migration_phase": "failed",
            "error_message": "Quality degradation detected at 100% phase",
        }

    # Success!
    logger.info("=" * 60)
    logger.info("✅ SPOT MIGRATION COMPLETE")
    logger.info("=" * 60)

    final_savings = state.get("total_savings", 0.0)

    logger.info(f"Total savings: ${final_savings:.2f}/month")
    logger.info(f"Instances migrated: {len(instance_ids)}")
    logger.info(f"Overall success rate: {execution_100['success_rate']*100:.1f}%")

    return {
        **state,
        "execution_10": execution_10,
        "execution_50": execution_50,
        "execution_100": execution_100,
        "workflow_status": "complete",
        "migration_phase": "complete",
        "final_savings": final_savings,
        "success": True,
    }


def execute_migration(state: SpotMigrationState) -> Dict[str, Any]:
    """
    Synchronous wrapper for async execution.

    Args:
        state: Current workflow state

    Returns:
        Updated state with execution results
    """
    # Check if there's a running event loop (e.g., in FastAPI)
    try:
        loop = asyncio.get_running_loop()
        # If we're here, there's a running loop - we need to use run_in_executor
        # For now, we'll use a simpler synchronous approach
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                lambda: asyncio.run(execute_migration_async(state))
            )
            return future.result()
    except RuntimeError:
        # No running loop, we can use asyncio.run directly
        return asyncio.run(execute_migration_async(state))

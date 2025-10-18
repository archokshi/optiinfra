"""
Quality monitoring during spot migration.
Ensures no quality degradation during migration.
"""

import logging
from typing import Any, Dict

from src.utils.aws_simulator import aws_simulator
from src.workflows.state import QualityMetrics, SpotMigrationState

logger = logging.getLogger("cost_agent")


def monitor_quality(state: SpotMigrationState) -> Dict[str, Any]:
    """
    Monitor quality metrics during and after migration.

    This node:
    1. Establishes quality baseline
    2. Monitors current quality
    3. Calculates degradation
    4. Triggers rollback if needed

    Args:
        state: Current workflow state

    Returns:
        Updated state with quality metrics
    """
    logger.info("Monitoring quality metrics")

    # Get baseline metrics
    baseline_metrics = aws_simulator.get_quality_metrics(baseline=True)

    quality_baseline: QualityMetrics = {
        "baseline_latency": baseline_metrics["latency"],
        "current_latency": baseline_metrics["latency"],
        "baseline_error_rate": baseline_metrics["error_rate"],
        "current_error_rate": baseline_metrics["error_rate"],
        "quality_score": 1.0,
        "degradation_percentage": 0.0,
        "acceptable": True,
    }

    logger.info(
        f"Baseline established: "
        f"Latency={baseline_metrics['latency']:.1f}ms, "
        f"Error rate={baseline_metrics['error_rate']:.3f}%"
    )

    # Get current metrics (after migration)
    current_metrics = aws_simulator.get_quality_metrics(baseline=False)

    # Calculate degradation
    latency_change = (
        (current_metrics["latency"] - baseline_metrics["latency"])
        / baseline_metrics["latency"]
    ) * 100

    error_rate_change = (
        (
            (current_metrics["error_rate"] - baseline_metrics["error_rate"])
            / baseline_metrics["error_rate"]
        )
        * 100
        if baseline_metrics["error_rate"] > 0
        else 0
    )

    # Overall degradation (weighted average)
    degradation = latency_change * 0.7 + error_rate_change * 0.3

    quality_current: QualityMetrics = {
        "baseline_latency": baseline_metrics["latency"],
        "current_latency": current_metrics["latency"],
        "baseline_error_rate": baseline_metrics["error_rate"],
        "current_error_rate": current_metrics["error_rate"],
        "quality_score": max(0.0, 1.0 - (degradation / 100)),
        "degradation_percentage": degradation,
        "acceptable": degradation < 5.0,  # < 5% threshold
    }

    logger.info(
        f"Current metrics: "
        f"Latency={current_metrics['latency']:.1f}ms "
        f"({latency_change:+.1f}%), "
        f"Error rate={current_metrics['error_rate']:.3f}% "
        f"({error_rate_change:+.1f}%)"
    )

    logger.info(
        f"Overall degradation: {degradation:.1f}% "
        f"({'ACCEPTABLE' if quality_current['acceptable'] else 'UNACCEPTABLE'})"
    )

    # Determine if rollback needed
    rollback_triggered = not quality_current["acceptable"]

    if rollback_triggered:
        logger.warning("⚠️ Quality degradation >5%, rollback triggered!")
    else:
        logger.info("✅ Quality maintained within acceptable limits")

    return {
        **state,
        "quality_baseline": quality_baseline,
        "quality_current": quality_current,
        "rollback_triggered": rollback_triggered,
        "workflow_status": "monitoring",
        "migration_phase": "monitoring",
    }

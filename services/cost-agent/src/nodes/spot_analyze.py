"""
Spot migration analysis node.
Identifies EC2 instances eligible for spot migration.
"""

import logging
from typing import Any, Dict

from src.utils.aws_simulator import aws_simulator
from src.workflows.state import SpotMigrationState

logger = logging.getLogger("cost_agent")


def analyze_spot_opportunities(state: SpotMigrationState) -> Dict[str, Any]:
    """
    Analyze EC2 instances for spot migration opportunities.

    This node:
    1. Examines EC2 instances
    2. Identifies spot-eligible workloads
    3. Calculates potential savings
    4. Assesses migration risk

    Args:
        state: Current workflow state

    Returns:
        Updated state with spot opportunities
    """
    logger.info(f"Analyzing spot opportunities for request {state['request_id']}")

    # Get EC2 instances (from state or generate for demo)
    if not state.get("ec2_instances"):
        logger.info("Generating sample EC2 instances for demo")
        instances = aws_simulator.generate_ec2_instances(count=10)
    else:
        instances = state["ec2_instances"]

    logger.info(f"Analyzing {len(instances)} EC2 instances")

    # Analyze for spot opportunities
    opportunities = aws_simulator.analyze_spot_opportunities(instances)

    # Calculate total savings
    total_savings = sum(opp["savings_amount"] for opp in opportunities)

    logger.info(
        f"Found {len(opportunities)} spot opportunities. "
        f"Potential savings: ${total_savings:.2f}/month"
    )

    # Log details
    for opp in opportunities:
        logger.info(
            f"  {opp['instance_id']}: ${opp['savings_amount']:.2f}/month "
            f"({opp['savings_percentage']:.1f}% savings, "
            f"{opp['risk_level']} risk)"
        )

    return {
        **state,
        "ec2_instances": instances,
        "spot_opportunities": opportunities,
        "total_savings": total_savings,
        "workflow_status": "analyzing",
        "migration_phase": "analyzing",
    }

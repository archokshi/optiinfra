"""
Multi-agent coordination node.
Gets approval from Performance, Resource, and Application agents.
"""

import logging
from typing import Any, Dict

from src.workflows.state import AgentApproval, SpotMigrationState

logger = logging.getLogger("cost_agent")


def coordinate_with_agents(state: SpotMigrationState) -> Dict[str, Any]:
    """
    Coordinate with other agents for approval.

    This node:
    1. Asks Performance Agent: "Is this safe?"
    2. Asks Resource Agent: "Will this work?"
    3. Asks Application Agent: "Establish quality baseline"
    4. Collects all approvals

    Args:
        state: Current workflow state

    Returns:
        Updated state with agent approvals
    """
    logger.info("Coordinating with other agents")

    opportunities = state.get("spot_opportunities", [])

    # In a real system, these would be HTTP calls to other agents
    # For PILOT demo, we simulate the responses

    # 1. Performance Agent approval
    logger.info("Requesting approval from Performance Agent...")
    performance_approval: AgentApproval = {
        "agent_type": "performance",
        "approved": True,
        "confidence": 0.92,
        "concerns": [],
        "recommendations": [
            "Spot instances may have slightly higher latency variability",
            "Monitor P95 latency during migration",
        ],
    }
    logger.info(
        f"Performance Agent: {performance_approval['approved']} "
        f"(confidence: {performance_approval['confidence']:.0%})"
    )

    # 2. Resource Agent approval
    logger.info("Requesting approval from Resource Agent...")
    resource_approval: AgentApproval = {
        "agent_type": "resource",
        "approved": True,
        "confidence": 0.95,
        "concerns": [],
        "recommendations": [
            "Ensure 2x spot capacity for low-risk workloads",
            "Use diverse AZs for redundancy",
        ],
    }
    logger.info(
        f"Resource Agent: {resource_approval['approved']} "
        f"(confidence: {resource_approval['confidence']:.0%})"
    )

    # 3. Application Agent approval (quality baseline)
    logger.info("Requesting quality baseline from Application Agent...")
    application_approval: AgentApproval = {
        "agent_type": "application",
        "approved": True,
        "confidence": 0.90,
        "concerns": [],
        "recommendations": [
            "Quality baseline established",
            "Will monitor for >5% degradation",
            "Auto-rollback enabled",
        ],
    }
    logger.info(
        f"Application Agent: {application_approval['approved']} "
        f"(confidence: {application_approval['confidence']:.0%})"
    )

    # Check if all agents approved
    all_approved = (
        performance_approval["approved"]
        and resource_approval["approved"]
        and application_approval["approved"]
    )

    if all_approved:
        logger.info("✅ All agents approved spot migration")
    else:
        logger.warning("⚠️ One or more agents did not approve")

    return {
        **state,
        "performance_approval": performance_approval,
        "resource_approval": resource_approval,
        "application_approval": application_approval,
        "coordination_complete": all_approved,
        "workflow_status": "coordinating",
        "migration_phase": "coordinating",
    }

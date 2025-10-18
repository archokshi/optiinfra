"""
Agent registration with orchestrator.
"""

import logging

from src.config import settings
from src.models.health import AgentRegistration

logger = logging.getLogger("cost_agent")


async def register_with_orchestrator() -> None:
    """
    Register this agent with the orchestrator.

    Sends agent information to orchestrator so it can route requests.
    """
    if not settings.orchestrator_url:
        logger.warning("Orchestrator URL not configured, skipping registration")
        return

    registration_data = AgentRegistration(
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        host="cost-agent",  # Docker service name
        port=settings.port,
        capabilities=[
            "spot_migration",
            "reserved_instances",
            "right_sizing",
        ],
    )

    try:
        # Note: This endpoint doesn't exist yet
        # (will be added in Foundation phase)
        # For now, just log that we would register
        logger.info(
            f"Would register with orchestrator at "
            f"{settings.orchestrator_url}/agents/register"
        )
        logger.info(f"Registration data: {registration_data.model_dump()}")

        # Uncomment when orchestrator has /agents/register endpoint
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{settings.orchestrator_url}/agents/register",
        #         json=registration_data.model_dump(),
        #         timeout=5.0,
        #     )
        #     response.raise_for_status()

    except Exception as e:
        logger.error(f"Failed to register with orchestrator: {e}")
        raise

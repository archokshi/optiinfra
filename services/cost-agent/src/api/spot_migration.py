"""
Spot migration API endpoint.
"""

import logging

from fastapi import APIRouter, HTTPException

from src.models.spot_migration import (
    AgentApprovalResponse,
    MigrationPhaseResponse,
    SpotMigrationRequest,
    SpotMigrationResponse,
    SpotOpportunityResponse,
)
from src.workflows.spot_migration import run_spot_migration_demo

router = APIRouter()
logger = logging.getLogger("cost_agent")


@router.post("/spot-migration", response_model=SpotMigrationResponse)
async def start_spot_migration(
    request: SpotMigrationRequest,
) -> SpotMigrationResponse:
    """
    Start spot migration workflow.

    This endpoint runs the complete spot migration demo:
    1. Analyzes EC2 instances
    2. Identifies spot opportunities
    3. Coordinates with other agents
    4. Executes gradual migration (10% → 50% → 100%)
    5. Monitors quality
    6. Reports results

    Args:
        request: Spot migration request

    Returns:
        SpotMigrationResponse: Complete results
    """
    logger.info(f"Starting spot migration for customer {request.customer_id}")

    try:
        # Run the workflow
        result = run_spot_migration_demo(customer_id=request.customer_id)

        # Convert to API response
        opportunities = [
            SpotOpportunityResponse(
                instance_id=opp["instance_id"],
                current_cost=opp["current_cost"],
                spot_cost=opp["spot_cost"],
                savings_amount=opp["savings_amount"],
                savings_percentage=opp["savings_percentage"],
                risk_level=opp["risk_level"],
            )
            for opp in result.get("spot_opportunities", [])
        ]

        # Agent approvals
        perf_approval = result.get("performance_approval")
        performance_approval = (
            AgentApprovalResponse(**perf_approval) if perf_approval else None
        )

        res_approval = result.get("resource_approval")
        resource_approval = (
            AgentApprovalResponse(**res_approval) if res_approval else None
        )

        app_approval = result.get("application_approval")
        application_approval = (
            AgentApprovalResponse(**app_approval) if app_approval else None
        )

        # Execution phases
        exec_10 = result.get("execution_10")
        execution_10_percent = (
            MigrationPhaseResponse(**exec_10) if exec_10 else None
        )

        exec_50 = result.get("execution_50")
        execution_50_percent = (
            MigrationPhaseResponse(**exec_50) if exec_50 else None
        )

        exec_100 = result.get("execution_100")
        execution_100_percent = (
            MigrationPhaseResponse(**exec_100) if exec_100 else None
        )

        response = SpotMigrationResponse(
            request_id=result["request_id"],
            customer_id=result["customer_id"],
            timestamp=result["timestamp"],
            instances_analyzed=len(result.get("ec2_instances", [])),
            opportunities_found=len(opportunities),
            total_savings=result.get("total_savings", 0.0),
            opportunities=opportunities,
            performance_approval=performance_approval,
            resource_approval=resource_approval,
            application_approval=application_approval,
            execution_10_percent=execution_10_percent,
            execution_50_percent=execution_50_percent,
            execution_100_percent=execution_100_percent,
            workflow_status=result.get("workflow_status", "unknown"),
            final_savings=result.get("final_savings", 0.0),
            success=result.get("success", False),
            error_message=result.get("error_message"),
        )

        logger.info(
            f"Spot migration complete: ${response.final_savings:.2f}/month savings"
        )

        return response

    except Exception as e:
        logger.error(f"Spot migration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Spot migration failed: {str(e)}"
        )

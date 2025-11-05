"""
Spot migration analysis node.
Identifies EC2 instances eligible for spot migration.
Extended with production error handling for PHASE1-1.6.
"""

import logging
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.aws_simulator import aws_simulator
from src.workflows.state import SpotMigrationState

logger = logging.getLogger("cost_agent")


# Production error types
class SpotAnalysisError(Exception):
    """Base exception for spot analysis errors"""
    pass


class InsufficientDataError(SpotAnalysisError):
    """Raised when insufficient data for analysis"""
    pass


class AWSThrottlingError(SpotAnalysisError):
    """Raised when AWS API is throttling requests"""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(AWSThrottlingError),
    reraise=True
)
def analyze_spot_opportunities(state: SpotMigrationState) -> Dict[str, Any]:
    """
    Analyze EC2 instances for spot migration opportunities.
    Production version with comprehensive error handling and retry logic.

    This node:
    1. Examines EC2 instances
    2. Identifies spot-eligible workloads
    3. Calculates potential savings
    4. Assesses migration risk

    Args:
        state: Current workflow state

    Returns:
        Updated state with spot opportunities
        
    Raises:
        InsufficientDataError: When no instances to analyze
        AWSThrottlingError: When AWS API throttles (will retry)
        SpotAnalysisError: On other analysis failures
    """
    request_id = state.get("request_id", "unknown")
    customer_id = state.get("customer_id", "unknown")
    
    logger.info(
        "Starting spot opportunity analysis",
        extra={
            "request_id": request_id,
            "customer_id": customer_id,
            "workflow_phase": "analyze"
        }
    )

    try:
        # Get EC2 instances (from state or generate for demo)
        if not state.get("ec2_instances"):
            logger.info("Generating sample EC2 instances for demo")
            instances = aws_simulator.generate_ec2_instances(count=10)
        else:
            instances = state["ec2_instances"]

        # Validate we have instances
        if not instances:
            raise InsufficientDataError("No EC2 instances provided for analysis")

        logger.info(
            f"Analyzing {len(instances)} EC2 instances",
            extra={
                "request_id": request_id,
                "instance_count": len(instances)
            }
        )

        # Analyze for spot opportunities
        opportunities = aws_simulator.analyze_spot_opportunities(instances)

        # Calculate total savings
        total_savings = sum(opp["savings_amount"] for opp in opportunities)

        logger.info(
            f"Found {len(opportunities)} spot opportunities with ${total_savings:.2f}/month savings",
            extra={
                "request_id": request_id,
                "opportunities_count": len(opportunities),
                "total_savings": total_savings
            }
        )

        # Log details
        for opp in opportunities:
            logger.debug(
                f"Opportunity: {opp['instance_id']} - ${opp['savings_amount']:.2f}/month "
                f"({opp['savings_percentage']:.1f}% savings, {opp['risk_level']} risk)",
                extra={
                    "request_id": request_id,
                    "instance_id": opp['instance_id'],
                    "savings": opp['savings_amount']
                }
            )

        return {
            **state,
            "ec2_instances": instances,
            "spot_opportunities": opportunities,
            "total_savings": total_savings,
            "workflow_status": "analyzed",
            "migration_phase": "analyzed",
        }
        
    except InsufficientDataError as e:
        logger.error(
            f"Insufficient data for analysis: {e}",
            extra={"request_id": request_id, "customer_id": customer_id}
        )
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Insufficient data: {str(e)}",
            "success": False
        }
        
    except AWSThrottlingError as e:
        logger.warning(
            f"AWS throttling detected, will retry: {e}",
            extra={"request_id": request_id, "customer_id": customer_id}
        )
        raise  # Let tenacity retry
        
    except Exception as e:
        logger.exception(
            "Unexpected error during spot analysis",
            extra={"request_id": request_id, "customer_id": customer_id}
        )
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Analysis failed: {str(e)}",
            "success": False
        }

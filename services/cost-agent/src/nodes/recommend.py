"""
Recommendation node - Generates cost optimization recommendations.
"""

import logging
import uuid
from typing import Any, Dict

from src.workflows.state import CostOptimizationState, Recommendation

logger = logging.getLogger("cost_agent")


def generate_recommendations(state: CostOptimizationState) -> Dict[str, Any]:
    """
    Generate actionable cost optimization recommendations.

    This is simplified. In production, this would:
    - Use LLM to generate detailed recommendations
    - Consider business context and constraints
    - Prioritize by ROI and implementation complexity

    Args:
        state: Current workflow state with analysis results

    Returns:
        Updated state with recommendations
    """
    logger.info("Generating recommendations")

    recommendations = []
    total_savings = 0.0

    for analysis in state.get("analysis_results", []):
        if analysis["waste_detected"]:
            resource_id = analysis["metrics"]["resource_id"]
            waste_amount = analysis["waste_amount"]

            # Generate recommendation based on waste pattern
            rec: Recommendation = {
                "recommendation_id": str(uuid.uuid4()),
                "recommendation_type": "right_sizing",
                "resource_id": resource_id,
                "description": (
                    f"Right-size resource {resource_id} to match utilization"
                ),
                "estimated_savings": waste_amount,
                "confidence_score": 0.85,
                "implementation_steps": [
                    f"1. Analyze workload patterns for {resource_id}",
                    "2. Identify appropriate smaller instance size",
                    "3. Schedule downtime window",
                    "4. Resize instance",
                    "5. Monitor performance for 24 hours",
                ],
            }

            recommendations.append(rec)
            total_savings += waste_amount

    logger.info(
        f"Generated {len(recommendations)} recommendations. "
        f"Total potential savings: ${total_savings:.2f}/month"
    )

    return {
        **state,
        "recommendations": recommendations,
        "total_potential_savings": total_savings,
        "workflow_status": "recommending",
    }

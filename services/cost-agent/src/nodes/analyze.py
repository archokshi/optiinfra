"""
Analysis node - Analyzes resources for cost optimization opportunities.
"""

import logging
from typing import Any, Dict

from src.workflows.state import AnalysisResult, CostOptimizationState

logger = logging.getLogger("cost_agent")


def analyze_resources(state: CostOptimizationState) -> Dict[str, Any]:
    """
    Analyze resources to detect waste and inefficiencies.

    This is a simplified version. In production, this would:
    - Query actual cloud provider APIs
    - Run ML models for anomaly detection
    - Compare against industry benchmarks

    Args:
        state: Current workflow state with resources

    Returns:
        Updated state with analysis results
    """
    logger.info(f"Analyzing {len(state['resources'])} resources")

    analysis_results = []
    total_waste = 0.0

    for resource in state["resources"]:
        # Simple heuristic: if utilization < 30%, flag as waste
        waste_detected = resource["utilization"] < 0.3

        if waste_detected:
            waste_amount = resource["cost_per_month"] * 0.5  # Assume 50% can be saved
            waste_percentage = 50.0

            result: AnalysisResult = {
                "waste_detected": True,
                "waste_amount": waste_amount,
                "waste_percentage": waste_percentage,
                "inefficiency_reasons": [
                    f"Low utilization: {resource['utilization']*100:.1f}%",
                    "Resource is over-provisioned",
                ],
                "metrics": {
                    "resource_id": resource["resource_id"],
                    "current_cost": resource["cost_per_month"],
                    "utilization": resource["utilization"],
                },
            }

            total_waste += waste_amount
        else:
            result: AnalysisResult = {
                "waste_detected": False,
                "waste_amount": 0.0,
                "waste_percentage": 0.0,
                "inefficiency_reasons": [],
                "metrics": {
                    "resource_id": resource["resource_id"],
                    "current_cost": resource["cost_per_month"],
                    "utilization": resource["utilization"],
                },
            }

        analysis_results.append(result)

    logger.info(f"Analysis complete. Total waste detected: ${total_waste:.2f}/month")

    return {
        **state,
        "analysis_results": analysis_results,
        "total_waste_detected": total_waste,
        "workflow_status": "analyzing",
    }

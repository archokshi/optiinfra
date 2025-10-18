"""
Summary node - Creates executive summary of analysis and recommendations.
"""

import logging
from typing import Any, Dict

from src.workflows.state import CostOptimizationState

logger = logging.getLogger("cost_agent")


def create_summary(state: CostOptimizationState) -> Dict[str, Any]:
    """
    Create an executive summary of the cost optimization analysis.

    In production, this would use an LLM to generate a natural language summary.

    Args:
        state: Current workflow state

    Returns:
        Updated state with summary
    """
    logger.info("Creating summary")

    num_resources = len(state["resources"])
    num_recommendations = len(state.get("recommendations", []))
    total_waste = state.get("total_waste_detected", 0.0)
    total_savings = state.get("total_potential_savings", 0.0)

    avg_savings = (
        total_savings / num_recommendations if num_recommendations > 0 else 0
    )

    summary = f"""
Cost Optimization Analysis Summary
===================================

Resources Analyzed: {num_resources}
Waste Detected: ${total_waste:.2f}/month
Recommendations: {num_recommendations}
Potential Savings: ${total_savings:.2f}/month

Key Findings:
- {num_recommendations} optimization opportunities identified
- Average savings potential: ${avg_savings:.2f} per recommendation
- Estimated ROI implementation time: 2-4 weeks

Next Steps:
1. Review recommendations with stakeholders
2. Prioritize by business impact
3. Create implementation plan
4. Schedule execution windows
""".strip()

    logger.info("Summary created")

    return {
        **state,
        "summary": summary,
        "workflow_status": "complete",
    }

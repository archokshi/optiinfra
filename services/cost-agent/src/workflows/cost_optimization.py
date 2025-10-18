"""
Main LangGraph workflow for cost optimization.
"""

import logging

from langgraph.graph import END, StateGraph

from src.nodes.analyze import analyze_resources
from src.nodes.recommend import generate_recommendations
from src.nodes.summarize import create_summary
from src.workflows.state import CostOptimizationState

logger = logging.getLogger("cost_agent")


def create_cost_optimization_workflow() -> StateGraph:
    """
    Create the cost optimization workflow graph.

    Flow:
    START → analyze → recommend → summarize → END

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph with our state type
    workflow = StateGraph(CostOptimizationState)

    # Add nodes
    workflow.add_node("analyze", analyze_resources)
    workflow.add_node("recommend", generate_recommendations)
    workflow.add_node("summarize", create_summary)

    # Define the flow
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "recommend")
    workflow.add_edge("recommend", "summarize")
    workflow.add_edge("summarize", END)

    # Compile the graph
    app = workflow.compile()

    logger.info("Cost optimization workflow created")

    return app


def visualize_workflow(workflow: StateGraph, output_path: str = "workflow.png"):
    """
    Visualize the workflow graph (optional, requires matplotlib).

    Args:
        workflow: The workflow to visualize
        output_path: Where to save the visualization
    """
    try:
        logger.info(f"Workflow visualization would be saved to {output_path}")
        # In practice: draw_mermaid(workflow).render(output_path)

    except ImportError:
        logger.warning("Matplotlib not available, skipping visualization")


# Create a singleton instance
cost_optimization_workflow = create_cost_optimization_workflow()

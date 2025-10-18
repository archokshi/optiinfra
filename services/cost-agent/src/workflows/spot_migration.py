"""
Complete spot migration workflow using LangGraph.
This is the end-to-end demo for PILOT-05.
"""

import logging
from datetime import datetime

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

from src.nodes.spot_analyze import analyze_spot_opportunities
from src.nodes.spot_coordinate import coordinate_with_agents
from src.nodes.spot_execute import execute_migration
from src.nodes.spot_monitor import monitor_quality
from src.workflows.state import SpotMigrationState

logger = logging.getLogger("cost_agent")


def create_spot_migration_workflow() -> StateGraph:
    """
    Create the complete spot migration workflow.

    Flow:
    START → analyze → coordinate → execute → monitor → END

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph
    workflow = StateGraph(SpotMigrationState)

    # Add nodes
    workflow.add_node("analyze", analyze_spot_opportunities)
    workflow.add_node("coordinate", coordinate_with_agents)
    workflow.add_node("execute", execute_migration)
    workflow.add_node("monitor", monitor_quality)

    # Define the flow
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "coordinate")
    workflow.add_edge("coordinate", "execute")
    workflow.add_edge("execute", "monitor")
    workflow.add_edge("monitor", END)

    # Compile
    app = workflow.compile()

    logger.info("Spot migration workflow created")

    return app


# Create singleton instance
spot_migration_workflow = create_spot_migration_workflow()


def run_spot_migration_demo(customer_id: str = "demo-customer-001") -> dict:
    """
    Run the complete spot migration demo.

    This is the main entry point for PILOT-05 demonstration.

    Args:
        customer_id: Customer identifier

    Returns:
        Final workflow state with results
    """
    logger.info("=" * 80)
    logger.info("OPTIINFRA PILOT-05: SPOT MIGRATION DEMO")
    logger.info("=" * 80)

    # Initialize state
    initial_state: SpotMigrationState = {
        "request_id": f"spot-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "customer_id": customer_id,
        "timestamp": datetime.utcnow(),
        "ec2_instances": [],  # Will be generated
        "spot_opportunities": None,
        "total_savings": 0.0,
        "performance_approval": None,
        "resource_approval": None,
        "application_approval": None,
        "coordination_complete": False,
        "customer_approved": True,  # Auto-approved for demo
        "approval_timestamp": datetime.utcnow(),
        "migration_phase": "pending",
        "execution_10": None,
        "execution_50": None,
        "execution_100": None,
        "quality_baseline": None,
        "quality_current": None,
        "rollback_triggered": False,
        "workflow_status": "pending",
        "final_savings": 0.0,
        "migration_duration": None,
        "success": False,
        "error_message": None,
    }

    # Run workflow
    config = RunnableConfig(run_name=f"spot_migration_{initial_state['request_id']}")

    try:
        result = spot_migration_workflow.invoke(initial_state, config)

        # Print summary
        logger.info("=" * 80)
        logger.info("DEMO COMPLETE - RESULTS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Request ID: {result['request_id']}")
        logger.info(f"Status: {result['workflow_status']}")
        logger.info(f"EC2 Instances Analyzed: {len(result.get('ec2_instances', []))}")
        logger.info(
            f"Spot Opportunities Found: {len(result.get('spot_opportunities', []))}"
        )
        logger.info(f"Total Monthly Savings: ${result.get('final_savings', 0):.2f}")

        if result.get("execution_100"):
            exec_100 = result["execution_100"]
            logger.info(
                f"Migration Success Rate: {exec_100['success_rate']*100:.1f}%"
            )

        if result.get("quality_current"):
            quality = result["quality_current"]
            logger.info(
                f"Quality Degradation: {quality['degradation_percentage']:.1f}% "
                f"({'ACCEPTABLE' if quality['acceptable'] else 'UNACCEPTABLE'})"
            )

        logger.info("=" * 80)

        return result

    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        raise

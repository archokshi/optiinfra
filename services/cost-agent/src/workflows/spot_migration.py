"""
Complete spot migration workflow using LangGraph.
This is the end-to-end demo for PILOT-05.
Extended with production features for PHASE1-1.6.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

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


# ============================================================================
# PHASE1-1.6: Production Spot Migration Workflow
# ============================================================================


class ProductionSpotMigrationWorkflow:
    """
    Production-ready spot migration workflow with real cloud integration.
    Extends PILOT-05 implementation with:
    - Real AWS/GCP/Azure collectors
    - Production error handling
    - Metrics storage (ClickHouse + Prometheus)
    - Security validation
    """
    
    def __init__(
        self,
        aws_credentials: Optional[Dict[str, str]] = None,
        gcp_credentials: Optional[Dict[str, str]] = None,
        azure_credentials: Optional[Dict[str, str]] = None
    ):
        """
        Initialize production workflow with cloud credentials.
        
        Args:
            aws_credentials: AWS credentials dict (access_key, secret_key, region)
            gcp_credentials: GCP credentials dict (project_id, credentials_path)
            azure_credentials: Azure credentials dict (tenant_id, client_id, client_secret)
        """
        # Import collectors (lazy import to avoid circular dependencies)
        try:
            from src.collectors.aws import EC2CostCollector
            self.aws_collector = EC2CostCollector() if aws_credentials else None
        except (ImportError, Exception) as e:
            logger.warning(f"AWS collector not available: {e}")
            self.aws_collector = None
        
        try:
            from src.collectors.gcp import GCPBaseCollector
            self.gcp_collector = GCPBaseCollector() if gcp_credentials else None
        except (ImportError, Exception) as e:
            logger.warning(f"GCP collector not available: {e}")
            self.gcp_collector = None
        
        try:
            from src.collectors.azure import AzureBaseCollector
            self.azure_collector = AzureBaseCollector() if azure_credentials else None
        except (ImportError, Exception) as e:
            logger.warning(f"Azure collector not available: {e}")
            self.azure_collector = None
        
        logger.info("Production spot migration workflow initialized")
    
    async def collect_instances(
        self,
        customer_id: str,
        cloud_provider: str
    ) -> List[Dict[str, Any]]:
        """
        Collect instances from real cloud providers.
        
        Args:
            customer_id: Customer identifier
            cloud_provider: 'aws', 'gcp', or 'azure'
        
        Returns:
            List of instance dicts
        
        Raises:
            ValueError: If cloud provider not supported or credentials not configured
        """
        logger.info(
            f"Collecting instances from {cloud_provider} for customer {customer_id}",
            extra={"customer_id": customer_id, "cloud_provider": cloud_provider}
        )
        
        try:
            if cloud_provider == "aws":
                if not self.aws_collector:
                    raise ValueError("AWS credentials not configured")
                # EC2CostCollector.collect() returns EC2 instance data
                instances = await self.aws_collector.collect()
                
            elif cloud_provider == "gcp":
                if not self.gcp_collector:
                    raise ValueError("GCP credentials not configured")
                instances = await self.gcp_collector.collect()
                
            elif cloud_provider == "azure":
                if not self.azure_collector:
                    raise ValueError("Azure credentials not configured")
                instances = await self.azure_collector.collect()
                
            else:
                raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
            
            logger.info(
                f"Collected {len(instances)} instances from {cloud_provider}",
                extra={
                    "customer_id": customer_id,
                    "cloud_provider": cloud_provider,
                    "instance_count": len(instances)
                }
            )
            
            return instances
            
        except Exception as e:
            logger.exception(
                f"Failed to collect instances from {cloud_provider}",
                extra={"customer_id": customer_id, "cloud_provider": cloud_provider}
            )
            raise
    
    def create_workflow(self) -> StateGraph:
        """
        Create production spot migration workflow.
        Same structure as PILOT-05 but with production features.
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(SpotMigrationState)
        
        # Add nodes (same as PILOT-05)
        workflow.add_node("analyze", analyze_spot_opportunities)
        workflow.add_node("coordinate", coordinate_with_agents)
        workflow.add_node("execute", execute_migration)
        workflow.add_node("monitor", monitor_quality)
        
        # Define the flow (same as PILOT-05)
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "coordinate")
        workflow.add_edge("coordinate", "execute")
        workflow.add_edge("execute", "monitor")
        workflow.add_edge("monitor", END)
        
        # Compile
        app = workflow.compile()
        
        logger.info("Production spot migration workflow compiled")
        return app
    
    async def run_migration(
        self,
        customer_id: str,
        cloud_provider: str = "aws",
        instance_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run production spot migration with real cloud integration.
        
        Args:
            customer_id: Customer identifier
            cloud_provider: Cloud provider ('aws', 'gcp', 'azure')
            instance_ids: Optional list of specific instance IDs to migrate
        
        Returns:
            Final workflow state with results
        """
        from src.database.clickhouse_metrics import get_metrics_client
        from src.monitoring.prometheus_metrics import (
            record_migration_start,
            record_migration_complete,
            record_migration_error
        )
        
        request_id = f"spot-prod-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(
            f"Starting production spot migration for {customer_id}",
            extra={
                "request_id": request_id,
                "customer_id": customer_id,
                "cloud_provider": cloud_provider
            }
        )
        
        # Record start
        record_migration_start(customer_id, cloud_provider)
        
        start_time = datetime.utcnow()
        
        try:
            # Collect instances from real cloud provider
            instances = await self.collect_instances(customer_id, cloud_provider)
            
            # Filter to specific instances if requested
            if instance_ids:
                instances = [i for i in instances if i.get("instance_id") in instance_ids]
            
            # Initialize state
            initial_state: SpotMigrationState = {
                "request_id": request_id,
                "customer_id": customer_id,
                "timestamp": start_time,
                "ec2_instances": instances,
                "spot_opportunities": None,
                "total_savings": 0.0,
                "performance_approval": None,
                "resource_approval": None,
                "application_approval": None,
                "coordination_complete": False,
                "customer_approved": True,
                "approval_timestamp": start_time,
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
            workflow = self.create_workflow()
            config = RunnableConfig(run_name=f"spot_migration_{request_id}")
            result = workflow.invoke(initial_state, config)
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            result["migration_duration"] = duration
            
            # Record metrics
            record_migration_complete(
                customer_id,
                cloud_provider,
                duration,
                result.get("final_savings", 0.0),
                len(result.get("spot_opportunities", []))
            )
            
            # Store in ClickHouse
            metrics_client = get_metrics_client()
            await metrics_client.insert_migration_event({
                "request_id": request_id,
                "customer_id": customer_id,
                "cloud_provider": cloud_provider,
                "workflow_phase": "complete",
                "instances_analyzed": len(instances),
                "opportunities_found": len(result.get("spot_opportunities", [])),
                "total_savings": result.get("final_savings", 0.0),
                "success": result.get("success", False),
                "duration_ms": int(duration * 1000)
            })
            
            logger.info(
                f"Production spot migration completed for {customer_id}",
                extra={
                    "request_id": request_id,
                    "customer_id": customer_id,
                    "savings": result.get("final_savings", 0.0),
                    "duration": duration
                }
            )
            
            return result
            
        except Exception as e:
            logger.exception(
                f"Production spot migration failed for {customer_id}",
                extra={"request_id": request_id, "customer_id": customer_id}
            )
            
            # Record error
            error_type = type(e).__name__
            record_migration_error(customer_id, error_type)
            
            # Store error in ClickHouse
            try:
                metrics_client = get_metrics_client()
                await metrics_client.insert_migration_event({
                    "request_id": request_id,
                    "customer_id": customer_id,
                    "cloud_provider": cloud_provider,
                    "workflow_phase": "failed",
                    "success": False,
                    "error_message": str(e)
                })
            except Exception as metrics_error:
                logger.error(f"Failed to record error metrics: {metrics_error}")
            
            raise

"""
Optimization Workflow

LangGraph workflow for gradual optimization rollout.
"""

import logging
from typing import Dict, Any
from datetime import datetime
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.models.workflow import (
    WorkflowState,
    WorkflowStatus,
    RolloutStage,
    RolloutStatus
)
from src.collectors.vllm_collector import VLLMCollector
from src.collectors.tgi_collector import TGICollector
from src.collectors.sglang_collector import SGLangCollector
from src.analysis.engine import AnalysisEngine
from src.optimization.engine import OptimizationEngine
from src.llm.llm_integration import LLMIntegrationLayer
from src.config import settings

logger = logging.getLogger(__name__)


class OptimizationWorkflow:
    """LangGraph workflow for optimization rollout."""
    
    def __init__(self):
        """Initialize workflow."""
        self.analysis_engine = AnalysisEngine()
        self.optimization_engine = OptimizationEngine()
        
        # Initialize LLM integration layer
        try:
            self.llm_layer = LLMIntegrationLayer()
            logger.info("LLM integration layer initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM layer: {e}")
            self.llm_layer = None
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Define the graph
        workflow = StateGraph(dict)  # Use dict for state
        
        # Add nodes
        workflow.add_node("collect_metrics", self.collect_metrics)
        workflow.add_node("analyze_performance", self.analyze_performance)
        workflow.add_node("generate_optimizations", self.generate_optimizations)
        workflow.add_node("await_approval", self.await_approval)
        workflow.add_node("rollout_10", lambda state: self.rollout_stage(state, RolloutStage.STAGE_10))
        workflow.add_node("monitor_10", lambda state: self.monitor_stage(state, RolloutStage.STAGE_10))
        workflow.add_node("rollout_50", lambda state: self.rollout_stage(state, RolloutStage.STAGE_50))
        workflow.add_node("monitor_50", lambda state: self.monitor_stage(state, RolloutStage.STAGE_50))
        workflow.add_node("rollout_100", lambda state: self.rollout_stage(state, RolloutStage.STAGE_100))
        workflow.add_node("complete", self.complete)
        workflow.add_node("rollback", self.rollback)
        
        # Define edges
        workflow.set_entry_point("collect_metrics")
        workflow.add_edge("collect_metrics", "analyze_performance")
        workflow.add_edge("analyze_performance", "generate_optimizations")
        
        # Conditional: approval required?
        workflow.add_conditional_edges(
            "generate_optimizations",
            self.should_await_approval,
            {
                "await_approval": "await_approval",
                "rollout": "rollout_10"
            }
        )
        
        # Conditional: approved?
        workflow.add_conditional_edges(
            "await_approval",
            self.is_approved,
            {
                "approved": "rollout_10",
                "rejected": END
            }
        )
        
        # 10% stage
        workflow.add_edge("rollout_10", "monitor_10")
        workflow.add_conditional_edges(
            "monitor_10",
            self.is_healthy,
            {
                "healthy": "rollout_50",
                "unhealthy": "rollback"
            }
        )
        
        # 50% stage
        workflow.add_edge("rollout_50", "monitor_50")
        workflow.add_conditional_edges(
            "monitor_50",
            self.is_healthy,
            {
                "healthy": "rollout_100",
                "unhealthy": "rollback"
            }
        )
        
        # 100% stage
        workflow.add_edge("rollout_100", "complete")
        workflow.add_edge("complete", END)
        workflow.add_edge("rollback", END)
        
        return workflow.compile(checkpointer=MemorySaver())
    
    async def collect_metrics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics from instance."""
        logger.info(f"[{state['workflow_id']}] Collecting metrics from {state['instance_id']}")
        
        state["status"] = WorkflowStatus.COLLECTING.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        try:
            # Collect based on instance type
            instance_type = state["instance_type"]
            instance_id = state["instance_id"]
            endpoint = f"http://{instance_id}/metrics"
            
            if instance_type == "vllm":
                async with VLLMCollector() as collector:
                    metrics = await collector.collect(instance_id, endpoint)
            elif instance_type == "tgi":
                async with TGICollector() as collector:
                    metrics = await collector.collect(instance_id, endpoint)
            elif instance_type == "sglang":
                async with SGLangCollector() as collector:
                    metrics = await collector.collect(instance_id, endpoint)
            else:
                raise ValueError(f"Unknown instance type: {instance_type}")
            
            state["metrics"] = metrics.model_dump()
            logger.info(f"[{state['workflow_id']}] Metrics collected successfully")
            
        except Exception as e:
            logger.error(f"[{state['workflow_id']}] Failed to collect metrics: {e}")
            state["status"] = WorkflowStatus.FAILED.value
            state["error_message"] = f"Metrics collection failed: {str(e)}"
        
        return state
    
    async def analyze_performance(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance and detect bottlenecks."""
        logger.info(f"[{state['workflow_id']}] Analyzing performance")
        
        state["status"] = WorkflowStatus.ANALYZING.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        try:
            # Reconstruct metrics object
            metrics_data = state.get("metrics")
            if not metrics_data:
                raise ValueError("No metrics available for analysis")
            
            # Run analysis engine
            # For simplicity, we'll create a mock analysis result
            # In production, reconstruct the metrics object and analyze
            from src.models.analysis import AnalysisResult
            
            analysis_result = AnalysisResult(
                instance_id=state["instance_id"],
                instance_type=state["instance_type"],
                bottlenecks=[],
                slo_statuses=[],
                overall_health_score=75.0,
                recommendations=[]
            )
            
            state["analysis_result"] = analysis_result.model_dump()
            logger.info(f"[{state['workflow_id']}] Analysis completed, health score: {analysis_result.overall_health_score}")
            
        except Exception as e:
            logger.error(f"[{state['workflow_id']}] Analysis failed: {e}")
            state["status"] = WorkflowStatus.FAILED.value
            state["error_message"] = f"Analysis failed: {str(e)}"
        
        return state
    
    async def generate_optimizations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization recommendations."""
        logger.info(f"[{state['workflow_id']}] Generating optimizations")
        
        state["status"] = WorkflowStatus.OPTIMIZING.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        try:
            # For simplicity, create a mock optimization plan
            from src.models.optimization import OptimizationPlan
            
            optimization_plan = OptimizationPlan(
                instance_id=state["instance_id"],
                instance_type=state["instance_type"],
                optimizations=[],
                estimated_total_improvement="30-50% overall performance improvement expected"
            )
            
            state["optimization_plan"] = optimization_plan.model_dump()
            logger.info(f"[{state['workflow_id']}] Optimizations generated")
            
            # Enhance with LLM if enabled
            enable_llm = state.get("enable_llm", True)
            
            if enable_llm and self.llm_layer and settings.llm_enabled:
                try:
                    logger.info(f"[{state['workflow_id']}] Enhancing with LLM insights")
                    
                    # Prepare data for LLM enhancement
                    metrics = state.get("metrics", {})
                    analysis_result = state.get("analysis_result", {})
                    
                    enhanced_report = await self.llm_layer.enhance_analysis_report(
                        instance_id=state["instance_id"],
                        instance_type=state["instance_type"],
                        metrics=metrics,
                        bottlenecks=analysis_result.get("bottlenecks", []),
                        optimizations=optimization_plan.optimizations,
                        enable_llm=True
                    )
                    
                    state["llm_insights"] = enhanced_report.get("llm_insights", {})
                    logger.info(f"[{state['workflow_id']}] LLM enhancement completed")
                    
                except Exception as e:
                    logger.error(f"[{state['workflow_id']}] LLM enhancement failed: {e}")
                    # Graceful degradation - continue without LLM insights
            else:
                logger.info(f"[{state['workflow_id']}] LLM enhancement disabled or not available")
            
        except Exception as e:
            logger.error(f"[{state['workflow_id']}] Optimization generation failed: {e}")
            state["status"] = WorkflowStatus.FAILED.value
            state["error_message"] = f"Optimization generation failed: {str(e)}"
        
        return state
    
    async def await_approval(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for human approval."""
        logger.info(f"[{state['workflow_id']}] Awaiting approval")
        
        state["status"] = WorkflowStatus.AWAITING_APPROVAL.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        # This is a human-in-the-loop step
        # Approval will be provided via API
        # For now, we'll simulate immediate approval if auto_rollout is True
        if state.get("auto_rollout", False):
            state["approved"] = True
            state["approved_by"] = "auto"
            state["approved_at"] = datetime.utcnow().isoformat()
            logger.info(f"[{state['workflow_id']}] Auto-approved")
        
        return state
    
    async def rollout_stage(self, state: Dict[str, Any], stage: RolloutStage) -> Dict[str, Any]:
        """Roll out optimization to a percentage of traffic."""
        logger.info(f"[{state['workflow_id']}] Rolling out to {stage.value}")
        
        state["status"] = WorkflowStatus.ROLLING_OUT.value
        state["current_stage"] = stage.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        # Get current health score
        analysis_result = state.get("analysis_result", {})
        health_score_before = analysis_result.get("overall_health_score", 0.0)
        
        # Create rollout status
        rollout_status = {
            "stage": stage.value,
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "health_score_before": health_score_before,
            "health_score_after": None,
            "metrics_snapshot": None,
            "issues": []
        }
        
        # Apply configuration changes (simulated)
        logger.info(f"[{state['workflow_id']}] Applying config changes for {stage.value}")
        await asyncio.sleep(1)  # Simulate deployment time
        
        rollout_status["status"] = "success"
        rollout_status["completed_at"] = datetime.utcnow().isoformat()
        
        # Add to history
        if "rollout_history" not in state:
            state["rollout_history"] = []
        state["rollout_history"].append(rollout_status)
        
        logger.info(f"[{state['workflow_id']}] Rollout to {stage.value} completed")
        
        return state
    
    async def monitor_stage(self, state: Dict[str, Any], stage: RolloutStage) -> Dict[str, Any]:
        """Monitor health after rollout stage."""
        monitoring_duration = state.get("monitoring_duration_seconds", 300)
        logger.info(f"[{state['workflow_id']}] Monitoring {stage.value} for {monitoring_duration}s")
        
        state["status"] = WorkflowStatus.MONITORING.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        # Simulate monitoring period (cap at 5s for demo)
        await asyncio.sleep(min(monitoring_duration, 5))
        
        # Simulate health improvement after rollout
        rollout_history = state.get("rollout_history", [])
        if rollout_history:
            last_rollout = rollout_history[-1]
            health_before = last_rollout["health_score_before"]
            
            # Simulate 10-20% improvement
            health_after = min(health_before * 1.15, 100.0)
            
            last_rollout["health_score_after"] = health_after
            logger.info(f"[{state['workflow_id']}] Health score after {stage.value}: {health_after}")
        
        return state
    
    async def complete(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Complete the workflow successfully."""
        logger.info(f"[{state['workflow_id']}] Workflow completed successfully")
        
        state["status"] = WorkflowStatus.COMPLETED.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        # Set final health score
        rollout_history = state.get("rollout_history", [])
        if rollout_history:
            state["final_health_score"] = rollout_history[-1].get("health_score_after")
        
        optimization_plan = state.get("optimization_plan", {})
        state["total_improvement"] = optimization_plan.get("estimated_total_improvement", "Unknown")
        
        return state
    
    async def rollback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback changes due to health issues."""
        logger.warning(f"[{state['workflow_id']}] Rolling back changes")
        
        state["status"] = WorkflowStatus.ROLLED_BACK.value
        state["updated_at"] = datetime.utcnow().isoformat()
        
        # Get the health score that triggered rollback
        rollout_history = state.get("rollout_history", [])
        if rollout_history:
            last_rollout = rollout_history[-1]
            health_after = last_rollout.get("health_score_after", 0.0)
            threshold = state.get("health_threshold", 0.9)
            state["error_message"] = f"Health score dropped below threshold ({health_after} < {threshold}), rolled back changes"
        else:
            state["error_message"] = "Rollback triggered due to health issues"
        
        # Restore original configuration (simulated)
        logger.info(f"[{state['workflow_id']}] Restoring original configuration")
        await asyncio.sleep(1)
        
        return state
    
    def should_await_approval(self, state: Dict[str, Any]) -> str:
        """Check if approval is required."""
        requires_approval = state.get("requires_approval", True)
        approved = state.get("approved")
        auto_rollout = state.get("auto_rollout", False)
        
        if requires_approval and not approved and not auto_rollout:
            return "await_approval"
        return "rollout"
    
    def is_approved(self, state: Dict[str, Any]) -> str:
        """Check if workflow is approved."""
        if state.get("approved"):
            return "approved"
        return "rejected"
    
    def is_healthy(self, state: Dict[str, Any]) -> str:
        """Check if instance is healthy after rollout."""
        rollout_history = state.get("rollout_history", [])
        if not rollout_history:
            return "unhealthy"
        
        latest_rollout = rollout_history[-1]
        health_after = latest_rollout.get("health_score_after")
        
        if health_after is None:
            return "unhealthy"
        
        threshold = state.get("health_threshold", 0.9)
        health_threshold_absolute = threshold * 100  # Convert to 0-100 scale
        
        if health_after >= health_threshold_absolute:
            return "healthy"
        
        return "unhealthy"
    
    async def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the workflow."""
        logger.info(f"Starting workflow {initial_state['workflow_id']}")
        
        # Execute workflow
        result = await self.graph.ainvoke(initial_state)
        
        return result

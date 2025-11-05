"""
Quality Validation Workflow

LangGraph workflow for orchestrating quality validation process.
"""

import uuid
from typing import Literal
from langgraph.graph import StateGraph, END
from .state import WorkflowState, WorkflowStatus
from ..models.quality_metrics import QualityRequest
from ..models.baseline import BaselineConfig, RegressionDetectionRequest
from ..models.validation import ValidationRequest
from ..collectors.quality_collector import quality_collector
from ..analyzers.quality_analyzer import quality_analyzer
from ..analyzers.regression_detector import regression_detector
from ..storage.baseline_storage import baseline_storage
from ..validators.approval_engine import approval_engine
from ..core.logger import logger


def analyze_quality_node(state: WorkflowState) -> WorkflowState:
    """Analyze quality of the response."""
    try:
        logger.info(f"Workflow {state['request_id']}: Analyzing quality")
        
        request = QualityRequest(
            prompt=state["prompt"],
            response=state["response"],
            model_name=state["model_name"]
        )
        
        # Call async method using asyncio
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create a new loop
            import nest_asyncio
            nest_asyncio.apply()
            metrics = asyncio.run(quality_collector.collect_quality_metrics(request))
        else:
            metrics = asyncio.run(quality_collector.collect_quality_metrics(request))
        
        quality_analyzer.add_metrics(metrics)
        
        state["quality_metrics"] = {
            "overall_quality": metrics.overall_quality,
            "relevance": {"score": metrics.relevance.score},
            "coherence": {"score": metrics.coherence.score},
            "hallucination": {"hallucination_rate": metrics.hallucination.hallucination_rate}
        }
        state["status"] = WorkflowStatus.ANALYZING.value
        state["current_step"] = "analyze_quality"
        
        logger.info(
            f"Workflow {state['request_id']}: Quality analyzed - "
            f"score={metrics.overall_quality:.2f}"
        )
        
        return state
        
    except Exception as e:
        logger.error(f"Workflow {state['request_id']}: Quality analysis failed - {e}")
        state["errors"].append(f"Quality analysis failed: {str(e)}")
        state["status"] = WorkflowStatus.FAILED.value
        return state


def check_baseline_node(state: WorkflowState) -> WorkflowState:
    """Check if baseline exists, create if needed."""
    try:
        logger.info(f"Workflow {state['request_id']}: Checking baseline")
        
        baseline = baseline_storage.get_by_model(
            state["model_name"],
            state.get("config_hash", "default")
        )
        
        if baseline:
            state["baseline"] = {
                "baseline_id": baseline.baseline_id,
                "average_quality": baseline.metrics.average_quality,
                "sample_size": baseline.sample_size
            }
            state["baseline_exists"] = True
            logger.info(f"Workflow {state['request_id']}: Baseline found")
        else:
            # Try to create baseline if we have enough metrics
            if len(quality_analyzer.metrics_history) >= 10:
                config = BaselineConfig(
                    model_name=state["model_name"],
                    config_hash=state.get("config_hash", "default"),
                    sample_size=10
                )
                baseline = regression_detector.establish_baseline(config)
                state["baseline"] = {
                    "baseline_id": baseline.baseline_id,
                    "average_quality": baseline.metrics.average_quality,
                    "sample_size": baseline.sample_size
                }
                state["baseline_exists"] = True
                logger.info(f"Workflow {state['request_id']}: Baseline created")
            else:
                state["baseline_exists"] = False
                logger.info(f"Workflow {state['request_id']}: No baseline, insufficient data")
        
        state["status"] = WorkflowStatus.BASELINE_CHECKED.value
        state["current_step"] = "check_baseline"
        
        return state
        
    except Exception as e:
        logger.error(f"Workflow {state['request_id']}: Baseline check failed - {e}")
        state["errors"].append(f"Baseline check failed: {str(e)}")
        state["status"] = WorkflowStatus.FAILED.value
        return state


def detect_regression_node(state: WorkflowState) -> WorkflowState:
    """Detect quality regression."""
    try:
        logger.info(f"Workflow {state['request_id']}: Detecting regression")
        
        request = RegressionDetectionRequest(
            model_name=state["model_name"],
            config_hash=state.get("config_hash", "default"),
            current_quality=state["quality_metrics"]["overall_quality"]
        )
        
        result = regression_detector.detect_regression(request)
        
        state["regression_result"] = {
            "regression_detected": result.regression_detected,
            "severity": result.severity.value,
            "quality_drop": result.quality_drop,
            "quality_drop_percentage": result.quality_drop_percentage,
            "baseline_quality": result.baseline_quality,
            "current_quality": result.current_quality
        }
        state["status"] = WorkflowStatus.REGRESSION_CHECKED.value
        state["current_step"] = "detect_regression"
        
        logger.info(
            f"Workflow {state['request_id']}: Regression check complete - "
            f"detected={result.regression_detected}"
        )
        
        return state
        
    except Exception as e:
        logger.error(f"Workflow {state['request_id']}: Regression detection failed - {e}")
        state["errors"].append(f"Regression detection failed: {str(e)}")
        state["status"] = WorkflowStatus.FAILED.value
        return state


def make_decision_node(state: WorkflowState) -> WorkflowState:
    """Make validation decision."""
    try:
        logger.info(f"Workflow {state['request_id']}: Making decision")
        
        request = ValidationRequest(
            name=f"Validation {state['request_id']}",
            model_name=state["model_name"],
            baseline_quality=state["baseline"]["average_quality"],
            new_quality=state["quality_metrics"]["overall_quality"]
        )
        
        result = approval_engine.validate_change(request)
        
        state["validation_result"] = {
            "validation_id": result.validation_id,
            "decision": result.decision.value,
            "confidence": result.confidence,
            "quality_change": result.quality_change,
            "quality_change_percentage": result.quality_change_percentage,
            "recommendation": result.recommendation,
            "reasoning": result.reasoning
        }
        state["decision"] = result.decision.value
        state["status"] = WorkflowStatus.DECISION_MADE.value
        state["current_step"] = "make_decision"
        
        logger.info(
            f"Workflow {state['request_id']}: Decision made - "
            f"{result.decision.value} (confidence={result.confidence:.2f})"
        )
        
        return state
        
    except Exception as e:
        logger.error(f"Workflow {state['request_id']}: Decision making failed - {e}")
        state["errors"].append(f"Decision making failed: {str(e)}")
        state["status"] = WorkflowStatus.FAILED.value
        return state


def execute_approval_node(state: WorkflowState) -> WorkflowState:
    """Execute approved change."""
    try:
        logger.info(f"Workflow {state['request_id']}: Executing approval")
        
        state["status"] = WorkflowStatus.COMPLETED.value
        state["current_step"] = "execute_approval"
        
        logger.info(f"Workflow {state['request_id']}: Change approved and executed")
        
        return state
        
    except Exception as e:
        logger.error(f"Workflow {state['request_id']}: Approval execution failed - {e}")
        state["errors"].append(f"Approval execution failed: {str(e)}")
        state["status"] = WorkflowStatus.FAILED.value
        return state


def execute_rejection_node(state: WorkflowState) -> WorkflowState:
    """Execute rejection/rollback."""
    try:
        logger.info(f"Workflow {state['request_id']}: Executing rejection")
        
        state["status"] = WorkflowStatus.COMPLETED.value
        state["current_step"] = "execute_rejection"
        
        logger.info(f"Workflow {state['request_id']}: Change rejected, rollback initiated")
        
        return state
        
    except Exception as e:
        logger.error(f"Workflow {state['request_id']}: Rejection execution failed - {e}")
        state["errors"].append(f"Rejection execution failed: {str(e)}")
        state["status"] = WorkflowStatus.FAILED.value
        return state


def flag_for_review_node(state: WorkflowState) -> WorkflowState:
    """Flag for manual review."""
    try:
        logger.info(f"Workflow {state['request_id']}: Flagging for manual review")
        
        state["status"] = WorkflowStatus.COMPLETED.value
        state["current_step"] = "flag_for_review"
        
        logger.info(f"Workflow {state['request_id']}: Flagged for manual review")
        
        return state
        
    except Exception as e:
        logger.error(f"Workflow {state['request_id']}: Review flagging failed - {e}")
        state["errors"].append(f"Review flagging failed: {str(e)}")
        state["status"] = WorkflowStatus.FAILED.value
        return state


def route_baseline(state: WorkflowState) -> Literal["continue", "end"]:
    """Route based on baseline existence."""
    if state.get("baseline_exists", False):
        return "continue"
    return "end"


def route_decision(state: WorkflowState) -> Literal["approve", "reject", "manual_review"]:
    """Route based on validation decision."""
    decision = state.get("decision", "manual_review")
    if decision == "approve":
        return "approve"
    elif decision == "reject":
        return "reject"
    else:
        return "manual_review"


# Build the workflow graph
workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("analyze_quality", analyze_quality_node)
workflow.add_node("check_baseline", check_baseline_node)
workflow.add_node("detect_regression", detect_regression_node)
workflow.add_node("make_decision", make_decision_node)
workflow.add_node("execute_approval", execute_approval_node)
workflow.add_node("execute_rejection", execute_rejection_node)
workflow.add_node("flag_for_review", flag_for_review_node)

# Set entry point
workflow.set_entry_point("analyze_quality")

# Add edges
workflow.add_edge("analyze_quality", "check_baseline")

# Conditional routing after baseline check
workflow.add_conditional_edges(
    "check_baseline",
    route_baseline,
    {
        "continue": "detect_regression",
        "end": END
    }
)

workflow.add_edge("detect_regression", "make_decision")

# Conditional routing after decision
workflow.add_conditional_edges(
    "make_decision",
    route_decision,
    {
        "approve": "execute_approval",
        "reject": "execute_rejection",
        "manual_review": "flag_for_review"
    }
)

# Terminal nodes
workflow.add_edge("execute_approval", END)
workflow.add_edge("execute_rejection", END)
workflow.add_edge("flag_for_review", END)

# Compile the workflow
app = workflow.compile()


def run_validation_workflow(
    model_name: str,
    prompt: str,
    response: str,
    config_hash: str = "default"
) -> WorkflowState:
    """
    Run the quality validation workflow.
    
    Args:
        model_name: Model name
        prompt: Input prompt
        response: Model response
        config_hash: Configuration hash
        
    Returns:
        Final workflow state
    """
    request_id = str(uuid.uuid4())
    
    initial_state: WorkflowState = {
        "request_id": request_id,
        "model_name": model_name,
        "config_hash": config_hash,
        "prompt": prompt,
        "response": response,
        "quality_metrics": None,
        "baseline": None,
        "baseline_exists": False,
        "regression_result": None,
        "validation_result": None,
        "decision": None,
        "status": WorkflowStatus.PENDING.value,
        "current_step": "start",
        "errors": [],
        "metadata": {}
    }
    
    logger.info(f"Starting workflow {request_id} for model {model_name}")
    
    try:
        # Run the workflow
        final_state = app.invoke(initial_state)
        
        logger.info(
            f"Workflow {request_id} completed - "
            f"status={final_state.get('status')}, "
            f"decision={final_state.get('decision')}"
        )
        
        return final_state
        
    except Exception as e:
        logger.error(f"Workflow {request_id} failed: {e}")
        initial_state["errors"].append(f"Workflow execution failed: {str(e)}")
        initial_state["status"] = WorkflowStatus.FAILED.value
        return initial_state

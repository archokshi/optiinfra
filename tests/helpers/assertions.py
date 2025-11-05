"""
Custom assertions for E2E tests.
"""
from typing import Dict, Any, List


def assert_optimization_successful(optimization: Dict[str, Any]):
    """Assert that optimization completed successfully."""
    assert optimization.get("status") == "completed", \
        f"Expected optimization to complete, got status: {optimization.get('status')}"
    
    assert "result" in optimization, \
        "Optimization result missing"
    
    assert optimization.get("result", {}).get("success") is True, \
        f"Optimization failed: {optimization.get('result', {}).get('error')}"


def assert_cost_reduced(before: float, after: float, min_reduction_pct: float = 10.0):
    """Assert that cost was reduced by at least min_reduction_pct."""
    reduction_pct = ((before - after) / before) * 100
    
    assert reduction_pct >= min_reduction_pct, \
        f"Expected cost reduction of at least {min_reduction_pct}%, got {reduction_pct:.2f}%"


def assert_latency_improved(before: float, after: float, max_degradation_pct: float = 5.0):
    """Assert that latency improved or degraded less than max_degradation_pct."""
    degradation_pct = ((after - before) / before) * 100
    
    assert degradation_pct <= max_degradation_pct, \
        f"Latency degraded by {degradation_pct:.2f}%, max allowed: {max_degradation_pct}%"


def assert_quality_maintained(quality_metrics: List[Dict[str, Any]], threshold: float = 0.95):
    """Assert that quality remained above threshold."""
    for metric in quality_metrics:
        score = metric.get("score", 0)
        assert score >= threshold, \
            f"Quality score {score} below threshold {threshold}"


def assert_multi_agent_coordination(events: List[Dict[str, Any]]):
    """Assert proper multi-agent coordination."""
    agent_types = {event.get("agent_type") for event in events if event.get("agent_type")}
    
    assert len(agent_types) > 1, \
        "Expected multiple agents to participate"
    
    # Check orchestrator coordinated
    orchestrator_events = [e for e in events if e.get("source") == "orchestrator"]
    assert len(orchestrator_events) > 0, \
        "Expected orchestrator coordination events"


def assert_savings_match_prediction(
    predicted_savings: float,
    actual_savings: float,
    tolerance_pct: float = 15.0
):
    """Assert actual savings match predicted within tolerance."""
    if predicted_savings == 0:
        return  # Skip if no savings predicted
    
    accuracy_pct = (actual_savings / predicted_savings) * 100
    lower_bound = 100 - tolerance_pct
    upper_bound = 100 + tolerance_pct
    
    assert lower_bound <= accuracy_pct <= upper_bound, \
        f"Savings prediction accuracy {accuracy_pct:.1f}% outside tolerance ({lower_bound}-{upper_bound}%)"


def assert_no_quality_degradation(
    baseline_quality: float,
    current_quality: float,
    max_degradation_pct: float = 5.0
):
    """Assert quality has not degraded beyond acceptable threshold."""
    degradation_pct = ((baseline_quality - current_quality) / baseline_quality) * 100
    
    assert degradation_pct <= max_degradation_pct, \
        f"Quality degraded by {degradation_pct:.2f}%, max allowed: {max_degradation_pct}%"


def assert_rollback_successful(rollback_result: Dict[str, Any]):
    """Assert that rollback completed successfully."""
    assert rollback_result.get("status") == "rolled_back", \
        f"Expected rollback status, got: {rollback_result.get('status')}"
    
    assert rollback_result.get("original_state_restored") is True, \
        "Original state was not restored"


def assert_execution_steps_completed(
    execution_steps: List[Dict[str, Any]],
    expected_steps: List[str]
):
    """Assert all expected execution steps completed."""
    completed_steps = {
        step.get("name") for step in execution_steps 
        if step.get("status") == "completed"
    }
    
    for expected_step in expected_steps:
        assert expected_step in completed_steps, \
            f"Expected step '{expected_step}' to complete"

"""
Right-Sizing Analysis Module

This module analyzes instance utilization patterns to identify optimization opportunities.
It detects over-provisioned and under-provisioned instances based on CPU, memory,
network, and disk utilization metrics.
"""

import logging
from typing import Dict, List, Any, Optional
from statistics import mean, stdev
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def analyze_utilization_patterns(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze instance utilization patterns to identify optimization candidates.
    
    Args:
        state: Workflow state containing:
            - instance_metrics: List of instances with metrics
            - min_utilization_threshold: Minimum utilization for over-provisioning
            - max_utilization_threshold: Maximum utilization for under-provisioning
    
    Returns:
        Updated state with optimization_candidates
    """
    try:
        instance_metrics = state.get("instance_metrics", [])
        min_threshold = state.get("min_utilization_threshold", 40.0)
        max_threshold = state.get("max_utilization_threshold", 80.0)
        
        logger.info(
            f"Analyzing utilization for {len(instance_metrics)} instances",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id"),
                "min_threshold": min_threshold,
                "max_threshold": max_threshold
            }
        )
        
        optimization_candidates = []
        over_provisioned_count = 0
        under_provisioned_count = 0
        optimal_count = 0
        
        for instance in instance_metrics:
            try:
                # Calculate resource metrics
                metrics = calculate_resource_metrics(instance)
                
                # Detect provisioning issue
                provisioning_issue = detect_provisioning_issue(
                    metrics,
                    min_threshold,
                    max_threshold
                )
                
                # Calculate optimization score
                optimization_score = calculate_optimization_score(
                    metrics,
                    provisioning_issue
                )
                
                # Track counts
                if provisioning_issue == "over_provisioned":
                    over_provisioned_count += 1
                elif provisioning_issue == "under_provisioned":
                    under_provisioned_count += 1
                elif provisioning_issue == "optimal":
                    optimal_count += 1
                
                # Add to candidates if not optimal
                if provisioning_issue in ["over_provisioned", "under_provisioned"]:
                    candidate = {
                        **instance,
                        "metrics": metrics,
                        "provisioning_issue": provisioning_issue,
                        "optimization_score": optimization_score
                    }
                    optimization_candidates.append(candidate)
                    
                    logger.debug(
                        f"Optimization candidate: {instance.get('instance_id')} - "
                        f"{provisioning_issue} (score: {optimization_score:.2f})",
                        extra={
                            "instance_id": instance.get("instance_id"),
                            "provisioning_issue": provisioning_issue,
                            "optimization_score": optimization_score
                        }
                    )
                
            except Exception as e:
                logger.warning(
                    f"Failed to analyze instance {instance.get('instance_id')}: {e}",
                    extra={"instance_id": instance.get("instance_id")}
                )
                continue
        
        logger.info(
            f"Analysis complete: {len(optimization_candidates)} candidates found "
            f"(over: {over_provisioned_count}, under: {under_provisioned_count}, "
            f"optimal: {optimal_count})",
            extra={
                "request_id": state.get("request_id"),
                "optimization_candidates": len(optimization_candidates),
                "over_provisioned": over_provisioned_count,
                "under_provisioned": under_provisioned_count,
                "optimal": optimal_count
            }
        )
        
        return {
            **state,
            "optimization_candidates": optimization_candidates,
            "over_provisioned_count": over_provisioned_count,
            "under_provisioned_count": under_provisioned_count,
            "optimal_count": optimal_count,
            "workflow_status": "analyzed"
        }
        
    except Exception as e:
        logger.error(
            f"Error analyzing utilization patterns: {e}",
            extra={"request_id": state.get("request_id")},
            exc_info=True
        )
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Analysis failed: {str(e)}"
        }


def calculate_resource_metrics(instance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate resource utilization metrics from instance data.
    
    Args:
        instance: Instance data with metrics_history
    
    Returns:
        Dictionary with calculated metrics
    """
    metrics_history = instance.get("metrics_history", [])
    
    if not metrics_history:
        raise ValueError("No metrics history available")
    
    # Extract metric values
    cpu_values = [m.get("cpu_utilization", 0) for m in metrics_history if m.get("cpu_utilization") is not None]
    memory_values = [m.get("memory_utilization", 0) for m in metrics_history if m.get("memory_utilization") is not None]
    network_in_values = [m.get("network_in_mbps", 0) for m in metrics_history if m.get("network_in_mbps") is not None]
    network_out_values = [m.get("network_out_mbps", 0) for m in metrics_history if m.get("network_out_mbps") is not None]
    disk_read_iops = [m.get("disk_read_iops", 0) for m in metrics_history if m.get("disk_read_iops") is not None]
    disk_write_iops = [m.get("disk_write_iops", 0) for m in metrics_history if m.get("disk_write_iops") is not None]
    
    # Calculate percentiles
    def percentile(values: List[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    # CPU metrics
    cpu_p50 = percentile(cpu_values, 50) if cpu_values else 0.0
    cpu_p95 = percentile(cpu_values, 95) if cpu_values else 0.0
    cpu_p99 = percentile(cpu_values, 99) if cpu_values else 0.0
    cpu_max = max(cpu_values) if cpu_values else 0.0
    cpu_avg = mean(cpu_values) if cpu_values else 0.0
    cpu_std = stdev(cpu_values) if len(cpu_values) > 1 else 0.0
    
    # Memory metrics
    memory_p50 = percentile(memory_values, 50) if memory_values else 0.0
    memory_p95 = percentile(memory_values, 95) if memory_values else 0.0
    memory_p99 = percentile(memory_values, 99) if memory_values else 0.0
    memory_max = max(memory_values) if memory_values else 0.0
    memory_avg = mean(memory_values) if memory_values else 0.0
    memory_std = stdev(memory_values) if len(memory_values) > 1 else 0.0
    
    # Network metrics
    network_in_p95 = percentile(network_in_values, 95) if network_in_values else 0.0
    network_out_p95 = percentile(network_out_values, 95) if network_out_values else 0.0
    
    # Disk metrics
    disk_read_iops_p95 = percentile(disk_read_iops, 95) if disk_read_iops else 0.0
    disk_write_iops_p95 = percentile(disk_write_iops, 95) if disk_write_iops else 0.0
    
    # Throttling events
    throttling_events = sum(m.get("throttling_events", 0) for m in metrics_history)
    
    # Burstable credit balance (for T-family instances)
    credit_values = [m.get("burstable_credit_balance") for m in metrics_history if m.get("burstable_credit_balance") is not None]
    burstable_credit_balance = mean(credit_values) if credit_values else None
    
    return {
        "cpu_p50": cpu_p50,
        "cpu_p95": cpu_p95,
        "cpu_p99": cpu_p99,
        "cpu_max": cpu_max,
        "cpu_avg": cpu_avg,
        "cpu_std": cpu_std,
        "memory_p50": memory_p50,
        "memory_p95": memory_p95,
        "memory_p99": memory_p99,
        "memory_max": memory_max,
        "memory_avg": memory_avg,
        "memory_std": memory_std,
        "network_in_p95": network_in_p95,
        "network_out_p95": network_out_p95,
        "disk_read_iops_p95": disk_read_iops_p95,
        "disk_write_iops_p95": disk_write_iops_p95,
        "throttling_events": throttling_events,
        "burstable_credit_balance": burstable_credit_balance,
        "data_points": len(metrics_history)
    }


def detect_provisioning_issue(
    metrics: Dict[str, Any],
    min_threshold: float = 40.0,
    max_threshold: float = 80.0
) -> str:
    """
    Detect if instance is over-provisioned, under-provisioned, or optimal.
    
    Args:
        metrics: Resource metrics
        min_threshold: Minimum utilization threshold for over-provisioning
        max_threshold: Maximum utilization threshold for under-provisioning
    
    Returns:
        "over_provisioned", "under_provisioned", "optimal", or "unknown"
    """
    cpu_p95 = metrics.get("cpu_p95", 0)
    memory_p95 = metrics.get("memory_p95", 0)
    throttling_events = metrics.get("throttling_events", 0)
    
    # Under-provisioned: High utilization or throttling
    if cpu_p95 > max_threshold or memory_p95 > 85 or throttling_events > 0:
        return "under_provisioned"
    
    # Over-provisioned: Low utilization on both CPU and memory
    if cpu_p95 < min_threshold and memory_p95 < 50:
        return "over_provisioned"
    
    # Optimal: Within acceptable ranges
    if min_threshold <= cpu_p95 <= max_threshold and 50 <= memory_p95 <= 85:
        return "optimal"
    
    # Unknown: Mixed signals or edge cases
    return "unknown"


def calculate_optimization_score(
    metrics: Dict[str, Any],
    provisioning_issue: str
) -> float:
    """
    Calculate optimization score (0.0-1.0) indicating optimization potential.
    
    Higher score = higher optimization potential
    
    Args:
        metrics: Resource metrics
        provisioning_issue: Detected provisioning issue
    
    Returns:
        Score between 0.0 and 1.0
    """
    if provisioning_issue == "optimal":
        return 0.0
    
    cpu_p95 = metrics.get("cpu_p95", 0)
    memory_p95 = metrics.get("memory_p95", 0)
    cpu_std = metrics.get("cpu_std", 0)
    memory_std = metrics.get("memory_std", 0)
    
    score = 0.0
    
    if provisioning_issue == "over_provisioned":
        # Higher score for lower utilization
        cpu_gap = max(0, 40 - cpu_p95) / 40  # 0-1 range
        memory_gap = max(0, 50 - memory_p95) / 50  # 0-1 range
        
        # Average the gaps
        utilization_score = (cpu_gap + memory_gap) / 2
        
        # Bonus for stable utilization (low variance)
        stability_score = 1.0 - min(cpu_std / 100, 1.0)
        
        # Combined score (70% utilization, 30% stability)
        score = (utilization_score * 0.7) + (stability_score * 0.3)
    
    elif provisioning_issue == "under_provisioned":
        # Higher score for higher utilization or throttling
        cpu_excess = max(0, cpu_p95 - 80) / 20  # 0-1 range
        memory_excess = max(0, memory_p95 - 85) / 15  # 0-1 range
        
        # Throttling is a strong signal
        throttling_score = min(metrics.get("throttling_events", 0) / 10, 1.0)
        
        # Combined score
        score = max(cpu_excess, memory_excess, throttling_score)
    
    return min(max(score, 0.0), 1.0)  # Clamp to 0-1 range

"""
Idle Detection Module

This module identifies idle and underutilized cloud resources that are consuming
costs with minimal or no actual usage. It analyzes CPU, memory, network, and disk
utilization to detect waste and generate cost-saving recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from statistics import mean
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def detect_idle_resources(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect idle and underutilized resources.
    
    Args:
        state: Workflow state containing:
            - resource_data: List of resources with metrics
            - idle_threshold_cpu: CPU threshold for idle detection
            - idle_threshold_memory: Memory threshold for idle detection
            - lookback_days: Number of days to analyze
    
    Returns:
        Updated state with idle_resources
    """
    try:
        resource_data = state.get("resource_data", [])
        idle_threshold_cpu = state.get("idle_threshold_cpu", 5.0)
        idle_threshold_memory = state.get("idle_threshold_memory", 10.0)
        lookback_days = state.get("lookback_days", 7)
        
        logger.info(
            f"Detecting idle resources for {len(resource_data)} resources",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id"),
                "resources": len(resource_data),
                "cpu_threshold": idle_threshold_cpu,
                "memory_threshold": idle_threshold_memory
            }
        )
        
        idle_resources = []
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        total_monthly_waste = 0.0
        
        for resource in resource_data:
            try:
                # Analyze resource utilization
                utilization = analyze_resource_utilization(
                    resource,
                    idle_threshold_cpu,
                    idle_threshold_memory
                )
                
                # Check if resource is idle
                if utilization["is_idle"]:
                    # Calculate waste cost
                    waste_cost = calculate_waste_cost(
                        resource,
                        utilization["idle_duration_days"]
                    )
                    
                    # Generate recommendation
                    recommendation = generate_idle_recommendation(
                        utilization["idle_severity"],
                        resource.get("resource_type", "unknown")
                    )
                    
                    idle_resource = {
                        "resource_id": resource.get("resource_id"),
                        "resource_type": resource.get("resource_type"),
                        "resource_name": resource.get("resource_name"),
                        "region": resource.get("region"),
                        **utilization,
                        **waste_cost,
                        **recommendation
                    }
                    
                    idle_resources.append(idle_resource)
                    total_monthly_waste += waste_cost["monthly_waste"]
                    
                    # Count by severity
                    severity = utilization["idle_severity"]
                    if severity == "critical":
                        critical_count += 1
                    elif severity == "high":
                        high_count += 1
                    elif severity == "medium":
                        medium_count += 1
                    else:
                        low_count += 1
                    
                    logger.debug(
                        f"Idle resource detected: {resource.get('resource_id')} "
                        f"({severity} severity, ${waste_cost['monthly_waste']:.2f}/mo waste)",
                        extra={
                            "resource_id": resource.get("resource_id"),
                            "severity": severity,
                            "monthly_waste": waste_cost["monthly_waste"]
                        }
                    )
                
            except Exception as e:
                logger.warning(
                    f"Failed to analyze resource {resource.get('resource_id')}: {e}",
                    extra={"resource_id": resource.get("resource_id")}
                )
                continue
        
        logger.info(
            f"Idle detection complete: {len(idle_resources)} idle resources found "
            f"(critical: {critical_count}, high: {high_count}, medium: {medium_count}, low: {low_count}), "
            f"${total_monthly_waste:.2f}/mo total waste",
            extra={
                "request_id": state.get("request_id"),
                "idle_resources": len(idle_resources),
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count,
                "monthly_waste": total_monthly_waste
            }
        )
        
        return {
            **state,
            "idle_resources": idle_resources,
            "idle_by_severity": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "total_monthly_waste": total_monthly_waste,
            "total_annual_waste": total_monthly_waste * 12,
            "workflow_status": "idle_detected"
        }
        
    except Exception as e:
        logger.error(
            f"Error detecting idle resources: {e}",
            extra={"request_id": state.get("request_id")},
            exc_info=True
        )
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Idle detection failed: {str(e)}"
        }


def analyze_resource_utilization(
    resource: Dict[str, Any],
    cpu_threshold: float = 5.0,
    memory_threshold: float = 10.0
) -> Dict[str, Any]:
    """
    Analyze resource utilization to determine if it's idle.
    
    Args:
        resource: Resource data with metrics_history
        cpu_threshold: CPU idle threshold
        memory_threshold: Memory idle threshold
    
    Returns:
        Dictionary with utilization analysis
    """
    metrics_history = resource.get("metrics_history", [])
    
    if not metrics_history:
        return {
            "is_idle": False,
            "idle_severity": "unknown",
            "idle_duration_days": 0,
            "cpu_avg": 0.0,
            "memory_avg": 0.0,
            "network_in_avg": 0.0,
            "network_out_avg": 0.0,
            "disk_read_ops": 0.0,
            "disk_write_ops": 0.0,
            "last_active_timestamp": None
        }
    
    # Calculate average metrics
    cpu_values = [m.get("cpu_utilization", 0) for m in metrics_history]
    memory_values = [m.get("memory_utilization", 0) for m in metrics_history]
    network_in_values = [m.get("network_in_kbps", 0) for m in metrics_history]
    network_out_values = [m.get("network_out_kbps", 0) for m in metrics_history]
    disk_read_values = [m.get("disk_read_ops", 0) for m in metrics_history]
    disk_write_values = [m.get("disk_write_ops", 0) for m in metrics_history]
    
    cpu_avg = mean(cpu_values) if cpu_values else 0.0
    memory_avg = mean(memory_values) if memory_values else 0.0
    network_in_avg = mean(network_in_values) if network_in_values else 0.0
    network_out_avg = mean(network_out_values) if network_out_values else 0.0
    disk_read_ops = mean(disk_read_values) if disk_read_values else 0.0
    disk_write_ops = mean(disk_write_values) if disk_write_values else 0.0
    
    # Classify idle severity
    idle_severity = classify_idle_severity(
        cpu_avg,
        memory_avg,
        network_in_avg,
        disk_read_ops + disk_write_ops
    )
    
    # Determine if resource is idle
    is_idle = idle_severity in ["critical", "high", "medium", "low"]
    
    # Calculate idle duration (days with low activity)
    idle_duration_days = len(metrics_history) // 24  # Assuming hourly metrics
    
    # Find last active timestamp
    last_active_timestamp = None
    for i in range(len(metrics_history) - 1, -1, -1):
        metric = metrics_history[i]
        if (metric.get("cpu_utilization", 0) > cpu_threshold or
            metric.get("memory_utilization", 0) > memory_threshold):
            last_active_timestamp = metric.get("timestamp")
            break
    
    return {
        "is_idle": is_idle,
        "idle_severity": idle_severity,
        "idle_duration_days": idle_duration_days,
        "cpu_avg": cpu_avg,
        "memory_avg": memory_avg,
        "network_in_avg": network_in_avg,
        "network_out_avg": network_out_avg,
        "disk_read_ops": disk_read_ops,
        "disk_write_ops": disk_write_ops,
        "last_active_timestamp": last_active_timestamp
    }


def classify_idle_severity(
    cpu_avg: float,
    memory_avg: float,
    network_avg: float,
    disk_ops: float
) -> str:
    """
    Classify idle severity based on utilization metrics.
    
    Args:
        cpu_avg: Average CPU utilization
        memory_avg: Average memory utilization
        network_avg: Average network throughput
        disk_ops: Average disk operations
    
    Returns:
        Severity level: "critical", "high", "medium", "low", or "active"
    """
    # Critical: Completely idle (0% utilization)
    if cpu_avg < 1 and memory_avg < 5 and network_avg < 1 and disk_ops < 10:
        return "critical"
    
    # High: Very low utilization
    if cpu_avg < 5 and memory_avg < 10 and network_avg < 10:
        return "high"
    
    # Medium: Low utilization
    if cpu_avg < 10 and memory_avg < 20:
        return "medium"
    
    # Low: Minimal activity
    if cpu_avg < 15 and memory_avg < 30:
        return "low"
    
    # Active: Normal utilization
    return "active"


def calculate_waste_cost(
    resource: Dict[str, Any],
    idle_duration_days: int
) -> Dict[str, float]:
    """
    Calculate waste cost for idle resource.
    
    Args:
        resource: Resource data with cost information
        idle_duration_days: Number of days resource has been idle
    
    Returns:
        Dictionary with waste cost metrics
    """
    hourly_cost = resource.get("hourly_cost", 0.0)
    
    # Calculate waste costs
    daily_waste = hourly_cost * 24
    monthly_waste = daily_waste * 30
    annual_waste = monthly_waste * 12
    
    # Calculate total waste to date
    total_waste_to_date = daily_waste * idle_duration_days
    
    return {
        "hourly_cost": hourly_cost,
        "daily_waste": daily_waste,
        "monthly_waste": monthly_waste,
        "annual_waste": annual_waste,
        "total_waste_to_date": total_waste_to_date
    }


def generate_idle_recommendation(
    idle_severity: str,
    resource_type: str
) -> Dict[str, Any]:
    """
    Generate recommendation for idle resource.
    
    Args:
        idle_severity: Idle severity level
        resource_type: Type of resource
    
    Returns:
        Dictionary with recommendation details
    """
    if idle_severity == "critical":
        return {
            "recommendation": "terminate",
            "recommendation_reason": "Resource has been completely idle with 0% utilization. "
                                   "Immediate termination recommended to eliminate waste.",
            "priority": "high",
            "estimated_savings": None  # Will be calculated from waste cost
        }
    
    elif idle_severity == "high":
        if resource_type in ["ec2", "rds"]:
            return {
                "recommendation": "hibernate",
                "recommendation_reason": "Resource has very low utilization (< 5%). "
                                       "Consider hibernation or scheduled shutdown during off-hours.",
                "priority": "high",
                "estimated_savings": None
            }
        else:
            return {
                "recommendation": "terminate",
                "recommendation_reason": "Resource has very low utilization (< 5%). "
                                       "Termination recommended unless required for specific use case.",
                "priority": "high",
                "estimated_savings": None
            }
    
    elif idle_severity == "medium":
        return {
            "recommendation": "review",
            "recommendation_reason": "Resource has low utilization (< 10%). "
                                   "Review usage patterns and consider downsizing or scheduled operations.",
            "priority": "medium",
            "estimated_savings": None
        }
    
    elif idle_severity == "low":
        return {
            "recommendation": "monitor",
            "recommendation_reason": "Resource has minimal activity (< 15%). "
                                   "Continue monitoring for optimization opportunities.",
            "priority": "low",
            "estimated_savings": None
        }
    
    else:
        return {
            "recommendation": "none",
            "recommendation_reason": "Resource is actively used.",
            "priority": "none",
            "estimated_savings": 0.0
        }


def generate_idle_recommendations(idle_resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate prioritized recommendations for all idle resources.
    
    Args:
        idle_resources: List of idle resources
    
    Returns:
        List of prioritized recommendations
    """
    recommendations = []
    
    # Sort by monthly waste (highest first)
    sorted_resources = sorted(
        idle_resources,
        key=lambda x: x.get("monthly_waste", 0),
        reverse=True
    )
    
    for resource in sorted_resources:
        recommendation = {
            "resource_id": resource["resource_id"],
            "resource_type": resource["resource_type"],
            "severity": resource["idle_severity"],
            "action": resource["recommendation"],
            "reason": resource["recommendation_reason"],
            "monthly_savings": resource["monthly_waste"],
            "annual_savings": resource["annual_waste"],
            "priority": resource["priority"]
        }
        recommendations.append(recommendation)
    
    return recommendations

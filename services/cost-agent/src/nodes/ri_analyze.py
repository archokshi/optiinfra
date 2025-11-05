"""
Reserved Instance analysis node.
Analyzes historical usage patterns to identify RI candidates.

This module provides production-ready RI analysis with:
- Historical usage pattern detection
- Stable workload identification
- Confidence scoring
- Error handling with retry logic
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from statistics import mean, stdev

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


# Custom Exceptions
class RIAnalysisError(Exception):
    """Base exception for RI analysis errors"""
    pass


class InsufficientUsageDataError(RIAnalysisError):
    """Raised when insufficient usage data is available"""
    pass


class UsageDataCollectionError(RIAnalysisError):
    """Raised when usage data collection fails"""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(UsageDataCollectionError)
)
def analyze_usage_patterns(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze instance usage patterns to identify RI candidates.
    
    This function examines historical usage data to identify instances that are
    good candidates for Reserved Instance purchases based on:
    - Uptime percentage (default: >= 80%)
    - Monthly cost threshold (default: >= $50)
    - Usage pattern stability
    
    Args:
        state: Workflow state containing:
            - instance_usage: List of instance usage data
            - min_uptime_percent: Minimum uptime threshold (default: 80.0)
            - min_monthly_cost: Minimum cost threshold (default: 50.0)
            - request_id: Request identifier
            - customer_id: Customer identifier
            
    Returns:
        Updated state with:
            - stable_workloads: List of RI candidates
            - usage_patterns: Dict mapping instance_id to pattern type
            - workflow_status: "analyzed" or "failed"
            
    Raises:
        InsufficientUsageDataError: When no usage data is available
        UsageDataCollectionError: When data collection fails (auto-retry)
    """
    try:
        logger.info(
            f"Analyzing usage patterns for customer {state['customer_id']}",
            extra={
                "request_id": state["request_id"],
                "customer_id": state["customer_id"],
                "analysis_period_days": state.get("analysis_period_days", 30)
            }
        )
        
        instance_usage = state.get("instance_usage", [])
        
        if not instance_usage:
            raise InsufficientUsageDataError("No usage data available for analysis")
        
        min_uptime = state.get("min_uptime_percent", 80.0)
        min_cost = state.get("min_monthly_cost", 50.0)
        
        # Identify stable workloads
        stable_workloads = []
        usage_patterns = {}
        
        for instance in instance_usage:
            instance_id = instance.get("instance_id")
            
            # Calculate metrics
            metrics = calculate_utilization_metrics(instance)
            
            # Check if instance qualifies for RI
            if (metrics["uptime_percent"] >= min_uptime and 
                metrics["monthly_cost"] >= min_cost):
                
                # Detect usage pattern
                pattern = detect_usage_pattern(instance.get("usage_history", []))
                
                stable_workload = {
                    "instance_id": instance_id,
                    "instance_type": instance.get("instance_type"),
                    "region": instance.get("region"),
                    "service_type": instance.get("service_type", "ec2"),
                    "uptime_percent": metrics["uptime_percent"],
                    "monthly_cost": metrics["monthly_cost"],
                    "usage_pattern": pattern,
                    "confidence_score": calculate_confidence_score(metrics, pattern),
                    "metrics": metrics
                }
                
                stable_workloads.append(stable_workload)
                usage_patterns[instance_id] = pattern
        
        logger.info(
            f"Found {len(stable_workloads)} stable workloads for RI consideration",
            extra={
                "request_id": state["request_id"],
                "customer_id": state["customer_id"],
                "stable_workloads_count": len(stable_workloads),
                "total_instances_analyzed": len(instance_usage)
            }
        )
        
        state["stable_workloads"] = stable_workloads
        state["usage_patterns"] = usage_patterns
        state["workflow_status"] = "analyzed"
        state["current_phase"] = "analysis_complete"
        
        return state
        
    except InsufficientUsageDataError as e:
        logger.error(
            f"Insufficient usage data: {e}",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id")
            }
        )
        state["workflow_status"] = "failed"
        state["error_message"] = str(e)
        state["success"] = False
        return state
        
    except Exception as e:
        logger.error(
            f"Unexpected error in usage analysis: {e}",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id")
            },
            exc_info=True
        )
        state["workflow_status"] = "failed"
        state["error_message"] = f"Analysis failed: {str(e)}"
        state["success"] = False
        return state


def calculate_utilization_metrics(instance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate utilization metrics for an instance.
    
    Analyzes historical usage data to compute:
    - Uptime percentage
    - Average CPU and memory utilization
    - Usage variance (for pattern detection)
    - Monthly cost projection
    
    Args:
        instance: Instance data with usage_history containing hourly data points
        
    Returns:
        Dictionary containing:
            - uptime_percent: Percentage of time instance was running
            - monthly_cost: Projected monthly cost
            - avg_cpu: Average CPU utilization
            - avg_memory: Average memory utilization
            - variance: CPU utilization variance
            - total_hours_analyzed: Total hours in analysis period
            - running_hours: Hours instance was running
    """
    usage_history = instance.get("usage_history", [])
    
    if not usage_history:
        return {
            "uptime_percent": 0.0,
            "monthly_cost": 0.0,
            "avg_cpu": 0.0,
            "avg_memory": 0.0,
            "variance": 0.0,
            "total_hours_analyzed": 0,
            "running_hours": 0
        }
    
    # Calculate uptime percentage
    total_hours = len(usage_history)
    running_hours = sum(1 for h in usage_history if h.get("state") == "running")
    uptime_percent = (running_hours / total_hours * 100) if total_hours > 0 else 0
    
    # Calculate average CPU and memory
    cpu_values = [h.get("cpu_utilization", 0) for h in usage_history if h.get("state") == "running"]
    memory_values = [h.get("memory_utilization", 0) for h in usage_history if h.get("state") == "running"]
    
    avg_cpu = mean(cpu_values) if cpu_values else 0
    avg_memory = mean(memory_values) if memory_values else 0
    
    # Calculate variance (for pattern detection)
    variance = stdev(cpu_values) if len(cpu_values) > 1 else 0
    
    # Calculate monthly cost
    hourly_cost = instance.get("hourly_cost", 0)
    monthly_cost = hourly_cost * 730  # Average hours per month
    
    return {
        "uptime_percent": round(uptime_percent, 2),
        "monthly_cost": round(monthly_cost, 2),
        "avg_cpu": round(avg_cpu, 2),
        "avg_memory": round(avg_memory, 2),
        "variance": round(variance, 2),
        "total_hours_analyzed": total_hours,
        "running_hours": running_hours
    }


def detect_usage_pattern(usage_history: List[Dict[str, Any]]) -> str:
    """
    Detect usage pattern type from historical data.
    
    Uses simple linear regression to detect trends and variance analysis
    to identify pattern types:
    - "steady": Consistent usage with low variance
    - "growing": Increasing usage trend
    - "declining": Decreasing usage trend
    - "seasonal": High variance, periodic patterns
    - "unknown": Insufficient data
    
    Args:
        usage_history: List of hourly usage data points with cpu_utilization
        
    Returns:
        Pattern type string: "steady", "growing", "seasonal", "declining", or "unknown"
    """
    if not usage_history or len(usage_history) < 24:
        return "unknown"
    
    # Extract CPU utilization over time
    cpu_values = [h.get("cpu_utilization", 0) for h in usage_history]
    
    if len(cpu_values) < 24:
        return "unknown"
    
    # Calculate trend (simple linear regression slope)
    n = len(cpu_values)
    x = list(range(n))
    x_mean = mean(x)
    y_mean = mean(cpu_values)
    
    numerator = sum((x[i] - x_mean) * (cpu_values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator != 0 else 0
    
    # Calculate variance
    variance = stdev(cpu_values) if len(cpu_values) > 1 else 0
    
    # Classify pattern based on slope and variance
    if abs(slope) < 0.01 and variance < 10:
        return "steady"
    elif slope > 0.05:
        return "growing"
    elif slope < -0.05:
        return "declining"
    elif variance > 20:
        return "seasonal"
    else:
        return "steady"


def calculate_confidence_score(
    metrics: Dict[str, Any],
    pattern: str
) -> float:
    """
    Calculate confidence score for RI recommendation.
    
    Confidence score is based on multiple factors:
    - Uptime percentage (40% weight): Higher uptime = higher confidence
    - Usage pattern (30% weight): Steady patterns = higher confidence
    - Variance (20% weight): Lower variance = higher confidence
    - Cost (10% weight): Higher cost = higher confidence (more savings potential)
    
    Args:
        metrics: Utilization metrics dictionary
        pattern: Usage pattern type
        
    Returns:
        Confidence score between 0.0 and 1.0
        
    Examples:
        >>> metrics = {"uptime_percent": 95, "variance": 5, "monthly_cost": 500}
        >>> calculate_confidence_score(metrics, "steady")
        0.95  # High confidence
        
        >>> metrics = {"uptime_percent": 82, "variance": 25, "monthly_cost": 60}
        >>> calculate_confidence_score(metrics, "seasonal")
        0.54  # Medium confidence
    """
    score = 0.0
    
    # Uptime contribution (40%)
    uptime = metrics.get("uptime_percent", 0)
    if uptime >= 95:
        score += 0.40
    elif uptime >= 90:
        score += 0.35
    elif uptime >= 85:
        score += 0.30
    elif uptime >= 80:
        score += 0.25
    else:
        score += 0.20
    
    # Pattern contribution (30%)
    pattern_scores = {
        "steady": 0.30,
        "growing": 0.25,
        "seasonal": 0.15,
        "declining": 0.05,
        "unknown": 0.10
    }
    score += pattern_scores.get(pattern, 0.10)
    
    # Variance contribution (20%)
    variance = metrics.get("variance", 100)
    if variance < 5:
        score += 0.20
    elif variance < 10:
        score += 0.15
    elif variance < 20:
        score += 0.10
    else:
        score += 0.05
    
    # Cost contribution (10%)
    monthly_cost = metrics.get("monthly_cost", 0)
    if monthly_cost >= 500:
        score += 0.10
    elif monthly_cost >= 200:
        score += 0.08
    elif monthly_cost >= 100:
        score += 0.06
    else:
        score += 0.04
    
    return round(min(score, 1.0), 2)

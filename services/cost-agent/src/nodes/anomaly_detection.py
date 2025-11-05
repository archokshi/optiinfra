"""
Anomaly Detection Module

This module detects anomalies in cloud resource usage, costs, and configurations.
It uses statistical methods to identify unusual patterns that may indicate issues,
waste, or security concerns.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from statistics import mean, stdev
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def detect_anomalies(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect anomalies in resource usage, costs, and configurations.
    
    Args:
        state: Workflow state containing:
            - resource_data: List of resources with metrics
            - cost_history: Historical cost data
            - anomaly_sensitivity: Detection sensitivity (low, medium, high)
    
    Returns:
        Updated state with anomalies
    """
    try:
        resource_data = state.get("resource_data", [])
        cost_history = state.get("cost_history", [])
        sensitivity = state.get("anomaly_sensitivity", "medium")
        
        logger.info(
            f"Detecting anomalies for {len(resource_data)} resources",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id"),
                "resources": len(resource_data),
                "sensitivity": sensitivity
            }
        )
        
        all_anomalies = []
        cost_anomalies = 0
        usage_anomalies = 0
        config_anomalies = 0
        security_anomalies = 0
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        
        # Detect cost anomalies
        if cost_history:
            cost_anomaly_list = detect_cost_anomalies(cost_history, sensitivity)
            all_anomalies.extend(cost_anomaly_list)
            cost_anomalies = len(cost_anomaly_list)
        
        # Detect usage anomalies for each resource
        for resource in resource_data:
            try:
                # Usage anomalies
                usage_anomaly_list = detect_usage_anomalies(
                    resource.get("metrics_history", []),
                    resource.get("resource_id"),
                    resource.get("resource_type"),
                    sensitivity
                )
                all_anomalies.extend(usage_anomaly_list)
                usage_anomalies += len(usage_anomaly_list)
                
                # Configuration drift (if baseline provided)
                if "baseline_config" in resource:
                    config_anomaly_list = detect_configuration_drift(
                        resource.get("current_config", {}),
                        resource.get("baseline_config", {}),
                        resource.get("resource_id"),
                        resource.get("resource_type")
                    )
                    all_anomalies.extend(config_anomaly_list)
                    config_anomalies += len(config_anomaly_list)
                
            except Exception as e:
                logger.warning(
                    f"Failed to detect anomalies for resource {resource.get('resource_id')}: {e}",
                    extra={"resource_id": resource.get("resource_id")}
                )
                continue
        
        # Count by severity
        for anomaly in all_anomalies:
            severity = anomaly.get("severity", "low")
            if severity == "critical":
                critical_count += 1
            elif severity == "high":
                high_count += 1
            elif severity == "medium":
                medium_count += 1
            else:
                low_count += 1
        
        logger.info(
            f"Anomaly detection complete: {len(all_anomalies)} anomalies found "
            f"(cost: {cost_anomalies}, usage: {usage_anomalies}, config: {config_anomalies}), "
            f"severity (critical: {critical_count}, high: {high_count}, medium: {medium_count}, low: {low_count})",
            extra={
                "request_id": state.get("request_id"),
                "total_anomalies": len(all_anomalies),
                "cost_anomalies": cost_anomalies,
                "usage_anomalies": usage_anomalies,
                "config_anomalies": config_anomalies,
                "critical": critical_count,
                "high": high_count
            }
        )
        
        return {
            **state,
            "anomalies": all_anomalies,
            "anomalies_by_type": {
                "cost": cost_anomalies,
                "usage": usage_anomalies,
                "configuration": config_anomalies,
                "security": security_anomalies
            },
            "anomalies_by_severity": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "workflow_status": "anomalies_detected"
        }
        
    except Exception as e:
        logger.error(
            f"Error detecting anomalies: {e}",
            extra={"request_id": state.get("request_id")},
            exc_info=True
        )
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Anomaly detection failed: {str(e)}"
        }


def detect_cost_anomalies(
    cost_history: List[Dict[str, Any]],
    sensitivity: str = "medium"
) -> List[Dict[str, Any]]:
    """
    Detect cost anomalies using statistical methods.
    
    Args:
        cost_history: List of cost data points with timestamp and amount
        sensitivity: Detection sensitivity (low, medium, high)
    
    Returns:
        List of detected cost anomalies
    """
    if len(cost_history) < 7:  # Need at least a week of data
        return []
    
    anomalies = []
    
    # Extract cost values
    costs = [entry.get("amount", 0) for entry in cost_history]
    
    # Calculate baseline statistics
    baseline_mean = mean(costs[:-1])  # Exclude latest for comparison
    baseline_std = stdev(costs[:-1]) if len(costs) > 2 else 0
    
    # Set threshold based on sensitivity
    threshold_multiplier = {
        "low": 3.0,      # 3 standard deviations
        "medium": 2.0,   # 2 standard deviations
        "high": 1.5      # 1.5 standard deviations
    }.get(sensitivity, 2.0)
    
    # Check latest cost for spike
    latest_cost = costs[-1]
    latest_entry = cost_history[-1]
    
    # Z-score anomaly detection
    if baseline_std > 0:
        z_score = (latest_cost - baseline_mean) / baseline_std
        
        if abs(z_score) > threshold_multiplier:
            deviation_percent = ((latest_cost - baseline_mean) / baseline_mean * 100) if baseline_mean > 0 else 0
            
            anomaly_type = "cost_spike" if z_score > 0 else "cost_drop"
            severity = classify_anomaly_severity(abs(deviation_percent))
            
            anomaly = {
                "anomaly_id": f"cost_{latest_entry.get('timestamp', datetime.utcnow().isoformat())}",
                "anomaly_type": anomaly_type,
                "resource_id": None,
                "resource_type": None,
                "region": latest_entry.get("region", "all"),
                "detected_at": datetime.utcnow().isoformat(),
                "anomaly_score": min(abs(z_score) / 5.0, 1.0),  # Normalize to 0-1
                "severity": severity,
                "metric_name": "daily_cost",
                "expected_value": baseline_mean,
                "actual_value": latest_cost,
                "deviation_percent": deviation_percent,
                "description": f"{'Sudden cost spike' if z_score > 0 else 'Unexpected cost drop'} detected: "
                             f"${latest_cost:.2f} vs expected ${baseline_mean:.2f} "
                             f"({abs(deviation_percent):.1f}% deviation)",
                "potential_causes": [
                    "New resources launched" if z_score > 0 else "Resources terminated",
                    "Pricing changes",
                    "Usage pattern change",
                    "Configuration change"
                ],
                "recommended_actions": [
                    "Review recent resource changes",
                    "Check for unauthorized resource creation" if z_score > 0 else "Verify expected terminations",
                    "Analyze cost breakdown by service"
                ],
                "cost_impact": abs(latest_cost - baseline_mean),
                "security_impact": "medium" if z_score > 0 and deviation_percent > 100 else "low"
            }
            
            anomalies.append(anomaly)
    
    # Detect gradual trend (increasing costs over time)
    if len(costs) >= 14:  # Need 2 weeks for trend analysis
        first_week_avg = mean(costs[:7])
        second_week_avg = mean(costs[7:14])
        
        if second_week_avg > first_week_avg * 1.2:  # 20% increase
            trend_percent = ((second_week_avg - first_week_avg) / first_week_avg * 100)
            
            anomaly = {
                "anomaly_id": f"cost_trend_{datetime.utcnow().isoformat()}",
                "anomaly_type": "cost_trend",
                "resource_id": None,
                "resource_type": None,
                "region": "all",
                "detected_at": datetime.utcnow().isoformat(),
                "anomaly_score": min(trend_percent / 100, 1.0),
                "severity": "medium" if trend_percent < 50 else "high",
                "metric_name": "weekly_cost_trend",
                "expected_value": first_week_avg,
                "actual_value": second_week_avg,
                "deviation_percent": trend_percent,
                "description": f"Gradual cost increase detected: {trend_percent:.1f}% increase over 2 weeks",
                "potential_causes": [
                    "Gradual resource scaling",
                    "Increased usage",
                    "Resource sprawl",
                    "Inefficient resource usage"
                ],
                "recommended_actions": [
                    "Review resource growth patterns",
                    "Identify cost drivers",
                    "Consider right-sizing opportunities",
                    "Implement cost controls"
                ],
                "cost_impact": second_week_avg - first_week_avg,
                "security_impact": "low"
            }
            
            anomalies.append(anomaly)
    
    return anomalies


def detect_usage_anomalies(
    metrics_history: List[Dict[str, Any]],
    resource_id: str,
    resource_type: str,
    sensitivity: str = "medium"
) -> List[Dict[str, Any]]:
    """
    Detect usage anomalies in resource metrics.
    
    Args:
        metrics_history: List of metric data points
        resource_id: Resource identifier
        resource_type: Resource type
        sensitivity: Detection sensitivity
    
    Returns:
        List of detected usage anomalies
    """
    if len(metrics_history) < 24:  # Need at least 24 hours of data
        return []
    
    anomalies = []
    
    # Extract metric values
    cpu_values = [m.get("cpu_utilization", 0) for m in metrics_history]
    memory_values = [m.get("memory_utilization", 0) for m in metrics_history]
    
    # Set threshold based on sensitivity
    threshold_multiplier = {
        "low": 3.0,
        "medium": 2.0,
        "high": 1.5
    }.get(sensitivity, 2.0)
    
    # CPU spike detection
    if cpu_values:
        cpu_mean = mean(cpu_values[:-1])
        cpu_std = stdev(cpu_values[:-1]) if len(cpu_values) > 2 else 0
        latest_cpu = cpu_values[-1]
        
        if cpu_std > 0:
            cpu_z_score = (latest_cpu - cpu_mean) / cpu_std
            
            if cpu_z_score > threshold_multiplier and latest_cpu > 80:
                deviation_percent = ((latest_cpu - cpu_mean) / cpu_mean * 100) if cpu_mean > 0 else 0
                
                anomaly = {
                    "anomaly_id": f"cpu_spike_{resource_id}_{datetime.utcnow().isoformat()}",
                    "anomaly_type": "usage_spike",
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "region": "unknown",
                    "detected_at": datetime.utcnow().isoformat(),
                    "anomaly_score": min(cpu_z_score / 5.0, 1.0),
                    "severity": "high" if latest_cpu > 90 else "medium",
                    "metric_name": "cpu_utilization",
                    "expected_value": cpu_mean,
                    "actual_value": latest_cpu,
                    "deviation_percent": deviation_percent,
                    "description": f"CPU spike detected: {latest_cpu:.1f}% vs expected {cpu_mean:.1f}%",
                    "potential_causes": [
                        "Traffic spike",
                        "Resource-intensive process",
                        "DDoS attack",
                        "Inefficient code"
                    ],
                    "recommended_actions": [
                        "Investigate running processes",
                        "Check for unusual traffic patterns",
                        "Consider auto-scaling",
                        "Review application logs"
                    ],
                    "cost_impact": None,
                    "security_impact": "medium"
                }
                
                anomalies.append(anomaly)
    
    # Memory leak detection (gradual increase)
    if len(memory_values) >= 48:  # 2 days of hourly data
        first_day_avg = mean(memory_values[:24])
        second_day_avg = mean(memory_values[24:48])
        
        if second_day_avg > first_day_avg + 20 and second_day_avg > 70:  # 20% increase and high usage
            trend_percent = ((second_day_avg - first_day_avg) / first_day_avg * 100) if first_day_avg > 0 else 0
            
            anomaly = {
                "anomaly_id": f"memory_leak_{resource_id}_{datetime.utcnow().isoformat()}",
                "anomaly_type": "memory_leak",
                "resource_id": resource_id,
                "resource_type": resource_type,
                "region": "unknown",
                "detected_at": datetime.utcnow().isoformat(),
                "anomaly_score": min(trend_percent / 100, 1.0),
                "severity": "high" if second_day_avg > 85 else "medium",
                "metric_name": "memory_utilization",
                "expected_value": first_day_avg,
                "actual_value": second_day_avg,
                "deviation_percent": trend_percent,
                "description": f"Potential memory leak detected: gradual increase from {first_day_avg:.1f}% to {second_day_avg:.1f}%",
                "potential_causes": [
                    "Memory leak in application",
                    "Inefficient memory management",
                    "Growing cache without limits",
                    "Resource not being freed"
                ],
                "recommended_actions": [
                    "Investigate application memory usage",
                    "Review application logs",
                    "Consider restarting service",
                    "Implement memory monitoring"
                ],
                "cost_impact": None,
                "security_impact": "low"
            }
            
            anomalies.append(anomaly)
    
    return anomalies


def detect_configuration_drift(
    current_config: Dict[str, Any],
    baseline_config: Dict[str, Any],
    resource_id: str,
    resource_type: str
) -> List[Dict[str, Any]]:
    """
    Detect configuration drift from baseline.
    
    Args:
        current_config: Current resource configuration
        baseline_config: Baseline configuration
        resource_id: Resource identifier
        resource_type: Resource type
    
    Returns:
        List of detected configuration anomalies
    """
    anomalies = []
    
    # Check for security group changes
    if "security_groups" in current_config and "security_groups" in baseline_config:
        current_sgs = set(current_config["security_groups"])
        baseline_sgs = set(baseline_config["security_groups"])
        
        if current_sgs != baseline_sgs:
            added = current_sgs - baseline_sgs
            removed = baseline_sgs - current_sgs
            
            severity = "high" if added else "medium"
            
            anomaly = {
                "anomaly_id": f"config_drift_{resource_id}_sg_{datetime.utcnow().isoformat()}",
                "anomaly_type": "configuration_drift",
                "resource_id": resource_id,
                "resource_type": resource_type,
                "region": current_config.get("region", "unknown"),
                "detected_at": datetime.utcnow().isoformat(),
                "anomaly_score": 0.8,
                "severity": severity,
                "metric_name": "security_groups",
                "expected_value": list(baseline_sgs),
                "actual_value": list(current_sgs),
                "deviation_percent": 0,
                "description": f"Security group configuration changed. Added: {added}, Removed: {removed}",
                "potential_causes": [
                    "Manual configuration change",
                    "Automated deployment",
                    "Unauthorized access",
                    "Configuration management tool"
                ],
                "recommended_actions": [
                    "Review change history",
                    "Verify authorization",
                    "Check for security implications",
                    "Update baseline if intentional"
                ],
                "cost_impact": None,
                "security_impact": "high" if added else "medium"
            }
            
            anomalies.append(anomaly)
    
    # Check for public access changes
    if "public_access" in current_config and "public_access" in baseline_config:
        if current_config["public_access"] and not baseline_config["public_access"]:
            anomaly = {
                "anomaly_id": f"config_drift_{resource_id}_public_{datetime.utcnow().isoformat()}",
                "anomaly_type": "security_risk",
                "resource_id": resource_id,
                "resource_type": resource_type,
                "region": current_config.get("region", "unknown"),
                "detected_at": datetime.utcnow().isoformat(),
                "anomaly_score": 1.0,
                "severity": "critical",
                "metric_name": "public_access",
                "expected_value": False,
                "actual_value": True,
                "deviation_percent": 0,
                "description": "Resource made publicly accessible",
                "potential_causes": [
                    "Configuration error",
                    "Unauthorized change",
                    "Security misconfiguration"
                ],
                "recommended_actions": [
                    "Immediately review access requirements",
                    "Restrict access if not required",
                    "Investigate who made the change",
                    "Enable access logging"
                ],
                "cost_impact": None,
                "security_impact": "critical"
            }
            
            anomalies.append(anomaly)
    
    return anomalies


def classify_anomaly_severity(deviation_percent: float) -> str:
    """
    Classify anomaly severity based on deviation percentage.
    
    Args:
        deviation_percent: Percentage deviation from expected
    
    Returns:
        Severity level: "critical", "high", "medium", or "low"
    """
    abs_deviation = abs(deviation_percent)
    
    if abs_deviation > 200:
        return "critical"
    elif abs_deviation > 100:
        return "high"
    elif abs_deviation > 50:
        return "medium"
    else:
        return "low"


def calculate_anomaly_score(
    deviation: float,
    baseline_std: float,
    severity: str
) -> float:
    """
    Calculate anomaly score (0.0-1.0).
    
    Args:
        deviation: Absolute deviation from expected
        baseline_std: Baseline standard deviation
        severity: Anomaly severity
    
    Returns:
        Score between 0.0 and 1.0
    """
    # Base score from statistical deviation
    if baseline_std > 0:
        z_score = abs(deviation / baseline_std)
        stat_score = min(z_score / 5.0, 1.0)  # Normalize to 0-1
    else:
        stat_score = 0.5
    
    # Adjust by severity
    severity_multiplier = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.6,
        "low": 0.4
    }.get(severity, 0.5)
    
    return min(stat_score * severity_multiplier, 1.0)

"""
Analysis Report Generation Module

This module generates comprehensive analysis reports that aggregate idle resources
and anomalies, calculate total waste, prioritize findings, and create executive
summaries for decision-making.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def generate_analysis_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive analysis report.
    
    Args:
        state: Workflow state containing:
            - idle_resources: List of idle resources
            - anomalies: List of detected anomalies
            - idle_by_severity: Idle resource counts by severity
            - anomalies_by_type: Anomaly counts by type
    
    Returns:
        Updated state with analysis_report
    """
    try:
        idle_resources = state.get("idle_resources", [])
        anomalies = state.get("anomalies", [])
        
        logger.info(
            f"Generating analysis report for {len(idle_resources)} idle resources "
            f"and {len(anomalies)} anomalies",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id"),
                "idle_resources": len(idle_resources),
                "anomalies": len(anomalies)
            }
        )
        
        # Calculate total waste
        waste_summary = calculate_total_waste(idle_resources)
        
        # Prioritize findings
        prioritized_findings = prioritize_findings(idle_resources, anomalies)
        
        # Generate executive summary
        executive_summary = generate_executive_summary(
            idle_resources,
            anomalies,
            waste_summary,
            prioritized_findings
        )
        
        # Build complete report
        analysis_report = {
            "report_id": state.get("request_id"),
            "customer_id": state.get("customer_id"),
            "cloud_provider": state.get("cloud_provider"),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "lookback_days": state.get("lookback_days", 7),
            
            # Idle resources
            "total_idle_resources": len(idle_resources),
            "idle_resources": idle_resources,
            "idle_by_severity": state.get("idle_by_severity", {}),
            "total_monthly_waste": waste_summary["total_monthly_waste"],
            "total_annual_waste": waste_summary["total_annual_waste"],
            "waste_by_resource_type": waste_summary["waste_by_resource_type"],
            
            # Anomalies
            "total_anomalies": len(anomalies),
            "anomalies": anomalies,
            "anomalies_by_type": state.get("anomalies_by_type", {}),
            "anomalies_by_severity": state.get("anomalies_by_severity", {}),
            
            # Summary
            "executive_summary": executive_summary,
            "top_findings": prioritized_findings[:10],  # Top 10
            "recommended_actions": generate_recommended_actions(prioritized_findings),
            
            # Metadata
            "analysis_duration_seconds": 0.0,  # Will be updated by workflow
            "success": True,
            "error_message": None
        }
        
        logger.info(
            f"Analysis report generated: {len(idle_resources)} idle resources, "
            f"${waste_summary['total_monthly_waste']:.2f}/mo waste, "
            f"{len(anomalies)} anomalies",
            extra={
                "request_id": state.get("request_id"),
                "monthly_waste": waste_summary["total_monthly_waste"],
                "anomalies": len(anomalies)
            }
        )
        
        return {
            **state,
            "analysis_report": analysis_report,
            "workflow_status": "report_generated"
        }
        
    except Exception as e:
        logger.error(
            f"Error generating analysis report: {e}",
            extra={"request_id": state.get("request_id")},
            exc_info=True
        )
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Report generation failed: {str(e)}"
        }


def calculate_total_waste(idle_resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate total waste from idle resources.
    
    Args:
        idle_resources: List of idle resources
    
    Returns:
        Dictionary with waste summary
    """
    total_monthly_waste = sum(r.get("monthly_waste", 0) for r in idle_resources)
    total_annual_waste = total_monthly_waste * 12
    
    # Breakdown by resource type
    waste_by_type = {}
    for resource in idle_resources:
        resource_type = resource.get("resource_type", "unknown")
        monthly_waste = resource.get("monthly_waste", 0)
        
        if resource_type not in waste_by_type:
            waste_by_type[resource_type] = {
                "count": 0,
                "monthly_waste": 0.0,
                "annual_waste": 0.0
            }
        
        waste_by_type[resource_type]["count"] += 1
        waste_by_type[resource_type]["monthly_waste"] += monthly_waste
        waste_by_type[resource_type]["annual_waste"] += monthly_waste * 12
    
    # Breakdown by severity
    waste_by_severity = {}
    for resource in idle_resources:
        severity = resource.get("idle_severity", "unknown")
        monthly_waste = resource.get("monthly_waste", 0)
        
        if severity not in waste_by_severity:
            waste_by_severity[severity] = {
                "count": 0,
                "monthly_waste": 0.0,
                "annual_waste": 0.0
            }
        
        waste_by_severity[severity]["count"] += 1
        waste_by_severity[severity]["monthly_waste"] += monthly_waste
        waste_by_severity[severity]["annual_waste"] += monthly_waste * 12
    
    return {
        "total_monthly_waste": total_monthly_waste,
        "total_annual_waste": total_annual_waste,
        "waste_by_resource_type": waste_by_type,
        "waste_by_severity": waste_by_severity
    }


def prioritize_findings(
    idle_resources: List[Dict[str, Any]],
    anomalies: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Prioritize all findings by severity and impact.
    
    Args:
        idle_resources: List of idle resources
        anomalies: List of anomalies
    
    Returns:
        List of prioritized findings
    """
    all_findings = []
    
    # Add idle resources as findings
    for resource in idle_resources:
        priority_score = calculate_priority_score(
            severity=resource.get("idle_severity"),
            cost_impact=resource.get("monthly_waste", 0),
            finding_type="idle_resource"
        )
        
        finding = {
            "type": "idle_resource",
            "resource_id": resource.get("resource_id"),
            "resource_type": resource.get("resource_type"),
            "severity": resource.get("idle_severity"),
            "description": f"Idle {resource.get('resource_type')} resource with "
                         f"{resource.get('cpu_avg', 0):.1f}% CPU, "
                         f"{resource.get('memory_avg', 0):.1f}% memory utilization",
            "cost_impact": resource.get("monthly_waste", 0),
            "recommendation": resource.get("recommendation"),
            "priority_score": priority_score,
            "priority_tier": classify_priority_tier(priority_score)
        }
        all_findings.append(finding)
    
    # Add anomalies as findings
    for anomaly in anomalies:
        priority_score = calculate_priority_score(
            severity=anomaly.get("severity"),
            cost_impact=anomaly.get("cost_impact", 0),
            finding_type="anomaly"
        )
        
        finding = {
            "type": "anomaly",
            "anomaly_type": anomaly.get("anomaly_type"),
            "resource_id": anomaly.get("resource_id"),
            "resource_type": anomaly.get("resource_type"),
            "severity": anomaly.get("severity"),
            "description": anomaly.get("description"),
            "cost_impact": anomaly.get("cost_impact"),
            "security_impact": anomaly.get("security_impact"),
            "recommendation": ", ".join(anomaly.get("recommended_actions", [])[:2]),
            "priority_score": priority_score,
            "priority_tier": classify_priority_tier(priority_score)
        }
        all_findings.append(finding)
    
    # Sort by priority score (highest first)
    all_findings.sort(key=lambda x: x["priority_score"], reverse=True)
    
    return all_findings


def calculate_priority_score(
    severity: str,
    cost_impact: float,
    finding_type: str
) -> float:
    """
    Calculate priority score for a finding.
    
    Args:
        severity: Severity level
        cost_impact: Monthly cost impact
        finding_type: Type of finding
    
    Returns:
        Priority score (0-100)
    """
    # Base score from severity
    severity_scores = {
        "critical": 40,
        "high": 30,
        "medium": 20,
        "low": 10,
        "unknown": 5
    }
    score = severity_scores.get(severity, 10)
    
    # Add cost impact score (0-40 points)
    if cost_impact:
        cost_score = min(cost_impact / 25, 40)  # $25/mo = 1 point, max 40
        score += cost_score
    
    # Add type bonus
    if finding_type == "anomaly":
        score += 10  # Anomalies get priority for investigation
    
    return min(score, 100)


def classify_priority_tier(priority_score: float) -> str:
    """
    Classify priority tier based on score.
    
    Args:
        priority_score: Priority score
    
    Returns:
        Priority tier: "critical", "high", "medium", or "low"
    """
    if priority_score >= 70:
        return "critical"
    elif priority_score >= 50:
        return "high"
    elif priority_score >= 30:
        return "medium"
    else:
        return "low"


def generate_executive_summary(
    idle_resources: List[Dict[str, Any]],
    anomalies: List[Dict[str, Any]],
    waste_summary: Dict[str, Any],
    prioritized_findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate executive summary of analysis.
    
    Args:
        idle_resources: List of idle resources
        anomalies: List of anomalies
        waste_summary: Waste calculation summary
        prioritized_findings: Prioritized findings
    
    Returns:
        Executive summary dictionary
    """
    # Count critical/high priority findings
    critical_findings = [f for f in prioritized_findings if f["priority_tier"] == "critical"]
    high_findings = [f for f in prioritized_findings if f["priority_tier"] == "high"]
    
    # Calculate potential savings
    idle_savings = waste_summary["total_monthly_waste"]
    
    # Identify top cost drivers
    top_cost_drivers = sorted(
        idle_resources,
        key=lambda x: x.get("monthly_waste", 0),
        reverse=True
    )[:5]
    
    # Count security issues
    security_anomalies = [
        a for a in anomalies
        if a.get("security_impact") in ["critical", "high"]
    ]
    
    return {
        "total_findings": len(prioritized_findings),
        "critical_issues": len(critical_findings),
        "high_priority_issues": len(high_findings),
        "total_idle_resources": len(idle_resources),
        "total_anomalies": len(anomalies),
        "potential_monthly_savings": idle_savings,
        "potential_annual_savings": idle_savings * 12,
        "top_cost_drivers": [
            {
                "resource_id": r.get("resource_id"),
                "resource_type": r.get("resource_type"),
                "monthly_waste": r.get("monthly_waste")
            }
            for r in top_cost_drivers
        ],
        "security_issues_count": len(security_anomalies),
        "immediate_actions_required": len(critical_findings),
        "summary_text": generate_summary_text(
            len(idle_resources),
            len(anomalies),
            idle_savings,
            len(critical_findings)
        )
    }


def generate_summary_text(
    idle_count: int,
    anomaly_count: int,
    monthly_savings: float,
    critical_count: int
) -> str:
    """
    Generate human-readable summary text.
    
    Args:
        idle_count: Number of idle resources
        anomaly_count: Number of anomalies
        monthly_savings: Monthly savings potential
        critical_count: Number of critical findings
    
    Returns:
        Summary text
    """
    parts = []
    
    if idle_count > 0:
        parts.append(f"Found {idle_count} idle resource{'s' if idle_count != 1 else ''} "
                    f"wasting ${monthly_savings:,.2f}/month")
    
    if anomaly_count > 0:
        parts.append(f"detected {anomaly_count} anomal{'ies' if anomaly_count != 1 else 'y'}")
    
    if critical_count > 0:
        parts.append(f"{critical_count} critical issue{'s' if critical_count != 1 else ''} "
                    f"require{'s' if critical_count == 1 else ''} immediate attention")
    
    if not parts:
        return "No significant issues detected. Resources are optimally utilized."
    
    return "Analysis complete: " + ", ".join(parts) + "."


def generate_recommended_actions(prioritized_findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate recommended actions from prioritized findings.
    
    Args:
        prioritized_findings: List of prioritized findings
    
    Returns:
        List of recommended actions
    """
    actions = []
    
    # Group by priority tier
    critical_findings = [f for f in prioritized_findings if f["priority_tier"] == "critical"]
    high_findings = [f for f in prioritized_findings if f["priority_tier"] == "high"]
    
    # Critical actions
    for finding in critical_findings[:5]:  # Top 5 critical
        action = {
            "priority": "critical",
            "action": finding.get("recommendation", "Review immediately"),
            "resource_id": finding.get("resource_id"),
            "estimated_savings": finding.get("cost_impact"),
            "timeline": "Immediate"
        }
        actions.append(action)
    
    # High priority actions
    for finding in high_findings[:5]:  # Top 5 high
        action = {
            "priority": "high",
            "action": finding.get("recommendation", "Review and address"),
            "resource_id": finding.get("resource_id"),
            "estimated_savings": finding.get("cost_impact"),
            "timeline": "Within 24 hours"
        }
        actions.append(action)
    
    return actions

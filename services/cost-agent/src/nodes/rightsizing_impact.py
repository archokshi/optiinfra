"""
Right-Sizing Impact Analysis Module

This module calculates the overall impact of right-sizing recommendations,
including cost savings, performance risk, and migration complexity.
"""

import logging
from typing import Dict, List, Any
from statistics import mean
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def calculate_impact_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate comprehensive impact analysis for all recommendations.
    
    Args:
        state: Workflow state containing rightsizing_recommendations
    
    Returns:
        Updated state with impact_analysis
    """
    try:
        recommendations = state.get("rightsizing_recommendations", [])
        
        logger.info(
            f"Calculating impact analysis for {len(recommendations)} recommendations",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id"),
                "recommendations": len(recommendations)
            }
        )
        
        if not recommendations:
            logger.warning("No recommendations to analyze")
            return {
                **state,
                "impact_analysis": {},
                "workflow_status": "impact_calculated"
            }
        
        # Calculate cost impact
        cost_impact = calculate_cost_impact(recommendations)
        
        # Calculate performance impact
        performance_impact = calculate_performance_impact(recommendations)
        
        # Calculate migration complexity
        migration_complexity = calculate_migration_complexity(recommendations)
        
        # Generate impact summary
        impact_summary = generate_impact_summary(
            recommendations,
            cost_impact,
            performance_impact,
            migration_complexity
        )
        
        # Combine all impact data
        impact_analysis = {
            **cost_impact,
            **performance_impact,
            **migration_complexity,
            **impact_summary
        }
        
        logger.info(
            f"Impact analysis complete: ${impact_analysis['total_monthly_savings']:.2f}/mo savings, "
            f"{impact_analysis['low_risk_count']} low-risk recommendations",
            extra={
                "request_id": state.get("request_id"),
                "monthly_savings": impact_analysis["total_monthly_savings"],
                "low_risk": impact_analysis["low_risk_count"]
            }
        )
        
        return {
            **state,
            "impact_analysis": impact_analysis,
            "workflow_status": "impact_calculated"
        }
        
    except Exception as e:
        logger.error(
            f"Error calculating impact analysis: {e}",
            extra={"request_id": state.get("request_id")},
            exc_info=True
        )
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Impact analysis failed: {str(e)}"
        }


def calculate_cost_impact(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate total cost impact of recommendations.
    
    Args:
        recommendations: List of recommendations
    
    Returns:
        Dictionary with cost impact metrics
    """
    total_current_cost = sum(rec["current_hourly_cost"] * 730 for rec in recommendations)
    total_recommended_cost = sum(rec["recommended_hourly_cost"] * 730 for rec in recommendations)
    total_monthly_savings = sum(rec["monthly_savings"] for rec in recommendations)
    total_annual_savings = sum(rec["annual_savings"] for rec in recommendations)
    
    average_savings_percent = mean(rec["savings_percent"] for rec in recommendations) if recommendations else 0
    
    # Breakdown by service type
    service_breakdown = {}
    for rec in recommendations:
        service_type = rec.get("service_type", "ec2")
        if service_type not in service_breakdown:
            service_breakdown[service_type] = {
                "count": 0,
                "monthly_savings": 0.0,
                "annual_savings": 0.0
            }
        service_breakdown[service_type]["count"] += 1
        service_breakdown[service_type]["monthly_savings"] += rec["monthly_savings"]
        service_breakdown[service_type]["annual_savings"] += rec["annual_savings"]
    
    return {
        "total_current_monthly_cost": total_current_cost,
        "total_recommended_monthly_cost": total_recommended_cost,
        "total_monthly_savings": total_monthly_savings,
        "total_annual_savings": total_annual_savings,
        "average_savings_percent": average_savings_percent,
        "service_breakdown": service_breakdown
    }


def calculate_performance_impact(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate performance impact and risk distribution.
    
    Args:
        recommendations: List of recommendations
    
    Returns:
        Dictionary with performance impact metrics
    """
    low_risk_count = sum(1 for rec in recommendations if rec["performance_risk"] == "low")
    medium_risk_count = sum(1 for rec in recommendations if rec["performance_risk"] == "medium")
    high_risk_count = sum(1 for rec in recommendations if rec["performance_risk"] == "high")
    
    # Instances requiring testing
    requires_testing = [
        rec["instance_id"]
        for rec in recommendations
        if rec["requires_testing"]
    ]
    
    # Performance improvement opportunities (upsizing)
    performance_improvements = [
        rec["instance_id"]
        for rec in recommendations
        if rec["optimization_type"] == "upsize"
    ]
    
    # Risk factors summary
    all_risk_factors = []
    for rec in recommendations:
        all_risk_factors.extend(rec.get("risk_factors", []))
    
    # Count unique risk factors
    risk_factor_counts = {}
    for factor in all_risk_factors:
        risk_factor_counts[factor] = risk_factor_counts.get(factor, 0) + 1
    
    return {
        "low_risk_count": low_risk_count,
        "medium_risk_count": medium_risk_count,
        "high_risk_count": high_risk_count,
        "requires_testing_count": len(requires_testing),
        "requires_testing_instances": requires_testing,
        "performance_improvement_count": len(performance_improvements),
        "performance_improvement_instances": performance_improvements,
        "risk_factor_distribution": risk_factor_counts
    }


def calculate_migration_complexity(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate migration complexity distribution.
    
    Args:
        recommendations: List of recommendations
    
    Returns:
        Dictionary with migration complexity metrics
    """
    simple_migrations = sum(1 for rec in recommendations if rec["migration_complexity"] == "simple")
    moderate_migrations = sum(1 for rec in recommendations if rec["migration_complexity"] == "moderate")
    complex_migrations = sum(1 for rec in recommendations if rec["migration_complexity"] == "complex")
    
    # Total estimated downtime
    total_downtime_minutes = sum(rec["estimated_downtime_minutes"] for rec in recommendations)
    
    # Breakdown by optimization type
    downsize_migrations = [rec for rec in recommendations if rec["optimization_type"] == "downsize"]
    upsize_migrations = [rec for rec in recommendations if rec["optimization_type"] == "upsize"]
    family_change_migrations = [rec for rec in recommendations if rec["optimization_type"] == "family_change"]
    
    return {
        "simple_migrations": simple_migrations,
        "moderate_migrations": moderate_migrations,
        "complex_migrations": complex_migrations,
        "total_estimated_downtime_minutes": total_downtime_minutes,
        "downsize_migrations_count": len(downsize_migrations),
        "upsize_migrations_count": len(upsize_migrations),
        "family_change_migrations_count": len(family_change_migrations)
    }


def generate_impact_summary(
    recommendations: List[Dict[str, Any]],
    cost_impact: Dict[str, Any],
    performance_impact: Dict[str, Any],
    migration_complexity: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate executive summary and prioritized recommendations.
    
    Args:
        recommendations: List of recommendations
        cost_impact: Cost impact data
        performance_impact: Performance impact data
        migration_complexity: Migration complexity data
    
    Returns:
        Dictionary with summary and prioritization
    """
    # Identify quick wins (high savings, low risk, simple migration)
    quick_wins = []
    for rec in recommendations:
        if (rec["performance_risk"] == "low" and
            rec["migration_complexity"] == "simple" and
            rec["monthly_savings"] > 20):  # At least $20/month savings
            quick_wins.append({
                "instance_id": rec["instance_id"],
                "current_type": rec["current_instance_type"],
                "recommended_type": rec["recommended_instance_type"],
                "monthly_savings": rec["monthly_savings"],
                "savings_percent": rec["savings_percent"]
            })
    
    # Sort quick wins by savings
    quick_wins.sort(key=lambda x: x["monthly_savings"], reverse=True)
    
    # Prioritize all recommendations
    prioritized_recommendations = []
    for rec in recommendations:
        # Calculate priority score (higher is better)
        priority_score = 0
        
        # Savings contribution (0-50 points)
        savings_score = min(rec["monthly_savings"] / 10, 50)
        priority_score += savings_score
        
        # Risk penalty (0-30 points)
        if rec["performance_risk"] == "low":
            risk_score = 30
        elif rec["performance_risk"] == "medium":
            risk_score = 15
        else:
            risk_score = 0
        priority_score += risk_score
        
        # Complexity bonus (0-20 points)
        if rec["migration_complexity"] == "simple":
            complexity_score = 20
        elif rec["migration_complexity"] == "moderate":
            complexity_score = 10
        else:
            complexity_score = 0
        priority_score += complexity_score
        
        prioritized_recommendations.append({
            "instance_id": rec["instance_id"],
            "current_type": rec["current_instance_type"],
            "recommended_type": rec["recommended_instance_type"],
            "monthly_savings": rec["monthly_savings"],
            "performance_risk": rec["performance_risk"],
            "migration_complexity": rec["migration_complexity"],
            "priority_score": priority_score,
            "priority_tier": "high" if priority_score >= 70 else "medium" if priority_score >= 40 else "low"
        })
    
    # Sort by priority score
    prioritized_recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
    
    # Implementation roadmap
    high_priority = [r for r in prioritized_recommendations if r["priority_tier"] == "high"]
    medium_priority = [r for r in prioritized_recommendations if r["priority_tier"] == "medium"]
    low_priority = [r for r in prioritized_recommendations if r["priority_tier"] == "low"]
    
    implementation_roadmap = {
        "phase_1_quick_wins": {
            "count": len(quick_wins),
            "instances": [qw["instance_id"] for qw in quick_wins[:10]],  # Top 10
            "estimated_savings": sum(qw["monthly_savings"] for qw in quick_wins[:10]),
            "timeline": "Week 1"
        },
        "phase_2_high_priority": {
            "count": len(high_priority),
            "instances": [r["instance_id"] for r in high_priority[:20]],  # Top 20
            "estimated_savings": sum(r["monthly_savings"] for r in high_priority[:20]),
            "timeline": "Weeks 2-3"
        },
        "phase_3_medium_priority": {
            "count": len(medium_priority),
            "instances": [r["instance_id"] for r in medium_priority[:20]],  # Top 20
            "estimated_savings": sum(r["monthly_savings"] for r in medium_priority[:20]),
            "timeline": "Weeks 4-6"
        },
        "phase_4_low_priority": {
            "count": len(low_priority),
            "instances": [r["instance_id"] for r in low_priority[:10]],  # Top 10
            "estimated_savings": sum(r["monthly_savings"] for r in low_priority[:10]),
            "timeline": "Weeks 7+"
        }
    }
    
    # Executive summary
    executive_summary = {
        "total_recommendations": len(recommendations),
        "total_monthly_savings": cost_impact["total_monthly_savings"],
        "total_annual_savings": cost_impact["total_annual_savings"],
        "average_savings_percent": cost_impact["average_savings_percent"],
        "quick_wins_count": len(quick_wins),
        "quick_wins_savings": sum(qw["monthly_savings"] for qw in quick_wins),
        "low_risk_percentage": (performance_impact["low_risk_count"] / len(recommendations) * 100) if recommendations else 0,
        "simple_migration_percentage": (migration_complexity["simple_migrations"] / len(recommendations) * 100) if recommendations else 0,
        "estimated_total_downtime_hours": migration_complexity["total_estimated_downtime_minutes"] / 60
    }
    
    return {
        "quick_wins": quick_wins[:10],  # Top 10 quick wins
        "quick_wins_count": len(quick_wins),
        "prioritized_recommendations": prioritized_recommendations,
        "implementation_roadmap": implementation_roadmap,
        "executive_summary": executive_summary
    }

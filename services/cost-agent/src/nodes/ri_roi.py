"""
Reserved Instance ROI calculator.
Performs comprehensive ROI analysis for RI recommendations.

This module provides:
- Break-even analysis
- NPV (Net Present Value) calculation
- Total savings projections
- Risk-adjusted ROI
"""

import logging
from typing import Dict, Any, List
from statistics import mean

logger = logging.getLogger(__name__)


def calculate_roi_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive ROI analysis for RI recommendations.
    
    Calculates:
    - Average break-even period
    - Total projected savings
    - ROI percentage
    - Risk-adjusted metrics
    - Coverage improvement potential
    
    Args:
        state: Workflow state containing:
            - ri_recommendations: List of RI recommendations
            - customer_id: Customer identifier
            - request_id: Request identifier
            
    Returns:
        Updated state with:
            - roi_analysis: Comprehensive ROI metrics
            - workflow_status: "roi_calculated"
    """
    try:
        logger.info(
            f"Calculating ROI analysis for customer {state['customer_id']}",
            extra={
                "request_id": state["request_id"],
                "customer_id": state["customer_id"],
                "recommendations_count": len(state.get("ri_recommendations", []))
            }
        )
        
        recommendations = state.get("ri_recommendations", [])
        
        if not recommendations:
            logger.warning("No recommendations available for ROI analysis")
            state["roi_analysis"] = {
                "average_breakeven_months": 0,
                "total_investment": 0.0,
                "total_return_1yr": 0.0,
                "total_return_3yr": 0.0,
                "roi_percent_1yr": 0.0,
                "roi_percent_3yr": 0.0,
                "risk_adjusted_roi": 0.0
            }
            state["workflow_status"] = "roi_calculated"
            state["current_phase"] = "roi_complete"
            return state
        
        # Calculate aggregate metrics
        total_upfront = sum(r["ri_cost_upfront"] for r in recommendations)
        total_monthly_savings = sum(r["monthly_savings"] for r in recommendations)
        total_annual_savings = sum(r["annual_savings"] for r in recommendations)
        
        # Calculate average break-even
        breakeven_values = [r["breakeven_months"] for r in recommendations]
        avg_breakeven = mean(breakeven_values) if breakeven_values else 0
        
        # Calculate ROI for different time horizons
        roi_1yr = calculate_roi_percent(total_upfront, total_annual_savings)
        roi_3yr = calculate_roi_percent(total_upfront, total_annual_savings * 3)
        
        # Calculate risk-adjusted ROI
        risk_adjusted_roi = calculate_risk_adjusted_roi(recommendations)
        
        # Calculate NPV (Net Present Value) with 5% discount rate
        npv_1yr = calculate_npv(total_upfront, total_monthly_savings, 12, 0.05)
        npv_3yr = calculate_npv(total_upfront, total_monthly_savings, 36, 0.05)
        
        # Count recommendations by term
        one_year_count = sum(1 for r in recommendations if r["term"] == "1year")
        three_year_count = sum(1 for r in recommendations if r["term"] == "3year")
        
        # Count by risk level
        low_risk_count = sum(1 for r in recommendations if r["risk_level"] == "low")
        medium_risk_count = sum(1 for r in recommendations if r["risk_level"] == "medium")
        high_risk_count = sum(1 for r in recommendations if r["risk_level"] == "high")
        
        roi_analysis = {
            "average_breakeven_months": round(avg_breakeven, 1),
            "total_investment": round(total_upfront, 2),
            "total_monthly_savings": round(total_monthly_savings, 2),
            "total_annual_savings": round(total_annual_savings, 2),
            "total_return_1yr": round(total_annual_savings, 2),
            "total_return_3yr": round(total_annual_savings * 3, 2),
            "roi_percent_1yr": round(roi_1yr, 2),
            "roi_percent_3yr": round(roi_3yr, 2),
            "risk_adjusted_roi": round(risk_adjusted_roi, 2),
            "npv_1yr": round(npv_1yr, 2),
            "npv_3yr": round(npv_3yr, 2),
            "one_year_ris": one_year_count,
            "three_year_ris": three_year_count,
            "low_risk_count": low_risk_count,
            "medium_risk_count": medium_risk_count,
            "high_risk_count": high_risk_count,
            "recommendation_summary": generate_recommendation_summary(recommendations)
        }
        
        logger.info(
            f"ROI analysis complete: {avg_breakeven:.1f} month breakeven, {roi_1yr:.1f}% 1-year ROI",
            extra={
                "request_id": state["request_id"],
                "customer_id": state["customer_id"],
                "average_breakeven_months": avg_breakeven,
                "roi_percent_1yr": roi_1yr
            }
        )
        
        state["roi_analysis"] = roi_analysis
        state["workflow_status"] = "roi_calculated"
        state["current_phase"] = "roi_complete"
        
        return state
        
    except Exception as e:
        logger.error(
            f"Error calculating ROI analysis: {e}",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id")
            },
            exc_info=True
        )
        state["workflow_status"] = "failed"
        state["error_message"] = f"ROI calculation failed: {str(e)}"
        state["success"] = False
        return state


def calculate_roi_percent(investment: float, total_return: float) -> float:
    """
    Calculate ROI percentage.
    
    Formula: ((Total Return - Investment) / Investment) * 100
    
    Args:
        investment: Initial investment (upfront cost)
        total_return: Total return over period
        
    Returns:
        ROI percentage
    """
    if investment == 0:
        return 0.0
    
    roi = ((total_return - investment) / investment) * 100
    return roi


def calculate_risk_adjusted_roi(recommendations: List[Dict[str, Any]]) -> float:
    """
    Calculate risk-adjusted ROI.
    
    Applies risk multipliers to savings based on risk level:
    - Low risk: 1.0x (no adjustment)
    - Medium risk: 0.85x (15% reduction)
    - High risk: 0.70x (30% reduction)
    
    Args:
        recommendations: List of RI recommendations
        
    Returns:
        Risk-adjusted ROI percentage
    """
    risk_multipliers = {
        "low": 1.0,
        "medium": 0.85,
        "high": 0.70
    }
    
    total_investment = sum(r["ri_cost_upfront"] for r in recommendations)
    
    risk_adjusted_savings = sum(
        r["annual_savings"] * risk_multipliers.get(r["risk_level"], 0.85)
        for r in recommendations
    )
    
    if total_investment == 0:
        return 0.0
    
    return ((risk_adjusted_savings - total_investment) / total_investment) * 100


def calculate_npv(
    initial_investment: float,
    monthly_cash_flow: float,
    months: int,
    annual_discount_rate: float = 0.05
) -> float:
    """
    Calculate Net Present Value (NPV).
    
    NPV accounts for the time value of money by discounting future cash flows.
    
    Args:
        initial_investment: Initial upfront cost
        monthly_cash_flow: Monthly savings
        months: Number of months
        annual_discount_rate: Annual discount rate (default: 5%)
        
    Returns:
        Net Present Value
    """
    monthly_discount_rate = annual_discount_rate / 12
    
    # Calculate present value of future cash flows
    pv_cash_flows = sum(
        monthly_cash_flow / ((1 + monthly_discount_rate) ** month)
        for month in range(1, months + 1)
    )
    
    # NPV = PV of cash flows - initial investment
    npv = pv_cash_flows - initial_investment
    
    return npv


def generate_recommendation_summary(
    recommendations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate a summary of recommendations by various dimensions.
    
    Args:
        recommendations: List of RI recommendations
        
    Returns:
        Summary dictionary with breakdowns
    """
    # By service type
    by_service = {}
    for rec in recommendations:
        service = rec["service_type"]
        if service not in by_service:
            by_service[service] = {
                "count": 0,
                "total_savings": 0.0,
                "total_upfront": 0.0
            }
        by_service[service]["count"] += 1
        by_service[service]["total_savings"] += rec["annual_savings"]
        by_service[service]["total_upfront"] += rec["ri_cost_upfront"]
    
    # By region
    by_region = {}
    for rec in recommendations:
        region = rec["region"]
        if region not in by_region:
            by_region[region] = {
                "count": 0,
                "total_savings": 0.0
            }
        by_region[region]["count"] += 1
        by_region[region]["total_savings"] += rec["annual_savings"]
    
    # By term
    by_term = {
        "1year": {
            "count": sum(1 for r in recommendations if r["term"] == "1year"),
            "total_savings": sum(r["annual_savings"] for r in recommendations if r["term"] == "1year")
        },
        "3year": {
            "count": sum(1 for r in recommendations if r["term"] == "3year"),
            "total_savings": sum(r["annual_savings"] for r in recommendations if r["term"] == "3year")
        }
    }
    
    # By payment option
    by_payment = {}
    for rec in recommendations:
        payment = rec["payment_option"]
        if payment not in by_payment:
            by_payment[payment] = {
                "count": 0,
                "total_savings": 0.0,
                "total_upfront": 0.0
            }
        by_payment[payment]["count"] += 1
        by_payment[payment]["total_savings"] += rec["annual_savings"]
        by_payment[payment]["total_upfront"] += rec["ri_cost_upfront"]
    
    # Top recommendations by savings
    top_recommendations = sorted(
        recommendations,
        key=lambda x: x["annual_savings"],
        reverse=True
    )[:5]
    
    top_recs_summary = [
        {
            "instance_type": r["instance_type"],
            "term": r["term"],
            "annual_savings": r["annual_savings"],
            "risk_level": r["risk_level"]
        }
        for r in top_recommendations
    ]
    
    return {
        "by_service_type": by_service,
        "by_region": by_region,
        "by_term": by_term,
        "by_payment_option": by_payment,
        "top_5_by_savings": top_recs_summary
    }

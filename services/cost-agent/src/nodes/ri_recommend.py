"""
Reserved Instance recommendation engine.
Generates optimal RI purchase recommendations based on usage analysis.

This module provides:
- RI matching logic for AWS/GCP/Azure
- Savings calculations for different terms
- Payment option recommendations
- Risk assessment
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# RI pricing data (simplified - in production, fetch from pricing APIs)
RI_DISCOUNT_RATES = {
    "aws": {
        "1year": {
            "all_upfront": 0.40,      # 40% savings
            "partial_upfront": 0.35,   # 35% savings
            "no_upfront": 0.30         # 30% savings
        },
        "3year": {
            "all_upfront": 0.60,       # 60% savings
            "partial_upfront": 0.55,   # 55% savings
            "no_upfront": 0.50         # 50% savings
        }
    },
    "gcp": {
        "1year": {"committed": 0.37},  # 37% savings (CUD)
        "3year": {"committed": 0.55}   # 55% savings (CUD)
    },
    "azure": {
        "1year": {"reserved": 0.40},   # 40% savings
        "3year": {"reserved": 0.62}    # 62% savings
    }
}


def generate_ri_recommendations(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate RI recommendations based on stable workloads.
    
    For each stable workload identified in the analysis phase:
    1. Match to appropriate RI offering
    2. Calculate savings for 1-year and 3-year terms
    3. Compare payment options
    4. Recommend optimal configuration
    5. Assess risk level
    
    Args:
        state: Workflow state containing:
            - stable_workloads: List of RI candidates
            - cloud_provider: Cloud provider (aws/gcp/azure)
            - customer_id: Customer identifier
            - request_id: Request identifier
            
    Returns:
        Updated state with:
            - ri_recommendations: List of RI recommendations
            - total_savings: Total projected savings
            - workflow_status: "recommendations_generated"
    """
    try:
        logger.info(
            f"Generating RI recommendations for customer {state['customer_id']}",
            extra={
                "request_id": state["request_id"],
                "customer_id": state["customer_id"],
                "stable_workloads_count": len(state.get("stable_workloads", []))
            }
        )
        
        stable_workloads = state.get("stable_workloads", [])
        cloud_provider = state.get("cloud_provider", "aws")
        
        if not stable_workloads:
            logger.warning("No stable workloads found for RI recommendations")
            state["ri_recommendations"] = []
            state["total_savings"] = 0.0
            state["workflow_status"] = "recommendations_generated"
            state["current_phase"] = "recommendations_complete"
            return state
        
        recommendations = []
        total_monthly_savings = 0.0
        total_annual_savings = 0.0
        total_upfront_cost = 0.0
        
        for workload in stable_workloads:
            # Generate recommendations for both 1-year and 3-year terms
            rec_1yr = generate_single_recommendation(
                workload, cloud_provider, "1year", state
            )
            rec_3yr = generate_single_recommendation(
                workload, cloud_provider, "3year", state
            )
            
            # Choose the best recommendation based on customer preferences
            best_rec = choose_best_recommendation(
                rec_1yr, rec_3yr, state.get("customer_preferences", {})
            )
            
            if best_rec:
                recommendations.append(best_rec)
                total_monthly_savings += best_rec["monthly_savings"]
                total_annual_savings += best_rec["annual_savings"]
                total_upfront_cost += best_rec["ri_cost_upfront"]
        
        # Calculate 3-year total savings
        total_three_year_savings = sum(
            r["total_savings"] for r in recommendations if r["term"] == "3year"
        )
        
        logger.info(
            f"Generated {len(recommendations)} RI recommendations",
            extra={
                "request_id": state["request_id"],
                "customer_id": state["customer_id"],
                "recommendations_count": len(recommendations),
                "total_monthly_savings": total_monthly_savings,
                "total_annual_savings": total_annual_savings
            }
        )
        
        state["ri_recommendations"] = recommendations
        state["total_monthly_savings"] = round(total_monthly_savings, 2)
        state["total_annual_savings"] = round(total_annual_savings, 2)
        state["total_three_year_savings"] = round(total_three_year_savings, 2)
        state["total_upfront_cost"] = round(total_upfront_cost, 2)
        state["workflow_status"] = "recommendations_generated"
        state["current_phase"] = "recommendations_complete"
        
        return state
        
    except Exception as e:
        logger.error(
            f"Error generating RI recommendations: {e}",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id")
            },
            exc_info=True
        )
        state["workflow_status"] = "failed"
        state["error_message"] = f"Recommendation generation failed: {str(e)}"
        state["success"] = False
        return state


def generate_single_recommendation(
    workload: Dict[str, Any],
    cloud_provider: str,
    term: str,
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a single RI recommendation for a workload.
    
    Args:
        workload: Stable workload data
        cloud_provider: Cloud provider (aws/gcp/azure)
        term: RI term ("1year" or "3year")
        state: Workflow state
        
    Returns:
        RI recommendation dictionary
    """
    on_demand_monthly_cost = workload["monthly_cost"]
    
    # Get discount rates for this provider and term
    discount_rates = RI_DISCOUNT_RATES.get(cloud_provider, {}).get(term, {})
    
    # For AWS, compare all payment options
    if cloud_provider == "aws":
        payment_options = []
        
        for payment_type, discount_rate in discount_rates.items():
            savings_calc = calculate_ri_savings(
                on_demand_monthly_cost,
                discount_rate,
                term,
                payment_type
            )
            payment_options.append({
                "payment_option": payment_type,
                **savings_calc
            })
        
        # Choose best payment option
        best_option = recommend_payment_option(
            payment_options,
            state.get("customer_preferences", {})
        )
        
    else:
        # GCP and Azure have simpler pricing
        payment_type = "committed" if cloud_provider == "gcp" else "reserved"
        discount_rate = list(discount_rates.values())[0]
        
        savings_calc = calculate_ri_savings(
            on_demand_monthly_cost,
            discount_rate,
            term,
            payment_type
        )
        best_option = {
            "payment_option": payment_type,
            **savings_calc
        }
    
    # Assess risk level
    risk_level = assess_risk_level(
        workload["usage_pattern"],
        workload["uptime_percent"],
        workload["metrics"].get("variance", 0)
    )
    
    return {
        "instance_id": workload["instance_id"],
        "instance_type": workload["instance_type"],
        "service_type": workload["service_type"],
        "region": workload["region"],
        "term": term,
        "payment_option": best_option["payment_option"],
        "quantity": 1,
        
        "on_demand_cost_monthly": on_demand_monthly_cost,
        "ri_cost_upfront": best_option["upfront_cost"],
        "ri_cost_monthly": best_option["monthly_cost"],
        
        "monthly_savings": best_option["monthly_savings"],
        "annual_savings": best_option["annual_savings"],
        "total_savings": best_option["total_savings"],
        "savings_percent": best_option["savings_percent"],
        "breakeven_months": best_option["breakeven_months"],
        
        "risk_level": risk_level,
        "confidence_score": workload["confidence_score"],
        "usage_pattern": workload["usage_pattern"]
    }


def calculate_ri_savings(
    on_demand_monthly_cost: float,
    discount_rate: float,
    term: str,
    payment_option: str
) -> Dict[str, float]:
    """
    Calculate savings for an RI purchase.
    
    Args:
        on_demand_monthly_cost: Current on-demand monthly cost
        discount_rate: Discount rate (e.g., 0.40 for 40% savings)
        term: RI term ("1year" or "3year")
        payment_option: Payment option type
        
    Returns:
        Dictionary with savings calculations
    """
    term_months = 12 if term == "1year" else 36
    
    # Calculate RI costs based on payment option
    if payment_option == "all_upfront":
        # Pay everything upfront, no monthly cost
        upfront_cost = on_demand_monthly_cost * term_months * (1 - discount_rate)
        monthly_cost = 0.0
        
    elif payment_option == "partial_upfront":
        # Pay 50% upfront, rest monthly
        total_ri_cost = on_demand_monthly_cost * term_months * (1 - discount_rate)
        upfront_cost = total_ri_cost * 0.5
        monthly_cost = (total_ri_cost * 0.5) / term_months
        
    else:  # no_upfront or committed/reserved
        # No upfront, pay monthly
        upfront_cost = 0.0
        monthly_cost = on_demand_monthly_cost * (1 - discount_rate)
    
    # Calculate savings
    monthly_savings = on_demand_monthly_cost - monthly_cost
    annual_savings = monthly_savings * 12
    total_savings = (on_demand_monthly_cost * term_months) - (upfront_cost + (monthly_cost * term_months))
    savings_percent = (total_savings / (on_demand_monthly_cost * term_months)) * 100
    
    # Calculate break-even point
    if monthly_savings > 0:
        breakeven_months = int(upfront_cost / monthly_savings) if monthly_savings > 0 else 0
    else:
        breakeven_months = term_months
    
    return {
        "upfront_cost": round(upfront_cost, 2),
        "monthly_cost": round(monthly_cost, 2),
        "monthly_savings": round(monthly_savings, 2),
        "annual_savings": round(annual_savings, 2),
        "total_savings": round(total_savings, 2),
        "savings_percent": round(savings_percent, 2),
        "breakeven_months": breakeven_months
    }


def recommend_payment_option(
    payment_options: List[Dict[str, Any]],
    customer_preferences: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Recommend the best payment option based on customer preferences.
    
    Args:
        payment_options: List of payment option calculations
        customer_preferences: Customer preferences dictionary
        
    Returns:
        Best payment option
    """
    preference = customer_preferences.get("payment_preference", "maximize_savings")
    
    if preference == "minimize_upfront":
        # Choose option with lowest upfront cost
        return min(payment_options, key=lambda x: x["upfront_cost"])
        
    elif preference == "fastest_breakeven":
        # Choose option with fastest break-even
        return min(payment_options, key=lambda x: x["breakeven_months"])
        
    else:  # maximize_savings (default)
        # Choose option with highest total savings
        return max(payment_options, key=lambda x: x["total_savings"])


def choose_best_recommendation(
    rec_1yr: Dict[str, Any],
    rec_3yr: Dict[str, Any],
    customer_preferences: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Choose between 1-year and 3-year RI recommendation.
    
    Args:
        rec_1yr: 1-year RI recommendation
        rec_3yr: 3-year RI recommendation
        customer_preferences: Customer preferences
        
    Returns:
        Best recommendation
    """
    preference = customer_preferences.get("term_preference", "auto")
    
    if preference == "1year":
        return rec_1yr
    elif preference == "3year":
        return rec_3yr
    else:  # auto - choose based on risk and savings
        # If high risk, prefer 1-year
        if rec_1yr["risk_level"] == "high":
            return rec_1yr
        # If low risk and 3-year has significantly better savings, choose 3-year
        elif (rec_1yr["risk_level"] == "low" and 
              rec_3yr["total_savings"] > rec_1yr["total_savings"] * 1.5):
            return rec_3yr
        # Default to 1-year for medium risk
        else:
            return rec_1yr


def assess_risk_level(
    usage_pattern: str,
    uptime_percent: float,
    variance: float
) -> str:
    """
    Assess risk level for RI purchase.
    
    Risk factors:
    - Usage pattern (steady = low risk, declining = high risk)
    - Uptime percentage (higher = lower risk)
    - Variance (lower = lower risk)
    
    Args:
        usage_pattern: Usage pattern type
        uptime_percent: Uptime percentage
        variance: CPU utilization variance
        
    Returns:
        Risk level: "low", "medium", or "high"
    """
    risk_score = 0
    
    # Pattern risk
    pattern_risk = {
        "steady": 0,
        "growing": 1,
        "seasonal": 2,
        "declining": 3,
        "unknown": 2
    }
    risk_score += pattern_risk.get(usage_pattern, 2)
    
    # Uptime risk
    if uptime_percent >= 95:
        risk_score += 0
    elif uptime_percent >= 90:
        risk_score += 1
    elif uptime_percent >= 85:
        risk_score += 2
    else:
        risk_score += 3
    
    # Variance risk
    if variance < 10:
        risk_score += 0
    elif variance < 20:
        risk_score += 1
    else:
        risk_score += 2
    
    # Classify risk
    if risk_score <= 2:
        return "low"
    elif risk_score <= 4:
        return "medium"
    else:
        return "high"

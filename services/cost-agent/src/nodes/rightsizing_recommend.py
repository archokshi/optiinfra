"""
Right-Sizing Recommendation Engine

This module generates optimal instance type recommendations based on actual
resource utilization patterns. It considers cost savings, performance risk,
and migration complexity.
"""

import logging
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# AWS EC2 Instance Type Catalog (simplified - in production, load from API/database)
AWS_INSTANCE_CATALOG = {
    # T3 family (burstable)
    "t3.nano": {"vcpus": 2, "memory_gb": 0.5, "hourly_cost": 0.0052, "network": "up_to_5gbps"},
    "t3.micro": {"vcpus": 2, "memory_gb": 1.0, "hourly_cost": 0.0104, "network": "up_to_5gbps"},
    "t3.small": {"vcpus": 2, "memory_gb": 2.0, "hourly_cost": 0.0208, "network": "up_to_5gbps"},
    "t3.medium": {"vcpus": 2, "memory_gb": 4.0, "hourly_cost": 0.0416, "network": "up_to_5gbps"},
    "t3.large": {"vcpus": 2, "memory_gb": 8.0, "hourly_cost": 0.0832, "network": "up_to_5gbps"},
    "t3.xlarge": {"vcpus": 4, "memory_gb": 16.0, "hourly_cost": 0.1664, "network": "up_to_5gbps"},
    "t3.2xlarge": {"vcpus": 8, "memory_gb": 32.0, "hourly_cost": 0.3328, "network": "up_to_5gbps"},
    
    # T4g family (ARM/Graviton, burstable)
    "t4g.nano": {"vcpus": 2, "memory_gb": 0.5, "hourly_cost": 0.0042, "network": "up_to_5gbps", "architecture": "arm"},
    "t4g.micro": {"vcpus": 2, "memory_gb": 1.0, "hourly_cost": 0.0084, "network": "up_to_5gbps", "architecture": "arm"},
    "t4g.small": {"vcpus": 2, "memory_gb": 2.0, "hourly_cost": 0.0168, "network": "up_to_5gbps", "architecture": "arm"},
    "t4g.medium": {"vcpus": 2, "memory_gb": 4.0, "hourly_cost": 0.0336, "network": "up_to_5gbps", "architecture": "arm"},
    "t4g.large": {"vcpus": 2, "memory_gb": 8.0, "hourly_cost": 0.0672, "network": "up_to_5gbps", "architecture": "arm"},
    "t4g.xlarge": {"vcpus": 4, "memory_gb": 16.0, "hourly_cost": 0.1344, "network": "up_to_5gbps", "architecture": "arm"},
    "t4g.2xlarge": {"vcpus": 8, "memory_gb": 32.0, "hourly_cost": 0.2688, "network": "up_to_5gbps", "architecture": "arm"},
    
    # M5 family (general purpose)
    "m5.large": {"vcpus": 2, "memory_gb": 8.0, "hourly_cost": 0.096, "network": "up_to_10gbps"},
    "m5.xlarge": {"vcpus": 4, "memory_gb": 16.0, "hourly_cost": 0.192, "network": "up_to_10gbps"},
    "m5.2xlarge": {"vcpus": 8, "memory_gb": 32.0, "hourly_cost": 0.384, "network": "up_to_10gbps"},
    "m5.4xlarge": {"vcpus": 16, "memory_gb": 64.0, "hourly_cost": 0.768, "network": "10gbps"},
    
    # C5 family (compute optimized)
    "c5.large": {"vcpus": 2, "memory_gb": 4.0, "hourly_cost": 0.085, "network": "up_to_10gbps"},
    "c5.xlarge": {"vcpus": 4, "memory_gb": 8.0, "hourly_cost": 0.17, "network": "up_to_10gbps"},
    "c5.2xlarge": {"vcpus": 8, "memory_gb": 16.0, "hourly_cost": 0.34, "network": "up_to_10gbps"},
    
    # R5 family (memory optimized)
    "r5.large": {"vcpus": 2, "memory_gb": 16.0, "hourly_cost": 0.126, "network": "up_to_10gbps"},
    "r5.xlarge": {"vcpus": 4, "memory_gb": 32.0, "hourly_cost": 0.252, "network": "up_to_10gbps"},
    "r5.2xlarge": {"vcpus": 8, "memory_gb": 64.0, "hourly_cost": 0.504, "network": "up_to_10gbps"},
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def generate_rightsizing_recommendations(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate right-sizing recommendations for optimization candidates.
    
    Args:
        state: Workflow state containing optimization_candidates
    
    Returns:
        Updated state with rightsizing_recommendations
    """
    try:
        candidates = state.get("optimization_candidates", [])
        customer_preferences = state.get("customer_preferences", {})
        include_arm = state.get("include_arm", True)
        
        logger.info(
            f"Generating recommendations for {len(candidates)} candidates",
            extra={
                "request_id": state.get("request_id"),
                "customer_id": state.get("customer_id"),
                "candidates": len(candidates)
            }
        )
        
        recommendations = []
        total_monthly_savings = 0.0
        total_annual_savings = 0.0
        downsize_count = 0
        upsize_count = 0
        family_change_count = 0
        
        for candidate in candidates:
            try:
                # Generate recommendation
                recommendation = generate_single_recommendation(
                    candidate,
                    customer_preferences,
                    include_arm
                )
                
                if recommendation:
                    recommendations.append(recommendation)
                    total_monthly_savings += recommendation["monthly_savings"]
                    total_annual_savings += recommendation["annual_savings"]
                    
                    # Track optimization types
                    if recommendation["optimization_type"] == "downsize":
                        downsize_count += 1
                    elif recommendation["optimization_type"] == "upsize":
                        upsize_count += 1
                    elif recommendation["optimization_type"] == "family_change":
                        family_change_count += 1
                    
                    logger.debug(
                        f"Recommendation: {candidate.get('instance_id')} "
                        f"{candidate.get('instance_type')} → {recommendation['recommended_instance_type']} "
                        f"(${recommendation['monthly_savings']:.2f}/mo savings)",
                        extra={
                            "instance_id": candidate.get("instance_id"),
                            "current": candidate.get("instance_type"),
                            "recommended": recommendation["recommended_instance_type"],
                            "savings": recommendation["monthly_savings"]
                        }
                    )
                
            except Exception as e:
                logger.warning(
                    f"Failed to generate recommendation for {candidate.get('instance_id')}: {e}",
                    extra={"instance_id": candidate.get("instance_id")}
                )
                continue
        
        logger.info(
            f"Generated {len(recommendations)} recommendations with "
            f"${total_monthly_savings:.2f}/mo total savings",
            extra={
                "request_id": state.get("request_id"),
                "recommendations": len(recommendations),
                "monthly_savings": total_monthly_savings,
                "annual_savings": total_annual_savings
            }
        )
        
        return {
            **state,
            "rightsizing_recommendations": recommendations,
            "total_monthly_savings": total_monthly_savings,
            "total_annual_savings": total_annual_savings,
            "downsize_count": downsize_count,
            "upsize_count": upsize_count,
            "family_change_count": family_change_count,
            "workflow_status": "recommendations_generated"
        }
        
    except Exception as e:
        logger.error(
            f"Error generating recommendations: {e}",
            extra={"request_id": state.get("request_id")},
            exc_info=True
        )
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Recommendation generation failed: {str(e)}"
        }


def generate_single_recommendation(
    candidate: Dict[str, Any],
    customer_preferences: Dict[str, Any],
    include_arm: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Generate a single right-sizing recommendation.
    
    Args:
        candidate: Optimization candidate with metrics
        customer_preferences: Customer preferences
        include_arm: Whether to include ARM/Graviton instances
    
    Returns:
        Recommendation dictionary or None
    """
    current_type = candidate.get("instance_type")
    metrics = candidate.get("metrics", {})
    provisioning_issue = candidate.get("provisioning_issue")
    
    # Find optimal instance type
    optimal = find_optimal_instance_type(
        current_type,
        metrics,
        provisioning_issue,
        customer_preferences,
        include_arm
    )
    
    if not optimal:
        return None
    
    # Calculate savings
    current_info = AWS_INSTANCE_CATALOG.get(current_type, {})
    recommended_info = AWS_INSTANCE_CATALOG.get(optimal["instance_type"], {})
    
    current_hourly = current_info.get("hourly_cost", 0)
    recommended_hourly = recommended_info.get("hourly_cost", 0)
    
    hourly_savings = current_hourly - recommended_hourly
    monthly_savings = hourly_savings * 730  # Average hours per month
    annual_savings = monthly_savings * 12
    savings_percent = (hourly_savings / current_hourly * 100) if current_hourly > 0 else 0
    
    # Assess performance risk
    performance_risk, risk_factors = assess_performance_risk(
        metrics,
        current_info,
        recommended_info,
        provisioning_issue
    )
    
    # Generate migration plan
    migration = generate_migration_plan(
        current_type,
        optimal["instance_type"],
        performance_risk
    )
    
    # Determine optimization type
    current_vcpus = current_info.get("vcpus", 0)
    recommended_vcpus = recommended_info.get("vcpus", 0)
    current_family = current_type.split(".")[0]
    recommended_family = optimal["instance_type"].split(".")[0]
    
    if current_family != recommended_family:
        optimization_type = "family_change"
    elif recommended_vcpus < current_vcpus:
        optimization_type = "downsize"
    elif recommended_vcpus > current_vcpus:
        optimization_type = "upsize"
    else:
        optimization_type = "same_size"
    
    return {
        "instance_id": candidate.get("instance_id"),
        "current_instance_type": current_type,
        "recommended_instance_type": optimal["instance_type"],
        "service_type": candidate.get("service_type", "ec2"),
        "region": candidate.get("region", "us-east-1"),
        
        # Current metrics
        "current_metrics": metrics,
        
        # Cost analysis
        "current_hourly_cost": current_hourly,
        "recommended_hourly_cost": recommended_hourly,
        "hourly_savings": hourly_savings,
        "monthly_savings": monthly_savings,
        "annual_savings": annual_savings,
        "savings_percent": savings_percent,
        
        # Capacity comparison
        "current_vcpus": current_vcpus,
        "recommended_vcpus": recommended_vcpus,
        "current_memory_gb": current_info.get("memory_gb", 0),
        "recommended_memory_gb": recommended_info.get("memory_gb", 0),
        
        # Risk assessment
        "performance_risk": performance_risk,
        "risk_factors": risk_factors,
        "confidence_score": candidate.get("optimization_score", 0.5),
        
        # Migration
        "migration_complexity": migration["complexity"],
        "estimated_downtime_minutes": migration["downtime_minutes"],
        "requires_testing": migration["requires_testing"],
        
        # Metadata
        "optimization_type": optimization_type,
        "provisioning_issue": provisioning_issue,
        "recommendation_reason": optimal.get("reason", "")
    }


def find_optimal_instance_type(
    current_type: str,
    metrics: Dict[str, Any],
    provisioning_issue: str,
    customer_preferences: Dict[str, Any],
    include_arm: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Find the optimal instance type based on utilization metrics.
    
    Args:
        current_type: Current instance type
        metrics: Resource utilization metrics
        provisioning_issue: over_provisioned or under_provisioned
        customer_preferences: Customer preferences
        include_arm: Whether to include ARM instances
    
    Returns:
        Dictionary with instance_type and reason, or None
    """
    current_info = AWS_INSTANCE_CATALOG.get(current_type)
    if not current_info:
        return None
    
    cpu_p95 = metrics.get("cpu_p95", 0)
    memory_p95 = metrics.get("memory_p95", 0)
    
    # Calculate required resources (with headroom)
    if provisioning_issue == "over_provisioned":
        # Size down based on actual usage + 20% headroom
        required_cpu_percent = cpu_p95 * 1.2
        required_memory_percent = memory_p95 * 1.2
    else:
        # Size up to handle peak + 30% headroom
        required_cpu_percent = min(cpu_p95 * 1.3, 100)
        required_memory_percent = min(memory_p95 * 1.3, 100)
    
    # Find matching instances
    candidates = []
    current_family = current_type.split(".")[0]
    
    for instance_type, info in AWS_INSTANCE_CATALOG.items():
        # Skip ARM if not included
        if not include_arm and info.get("architecture") == "arm":
            continue
        
        # Skip if same as current
        if instance_type == current_type:
            continue
        
        # Check if it meets requirements
        vcpu_ratio = required_cpu_percent / 100
        memory_ratio = required_memory_percent / 100
        
        required_vcpus = current_info["vcpus"] * vcpu_ratio
        required_memory = current_info["memory_gb"] * memory_ratio
        
        if info["vcpus"] >= required_vcpus and info["memory_gb"] >= required_memory:
            # Calculate priority score
            family = instance_type.split(".")[0]
            
            # Priority 1: Same family
            if family == current_family:
                priority = 1
            # Priority 2: T4g (ARM) if allowed
            elif family == "t4g" and include_arm:
                priority = 2
            # Priority 3: Other families
            else:
                priority = 3
            
            # Calculate cost savings
            cost_savings = current_info["hourly_cost"] - info["hourly_cost"]
            
            candidates.append({
                "instance_type": instance_type,
                "priority": priority,
                "cost_savings": cost_savings,
                "info": info
            })
    
    if not candidates:
        return None
    
    # Sort by priority (lower is better), then by cost savings (higher is better)
    candidates.sort(key=lambda x: (x["priority"], -x["cost_savings"]))
    
    best = candidates[0]
    
    # Generate reason
    if best["priority"] == 1:
        reason = f"Same family ({current_family}), optimized for workload"
    elif best["priority"] == 2:
        reason = "ARM/Graviton instance with better price-performance"
    else:
        reason = "Alternative family with better cost-performance ratio"
    
    return {
        "instance_type": best["instance_type"],
        "reason": reason
    }


def assess_performance_risk(
    metrics: Dict[str, Any],
    current_info: Dict[str, Any],
    recommended_info: Dict[str, Any],
    provisioning_issue: str
) -> tuple[str, List[str]]:
    """
    Assess performance risk of the recommendation.
    
    Args:
        metrics: Resource utilization metrics
        current_info: Current instance info
        recommended_info: Recommended instance info
        provisioning_issue: Provisioning issue type
    
    Returns:
        Tuple of (risk_level, risk_factors)
    """
    risk_factors = []
    
    cpu_p95 = metrics.get("cpu_p95", 0)
    memory_p95 = metrics.get("memory_p95", 0)
    cpu_p99 = metrics.get("cpu_p99", 0)
    memory_p99 = metrics.get("memory_p99", 0)
    
    # Calculate resource ratios
    vcpu_ratio = recommended_info["vcpus"] / current_info["vcpus"]
    memory_ratio = recommended_info["memory_gb"] / current_info["memory_gb"]
    
    # Risk factor 1: Downsizing with high peak utilization
    if vcpu_ratio < 1.0 and cpu_p99 > 70:
        risk_factors.append("High peak CPU utilization")
    
    if memory_ratio < 1.0 and memory_p99 > 75:
        risk_factors.append("High peak memory utilization")
    
    # Risk factor 2: Significant downsizing
    if vcpu_ratio < 0.5:
        risk_factors.append("Significant vCPU reduction")
    
    if memory_ratio < 0.5:
        risk_factors.append("Significant memory reduction")
    
    # Risk factor 3: Burstable to non-burstable or vice versa
    current_family = list(current_info.keys())[0].split(".")[0] if current_info else ""
    recommended_family = list(recommended_info.keys())[0].split(".")[0] if recommended_info else ""
    
    if current_family.startswith("t") != recommended_family.startswith("t"):
        risk_factors.append("Change in burstable behavior")
    
    # Risk factor 4: Architecture change
    if recommended_info.get("architecture") == "arm":
        risk_factors.append("Architecture change to ARM (requires testing)")
    
    # Determine overall risk level
    if len(risk_factors) == 0:
        risk_level = "low"
    elif len(risk_factors) <= 2:
        risk_level = "medium"
    else:
        risk_level = "high"
    
    # Override: Upsizing is always low risk
    if provisioning_issue == "under_provisioned" and vcpu_ratio >= 1.0:
        risk_level = "low"
        risk_factors = ["Performance improvement expected"]
    
    return risk_level, risk_factors


def generate_migration_plan(
    current_type: str,
    recommended_type: str,
    performance_risk: str
) -> Dict[str, Any]:
    """
    Generate migration plan for the recommendation.
    
    Args:
        current_type: Current instance type
        recommended_type: Recommended instance type
        performance_risk: Performance risk level
    
    Returns:
        Migration plan dictionary
    """
    current_family = current_type.split(".")[0]
    recommended_family = recommended_type.split(".")[0]
    
    # Determine complexity
    if current_family == recommended_family:
        complexity = "simple"
        downtime_minutes = 2
        requires_testing = False
    elif recommended_family == "t4g":
        complexity = "complex"
        downtime_minutes = 5
        requires_testing = True
    else:
        complexity = "moderate"
        downtime_minutes = 3
        requires_testing = performance_risk == "high"
    
    return {
        "complexity": complexity,
        "downtime_minutes": downtime_minutes,
        "requires_testing": requires_testing,
        "steps": [
            "1. Create AMI backup",
            "2. Stop instance (if required)",
            f"3. Change instance type to {recommended_type}",
            "4. Start instance",
            "5. Verify application health",
            "6. Monitor performance for 24 hours"
        ]
    }

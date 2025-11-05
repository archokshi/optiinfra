"""
Vultr cost analyzer.
Analyzes costs and identifies optimization opportunities.
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VultrCostAnalyzer:
    """
    Analyzes Vultr costs and identifies savings opportunities.
    """
    
    def analyze_costs(
        self,
        account_info: Dict[str, Any],
        pending_charges: Dict[str, Any],
        instances: List[Dict[str, Any]],
        invoices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Comprehensive cost analysis.
        
        Args:
            account_info: Account information
            pending_charges: Current month charges
            instances: List of instances
            invoices: Historical invoices
        
        Returns:
            Cost analysis with recommendations
        """
        # Calculate current spend
        current_monthly = pending_charges.get("pending_charges", 0)
        
        # GPU vs CPU breakdown
        gpu_instances = [i for i in instances if i.get("is_gpu")]
        cpu_instances = [i for i in instances if not i.get("is_gpu")]
        
        gpu_cost = sum(i.get("monthly_cost", 0) for i in gpu_instances)
        cpu_cost = sum(i.get("monthly_cost", 0) for i in cpu_instances)
        
        # Idle resources
        idle_instances = [
            i for i in instances
            if i.get("power_status") == "stopped" and i.get("monthly_cost", 0) > 0
        ]
        idle_cost = sum(i.get("monthly_cost", 0) for i in idle_instances)
        
        # Recommendations
        recommendations = []
        estimated_savings = 0
        
        # Recommendation 1: Delete idle instances
        if idle_instances:
            recommendations.append({
                "type": "delete_idle_instances",
                "priority": "high",
                "description": f"Delete {len(idle_instances)} stopped instances",
                "instances": [i["instance_id"] for i in idle_instances],
                "estimated_savings": idle_cost,
                "confidence": 0.95
            })
            estimated_savings += idle_cost
        
        # Recommendation 2: Snapshot optimization
        # Vultr charges $0.05/GB for snapshots
        # This would require additional API calls to get snapshot data
        
        # Recommendation 3: Right-size underutilized instances
        # Would require utilization metrics (CPU/RAM usage)
        # Placeholder for now
        
        from datetime import timezone
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cloud_provider": "vultr",
            
            # Current state
            "account_balance": account_info.get("balance", 0),
            "current_monthly_spend": current_monthly,
            "instance_count": len(instances),
            
            # Breakdown
            "cost_breakdown": {
                "gpu_cost": gpu_cost,
                "cpu_cost": cpu_cost,
                "gpu_percentage": (
                    (gpu_cost / (gpu_cost + cpu_cost) * 100)
                    if (gpu_cost + cpu_cost) > 0 else 0
                ),
            },
            
            # Waste identification
            "waste_analysis": {
                "idle_instances": len(idle_instances),
                "idle_cost": idle_cost,
                "idle_percentage": (
                    (idle_cost / current_monthly * 100)
                    if current_monthly > 0 else 0
                ),
            },
            
            # Recommendations
            "recommendations": recommendations,
            "total_estimated_savings": estimated_savings,
            "savings_percentage": (
                (estimated_savings / current_monthly * 100)
                if current_monthly > 0 else 0
            ),
        }
    
    def compare_with_competitors(
        self,
        vultr_costs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare Vultr costs with AWS/GCP/Azure.
        
        Args:
            vultr_costs: Current Vultr cost analysis
        
        Returns:
            Comparison analysis
        """
        # This is a simplified comparison
        # In reality, would need to compare similar instance types
        
        # Vultr is generally 20-40% cheaper than AWS/Azure
        # for comparable instances
        
        current_spend = vultr_costs["current_monthly_spend"]
        
        return {
            "vultr_cost": current_spend,
            "estimated_aws_cost": current_spend * 1.3,  # 30% more
            "estimated_gcp_cost": current_spend * 1.25,  # 25% more
            "estimated_azure_cost": current_spend * 1.35,  # 35% more
            "vultr_savings_vs_aws": current_spend * 0.3,
            "vultr_savings_vs_gcp": current_spend * 0.25,
            "vultr_savings_vs_azure": current_spend * 0.35,
            "note": "Estimates based on typical instance pricing comparisons"
        }

"""
Recommendation Fixtures.

Provides sample recommendation data for testing.
"""

from datetime import datetime, timedelta
from typing import List, Dict


def generate_spot_migration_recommendation(
    customer_id: str = "cust-test",
    instance_count: int = 10,
    monthly_savings: float = 1200.00
) -> Dict:
    """
    Generate spot migration recommendation.
    
    Args:
        customer_id: Customer ID
        instance_count: Number of instances
        monthly_savings: Estimated monthly savings
        
    Returns:
        Recommendation dictionary
    """
    return {
        "id": "rec-spot-123",
        "customer_id": customer_id,
        "type": "spot_migration",
        "title": f"Migrate {instance_count} EC2 instances to Spot",
        "description": f"Migrate {instance_count} non-critical workloads to Spot instances for cost savings",
        "estimated_monthly_savings": monthly_savings,
        "priority": "high",
        "risk_level": "low",
        "implementation_effort": "medium",
        "affected_resources": [f"i-{i:03d}" for i in range(instance_count)],
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {
            "current_instance_type": "t3.medium",
            "recommended_spot_type": "t3.medium",
            "availability_zones": ["us-east-1a", "us-east-1b"],
            "interruption_rate": "< 5%"
        }
    }


def generate_rightsizing_recommendation(
    customer_id: str = "cust-test",
    instance_id: str = "i-rightsizing-123",
    monthly_savings: float = 450.00
) -> Dict:
    """
    Generate rightsizing recommendation.
    
    Args:
        customer_id: Customer ID
        instance_id: Instance ID
        monthly_savings: Estimated monthly savings
        
    Returns:
        Recommendation dictionary
    """
    return {
        "id": "rec-rightsize-123",
        "customer_id": customer_id,
        "type": "rightsizing",
        "title": "Downsize over-provisioned instance",
        "description": "Instance is consistently using < 20% CPU and memory",
        "estimated_monthly_savings": monthly_savings,
        "priority": "medium",
        "risk_level": "low",
        "implementation_effort": "low",
        "affected_resources": [instance_id],
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {
            "current_instance_type": "m5.2xlarge",
            "recommended_instance_type": "m5.large",
            "avg_cpu_utilization": 18.5,
            "avg_memory_utilization": 22.3,
            "analysis_period_days": 30
        }
    }


def generate_reserved_instance_recommendation(
    customer_id: str = "cust-test",
    instance_count: int = 5,
    monthly_savings: float = 800.00
) -> Dict:
    """
    Generate reserved instance recommendation.
    
    Args:
        customer_id: Customer ID
        instance_count: Number of instances
        monthly_savings: Estimated monthly savings
        
    Returns:
        Recommendation dictionary
    """
    return {
        "id": "rec-ri-123",
        "customer_id": customer_id,
        "type": "reserved_instance",
        "title": f"Purchase Reserved Instances for {instance_count} instances",
        "description": f"Convert {instance_count} on-demand instances to 1-year Reserved Instances",
        "estimated_monthly_savings": monthly_savings,
        "priority": "high",
        "risk_level": "low",
        "implementation_effort": "low",
        "affected_resources": [f"i-ri-{i:03d}" for i in range(instance_count)],
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {
            "instance_type": "m5.xlarge",
            "term": "1-year",
            "payment_option": "partial_upfront",
            "upfront_cost": 2400.00,
            "total_savings_over_term": 9600.00
        }
    }


def generate_storage_optimization_recommendation(
    customer_id: str = "cust-test",
    volume_count: int = 15,
    monthly_savings: float = 320.00
) -> Dict:
    """
    Generate storage optimization recommendation.
    
    Args:
        customer_id: Customer ID
        volume_count: Number of volumes
        monthly_savings: Estimated monthly savings
        
    Returns:
        Recommendation dictionary
    """
    return {
        "id": "rec-storage-123",
        "customer_id": customer_id,
        "type": "storage_optimization",
        "title": f"Optimize {volume_count} underutilized EBS volumes",
        "description": f"Convert {volume_count} gp3 volumes to gp2 or reduce IOPS",
        "estimated_monthly_savings": monthly_savings,
        "priority": "low",
        "risk_level": "very_low",
        "implementation_effort": "low",
        "affected_resources": [f"vol-{i:03d}" for i in range(volume_count)],
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {
            "current_volume_type": "gp3",
            "recommended_volume_type": "gp2",
            "avg_iops_utilization": 15.2,
            "provisioned_iops": 3000,
            "recommended_iops": 1000
        }
    }


def generate_recommendation_batch(
    customer_id: str = "cust-test",
    count: int = 10
) -> List[Dict]:
    """
    Generate a batch of mixed recommendations.
    
    Args:
        customer_id: Customer ID
        count: Number of recommendations to generate
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    for i in range(count):
        if i % 4 == 0:
            rec = generate_spot_migration_recommendation(customer_id, instance_count=5 + i)
        elif i % 4 == 1:
            rec = generate_rightsizing_recommendation(customer_id, instance_id=f"i-{i:03d}")
        elif i % 4 == 2:
            rec = generate_reserved_instance_recommendation(customer_id, instance_count=3 + i)
        else:
            rec = generate_storage_optimization_recommendation(customer_id, volume_count=10 + i)
        
        rec["id"] = f"rec-batch-{i:03d}"
        recommendations.append(rec)
    
    return recommendations

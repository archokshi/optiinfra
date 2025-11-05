"""
E2E Test Data Generators.

Provides realistic test data for end-to-end integration tests.
"""

from datetime import datetime, timedelta
from typing import Dict, List
import random


def generate_e2e_cost_data(
    customer_id: str = "e2e-test",
    days: int = 30,
    base_cost: float = 15000.00
) -> Dict:
    """
    Generate realistic cost data for E2E tests.
    
    Args:
        customer_id: Customer ID
        days: Number of days to generate
        base_cost: Base daily cost
        
    Returns:
        Dictionary with cost data
    """
    daily_costs = []
    start_date = datetime.utcnow() - timedelta(days=days)
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        # Add trend and variation
        daily_cost = base_cost + (i * 100) + random.uniform(-500, 500)
        
        daily_costs.append({
            "date": date.strftime("%Y-%m-%d"),
            "total_cost": round(daily_cost, 2),
            "services": {
                "EC2": round(daily_cost * 0.55, 2),
                "RDS": round(daily_cost * 0.27, 2),
                "S3": round(daily_cost * 0.18, 2)
            }
        })
    
    return {
        "customer_id": customer_id,
        "provider": "aws",
        "period_start": daily_costs[0]["date"],
        "period_end": daily_costs[-1]["date"],
        "daily_costs": daily_costs,
        "total_cost": sum(d["total_cost"] for d in daily_costs)
    }


def generate_e2e_instances(count: int = 20) -> List[Dict]:
    """
    Generate instance data for E2E tests.
    
    Args:
        count: Number of instances to generate
        
    Returns:
        List of instance dictionaries
    """
    instances = []
    instance_types = ["t3.medium", "t3.large", "m5.xlarge", "m5.2xlarge", "c5.xlarge"]
    environments = ["production", "staging", "development"]
    workloads = ["web", "api", "batch", "database", "cache"]
    
    for i in range(count):
        instance_type = random.choice(instance_types)
        environment = random.choice(environments)
        workload = random.choice(workloads)
        
        # Generate realistic metrics based on instance type and workload
        if workload == "batch":
            avg_cpu = random.uniform(60, 90)
            avg_memory = random.uniform(70, 95)
        elif workload == "web":
            avg_cpu = random.uniform(20, 40)
            avg_memory = random.uniform(30, 50)
        else:
            avg_cpu = random.uniform(15, 35)
            avg_memory = random.uniform(25, 45)
        
        instances.append({
            "instance_id": f"i-e2e-{i:03d}",
            "instance_type": instance_type,
            "state": "running",
            "launch_time": (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat(),
            "availability_zone": f"us-east-1{random.choice(['a', 'b', 'c'])}",
            "tags": {
                "Name": f"e2e-instance-{i}",
                "Environment": environment,
                "Workload": workload,
                "Team": random.choice(["platform", "backend", "frontend"]),
                "CostCenter": random.choice(["engineering", "operations"])
            },
            "metrics": {
                "avg_cpu": round(avg_cpu, 2),
                "avg_memory": round(avg_memory, 2),
                "max_cpu": round(min(avg_cpu + random.uniform(20, 40), 100), 2),
                "max_memory": round(min(avg_memory + random.uniform(15, 30), 100), 2),
                "network_in": round(random.uniform(100, 1000), 2),
                "network_out": round(random.uniform(100, 1000), 2)
            },
            "cost": {
                "hourly": round(random.uniform(0.05, 0.50), 4),
                "monthly": round(random.uniform(36, 360), 2)
            }
        })
    
    return instances


def generate_e2e_workflow_state(workflow_type: str = "cost_optimization") -> Dict:
    """
    Generate workflow state for E2E tests.
    
    Args:
        workflow_type: Type of workflow
        
    Returns:
        Workflow state dictionary
    """
    return {
        "workflow_id": f"e2e-wf-{datetime.utcnow().timestamp()}",
        "workflow_type": workflow_type,
        "status": "in_progress",
        "current_step": "data_collection",
        "steps": [
            {"name": "data_collection", "status": "in_progress", "progress": 0},
            {"name": "analysis", "status": "pending", "progress": 0},
            {"name": "recommendation", "status": "pending", "progress": 0},
            {"name": "execution", "status": "pending", "progress": 0},
            {"name": "validation", "status": "pending", "progress": 0}
        ],
        "data": {},
        "metadata": {
            "customer_id": "e2e-test-customer",
            "initiated_by": "e2e-test",
            "priority": "normal"
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


def generate_e2e_recommendations(count: int = 5) -> List[Dict]:
    """
    Generate recommendations for E2E tests.
    
    Args:
        count: Number of recommendations to generate
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    types = ["spot_migration", "rightsizing", "reserved_instance", "storage_optimization"]
    
    for i in range(count):
        rec_type = random.choice(types)
        
        if rec_type == "spot_migration":
            savings = random.uniform(800, 1500)
            risk = "low"
            priority = "high"
        elif rec_type == "rightsizing":
            savings = random.uniform(300, 800)
            risk = "low"
            priority = "medium"
        elif rec_type == "reserved_instance":
            savings = random.uniform(600, 1200)
            risk = "very_low"
            priority = "high"
        else:
            savings = random.uniform(200, 500)
            risk = "very_low"
            priority = "low"
        
        recommendations.append({
            "id": f"rec-e2e-{i:03d}",
            "type": rec_type,
            "title": f"E2E {rec_type.replace('_', ' ').title()} Recommendation",
            "description": f"Test recommendation for {rec_type}",
            "estimated_monthly_savings": round(savings, 2),
            "priority": priority,
            "risk_level": risk,
            "status": "pending",
            "affected_resources": [f"i-e2e-{j:03d}" for j in range(random.randint(1, 5))],
            "created_at": datetime.utcnow().isoformat()
        })
    
    return recommendations


def generate_e2e_multi_cloud_data() -> Dict:
    """
    Generate multi-cloud cost data for E2E tests.
    
    Returns:
        Multi-cloud cost data dictionary
    """
    return {
        "customer_id": "e2e-test-customer",
        "providers": {
            "aws": {
                "total_cost": 15420.50,
                "services": [
                    {"service": "EC2", "cost": 8500.00},
                    {"service": "RDS", "cost": 4200.00},
                    {"service": "S3", "cost": 2720.50}
                ]
            },
            "gcp": {
                "total_cost": 12500.00,
                "services": [
                    {"service": "Compute Engine", "cost": 7500.00},
                    {"service": "Cloud SQL", "cost": 3125.00},
                    {"service": "Cloud Storage", "cost": 1875.00}
                ]
            },
            "azure": {
                "total_cost": 10800.00,
                "services": [
                    {"service": "Virtual Machines", "cost": 6264.00},
                    {"service": "SQL Database", "cost": 3024.00},
                    {"service": "Storage Accounts", "cost": 1512.00}
                ]
            }
        },
        "total_cost": 38720.50,
        "period": {
            "start": (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end": datetime.utcnow().strftime("%Y-%m-%d")
        }
    }


def generate_e2e_execution_result(
    recommendation_id: str,
    success: bool = True
) -> Dict:
    """
    Generate execution result for E2E tests.
    
    Args:
        recommendation_id: Recommendation ID
        success: Whether execution was successful
        
    Returns:
        Execution result dictionary
    """
    if success:
        return {
            "id": f"exec-e2e-{datetime.utcnow().timestamp()}",
            "recommendation_id": recommendation_id,
            "status": "completed",
            "success": True,
            "started_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": 300,
            "changes_applied": [
                {"resource": "i-e2e-001", "action": "migrated_to_spot", "status": "success"},
                {"resource": "i-e2e-002", "action": "migrated_to_spot", "status": "success"}
            ],
            "rollback_available": True
        }
    else:
        return {
            "id": f"exec-e2e-{datetime.utcnow().timestamp()}",
            "recommendation_id": recommendation_id,
            "status": "failed",
            "success": False,
            "started_at": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": 120,
            "error_message": "Insufficient spot capacity",
            "changes_applied": [],
            "rollback_available": False
        }


def generate_e2e_learning_data() -> Dict:
    """
    Generate learning loop data for E2E tests.
    
    Returns:
        Learning data dictionary
    """
    return {
        "customer_id": "e2e-test-customer",
        "total_recommendations": 50,
        "executed_recommendations": 40,
        "success_rate": 95.0,
        "average_savings_accuracy": 87.5,
        "total_predicted_savings": 25000.00,
        "total_actual_savings": 21875.00,
        "top_performing_types": [
            {"type": "spot_migration", "success_rate": 98.0, "avg_accuracy": 92.5},
            {"type": "rightsizing", "success_rate": 94.0, "avg_accuracy": 85.0},
            {"type": "reserved_instance", "success_rate": 96.0, "avg_accuracy": 88.0}
        ],
        "insights": [
            {
                "type": "pattern",
                "title": "Spot migrations highly successful",
                "confidence": 0.95,
                "impact": "high"
            }
        ]
    }

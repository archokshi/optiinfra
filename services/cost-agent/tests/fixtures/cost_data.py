"""
Cost Data Fixtures.

Provides sample cost data for testing.
"""

from datetime import datetime, timedelta
from typing import List, Dict
import random


def generate_daily_costs(days: int = 30, base_cost: float = 500.0, variation: float = 50.0) -> List[Dict]:
    """
    Generate daily cost data for testing.
    
    Args:
        days: Number of days to generate
        base_cost: Base daily cost
        variation: Random variation amount
        
    Returns:
        List of daily cost dictionaries
    """
    costs = []
    start_date = datetime.utcnow() - timedelta(days=days)
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        # Add some variation and trend
        daily_cost = base_cost + (i * 10) + random.uniform(-variation, variation)
        
        costs.append({
            "date": date.strftime("%Y-%m-%d"),
            "cost": round(daily_cost, 2),
            "services": {
                "EC2": round(daily_cost * 0.55, 2),
                "RDS": round(daily_cost * 0.27, 2),
                "S3": round(daily_cost * 0.18, 2)
            }
        })
    
    return costs


def generate_anomaly_data(
    days: int = 30,
    normal_cost: float = 500.0,
    spike_multiplier: float = 2.0,
    anomaly_days: List[int] = None
) -> List[Dict]:
    """
    Generate cost data with anomalies.
    
    Args:
        days: Number of days to generate
        normal_cost: Normal daily cost
        spike_multiplier: Multiplier for anomaly spikes
        anomaly_days: Days to inject anomalies (default: [10, 20, 25])
        
    Returns:
        List of daily cost dictionaries with anomalies
    """
    costs = generate_daily_costs(days, normal_cost, variation=30.0)
    
    # Default anomaly days
    if anomaly_days is None:
        anomaly_days = [10, 20, 25]
    
    # Add anomalies on specific days
    for day in anomaly_days:
        if day < len(costs):
            costs[day]["cost"] *= spike_multiplier
            costs[day]["anomaly"] = True
            costs[day]["services"]["EC2"] *= spike_multiplier
    
    return costs


def generate_aws_cost_response(
    start_date: str = "2025-10-01",
    end_date: str = "2025-10-23",
    total_cost: float = 15420.50
) -> Dict:
    """
    Generate mock AWS Cost Explorer response.
    
    Args:
        start_date: Start date string
        end_date: End date string
        total_cost: Total cost amount
        
    Returns:
        Mock AWS response dictionary
    """
    return {
        "ResultsByTime": [{
            "TimePeriod": {
                "Start": start_date,
                "End": end_date
            },
            "Total": {
                "UnblendedCost": {
                    "Amount": str(total_cost),
                    "Unit": "USD"
                }
            },
            "Groups": [
                {
                    "Keys": ["EC2"],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": str(total_cost * 0.55),
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": ["RDS"],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": str(total_cost * 0.27),
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": ["S3"],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": str(total_cost * 0.18),
                            "Unit": "USD"
                        }
                    }
                }
            ]
        }]
    }


def generate_gcp_cost_data(
    project_id: str = "test-project",
    total_cost: float = 12500.00
) -> List[Dict]:
    """
    Generate mock GCP cost data.
    
    Args:
        project_id: GCP project ID
        total_cost: Total cost amount
        
    Returns:
        List of GCP cost records
    """
    return [
        {
            "project_id": project_id,
            "service": "Compute Engine",
            "cost": round(total_cost * 0.60, 2),
            "currency": "USD"
        },
        {
            "project_id": project_id,
            "service": "Cloud SQL",
            "cost": round(total_cost * 0.25, 2),
            "currency": "USD"
        },
        {
            "project_id": project_id,
            "service": "Cloud Storage",
            "cost": round(total_cost * 0.15, 2),
            "currency": "USD"
        }
    ]


def generate_azure_cost_data(
    subscription_id: str = "test-subscription",
    total_cost: float = 10800.00
) -> Dict:
    """
    Generate mock Azure cost data.
    
    Args:
        subscription_id: Azure subscription ID
        total_cost: Total cost amount
        
    Returns:
        Mock Azure cost response
    """
    return {
        "properties": {
            "rows": [
                ["Virtual Machines", total_cost * 0.58],
                ["SQL Database", total_cost * 0.28],
                ["Storage Accounts", total_cost * 0.14]
            ],
            "columns": [
                {"name": "ServiceName", "type": "String"},
                {"name": "Cost", "type": "Number"}
            ]
        }
    }

"""
AWS EC2 simulator for testing spot migration without real AWS account.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.workflows.state import EC2Instance, SpotOpportunity


class AWSSimulator:
    """Simulates AWS EC2 API for testing"""

    def __init__(self):
        """Initialize simulator with sample data"""
        self.regions = ["us-east-1", "us-west-2", "eu-west-1"]
        self.instance_types = [
            "t3.large",
            "m5.xlarge",
            "c5.2xlarge",
            "r5.large",
            "m5.2xlarge",
        ]
        self.spot_savings = {
            "t3.large": 0.65,  # 65% cheaper
            "m5.xlarge": 0.60,  # 60% cheaper
            "c5.2xlarge": 0.70,  # 70% cheaper
            "r5.large": 0.55,  # 55% cheaper
            "m5.2xlarge": 0.62,  # 62% cheaper
        }

    def generate_ec2_instances(self, count: int = 10) -> List[EC2Instance]:
        """
        Generate sample EC2 instances.

        Args:
            count: Number of instances to generate

        Returns:
            List of EC2Instance dicts
        """
        instances = []

        for i in range(count):
            instance_type = random.choice(self.instance_types)
            region = random.choice(self.regions)

            # Calculate cost based on instance type
            base_costs = {
                "t3.large": 75,
                "m5.xlarge": 140,
                "c5.2xlarge": 310,
                "r5.large": 125,
                "m5.2xlarge": 385,
            }

            # Workload type affects spot eligibility
            workload_type = random.choice(["stable", "stable", "variable", "burst"])
            spot_eligible = workload_type == "stable"

            instance: EC2Instance = {
                "instance_id": f"i-{i:016x}",
                "instance_type": instance_type,
                "region": region,
                "availability_zone": f"{region}{random.choice(['a', 'b', 'c'])}",
                "state": "running",
                "launch_time": datetime.utcnow()
                - timedelta(days=random.randint(30, 365)),
                "cost_per_month": base_costs[instance_type],
                "spot_eligible": spot_eligible,
                "workload_type": workload_type,
                "utilization_metrics": {
                    "cpu": random.uniform(0.2, 0.9),
                    "memory": random.uniform(0.3, 0.85),
                    "network": random.uniform(0.1, 0.7),
                },
            }

            instances.append(instance)

        return instances

    def analyze_spot_opportunities(
        self, instances: List[EC2Instance]
    ) -> List[SpotOpportunity]:
        """
        Analyze instances for spot migration opportunities.

        Args:
            instances: List of EC2 instances

        Returns:
            List of spot opportunities
        """
        opportunities = []

        for instance in instances:
            if not instance["spot_eligible"]:
                continue

            instance_type = instance["instance_type"]
            current_cost = instance["cost_per_month"]

            # Calculate spot cost
            spot_discount = self.spot_savings.get(instance_type, 0.60)
            spot_cost = current_cost * (1 - spot_discount)
            savings_amount = current_cost - spot_cost
            savings_percentage = spot_discount * 100

            # Risk assessment based on workload
            if instance["workload_type"] == "stable":
                risk_level = "low"
                interruption_rate = 0.05  # 5% interruption rate
            elif instance["workload_type"] == "variable":
                risk_level = "medium"
                interruption_rate = 0.15
            else:
                risk_level = "high"
                interruption_rate = 0.30

            opportunity: SpotOpportunity = {
                "instance_id": instance["instance_id"],
                "current_cost": current_cost,
                "spot_cost": spot_cost,
                "savings_amount": savings_amount,
                "savings_percentage": savings_percentage,
                "risk_level": risk_level,
                "interruption_rate": interruption_rate,
                "recommended_capacity": 2 if risk_level == "low" else 3,
                "migration_strategy": "blue_green",
            }

            opportunities.append(opportunity)

        return opportunities

    def execute_spot_migration(
        self,
        instance_id: str,
        phase_percentage: int,
    ) -> Dict[str, Any]:
        """
        Simulate spot instance migration.

        Args:
            instance_id: Instance to migrate
            phase_percentage: 10, 50, or 100

        Returns:
            Migration result
        """
        # Simulate execution
        success_rate = random.uniform(0.95, 1.0)  # 95-100% success

        return {
            "instance_id": instance_id,
            "phase": f"{phase_percentage}%",
            "success": success_rate > 0.97,
            "success_rate": success_rate,
            "instances_migrated": phase_percentage // 10,
            "execution_time": random.uniform(30, 120),  # seconds
        }

    def get_quality_metrics(self, baseline: bool = False) -> Dict[str, float]:
        """
        Get quality metrics (latency, error rate).

        Args:
            baseline: If True, return baseline metrics

        Returns:
            Quality metrics dict
        """
        if baseline:
            return {
                "latency": random.uniform(50, 100),  # ms
                "error_rate": random.uniform(0.001, 0.005),  # 0.1-0.5%
            }
        else:
            # After migration - slightly worse but acceptable
            return {
                "latency": random.uniform(55, 110),  # ms
                "error_rate": random.uniform(0.001, 0.006),  # 0.1-0.6%
            }


# Global instance for use across modules
aws_simulator = AWSSimulator()

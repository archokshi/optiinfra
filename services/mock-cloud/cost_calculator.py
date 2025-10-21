"""
Mock Cloud Provider - Cost Calculator

Calculates costs and savings across different pricing models.
"""

from typing import Dict, List
from models import Instance, PricingModel, InstanceType


class CostCalculator:
    """Calculate costs and savings"""
    
    @staticmethod
    def calculate_monthly_cost(instance: Instance) -> float:
        """Calculate monthly cost for an instance"""
        if instance.state.value in ["stopped", "terminated"]:
            return 0.0
        
        # Assume 730 hours per month (24 * 30.4)
        return instance.hourly_rate * 730
    
    @staticmethod
    def calculate_annual_cost(instance: Instance) -> float:
        """Calculate annual cost for an instance"""
        if instance.state.value in ["stopped", "terminated"]:
            return 0.0
        
        # 8760 hours per year (24 * 365)
        return instance.hourly_rate * 8760
    
    @staticmethod
    def compare_pricing_models(instance_type: InstanceType) -> Dict:
        """Compare costs across pricing models for an instance type"""
        on_demand_monthly = instance_type.on_demand_hourly * 730
        spot_monthly = instance_type.spot_hourly * 730
        reserved_monthly = instance_type.reserved_hourly * 730
        
        spot_savings = on_demand_monthly - spot_monthly
        reserved_savings = on_demand_monthly - reserved_monthly
        
        return {
            "instance_type": instance_type.name,
            "provider": instance_type.provider.value,
            "costs": {
                "on_demand": {
                    "hourly": round(instance_type.on_demand_hourly, 4),
                    "monthly": round(on_demand_monthly, 2),
                    "annual": round(on_demand_monthly * 12, 2),
                },
                "spot": {
                    "hourly": round(instance_type.spot_hourly, 4),
                    "monthly": round(spot_monthly, 2),
                    "annual": round(spot_monthly * 12, 2),
                    "savings_vs_on_demand": {
                        "monthly": round(spot_savings, 2),
                        "annual": round(spot_savings * 12, 2),
                        "percentage": round(instance_type.spot_discount, 2),
                    }
                },
                "reserved": {
                    "hourly": round(instance_type.reserved_hourly, 4),
                    "monthly": round(reserved_monthly, 2),
                    "annual": round(reserved_monthly * 12, 2),
                    "savings_vs_on_demand": {
                        "monthly": round(reserved_savings, 2),
                        "annual": round(reserved_savings * 12, 2),
                        "percentage": round(instance_type.reserved_discount, 2),
                    }
                }
            }
        }
    
    @staticmethod
    def calculate_migration_savings(
        instances: List[Instance],
        target_pricing: PricingModel
    ) -> Dict:
        """Calculate savings from migrating instances to target pricing"""
        total_current_hourly = 0.0
        total_target_hourly = 0.0
        migrations = []
        
        for instance in instances:
            if instance.pricing_model == target_pricing:
                continue
            
            current_rate = instance.hourly_rate
            
            # Calculate target rate
            if target_pricing == PricingModel.SPOT:
                target_rate = instance.instance_type.spot_hourly
            elif target_pricing == PricingModel.RESERVED:
                target_rate = instance.instance_type.reserved_hourly
            else:
                target_rate = instance.instance_type.on_demand_hourly
            
            savings_hourly = current_rate - target_rate
            
            if savings_hourly > 0:
                total_current_hourly += current_rate
                total_target_hourly += target_rate
                
                migrations.append({
                    "instance_id": instance.id,
                    "instance_type": instance.instance_type.name,
                    "current_pricing": instance.pricing_model.value,
                    "target_pricing": target_pricing.value,
                    "current_hourly": round(current_rate, 4),
                    "target_hourly": round(target_rate, 4),
                    "savings_hourly": round(savings_hourly, 4),
                    "savings_monthly": round(savings_hourly * 730, 2),
                })
        
        total_savings_hourly = total_current_hourly - total_target_hourly
        
        return {
            "target_pricing": target_pricing.value,
            "total_instances": len(migrations),
            "total_savings": {
                "hourly": round(total_savings_hourly, 4),
                "monthly": round(total_savings_hourly * 730, 2),
                "annual": round(total_savings_hourly * 8760, 2),
            },
            "migrations": migrations,
        }

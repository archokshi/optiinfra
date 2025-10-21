"""
Mock Cloud Provider - Metrics Generator

Generates realistic resource utilization metrics.
"""

import random
from typing import Dict, List
from models import Instance


class MetricsGenerator:
    """Generate realistic metrics for instances"""
    
    @staticmethod
    def generate_metrics(instance: Instance) -> Dict:
        """Generate current metrics for an instance"""
        if instance.state.value != "running":
            return {
                "cpu_utilization": 0.0,
                "memory_utilization": 0.0,
                "gpu_utilization": 0.0,
                "network_in_mbps": 0.0,
                "network_out_mbps": 0.0,
                "disk_read_iops": 0,
                "disk_write_iops": 0,
            }
        
        return {
            "cpu_utilization": round(instance.cpu_utilization, 2),
            "memory_utilization": round(instance.memory_utilization, 2),
            "gpu_utilization": round(instance.gpu_utilization, 2),
            "network_in_mbps": round(instance.network_in_mbps, 2),
            "network_out_mbps": round(instance.network_out_mbps, 2),
            "disk_read_iops": random.randint(50, 500),
            "disk_write_iops": random.randint(20, 300),
        }
    
    @staticmethod
    def generate_time_series(instance: Instance, hours: int = 24) -> Dict:
        """Generate time series metrics for the past N hours"""
        if instance.state.value != "running":
            return {"error": "Instance is not running"}
        
        # Generate hourly data points
        timestamps = []
        cpu_data = []
        memory_data = []
        gpu_data = []
        
        base_cpu = instance.cpu_utilization
        base_memory = instance.memory_utilization
        base_gpu = instance.gpu_utilization
        
        for i in range(hours):
            timestamps.append(f"{hours - i} hours ago")
            
            # Add realistic fluctuations
            cpu = max(5.0, min(95.0, base_cpu + random.uniform(-15.0, 15.0)))
            memory = max(10.0, min(90.0, base_memory + random.uniform(-10.0, 10.0)))
            gpu = max(0.0, min(100.0, base_gpu + random.uniform(-20.0, 20.0))) if instance.instance_type.gpu_count > 0 else 0.0
            
            cpu_data.append(round(cpu, 2))
            memory_data.append(round(memory, 2))
            gpu_data.append(round(gpu, 2))
        
        return {
            "instance_id": instance.id,
            "hours": hours,
            "timestamps": timestamps,
            "metrics": {
                "cpu_utilization": cpu_data,
                "memory_utilization": memory_data,
                "gpu_utilization": gpu_data,
            },
            "statistics": {
                "cpu": {
                    "avg": round(sum(cpu_data) / len(cpu_data), 2),
                    "min": round(min(cpu_data), 2),
                    "max": round(max(cpu_data), 2),
                },
                "memory": {
                    "avg": round(sum(memory_data) / len(memory_data), 2),
                    "min": round(min(memory_data), 2),
                    "max": round(max(memory_data), 2),
                },
                "gpu": {
                    "avg": round(sum(gpu_data) / len(gpu_data), 2) if gpu_data else 0.0,
                    "min": round(min(gpu_data), 2) if gpu_data else 0.0,
                    "max": round(max(gpu_data), 2) if gpu_data else 0.0,
                }
            }
        }
    
    @staticmethod
    def get_recommendations(instance: Instance) -> List[Dict]:
        """Get optimization recommendations based on metrics"""
        recommendations = []
        
        if instance.state.value != "running":
            return recommendations
        
        # Check for idle instance
        if instance.is_idle:
            recommendations.append({
                "type": "terminate_idle",
                "severity": "high",
                "title": "Terminate Idle Instance",
                "description": f"Instance {instance.id} is idle (CPU < 10%, Memory < 20%)",
                "potential_savings_monthly": round(instance.hourly_rate * 730, 2),
            })
        
        # Check for underutilization
        elif instance.is_underutilized:
            # Estimate smaller instance type (half the size)
            estimated_new_rate = instance.hourly_rate * 0.5
            savings = instance.hourly_rate - estimated_new_rate
            
            recommendations.append({
                "type": "right_size",
                "severity": "medium",
                "title": "Right-Size Instance",
                "description": f"Instance {instance.id} is underutilized (CPU < 30%, Memory < 40%)",
                "current_type": instance.instance_type.name,
                "suggested_action": "Downsize to smaller instance type",
                "potential_savings_monthly": round(savings * 730, 2),
            })
        
        # Check for spot migration opportunity
        if instance.pricing_model.value == "on-demand":
            spot_savings = instance.hourly_rate - instance.instance_type.spot_hourly
            
            if spot_savings > 0:
                recommendations.append({
                    "type": "migrate_to_spot",
                    "severity": "medium",
                    "title": "Migrate to Spot Instance",
                    "description": f"Save {round(instance.instance_type.spot_discount, 1)}% by using spot pricing",
                    "current_pricing": "on-demand",
                    "target_pricing": "spot",
                    "potential_savings_monthly": round(spot_savings * 730, 2),
                })
        
        # Check for reserved instance opportunity (if long-running)
        if instance.uptime_hours > 720 and instance.pricing_model.value == "on-demand":  # 30 days
            reserved_savings = instance.hourly_rate - instance.instance_type.reserved_hourly
            
            if reserved_savings > 0:
                recommendations.append({
                    "type": "convert_to_reserved",
                    "severity": "low",
                    "title": "Convert to Reserved Instance",
                    "description": f"Long-running instance, save {round(instance.instance_type.reserved_discount, 1)}% with reserved pricing",
                    "current_pricing": "on-demand",
                    "target_pricing": "reserved",
                    "potential_savings_monthly": round(reserved_savings * 730, 2),
                })
        
        return recommendations

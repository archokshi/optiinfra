"""
Vultr instance collector.
Collects compute, GPU, and bare metal instance data.
"""

from typing import Dict, Any, List
import logging

from .client import VultrClient

logger = logging.getLogger(__name__)


class VultrInstanceCollector:
    """
    Collects instance data from Vultr API.
    """
    
    def __init__(self, client: VultrClient):
        """
        Initialize instance collector.
        
        Args:
            client: Configured VultrClient instance
        """
        self.client = client
    
    def collect_compute_instances(self) -> List[Dict[str, Any]]:
        """
        Collect all Cloud Compute instances.
        
        Returns:
            List of instance details
        """
        try:
            instances = self.client.list_instances()
            
            collected_instances = []
            for instance in instances:
                # Determine if GPU instance
                plan = instance.get("plan", "")
                is_gpu = "gpu" in plan.lower() or "vhf" in plan.lower()
                
                collected_instances.append({
                    "instance_id": instance.get("id"),
                    "label": instance.get("label"),
                    "hostname": instance.get("hostname"),
                    "plan": plan,
                    "region": instance.get("region"),
                    "os": instance.get("os"),
                    "status": instance.get("status"),
                    "power_status": instance.get("power_status"),
                    "vcpu_count": instance.get("vcpu_count"),
                    "ram": instance.get("ram"),  # in MB
                    "disk": instance.get("disk"),  # in GB
                    "is_gpu": is_gpu,
                    "monthly_cost": float(instance.get("monthly_cost", 0)),
                    "tags": instance.get("tags", []),
                    "created_at": instance.get("date_created"),
                })
            
            logger.info(f"Collected {len(collected_instances)} compute instances")
            return collected_instances
            
        except Exception as e:
            logger.error(f"Failed to collect compute instances: {e}")
            raise
    
    def collect_bare_metal_servers(self) -> List[Dict[str, Any]]:
        """
        Collect all Bare Metal servers.
        
        Returns:
            List of bare metal server details
        """
        try:
            servers = self.client.list_bare_metals()
            
            collected_servers = []
            for server in servers:
                collected_servers.append({
                    "server_id": server.get("id"),
                    "label": server.get("label"),
                    "plan": server.get("plan"),
                    "region": server.get("region"),
                    "os": server.get("os"),
                    "status": server.get("status"),
                    "cpu_count": server.get("cpu_count"),
                    "ram": server.get("ram"),
                    "disk": server.get("disk"),
                    "monthly_cost": float(server.get("monthly_cost", 0)),
                    "tags": server.get("tags", []),
                    "created_at": server.get("date_created"),
                })
            
            logger.info(f"Collected {len(collected_servers)} bare metal servers")
            return collected_servers
            
        except Exception as e:
            logger.error(f"Failed to collect bare metal servers: {e}")
            raise
    
    def analyze_instance_utilization(
        self,
        instances: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze instance utilization patterns.
        
        Args:
            instances: List of instances
        
        Returns:
            Utilization analysis
        """
        total_instances = len(instances)
        
        # Count by status
        running = sum(1 for i in instances if i["status"] == "active")
        stopped = sum(1 for i in instances if i["status"] != "active")
        
        # GPU instances
        gpu_instances = [i for i in instances if i.get("is_gpu")]
        gpu_count = len(gpu_instances)
        
        # Calculate costs
        total_monthly_cost = sum(i["monthly_cost"] for i in instances)
        gpu_monthly_cost = sum(i["monthly_cost"] for i in gpu_instances)
        
        # Identify idle (stopped but still charged)
        idle_instances = [
            i for i in instances
            if i["power_status"] == "stopped" and i["monthly_cost"] > 0
        ]
        idle_cost = sum(i["monthly_cost"] for i in idle_instances)
        
        return {
            "total_instances": total_instances,
            "running_instances": running,
            "stopped_instances": stopped,
            "gpu_instances": gpu_count,
            "gpu_percentage": (gpu_count / total_instances * 100) if total_instances else 0,
            "total_monthly_cost": total_monthly_cost,
            "gpu_monthly_cost": gpu_monthly_cost,
            "idle_instances": len(idle_instances),
            "idle_cost": idle_cost,
            "idle_waste_percentage": (
                (idle_cost / total_monthly_cost * 100) if total_monthly_cost else 0
            )
        }

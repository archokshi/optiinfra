"""
Mock Cloud Provider - Instance Models

Simulates AWS, GCP, and Azure instance types with realistic pricing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
import random


class CloudProvider(str, Enum):
    """Cloud provider types"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class InstanceState(str, Enum):
    """Instance lifecycle states"""
    PENDING = "pending"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    MIGRATING = "migrating"


class PricingModel(str, Enum):
    """Instance pricing models"""
    ON_DEMAND = "on-demand"
    SPOT = "spot"
    RESERVED = "reserved"


@dataclass
class InstanceType:
    """Instance type specification"""
    name: str
    provider: CloudProvider
    vcpus: int
    memory_gb: float
    gpu_count: int = 0
    gpu_type: Optional[str] = None
    on_demand_hourly: float = 0.0
    spot_hourly: float = 0.0
    reserved_hourly: float = 0.0
    
    @property
    def spot_discount(self) -> float:
        """Calculate spot discount percentage"""
        if self.on_demand_hourly > 0:
            return ((self.on_demand_hourly - self.spot_hourly) / self.on_demand_hourly) * 100
        return 0.0
    
    @property
    def reserved_discount(self) -> float:
        """Calculate reserved discount percentage"""
        if self.on_demand_hourly > 0:
            return ((self.on_demand_hourly - self.reserved_hourly) / self.on_demand_hourly) * 100
        return 0.0


@dataclass
class Instance:
    """Simulated cloud instance"""
    id: str
    instance_type: InstanceType
    pricing_model: PricingModel
    state: InstanceState = InstanceState.PENDING
    region: str = "us-east-1"
    availability_zone: str = "us-east-1a"
    tags: Dict[str, str] = field(default_factory=dict)
    launched_at: datetime = field(default_factory=datetime.now)
    state_transition_time: datetime = field(default_factory=datetime.now)
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    gpu_utilization: float = 0.0
    network_in_mbps: float = 0.0
    network_out_mbps: float = 0.0
    
    @property
    def hourly_rate(self) -> float:
        """Get current hourly rate based on pricing model"""
        if self.pricing_model == PricingModel.ON_DEMAND:
            return self.instance_type.on_demand_hourly
        elif self.pricing_model == PricingModel.SPOT:
            return self.instance_type.spot_hourly
        elif self.pricing_model == PricingModel.RESERVED:
            return self.instance_type.reserved_hourly
        return 0.0
    
    @property
    def uptime_hours(self) -> float:
        """Calculate uptime in hours"""
        if self.state == InstanceState.RUNNING:
            delta = datetime.now() - self.launched_at
            return delta.total_seconds() / 3600
        return 0.0
    
    @property
    def cost_so_far(self) -> float:
        """Calculate total cost accumulated"""
        return self.uptime_hours * self.hourly_rate
    
    @property
    def is_idle(self) -> bool:
        """Check if instance is idle (low utilization)"""
        return (
            self.cpu_utilization < 10.0 and
            self.memory_utilization < 20.0 and
            self.gpu_utilization < 5.0
        )
    
    @property
    def is_underutilized(self) -> bool:
        """Check if instance is underutilized"""
        return (
            self.cpu_utilization < 30.0 and
            self.memory_utilization < 40.0 and
            self.gpu_utilization < 20.0
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "instance_type": self.instance_type.name,
            "provider": self.instance_type.provider.value,
            "pricing_model": self.pricing_model.value,
            "state": self.state.value,
            "region": self.region,
            "availability_zone": self.availability_zone,
            "vcpus": self.instance_type.vcpus,
            "memory_gb": self.instance_type.memory_gb,
            "gpu_count": self.instance_type.gpu_count,
            "hourly_rate": self.hourly_rate,
            "uptime_hours": round(self.uptime_hours, 2),
            "cost_so_far": round(self.cost_so_far, 2),
            "launched_at": self.launched_at.isoformat(),
            "metrics": {
                "cpu_utilization": round(self.cpu_utilization, 2),
                "memory_utilization": round(self.memory_utilization, 2),
                "gpu_utilization": round(self.gpu_utilization, 2),
                "network_in_mbps": round(self.network_in_mbps, 2),
                "network_out_mbps": round(self.network_out_mbps, 2),
            },
            "tags": self.tags,
            "is_idle": self.is_idle,
            "is_underutilized": self.is_underutilized,
        }


# Instance type catalog with realistic pricing
INSTANCE_TYPES = {
    # AWS EC2 - General Purpose
    "t3.small": InstanceType("t3.small", CloudProvider.AWS, 2, 2, 0, None, 0.0208, 0.0062, 0.0146),
    "t3.medium": InstanceType("t3.medium", CloudProvider.AWS, 2, 4, 0, None, 0.0416, 0.0125, 0.0292),
    "t3.large": InstanceType("t3.large", CloudProvider.AWS, 2, 8, 0, None, 0.0832, 0.0250, 0.0583),
    "m5.large": InstanceType("m5.large", CloudProvider.AWS, 2, 8, 0, None, 0.096, 0.0288, 0.0672),
    "m5.xlarge": InstanceType("m5.xlarge", CloudProvider.AWS, 4, 16, 0, None, 0.192, 0.0576, 0.1344),
    "m5.2xlarge": InstanceType("m5.2xlarge", CloudProvider.AWS, 8, 32, 0, None, 0.384, 0.1152, 0.2688),
    
    # AWS EC2 - Compute Optimized
    "c5.large": InstanceType("c5.large", CloudProvider.AWS, 2, 4, 0, None, 0.085, 0.0255, 0.0595),
    "c5.xlarge": InstanceType("c5.xlarge", CloudProvider.AWS, 4, 8, 0, None, 0.17, 0.051, 0.119),
    "c5.2xlarge": InstanceType("c5.2xlarge", CloudProvider.AWS, 8, 16, 0, None, 0.34, 0.102, 0.238),
    
    # AWS EC2 - GPU Instances
    "p3.2xlarge": InstanceType("p3.2xlarge", CloudProvider.AWS, 8, 61, 1, "V100", 3.06, 0.918, 2.142),
    "p3.8xlarge": InstanceType("p3.8xlarge", CloudProvider.AWS, 32, 244, 4, "V100", 12.24, 3.672, 8.568),
    "g4dn.xlarge": InstanceType("g4dn.xlarge", CloudProvider.AWS, 4, 16, 1, "T4", 0.526, 0.1578, 0.3682),
    "g4dn.2xlarge": InstanceType("g4dn.2xlarge", CloudProvider.AWS, 8, 32, 1, "T4", 0.752, 0.2256, 0.5264),
    
    # GCP Compute Engine - General Purpose
    "n1-standard-1": InstanceType("n1-standard-1", CloudProvider.GCP, 1, 3.75, 0, None, 0.0475, 0.0142, 0.0332),
    "n1-standard-2": InstanceType("n1-standard-2", CloudProvider.GCP, 2, 7.5, 0, None, 0.095, 0.0285, 0.0665),
    "n1-standard-4": InstanceType("n1-standard-4", CloudProvider.GCP, 4, 15, 0, None, 0.19, 0.057, 0.133),
    "n1-standard-8": InstanceType("n1-standard-8", CloudProvider.GCP, 8, 30, 0, None, 0.38, 0.114, 0.266),
    
    # GCP Compute Engine - Compute Optimized
    "c2-standard-4": InstanceType("c2-standard-4", CloudProvider.GCP, 4, 16, 0, None, 0.2088, 0.0626, 0.1462),
    "c2-standard-8": InstanceType("c2-standard-8", CloudProvider.GCP, 8, 32, 0, None, 0.4176, 0.1253, 0.2923),
    
    # GCP Compute Engine - GPU Instances
    "n1-standard-4-v100": InstanceType("n1-standard-4-v100", CloudProvider.GCP, 4, 15, 1, "V100", 2.48, 0.744, 1.736),
    "n1-standard-8-v100": InstanceType("n1-standard-8-v100", CloudProvider.GCP, 8, 30, 2, "V100", 4.58, 1.374, 3.206),
    
    # Azure Virtual Machines - General Purpose
    "Standard_B2s": InstanceType("Standard_B2s", CloudProvider.AZURE, 2, 4, 0, None, 0.0416, 0.0125, 0.0291),
    "Standard_D2s_v3": InstanceType("Standard_D2s_v3", CloudProvider.AZURE, 2, 8, 0, None, 0.096, 0.0288, 0.0672),
    "Standard_D4s_v3": InstanceType("Standard_D4s_v3", CloudProvider.AZURE, 4, 16, 0, None, 0.192, 0.0576, 0.1344),
    "Standard_D8s_v3": InstanceType("Standard_D8s_v3", CloudProvider.AZURE, 8, 32, 0, None, 0.384, 0.1152, 0.2688),
    
    # Azure Virtual Machines - GPU Instances
    "Standard_NC6": InstanceType("Standard_NC6", CloudProvider.AZURE, 6, 56, 1, "K80", 0.90, 0.27, 0.63),
    "Standard_NC12": InstanceType("Standard_NC12", CloudProvider.AZURE, 12, 112, 2, "K80", 1.80, 0.54, 1.26),
}


def get_instance_type(name: str) -> Optional[InstanceType]:
    """Get instance type by name"""
    return INSTANCE_TYPES.get(name)


def list_instance_types(provider: Optional[CloudProvider] = None, has_gpu: Optional[bool] = None) -> list:
    """List instance types with optional filtering"""
    types = list(INSTANCE_TYPES.values())
    
    if provider:
        types = [t for t in types if t.provider == provider]
    
    if has_gpu is not None:
        if has_gpu:
            types = [t for t in types if t.gpu_count > 0]
        else:
            types = [t for t in types if t.gpu_count == 0]
    
    return types

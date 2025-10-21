"""
Mock Cloud Provider - Instance Manager

Manages simulated cloud instances with realistic behavior.
"""

import random
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from models import (
    Instance,
    InstanceState,
    InstanceType,
    PricingModel,
    CloudProvider,
    get_instance_type,
)


class InstanceManager:
    """Manages mock cloud instances"""
    
    def __init__(self):
        self.instances: Dict[str, Instance] = {}
        self._initialize_sample_instances()
    
    def _initialize_sample_instances(self):
        """Create some sample instances for testing"""
        # Create 5 AWS instances
        for i in range(5):
            instance_type = random.choice([
                "t3.large", "m5.xlarge", "c5.xlarge"
            ])
            pricing = random.choice([PricingModel.ON_DEMAND, PricingModel.SPOT])
            
            instance = self.create_instance(
                instance_type=instance_type,
                pricing_model=pricing,
                provider=CloudProvider.AWS,
                tags={"Environment": random.choice(["dev", "staging", "prod"])},
            )
        
        # Create 3 GCP instances
        for i in range(3):
            instance_type = random.choice([
                "n1-standard-4", "n1-standard-8"
            ])
            
            instance = self.create_instance(
                instance_type=instance_type,
                pricing_model=PricingModel.ON_DEMAND,
                provider=CloudProvider.GCP,
                tags={"Team": random.choice(["ml", "backend", "data"])},
            )
        
        # Create 2 Azure instances
        for i in range(2):
            instance_type = random.choice([
                "Standard_D4s_v3", "Standard_D8s_v3"
            ])
            
            instance = self.create_instance(
                instance_type=instance_type,
                pricing_model=PricingModel.ON_DEMAND,
                provider=CloudProvider.AZURE,
                tags={"Application": "web-server"},
            )
        
        # Start all instances
        for instance_id in list(self.instances.keys()):
            self.start_instance(instance_id)
    
    def create_instance(
        self,
        instance_type: str,
        pricing_model: PricingModel = PricingModel.ON_DEMAND,
        provider: CloudProvider = CloudProvider.AWS,
        region: str = "us-east-1",
        tags: Optional[Dict[str, str]] = None,
    ) -> Instance:
        """Create a new instance"""
        # Get instance type
        inst_type = get_instance_type(instance_type)
        if not inst_type:
            raise ValueError(f"Unknown instance type: {instance_type}")
        
        # Generate instance ID
        instance_id = self._generate_instance_id(provider)
        
        # Create instance
        instance = Instance(
            id=instance_id,
            instance_type=inst_type,
            pricing_model=pricing_model,
            state=InstanceState.PENDING,
            region=region,
            tags=tags or {},
        )
        
        # Store instance
        self.instances[instance_id] = instance
        
        return instance
    
    def start_instance(self, instance_id: str) -> Instance:
        """Start an instance"""
        instance = self.get_instance(instance_id)
        
        if instance.state == InstanceState.RUNNING:
            return instance
        
        # Simulate startup delay
        instance.state = InstanceState.PENDING
        time.sleep(0.1)  # Simulate 100ms delay
        
        # Transition to running
        instance.state = InstanceState.RUNNING
        instance.launched_at = datetime.now()
        instance.state_transition_time = datetime.now()
        
        # Initialize metrics with random realistic values
        instance.cpu_utilization = random.uniform(10.0, 80.0)
        instance.memory_utilization = random.uniform(20.0, 85.0)
        instance.gpu_utilization = random.uniform(0.0, 60.0) if instance.instance_type.gpu_count > 0 else 0.0
        instance.network_in_mbps = random.uniform(5.0, 100.0)
        instance.network_out_mbps = random.uniform(5.0, 100.0)
        
        return instance
    
    def stop_instance(self, instance_id: str) -> Instance:
        """Stop an instance"""
        instance = self.get_instance(instance_id)
        
        if instance.state != InstanceState.RUNNING:
            return instance
        
        # Simulate stopping
        instance.state = InstanceState.STOPPING
        time.sleep(0.05)  # Simulate 50ms delay
        
        instance.state = InstanceState.STOPPED
        instance.state_transition_time = datetime.now()
        
        # Zero out metrics
        instance.cpu_utilization = 0.0
        instance.memory_utilization = 0.0
        instance.gpu_utilization = 0.0
        instance.network_in_mbps = 0.0
        instance.network_out_mbps = 0.0
        
        return instance
    
    def terminate_instance(self, instance_id: str) -> Instance:
        """Terminate an instance"""
        instance = self.get_instance(instance_id)
        
        # Simulate termination
        instance.state = InstanceState.TERMINATING
        time.sleep(0.05)  # Simulate 50ms delay
        
        instance.state = InstanceState.TERMINATED
        instance.state_transition_time = datetime.now()
        
        return instance
    
    def migrate_to_spot(self, instance_id: str) -> Dict:
        """Migrate an instance to spot pricing"""
        instance = self.get_instance(instance_id)
        
        if instance.pricing_model == PricingModel.SPOT:
            return {
                "status": "already_spot",
                "message": f"Instance {instance_id} is already on spot pricing",
            }
        
        # Calculate savings
        old_rate = instance.hourly_rate
        old_pricing = instance.pricing_model
        
        # Simulate migration process
        instance.state = InstanceState.MIGRATING
        time.sleep(0.2)  # Simulate 200ms delay
        
        # Update to spot pricing
        instance.pricing_model = PricingModel.SPOT
        instance.state = InstanceState.RUNNING
        instance.state_transition_time = datetime.now()
        
        new_rate = instance.hourly_rate
        savings_hourly = old_rate - new_rate
        savings_monthly = savings_hourly * 730  # ~30 days
        savings_percentage = (savings_hourly / old_rate) * 100 if old_rate > 0 else 0
        
        return {
            "status": "completed",
            "instance_id": instance_id,
            "old_pricing": old_pricing.value,
            "new_pricing": instance.pricing_model.value,
            "old_hourly_rate": round(old_rate, 4),
            "new_hourly_rate": round(new_rate, 4),
            "savings_hourly": round(savings_hourly, 4),
            "savings_monthly": round(savings_monthly, 2),
            "savings_percentage": round(savings_percentage, 2),
        }
    
    def migrate_to_reserved(self, instance_id: str) -> Dict:
        """Migrate an instance to reserved pricing"""
        instance = self.get_instance(instance_id)
        
        if instance.pricing_model == PricingModel.RESERVED:
            return {
                "status": "already_reserved",
                "message": f"Instance {instance_id} is already on reserved pricing",
            }
        
        # Calculate savings
        old_rate = instance.hourly_rate
        old_pricing = instance.pricing_model
        
        # Simulate migration
        instance.state = InstanceState.MIGRATING
        time.sleep(0.1)  # Simulate 100ms delay
        
        # Update to reserved pricing
        instance.pricing_model = PricingModel.RESERVED
        instance.state = InstanceState.RUNNING
        instance.state_transition_time = datetime.now()
        
        new_rate = instance.hourly_rate
        savings_hourly = old_rate - new_rate
        savings_monthly = savings_hourly * 730
        savings_percentage = (savings_hourly / old_rate) * 100 if old_rate > 0 else 0
        
        return {
            "status": "completed",
            "instance_id": instance_id,
            "old_pricing": old_pricing.value,
            "new_pricing": instance.pricing_model.value,
            "old_hourly_rate": round(old_rate, 4),
            "new_hourly_rate": round(new_rate, 4),
            "savings_hourly": round(savings_hourly, 4),
            "savings_monthly": round(savings_monthly, 2),
            "savings_percentage": round(savings_percentage, 2),
        }
    
    def right_size(self, instance_id: str, new_instance_type: str) -> Dict:
        """Right-size an instance to a different type"""
        instance = self.get_instance(instance_id)
        
        # Get new instance type
        new_type = get_instance_type(new_instance_type)
        if not new_type:
            raise ValueError(f"Unknown instance type: {new_instance_type}")
        
        # Calculate savings
        old_type = instance.instance_type
        old_rate = instance.hourly_rate
        
        # Simulate right-sizing
        instance.state = InstanceState.MIGRATING
        time.sleep(0.15)  # Simulate 150ms delay
        
        # Update instance type
        instance.instance_type = new_type
        instance.state = InstanceState.RUNNING
        instance.state_transition_time = datetime.now()
        
        new_rate = instance.hourly_rate
        savings_hourly = old_rate - new_rate
        savings_monthly = savings_hourly * 730
        savings_percentage = (savings_hourly / old_rate) * 100 if old_rate > 0 else 0
        
        return {
            "status": "completed",
            "instance_id": instance_id,
            "old_instance_type": old_type.name,
            "new_instance_type": new_type.name,
            "old_vcpus": old_type.vcpus,
            "new_vcpus": new_type.vcpus,
            "old_memory_gb": old_type.memory_gb,
            "new_memory_gb": new_type.memory_gb,
            "old_hourly_rate": round(old_rate, 4),
            "new_hourly_rate": round(new_rate, 4),
            "savings_hourly": round(savings_hourly, 4),
            "savings_monthly": round(savings_monthly, 2),
            "savings_percentage": round(savings_percentage, 2),
        }
    
    def get_instance(self, instance_id: str) -> Instance:
        """Get an instance by ID"""
        if instance_id not in self.instances:
            raise ValueError(f"Instance not found: {instance_id}")
        return self.instances[instance_id]
    
    def list_instances(
        self,
        provider: Optional[CloudProvider] = None,
        pricing_model: Optional[PricingModel] = None,
        state: Optional[InstanceState] = None,
        tag_filter: Optional[Dict[str, str]] = None,
    ) -> List[Instance]:
        """List instances with optional filtering"""
        instances = list(self.instances.values())
        
        if provider:
            instances = [i for i in instances if i.instance_type.provider == provider]
        
        if pricing_model:
            instances = [i for i in instances if i.pricing_model == pricing_model]
        
        if state:
            instances = [i for i in instances if i.state == state]
        
        if tag_filter:
            instances = [
                i for i in instances
                if all(i.tags.get(k) == v for k, v in tag_filter.items())
            ]
        
        return instances
    
    def update_metrics(self):
        """Update metrics for all running instances (simulate fluctuations)"""
        for instance in self.instances.values():
            if instance.state == InstanceState.RUNNING:
                # Add small random fluctuations to metrics
                instance.cpu_utilization = max(0, min(100, 
                    instance.cpu_utilization + random.uniform(-5.0, 5.0)))
                instance.memory_utilization = max(0, min(100,
                    instance.memory_utilization + random.uniform(-3.0, 3.0)))
                if instance.instance_type.gpu_count > 0:
                    instance.gpu_utilization = max(0, min(100,
                        instance.gpu_utilization + random.uniform(-10.0, 10.0)))
                instance.network_in_mbps = max(0,
                    instance.network_in_mbps + random.uniform(-10.0, 10.0))
                instance.network_out_mbps = max(0,
                    instance.network_out_mbps + random.uniform(-10.0, 10.0))
    
    def get_total_cost(
        self,
        provider: Optional[CloudProvider] = None,
        pricing_model: Optional[PricingModel] = None,
    ) -> Dict:
        """Calculate total costs across instances"""
        instances = self.list_instances(provider=provider, pricing_model=pricing_model)
        
        total_hourly = sum(i.hourly_rate for i in instances if i.state == InstanceState.RUNNING)
        total_accumulated = sum(i.cost_so_far for i in instances)
        
        return {
            "total_instances": len(instances),
            "running_instances": len([i for i in instances if i.state == InstanceState.RUNNING]),
            "total_hourly_rate": round(total_hourly, 4),
            "total_monthly_estimate": round(total_hourly * 730, 2),
            "total_accumulated_cost": round(total_accumulated, 2),
        }
    
    def calculate_savings_potential(self) -> Dict:
        """Calculate potential savings from optimizations"""
        on_demand_instances = self.list_instances(pricing_model=PricingModel.ON_DEMAND)
        
        # Calculate spot migration savings
        spot_savings_hourly = 0.0
        spot_candidates = []
        
        for instance in on_demand_instances:
            if instance.state == InstanceState.RUNNING:
                current_rate = instance.hourly_rate
                spot_rate = instance.instance_type.spot_hourly
                savings = current_rate - spot_rate
                
                if savings > 0:
                    spot_savings_hourly += savings
                    spot_candidates.append({
                        "instance_id": instance.id,
                        "instance_type": instance.instance_type.name,
                        "current_rate": round(current_rate, 4),
                        "spot_rate": round(spot_rate, 4),
                        "savings_hourly": round(savings, 4),
                        "savings_monthly": round(savings * 730, 2),
                    })
        
        # Calculate right-sizing savings
        underutilized = [i for i in self.instances.values() if i.is_underutilized and i.state == InstanceState.RUNNING]
        rightsizing_savings_hourly = sum(i.hourly_rate * 0.3 for i in underutilized)  # Estimate 30% savings
        
        # Calculate idle instance savings
        idle = [i for i in self.instances.values() if i.is_idle and i.state == InstanceState.RUNNING]
        idle_savings_hourly = sum(i.hourly_rate for i in idle)
        
        total_savings_hourly = spot_savings_hourly + rightsizing_savings_hourly + idle_savings_hourly
        
        return {
            "spot_migration": {
                "candidates": len(spot_candidates),
                "savings_hourly": round(spot_savings_hourly, 4),
                "savings_monthly": round(spot_savings_hourly * 730, 2),
                "instances": spot_candidates,
            },
            "right_sizing": {
                "candidates": len(underutilized),
                "estimated_savings_hourly": round(rightsizing_savings_hourly, 4),
                "estimated_savings_monthly": round(rightsizing_savings_hourly * 730, 2),
            },
            "idle_instances": {
                "count": len(idle),
                "wasted_hourly": round(idle_savings_hourly, 4),
                "wasted_monthly": round(idle_savings_hourly * 730, 2),
            },
            "total_potential_savings": {
                "hourly": round(total_savings_hourly, 4),
                "monthly": round(total_savings_hourly * 730, 2),
                "annual": round(total_savings_hourly * 8760, 2),
            }
        }
    
    def _generate_instance_id(self, provider: CloudProvider) -> str:
        """Generate a realistic instance ID"""
        if provider == CloudProvider.AWS:
            return f"i-{uuid.uuid4().hex[:17]}"
        elif provider == CloudProvider.GCP:
            return f"gcp-{uuid.uuid4().hex[:12]}"
        elif provider == CloudProvider.AZURE:
            return f"vm-{uuid.uuid4().hex[:10]}"
        return f"instance-{uuid.uuid4().hex[:10]}"

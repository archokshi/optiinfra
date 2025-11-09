"""
Azure Resource Collector
Phase 6.5: Multi-Cloud Support
"""
import logging
from typing import List
from datetime import datetime

from ..base import BaseCollector
from ...models.metrics import ResourceMetric, CollectionResult
from .client import AzureClient

logger = logging.getLogger(__name__)


class AzureResourceCollector(BaseCollector):
    """Collects resource inventory from Azure"""
    
    def __init__(self, subscription_id: str, tenant_id: str, client_id: str, client_secret: str, customer_id: str):
        """
        Initialize Azure resource collector
        
        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure tenant ID
            client_id: Azure client ID
            client_secret: Azure client secret
            customer_id: Customer ID for tracking
        """
        super().__init__(client_id, customer_id)
        self.client = AzureClient(subscription_id, tenant_id, client_id, client_secret)
        self.resource_metrics: List[ResourceMetric] = []
        self.subscription_id = subscription_id
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "azure"
    
    def get_data_type(self) -> str:
        """Get data type"""
        return "resource"
    
    def validate_credentials(self) -> bool:
        """Validate Azure credentials"""
        try:
            self.client.list_virtual_machines()
            return True
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    def collect(self) -> CollectionResult:
        """Collect resource inventory from Azure"""
        started_at = datetime.now()
        self.log_collection_start()
        
        try:
            self.resource_metrics = []
            
            # Collect VMs
            self._collect_virtual_machines()
            
            completed_at = datetime.now()
            
            result = CollectionResult(
                customer_id=self.customer_id,
                provider=self.get_provider_name(),
                data_type=self.get_data_type(),
                success=True,
                records_collected=len(self.resource_metrics),
                started_at=started_at,
                completed_at=completed_at
            )
            
            self.log_collection_end(result)
            return result
            
        except Exception as e:
            return self.handle_error(e)
    
    def _collect_virtual_machines(self):
        """Collect VM inventory"""
        try:
            vms = self.client.list_virtual_machines()
            
            for vm in vms:
                vm_id = vm.get('id')
                vm_name = vm.get('name')
                status = vm.get('provisioning_state', 'unknown')
                location = vm.get('location', 'unknown')
                vm_size = vm.get('vm_size', 'unknown')
                
                metadata = {
                    "vm_size": vm_size,
                    "location": location,
                    "subscription_id": self.subscription_id
                }
                
                metric = ResourceMetric(
                    timestamp=datetime.now(),
                    customer_id=self.customer_id,
                    provider=self.get_provider_name(),
                    metric_type="inventory",
                    resource_id=vm_id,
                    resource_name=vm_name,
                    resource_type="virtual_machine",
                    status=status.lower(),
                    region=location,
                    utilization=0.0,
                    capacity=0.0,
                    unit="",
                    metadata=metadata
                )
                
                self.resource_metrics.append(metric)
            
            self.logger.info(f"Collected {len(vms)} Azure VMs")
            
        except Exception as e:
            self.logger.error(f"Failed to collect Azure VMs: {e}", exc_info=True)
    
    def get_metrics(self) -> List[ResourceMetric]:
        """Get collected metrics"""
        return self.resource_metrics

"""
Azure Performance Collector
Phase 6.5: Multi-Cloud Support
"""
import logging
from typing import List
from datetime import datetime

from ..base import BaseCollector
from ...models.metrics import PerformanceMetric, CollectionResult
from .client import AzureClient

logger = logging.getLogger(__name__)


class AzurePerformanceCollector(BaseCollector):
    """Collects performance metrics from Azure Monitor"""
    
    def __init__(self, subscription_id: str, tenant_id: str, client_id: str, client_secret: str, customer_id: str):
        """
        Initialize Azure performance collector
        
        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure tenant ID
            client_id: Azure client ID
            client_secret: Azure client secret
            customer_id: Customer ID for tracking
        """
        super().__init__(client_id, customer_id)
        self.client = AzureClient(subscription_id, tenant_id, client_id, client_secret)
        self.performance_metrics: List[PerformanceMetric] = []
        self.subscription_id = subscription_id
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "azure"
    
    def get_data_type(self) -> str:
        """Get data type"""
        return "performance"
    
    def validate_credentials(self) -> bool:
        """Validate Azure credentials"""
        try:
            self.client.list_virtual_machines()
            return True
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    def collect(self) -> CollectionResult:
        """Collect performance metrics from Azure"""
        started_at = datetime.now()
        self.log_collection_start()
        
        try:
            self.performance_metrics = []
            
            # Collect VM performance
            self._collect_vm_performance()
            
            completed_at = datetime.now()
            
            result = CollectionResult(
                customer_id=self.customer_id,
                provider=self.get_provider_name(),
                data_type=self.get_data_type(),
                success=True,
                records_collected=len(self.performance_metrics),
                started_at=started_at,
                completed_at=completed_at
            )
            
            self.log_collection_end(result)
            return result
            
        except Exception as e:
            return self.handle_error(e)
    
    def _collect_vm_performance(self):
        """Collect VM performance metrics"""
        try:
            vms = self.client.list_virtual_machines()
            
            for vm in vms:
                vm_id = vm.get('id')
                vm_name = vm.get('name')
                
                # Get CPU percentage
                cpu_metrics = self.client.get_metrics(
                    resource_uri=vm_id,
                    metric_names='Percentage CPU'
                )
                
                if cpu_metrics:
                    avg_cpu = sum(m['value'] for m in cpu_metrics) / len(cpu_metrics)
                    metric = PerformanceMetric(
                        timestamp=datetime.now(),
                        customer_id=self.customer_id,
                        provider=self.get_provider_name(),
                        metric_type="compute",
                        resource_id=vm_id,
                        resource_name=vm_name,
                        metric_name="cpu_utilization",
                        metric_value=avg_cpu,
                        unit="percent",
                        metadata={"location": vm.get('location'), "vm_size": vm.get('vm_size')},
                        workload_type="vm"
                    )
                    self.performance_metrics.append(metric)
            
            self.logger.info(f"Collected Azure performance metrics for {len(vms)} VMs")
            
        except Exception as e:
            self.logger.error(f"Failed to collect Azure performance: {e}", exc_info=True)
    
    def get_metrics(self) -> List[PerformanceMetric]:
        """Get collected metrics"""
        return self.performance_metrics

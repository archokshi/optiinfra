"""
GCP Resource Collector
Phase 6.5: Multi-Cloud Support
"""
import logging
from typing import List
from datetime import datetime

from ..base import BaseCollector
from ...models.metrics import ResourceMetric, CollectionResult
from .client import GCPClient

logger = logging.getLogger(__name__)


class GCPResourceCollector(BaseCollector):
    """Collects resource inventory from GCP"""
    
    def __init__(self, service_account_json: str, customer_id: str, project_id: str):
        """
        Initialize GCP resource collector
        
        Args:
            service_account_json: Service account JSON credentials
            customer_id: Customer ID for tracking
            project_id: GCP project ID
        """
        super().__init__(service_account_json, customer_id)
        self.client = GCPClient(service_account_json, project_id)
        self.resource_metrics: List[ResourceMetric] = []
        self.project_id = project_id
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "gcp"
    
    def get_data_type(self) -> str:
        """Get data type"""
        return "resource"
    
    def validate_credentials(self) -> bool:
        """Validate GCP credentials"""
        try:
            self.client.list_compute_instances()
            return True
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    def collect(self) -> CollectionResult:
        """Collect resource inventory from GCP"""
        started_at = datetime.now()
        self.log_collection_start()
        
        try:
            self.resource_metrics = []
            
            # Collect Compute Engine instances
            self._collect_compute_instances()
            
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
    
    def _collect_compute_instances(self):
        """Collect Compute Engine instance inventory"""
        try:
            instances = self.client.list_compute_instances()
            
            for instance in instances:
                instance_id = str(instance.get('id'))
                instance_name = instance.get('name')
                status = instance.get('status', 'UNKNOWN')
                machine_type = instance.get('machine_type', 'unknown')
                zone = instance.get('zone', 'unknown')
                
                metadata = {
                    "machine_type": machine_type,
                    "zone": zone,
                    "project_id": self.project_id
                }
                
                metric = ResourceMetric(
                    timestamp=datetime.now(),
                    customer_id=self.customer_id,
                    provider=self.get_provider_name(),
                    metric_type="inventory",
                    resource_id=instance_id,
                    resource_name=instance_name,
                    resource_type="compute_instance",
                    status=status.lower(),
                    region=zone,
                    utilization=0.0,
                    capacity=0.0,
                    unit="",
                    metadata=metadata
                )
                
                self.resource_metrics.append(metric)
            
            self.logger.info(f"Collected {len(instances)} GCP Compute instances")
            
        except Exception as e:
            self.logger.error(f"Failed to collect GCP instances: {e}", exc_info=True)
    
    def get_metrics(self) -> List[ResourceMetric]:
        """Get collected metrics"""
        return self.resource_metrics

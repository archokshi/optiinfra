"""
GCP Performance Collector
Phase 6.5: Multi-Cloud Support
"""
import logging
from typing import List
from datetime import datetime

from ..base import BaseCollector
from ...models.metrics import PerformanceMetric, CollectionResult
from .client import GCPClient

logger = logging.getLogger(__name__)


class GCPPerformanceCollector(BaseCollector):
    """Collects performance metrics from GCP Cloud Monitoring"""
    
    def __init__(self, service_account_json: str, customer_id: str, project_id: str):
        """
        Initialize GCP performance collector
        
        Args:
            service_account_json: Service account JSON credentials
            customer_id: Customer ID for tracking
            project_id: GCP project ID
        """
        super().__init__(service_account_json, customer_id)
        self.client = GCPClient(service_account_json, project_id)
        self.performance_metrics: List[PerformanceMetric] = []
        self.project_id = project_id
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "gcp"
    
    def get_data_type(self) -> str:
        """Get data type"""
        return "performance"
    
    def validate_credentials(self) -> bool:
        """Validate GCP credentials"""
        try:
            self.client.list_compute_instances()
            return True
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    def collect(self) -> CollectionResult:
        """Collect performance metrics from GCP"""
        started_at = datetime.now()
        self.log_collection_start()
        
        try:
            self.performance_metrics = []
            
            # Collect Compute Engine performance
            self._collect_compute_performance()
            
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
    
    def _collect_compute_performance(self):
        """Collect Compute Engine performance metrics"""
        try:
            instances = self.client.list_compute_instances()
            
            for instance in instances:
                instance_id = str(instance.get('id'))
                instance_name = instance.get('name')
                
                # Get CPU utilization
                cpu_metrics = self.client.get_monitoring_metrics(
                    metric_type="compute.googleapis.com/instance/cpu/utilization",
                    resource_type="gce_instance",
                    resource_labels={"instance_id": instance_id},
                    hours_ago=1
                )
                
                if cpu_metrics:
                    avg_cpu = sum(m['value'] for m in cpu_metrics) / len(cpu_metrics) * 100
                    metric = PerformanceMetric(
                        timestamp=datetime.now(),
                        customer_id=self.customer_id,
                        provider=self.get_provider_name(),
                        metric_type="compute",
                        resource_id=instance_id,
                        resource_name=instance_name,
                        metric_name="cpu_utilization",
                        metric_value=avg_cpu,
                        unit="percent",
                        metadata={"project_id": self.project_id, "machine_type": instance.get('machine_type')},
                        workload_type="instance"
                    )
                    self.performance_metrics.append(metric)
            
            self.logger.info(f"Collected GCP performance metrics for {len(instances)} instances")
            
        except Exception as e:
            self.logger.error(f"Failed to collect GCP performance: {e}", exc_info=True)
    
    def get_metrics(self) -> List[PerformanceMetric]:
        """Get collected metrics"""
        return self.performance_metrics

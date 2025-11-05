"""
Azure Client - Azure SDK wrapper
Phase 6.5: Multi-Cloud Support
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient

logger = logging.getLogger(__name__)


class AzureClient:
    """Wrapper for Azure SDK"""
    
    def __init__(self, subscription_id: str, tenant_id: str, client_id: str, client_secret: str):
        """
        Initialize Azure client
        
        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure tenant ID
            client_id: Azure client ID
            client_secret: Azure client secret
        """
        self.subscription_id = subscription_id
        
        # Create credential
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Initialize clients
        self.compute_client = ComputeManagementClient(
            credential=self.credential,
            subscription_id=subscription_id
        )
        
        self.monitor_client = MonitorManagementClient(
            credential=self.credential,
            subscription_id=subscription_id
        )
    
    def list_virtual_machines(self) -> List[Dict[str, Any]]:
        """List all virtual machines"""
        vms = []
        for vm in self.compute_client.virtual_machines.list_all():
            vms.append({
                'id': vm.id,
                'name': vm.name,
                'location': vm.location,
                'vm_size': vm.hardware_profile.vm_size if vm.hardware_profile else 'unknown',
                'provisioning_state': vm.provisioning_state
            })
        return vms
    
    def get_metrics(
        self,
        resource_uri: str,
        metric_names: str,
        timespan: str = None
    ) -> List[Dict[str, Any]]:
        """Get Azure Monitor metrics"""
        try:
            if not timespan:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=1)
                timespan = f"{start_time.isoformat()}/{end_time.isoformat()}"
            
            metrics_data = self.monitor_client.metrics.list(
                resource_uri=resource_uri,
                timespan=timespan,
                interval='PT5M',
                metricnames=metric_names,
                aggregation='Average'
            )
            
            results = []
            for metric in metrics_data.value:
                for timeseries in metric.timeseries:
                    for data in timeseries.data:
                        if data.average is not None:
                            results.append({
                                'value': data.average,
                                'timestamp': data.time_stamp
                            })
            return results
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []

"""
GCP Client - Google Cloud SDK wrapper
Phase 6.5: Multi-Cloud Support
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.cloud import monitoring_v3, compute_v1
import json

logger = logging.getLogger(__name__)


class GCPClient:
    """Wrapper for Google Cloud SDK"""
    
    def __init__(self, service_account_json: str, project_id: str):
        """
        Initialize GCP client
        
        Args:
            service_account_json: Service account JSON credentials
            project_id: GCP project ID
        """
        self.project_id = project_id
        
        # Parse service account JSON
        import tempfile
        import os
        
        # Create temp file for credentials
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write(service_account_json)
            self.credentials_path = f.name
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
        
        # Initialize clients
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.compute_client = compute_v1.InstancesClient()
    
    def list_compute_instances(self, zone: str = "us-central1-a") -> List[Dict[str, Any]]:
        """List Compute Engine instances"""
        try:
            request = compute_v1.ListInstancesRequest(
                project=self.project_id,
                zone=zone
            )
            instances = []
            for instance in self.compute_client.list(request=request):
                instances.append({
                    'id': instance.id,
                    'name': instance.name,
                    'status': instance.status,
                    'machine_type': instance.machine_type.split('/')[-1],
                    'zone': zone
                })
            return instances
        except Exception as e:
            logger.error(f"Failed to list instances: {e}")
            return []
    
    def get_monitoring_metrics(
        self,
        metric_type: str,
        resource_type: str,
        resource_labels: Dict[str, str],
        hours_ago: int = 1
    ) -> List[Dict[str, Any]]:
        """Get monitoring metrics"""
        try:
            project_name = f"projects/{self.project_id}"
            
            now = datetime.utcnow()
            interval = monitoring_v3.TimeInterval({
                "end_time": now,
                "start_time": now - timedelta(hours=hours_ago)
            })
            
            results = self.monitoring_client.list_time_series(
                request={
                    "name": project_name,
                    "filter": f'metric.type = "{metric_type}" AND resource.type = "{resource_type}"',
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
                }
            )
            
            metrics = []
            for result in results:
                for point in result.points:
                    metrics.append({
                        'value': point.value.double_value,
                        'timestamp': point.interval.end_time
                    })
            return metrics
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []

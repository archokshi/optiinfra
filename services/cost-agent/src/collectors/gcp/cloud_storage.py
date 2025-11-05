"""
GCP Cloud Storage Cost Collector

Collects GCS bucket costs and identifies storage optimization opportunities.
"""

import logging
from typing import Dict, Any, List
from google.cloud import storage
from google.cloud import monitoring_v3
from datetime import datetime, timedelta

from src.collectors.gcp.base import GCPBaseCollector

logger = logging.getLogger(__name__)


class CloudStorageCostCollector(GCPBaseCollector):
    """Collector for Cloud Storage bucket costs and optimization opportunities"""
    
    def __init__(self, **kwargs):
        """Initialize Cloud Storage cost collector"""
        super().__init__(**kwargs)
        self.storage_client = self.get_client(storage.Client)
        self.monitoring_client = self.get_client(monitoring_v3.MetricServiceClient)
    
    def collect_bucket_costs(self) -> List[Dict[str, Any]]:
        """
        Collect per-bucket GCS costs.
        
        Returns:
            List of bucket cost data
        """
        try:
            buckets = list(self.storage_client.list_buckets())
            logger.info(f"Found {len(buckets)} GCS buckets")
            
            bucket_costs = []
            
            for bucket in buckets:
                bucket_name = bucket.name
                
                try:
                    # Get bucket storage metrics
                    storage_metrics = self._get_bucket_storage_metrics(bucket_name)
                    
                    # Estimate cost
                    monthly_cost = self._estimate_bucket_cost(storage_metrics, bucket.location)
                    
                    bucket_data = {
                        'bucket_name': bucket_name,
                        'location': bucket.location,
                        'storage_class': bucket.storage_class,
                        'size_gb': storage_metrics['size_gb'],
                        'object_count': storage_metrics['object_count'],
                        'monthly_cost': monthly_cost,
                        'optimization': self._analyze_bucket(bucket, storage_metrics)
                    }
                    
                    bucket_costs.append(bucket_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to process bucket {bucket_name}: {e}")
                    continue
            
            logger.info(f"Collected cost data for {len(bucket_costs)} buckets")
            return bucket_costs
            
        except Exception as e:
            logger.error(f"Failed to collect GCS costs: {e}")
            raise
    
    def analyze_storage_classes(self) -> Dict[str, Any]:
        """
        Analyze storage class distribution and opportunities.
        
        Returns:
            Storage class analysis
        """
        try:
            buckets = list(self.storage_client.list_buckets())
            
            total_standard = 0.0
            total_nearline = 0.0
            total_coldline = 0.0
            total_archive = 0.0
            lifecycle_opportunities = []
            
            for bucket in buckets:
                bucket_name = bucket.name
                
                try:
                    metrics = self._get_bucket_storage_metrics(bucket_name)
                    size_gb = metrics['size_gb']
                    
                    # Track by storage class
                    if bucket.storage_class == 'STANDARD':
                        total_standard += size_gb
                    elif bucket.storage_class == 'NEARLINE':
                        total_nearline += size_gb
                    elif bucket.storage_class == 'COLDLINE':
                        total_coldline += size_gb
                    elif bucket.storage_class == 'ARCHIVE':
                        total_archive += size_gb
                    
                    # Check if bucket has lifecycle policy
                    has_lifecycle = self._has_lifecycle_policy(bucket)
                    
                    if not has_lifecycle and size_gb > 100 and bucket.storage_class == 'STANDARD':
                        # Opportunity: add lifecycle policy
                        potential_savings = size_gb * 0.020 * 0.5  # Save 50% by moving to Nearline
                        lifecycle_opportunities.append({
                            'bucket_name': bucket_name,
                            'standard_gb': size_gb,
                            'potential_monthly_savings': round(potential_savings, 2),
                            'recommendation': 'add_lifecycle_policy'
                        })
                
                except Exception as e:
                    logger.warning(f"Failed to analyze {bucket_name}: {e}")
                    continue
            
            return {
                'total_standard_gb': round(total_standard, 2),
                'total_nearline_gb': round(total_nearline, 2),
                'total_coldline_gb': round(total_coldline, 2),
                'total_archive_gb': round(total_archive, 2),
                'lifecycle_opportunities': lifecycle_opportunities,
                'total_potential_savings': round(
                    sum(opp['potential_monthly_savings'] for opp in lifecycle_opportunities),
                    2
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze storage classes: {e}")
            return {}
    
    def _get_bucket_storage_metrics(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket storage metrics from Cloud Monitoring.
        
        Args:
            bucket_name: Bucket name
        
        Returns:
            Storage metrics
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)
            
            # Get bucket size
            size_metric = self._get_monitoring_metric(
                bucket_name,
                'storage.googleapis.com/storage/total_bytes',
                start_time,
                end_time
            )
            
            # Get object count
            count_metric = self._get_monitoring_metric(
                bucket_name,
                'storage.googleapis.com/storage/object_count',
                start_time,
                end_time
            )
            
            size_bytes = size_metric.get('average', 0.0)
            object_count = int(count_metric.get('average', 0.0))
            
            return {
                'size_gb': round(size_bytes / (1024**3), 2),
                'object_count': object_count
            }
            
        except Exception as e:
            logger.warning(f"Failed to get metrics for {bucket_name}: {e}")
            return {
                'size_gb': 0.0,
                'object_count': 0
            }
    
    def _get_monitoring_metric(
        self,
        bucket_name: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Get Cloud Monitoring metric for GCS bucket"""
        try:
            project_name = f"projects/{self.project_id}"
            
            interval = monitoring_v3.TimeInterval(
                {
                    "end_time": {"seconds": int(end_time.timestamp())},
                    "start_time": {"seconds": int(start_time.timestamp())},
                }
            )
            
            filter_str = (
                f'metric.type = "{metric_type}" '
                f'AND resource.labels.bucket_name = "{bucket_name}"'
            )
            
            request = monitoring_v3.ListTimeSeriesRequest(
                {
                    "name": project_name,
                    "filter": filter_str,
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                }
            )
            
            self.log_api_call()
            results = self.monitoring_client.list_time_series(request=request)
            
            values = []
            for result in results:
                for point in result.points:
                    values.append(point.value.double_value)
            
            if not values:
                return {'average': 0.0}
            
            return {'average': sum(values) / len(values)}
            
        except Exception as e:
            logger.warning(f"Failed to get monitoring metric {metric_type}: {e}")
            return {'average': 0.0}
    
    def _estimate_bucket_cost(self, storage_metrics: Dict[str, Any], location: str) -> float:
        """Estimate monthly cost for bucket"""
        size_gb = storage_metrics['size_gb']
        
        # Storage costs vary by location and class
        # Using multi-region standard pricing as baseline
        storage_cost_per_gb = 0.020  # $0.020 per GB/month (Standard, multi-region)
        
        # Adjust for location type
        if 'us-' in location.lower() or 'eu-' in location.lower():
            storage_cost_per_gb = 0.020  # Regional
        
        storage_cost = size_gb * storage_cost_per_gb
        
        # Request costs (simplified - would need actual request metrics)
        request_cost = 0.0
        
        total_cost = storage_cost + request_cost
        return round(total_cost, 2)
    
    def _has_lifecycle_policy(self, bucket: storage.Bucket) -> bool:
        """Check if bucket has lifecycle policy"""
        try:
            bucket.reload()
            lifecycle_rules = bucket.lifecycle_rules
            return len(lifecycle_rules) > 0 if lifecycle_rules else False
        except Exception as e:
            logger.debug(f"Cannot check lifecycle for {bucket.name}: {e}")
            return False
    
    def _analyze_bucket(
        self,
        bucket: storage.Bucket,
        storage_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze bucket for optimization opportunities"""
        size_gb = storage_metrics['size_gb']
        storage_class = bucket.storage_class
        
        # Check if should use cheaper storage class
        needs_lifecycle = (
            storage_class == 'STANDARD' and
            size_gb > 100 and
            not self._has_lifecycle_policy(bucket)
        )
        
        return {
            'needs_lifecycle_policy': needs_lifecycle,
            'storage_class': storage_class,
            'recommendation': 'add_lifecycle_transitions' if needs_lifecycle else 'none'
        }

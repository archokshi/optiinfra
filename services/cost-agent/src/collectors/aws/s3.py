"""
AWS S3 Cost Collector

Collects S3 bucket costs and identifies storage optimization opportunities.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from src.collectors.aws.base import AWSBaseCollector

logger = logging.getLogger(__name__)


class S3CostCollector(AWSBaseCollector):
    """Collector for S3 bucket costs and optimization opportunities"""
    
    def __init__(self, **kwargs):
        """Initialize S3 cost collector"""
        super().__init__(**kwargs)
        self.s3_client = self.get_client('s3')
        self.cloudwatch_client = self.get_client('cloudwatch')
    
    def collect_bucket_costs(self) -> List[Dict[str, Any]]:
        """
        Collect per-bucket S3 costs.
        
        Returns:
            List of bucket cost data
        """
        try:
            buckets = self._get_all_buckets()
            logger.info(f"Found {len(buckets)} S3 buckets")
            
            bucket_costs = []
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                try:
                    # Get bucket location
                    location = self._get_bucket_location(bucket_name)
                    
                    # Get storage metrics
                    storage_metrics = self._get_bucket_storage_metrics(bucket_name)
                    
                    # Estimate cost
                    monthly_cost = self._estimate_bucket_cost(storage_metrics)
                    
                    bucket_data = {
                        'bucket_name': bucket_name,
                        'region': location,
                        'size_gb': storage_metrics['size_gb'],
                        'object_count': storage_metrics['object_count'],
                        'storage_class_distribution': storage_metrics['storage_classes'],
                        'monthly_cost': monthly_cost,
                        'optimization': self._analyze_bucket(storage_metrics)
                    }
                    
                    bucket_costs.append(bucket_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to process bucket {bucket_name}: {e}")
                    continue
            
            logger.info(f"Collected cost data for {len(bucket_costs)} buckets")
            return bucket_costs
            
        except Exception as e:
            logger.error(f"Failed to collect S3 costs: {e}")
            raise
    
    def analyze_storage_classes(self) -> Dict[str, Any]:
        """
        Analyze storage class distribution and opportunities.
        
        Returns:
            Storage class analysis
        """
        try:
            buckets = self._get_all_buckets()
            
            total_standard = 0.0
            total_ia = 0.0
            total_glacier = 0.0
            lifecycle_opportunities = []
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                try:
                    metrics = self._get_bucket_storage_metrics(bucket_name)
                    storage_classes = metrics['storage_classes']
                    
                    total_standard += storage_classes.get('STANDARD', 0.0)
                    total_ia += storage_classes.get('STANDARD_IA', 0.0)
                    total_glacier += storage_classes.get('GLACIER', 0.0)
                    
                    # Check if bucket has lifecycle policy
                    has_lifecycle = self._has_lifecycle_policy(bucket_name)
                    
                    if not has_lifecycle and storage_classes.get('STANDARD', 0) > 100:
                        # Opportunity: add lifecycle policy
                        potential_savings = storage_classes.get('STANDARD', 0) * 0.0125 * 0.5
                        lifecycle_opportunities.append({
                            'bucket_name': bucket_name,
                            'standard_gb': storage_classes.get('STANDARD', 0),
                            'potential_monthly_savings': round(potential_savings, 2),
                            'recommendation': 'add_lifecycle_policy'
                        })
                
                except Exception as e:
                    logger.warning(f"Failed to analyze {bucket_name}: {e}")
                    continue
            
            return {
                'total_standard_gb': round(total_standard, 2),
                'total_ia_gb': round(total_ia, 2),
                'total_glacier_gb': round(total_glacier, 2),
                'lifecycle_opportunities': lifecycle_opportunities,
                'total_potential_savings': round(
                    sum(opp['potential_monthly_savings'] for opp in lifecycle_opportunities),
                    2
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze storage classes: {e}")
            return {}
    
    def identify_incomplete_uploads(self) -> List[Dict[str, Any]]:
        """
        Identify buckets with incomplete multipart uploads.
        
        Returns:
            List of buckets with incomplete uploads
        """
        try:
            buckets = self._get_all_buckets()
            incomplete_uploads = []
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                try:
                    # List multipart uploads
                    response = self.s3_client.list_multipart_uploads(
                        Bucket=bucket_name
                    )
                    
                    uploads = response.get('Uploads', [])
                    
                    if uploads:
                        # Calculate wasted storage
                        total_size_mb = len(uploads) * 5  # Rough estimate
                        wasted_cost = (total_size_mb / 1024) * 0.023  # $0.023 per GB
                        
                        incomplete_uploads.append({
                            'bucket_name': bucket_name,
                            'incomplete_upload_count': len(uploads),
                            'estimated_wasted_storage_mb': total_size_mb,
                            'estimated_monthly_waste': round(wasted_cost, 2),
                            'recommendation': 'cleanup_incomplete_uploads'
                        })
                
                except Exception as e:
                    # Bucket might not allow listing uploads
                    logger.debug(f"Cannot list uploads for {bucket_name}: {e}")
                    continue
            
            logger.info(f"Found {len(incomplete_uploads)} buckets with incomplete uploads")
            return incomplete_uploads
            
        except Exception as e:
            logger.error(f"Failed to identify incomplete uploads: {e}")
            return []
    
    def _get_all_buckets(self) -> List[Dict[str, Any]]:
        """Get all S3 buckets"""
        try:
            self.log_api_call('s3', 'ListBuckets')
            
            response = self.s3_client.list_buckets()
            return response.get('Buckets', [])
            
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            return []
    
    def _get_bucket_location(self, bucket_name: str) -> str:
        """Get bucket region"""
        try:
            response = self.s3_client.get_bucket_location(Bucket=bucket_name)
            location = response.get('LocationConstraint')
            return location if location else 'us-east-1'
        except Exception as e:
            logger.warning(f"Failed to get location for {bucket_name}: {e}")
            return 'unknown'
    
    def _get_bucket_storage_metrics(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket storage metrics from CloudWatch.
        
        Note: CloudWatch metrics for S3 are updated daily and may lag.
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get bucket size
            size_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='BucketSizeBytes',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            # Get object count
            count_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='NumberOfObjects',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            size_datapoints = size_response.get('Datapoints', [])
            count_datapoints = count_response.get('Datapoints', [])
            
            size_bytes = size_datapoints[0]['Average'] if size_datapoints else 0
            object_count = int(count_datapoints[0]['Average']) if count_datapoints else 0
            
            return {
                'size_gb': round(size_bytes / (1024**3), 2),
                'object_count': object_count,
                'storage_classes': {
                    'STANDARD': round(size_bytes / (1024**3), 2),  # Simplified
                    'STANDARD_IA': 0.0,
                    'GLACIER': 0.0
                }
            }
            
        except Exception as e:
            logger.warning(f"Failed to get metrics for {bucket_name}: {e}")
            return {
                'size_gb': 0.0,
                'object_count': 0,
                'storage_classes': {}
            }
    
    def _estimate_bucket_cost(self, storage_metrics: Dict[str, Any]) -> float:
        """Estimate monthly cost for bucket"""
        size_gb = storage_metrics['size_gb']
        storage_classes = storage_metrics['storage_classes']
        
        # Storage costs (per GB per month)
        standard_cost = storage_classes.get('STANDARD', 0) * 0.023
        ia_cost = storage_classes.get('STANDARD_IA', 0) * 0.0125
        glacier_cost = storage_classes.get('GLACIER', 0) * 0.004
        
        # Request costs (simplified - would need actual request metrics)
        request_cost = 0.0
        
        total_cost = standard_cost + ia_cost + glacier_cost + request_cost
        return round(total_cost, 2)
    
    def _has_lifecycle_policy(self, bucket_name: str) -> bool:
        """Check if bucket has lifecycle policy"""
        try:
            self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            return True
        except self.s3_client.exceptions.NoSuchLifecycleConfiguration:
            return False
        except Exception as e:
            logger.debug(f"Cannot check lifecycle for {bucket_name}: {e}")
            return False
    
    def _analyze_bucket(self, storage_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bucket for optimization opportunities"""
        size_gb = storage_metrics['size_gb']
        storage_classes = storage_metrics['storage_classes']
        
        # Check if mostly in Standard (could use IA or Glacier)
        standard_pct = (
            storage_classes.get('STANDARD', 0) / size_gb * 100
            if size_gb > 0 else 0
        )
        
        needs_lifecycle = standard_pct > 80 and size_gb > 100
        
        return {
            'needs_lifecycle_policy': needs_lifecycle,
            'standard_percentage': round(standard_pct, 2),
            'recommendation': 'add_lifecycle_transitions' if needs_lifecycle else 'none'
        }

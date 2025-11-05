"""
AWS Performance Collector
Phase 6.5: Multi-Cloud Support
"""
import logging
from typing import List
from datetime import datetime, timedelta

from ..base import BaseCollector
from ...models.metrics import PerformanceMetric, CollectionResult
from .client import AWSClient

logger = logging.getLogger(__name__)


class AWSPerformanceCollector(BaseCollector):
    """Collects performance metrics from AWS CloudWatch"""
    
    def __init__(self, access_key_id: str, secret_access_key: str, customer_id: str, region: str = "us-east-1"):
        """
        Initialize AWS performance collector
        
        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            customer_id: Customer ID for tracking
            region: AWS region
        """
        super().__init__(access_key_id, customer_id)
        self.client = AWSClient(access_key_id, secret_access_key, region)
        self.performance_metrics: List[PerformanceMetric] = []
        self.region = region
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "aws"
    
    def get_data_type(self) -> str:
        """Get data type"""
        return "performance"
    
    def validate_credentials(self) -> bool:
        """Validate AWS credentials"""
        try:
            self.client.list_ec2_instances()
            return True
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    def collect(self) -> CollectionResult:
        """Collect performance metrics from AWS"""
        started_at = datetime.now()
        self.log_collection_start()
        
        try:
            self.performance_metrics = []
            
            # Collect EC2 performance metrics
            self._collect_ec2_performance()
            
            # Collect RDS performance metrics
            self._collect_rds_performance()
            
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
    
    def _collect_ec2_performance(self):
        """Collect EC2 instance performance metrics"""
        try:
            instances = self.client.list_ec2_instances()
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            for instance in instances:
                instance_id = instance.get('InstanceId')
                instance_name = self._get_instance_name(instance)
                
                # CPU Utilization
                cpu_metrics = self.client.get_cloudwatch_metrics(
                    namespace='AWS/EC2',
                    metric_name='CPUUtilization',
                    dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    start_time=start_time,
                    end_time=end_time
                )
                
                if cpu_metrics:
                    avg_cpu = sum(m['Average'] for m in cpu_metrics) / len(cpu_metrics)
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
                        metadata={"region": self.region, "instance_type": instance.get('InstanceType')},
                        workload_type="instance"
                    )
                    self.performance_metrics.append(metric)
            
            self.logger.info(f"Collected EC2 performance metrics for {len(instances)} instances")
            
        except Exception as e:
            self.logger.error(f"Failed to collect EC2 performance: {e}", exc_info=True)
    
    def _collect_rds_performance(self):
        """Collect RDS database performance metrics"""
        try:
            databases = self.client.list_rds_instances()
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            for db in databases:
                db_id = db.get('DBInstanceIdentifier')
                
                # CPU Utilization
                cpu_metrics = self.client.get_cloudwatch_metrics(
                    namespace='AWS/RDS',
                    metric_name='CPUUtilization',
                    dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                    start_time=start_time,
                    end_time=end_time
                )
                
                if cpu_metrics:
                    avg_cpu = sum(m['Average'] for m in cpu_metrics) / len(cpu_metrics)
                    metric = PerformanceMetric(
                        timestamp=datetime.now(),
                        customer_id=self.customer_id,
                        provider=self.get_provider_name(),
                        metric_type="database",
                        resource_id=db_id,
                        resource_name=db_id,
                        metric_name="cpu_utilization",
                        metric_value=avg_cpu,
                        unit="percent",
                        metadata={"region": self.region, "engine": db.get('Engine')},
                        workload_type="database"
                    )
                    self.performance_metrics.append(metric)
            
            self.logger.info(f"Collected RDS performance metrics for {len(databases)} databases")
            
        except Exception as e:
            self.logger.error(f"Failed to collect RDS performance: {e}", exc_info=True)
    
    def _get_instance_name(self, instance: dict) -> str:
        """Extract instance name from tags"""
        tags = instance.get('Tags', [])
        for tag in tags:
            if tag.get('Key') == 'Name':
                return tag.get('Value', instance.get('InstanceId'))
        return instance.get('InstanceId')
    
    def get_metrics(self) -> List[PerformanceMetric]:
        """Get collected metrics"""
        return self.performance_metrics

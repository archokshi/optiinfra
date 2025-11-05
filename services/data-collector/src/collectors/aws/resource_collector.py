"""
AWS Resource Collector
Phase 6.5: Multi-Cloud Support
"""
import logging
from typing import List
from datetime import datetime
import json

from ..base import BaseCollector
from ...models.metrics import ResourceMetric, CollectionResult
from .client import AWSClient

logger = logging.getLogger(__name__)


class AWSResourceCollector(BaseCollector):
    """Collects resource inventory from AWS"""
    
    def __init__(self, access_key_id: str, secret_access_key: str, customer_id: str, region: str = "us-east-1"):
        """
        Initialize AWS resource collector
        
        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            customer_id: Customer ID for tracking
            region: AWS region
        """
        super().__init__(access_key_id, customer_id)
        self.client = AWSClient(access_key_id, secret_access_key, region)
        self.resource_metrics: List[ResourceMetric] = []
        self.region = region
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "aws"
    
    def get_data_type(self) -> str:
        """Get data type"""
        return "resource"
    
    def validate_credentials(self) -> bool:
        """Validate AWS credentials"""
        try:
            self.client.list_ec2_instances()
            return True
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    def collect(self) -> CollectionResult:
        """Collect resource inventory from AWS"""
        started_at = datetime.now()
        self.log_collection_start()
        
        try:
            self.resource_metrics = []
            
            # Collect EC2 instances
            self._collect_ec2_instances()
            
            # Collect RDS databases
            self._collect_rds_databases()
            
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
    
    def _collect_ec2_instances(self):
        """Collect EC2 instance inventory"""
        try:
            instances = self.client.list_ec2_instances()
            
            for instance in instances:
                instance_id = instance.get('InstanceId')
                instance_name = self._get_instance_name(instance)
                state = instance.get('State', {}).get('Name', 'unknown')
                instance_type = instance.get('InstanceType', 'unknown')
                
                metadata = json.dumps({
                    "instance_type": instance_type,
                    "ami_id": instance.get('ImageId'),
                    "launch_time": str(instance.get('LaunchTime')),
                    "availability_zone": instance.get('Placement', {}).get('AvailabilityZone')
                })
                
                metric = ResourceMetric(
                    timestamp=datetime.now(),
                    customer_id=self.customer_id,
                    provider=self.get_provider_name(),
                    metric_type="inventory",
                    resource_id=instance_id,
                    resource_name=instance_name,
                    resource_type="ec2_instance",
                    status=state,
                    region=self.region,
                    utilization=0.0,
                    capacity=0.0,
                    unit="",
                    metadata=metadata
                )
                
                self.resource_metrics.append(metric)
            
            self.logger.info(f"Collected {len(instances)} EC2 instances")
            
        except Exception as e:
            self.logger.error(f"Failed to collect EC2 instances: {e}", exc_info=True)
    
    def _collect_rds_databases(self):
        """Collect RDS database inventory"""
        try:
            databases = self.client.list_rds_instances()
            
            for db in databases:
                db_id = db.get('DBInstanceIdentifier')
                status = db.get('DBInstanceStatus', 'unknown')
                engine = db.get('Engine', 'unknown')
                storage = db.get('AllocatedStorage', 0)
                
                metadata = json.dumps({
                    "engine": engine,
                    "engine_version": db.get('EngineVersion'),
                    "instance_class": db.get('DBInstanceClass'),
                    "multi_az": db.get('MultiAZ', False),
                    "storage_type": db.get('StorageType')
                })
                
                metric = ResourceMetric(
                    timestamp=datetime.now(),
                    customer_id=self.customer_id,
                    provider=self.get_provider_name(),
                    metric_type="inventory",
                    resource_id=db_id,
                    resource_name=db_id,
                    resource_type="rds_database",
                    status=status,
                    region=self.region,
                    utilization=0.0,
                    capacity=float(storage),
                    unit="GB",
                    metadata=metadata
                )
                
                self.resource_metrics.append(metric)
            
            self.logger.info(f"Collected {len(databases)} RDS databases")
            
        except Exception as e:
            self.logger.error(f"Failed to collect RDS databases: {e}", exc_info=True)
    
    def _get_instance_name(self, instance: dict) -> str:
        """Extract instance name from tags"""
        tags = instance.get('Tags', [])
        for tag in tags:
            if tag.get('Key') == 'Name':
                return tag.get('Value', instance.get('InstanceId'))
        return instance.get('InstanceId')
    
    def get_metrics(self) -> List[ResourceMetric]:
        """Get collected metrics"""
        return self.resource_metrics

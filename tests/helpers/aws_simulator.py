"""
AWS API Simulator using LocalStack

Simulates AWS EC2, IAM, and CloudWatch APIs for testing.
"""
import boto3
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class AWSSimulator:
    """AWS API simulator using LocalStack."""
    
    def __init__(self, endpoint_url: str = "http://localhost:4567"):
        self.endpoint_url = endpoint_url
        self.ec2_client = None
        self.iam_client = None
        self.cloudwatch_client = None
        self.created_resources = {
            "instances": [],
            "security_groups": [],
            "key_pairs": [],
        }
    
    def setup(self):
        """Initialize AWS clients and create test resources."""
        try:
            # Initialize clients
            self.ec2_client = boto3.client(
                'ec2',
                endpoint_url=self.endpoint_url,
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
            
            self.iam_client = boto3.client(
                'iam',
                endpoint_url=self.endpoint_url,
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
            
            self.cloudwatch_client = boto3.client(
                'cloudwatch',
                endpoint_url=self.endpoint_url,
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
            
            logger.info("✅ AWS simulator initialized")
        except Exception as e:
            logger.warning(f"Could not initialize AWS simulator: {e}")
    
    def create_test_instance(
        self,
        instance_type: str = "p4d.24xlarge",
        count: int = 1,
        tags: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """Create test EC2 instances."""
        if not self.ec2_client:
            return []
        
        try:
            response = self.ec2_client.run_instances(
                ImageId='ami-12345678',
                InstanceType=instance_type,
                MinCount=count,
                MaxCount=count,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': k, 'Value': v}
                            for k, v in (tags or {}).items()
                        ]
                    }
                ] if tags else []
            )
            
            instance_ids = [inst['InstanceId'] for inst in response['Instances']]
            self.created_resources['instances'].extend(instance_ids)
            
            logger.info(f"Created {count} test instances: {instance_ids}")
            return instance_ids
        except Exception as e:
            logger.warning(f"Could not create test instances: {e}")
            return []
    
    def create_spot_instance(
        self,
        instance_type: str = "p4d.24xlarge",
        count: int = 1
    ) -> List[str]:
        """Create spot instances."""
        if not self.ec2_client:
            return []
        
        try:
            response = self.ec2_client.request_spot_instances(
                InstanceCount=count,
                LaunchSpecification={
                    'ImageId': 'ami-12345678',
                    'InstanceType': instance_type,
                }
            )
            
            request_ids = [req['SpotInstanceRequestId'] for req in response['SpotInstanceRequests']]
            logger.info(f"Created {count} spot instance requests: {request_ids}")
            return request_ids
        except Exception as e:
            logger.warning(f"Could not create spot instances: {e}")
            return []
    
    def terminate_instance(self, instance_id: str):
        """Terminate an EC2 instance."""
        if not self.ec2_client:
            return
        
        try:
            self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            logger.info(f"Terminated instance: {instance_id}")
        except Exception as e:
            logger.warning(f"Could not terminate instance: {e}")
    
    def get_instance_status(self, instance_id: str) -> Optional[str]:
        """Get instance status."""
        if not self.ec2_client:
            return None
        
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            if response['Reservations']:
                state = response['Reservations'][0]['Instances'][0]['State']['Name']
                return state
        except Exception as e:
            logger.warning(f"Could not get instance status: {e}")
        
        return None
    
    def put_metric_data(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        dimensions: Optional[List[Dict[str, str]]] = None
    ):
        """Put metric data to CloudWatch."""
        if not self.cloudwatch_client:
            return
        
        try:
            self.cloudwatch_client.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Dimensions': dimensions or []
                    }
                ]
            )
        except Exception as e:
            logger.warning(f"Could not put metric data: {e}")
    
    def cleanup(self):
        """Clean up all created resources."""
        if not self.ec2_client:
            return
        
        try:
            # Terminate all created instances
            if self.created_resources['instances']:
                self.ec2_client.terminate_instances(
                    InstanceIds=self.created_resources['instances']
                )
                logger.info(f"Terminated {len(self.created_resources['instances'])} instances")
            
            self.created_resources = {
                "instances": [],
                "security_groups": [],
                "key_pairs": [],
            }
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

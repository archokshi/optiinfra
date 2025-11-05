"""
AWS Client - Boto3 wrapper for AWS services
Phase 6.5: Multi-Cloud Support
"""
import boto3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AWSClient:
    """Wrapper for AWS boto3 client"""
    
    def __init__(self, access_key_id: str, secret_access_key: str, region: str = "us-east-1"):
        """
        Initialize AWS client
        
        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        
        # Initialize clients
        self.ce_client = boto3.client(
            'ce',  # Cost Explorer
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
        
        self.cloudwatch_client = boto3.client(
            'cloudwatch',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
        
        self.ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
        
        self.rds_client = boto3.client(
            'rds',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
    
    def get_cost_and_usage(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get cost and usage data"""
        return self.ce_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
    
    def list_ec2_instances(self) -> List[Dict[str, Any]]:
        """List all EC2 instances"""
        response = self.ec2_client.describe_instances()
        instances = []
        for reservation in response.get('Reservations', []):
            instances.extend(reservation.get('Instances', []))
        return instances
    
    def get_cloudwatch_metrics(
        self,
        namespace: str,
        metric_name: str,
        dimensions: List[Dict[str, str]],
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get CloudWatch metrics"""
        response = self.cloudwatch_client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5 minutes
            Statistics=['Average']
        )
        return response.get('Datapoints', [])
    
    def list_rds_instances(self) -> List[Dict[str, Any]]:
        """List all RDS instances"""
        response = self.rds_client.describe_db_instances()
        return response.get('DBInstances', [])

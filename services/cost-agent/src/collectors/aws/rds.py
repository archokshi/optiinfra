"""
AWS RDS Cost Collector

Collects RDS database costs and identifies idle/underutilized databases.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.collectors.aws.base import AWSBaseCollector

logger = logging.getLogger(__name__)


class RDSCostCollector(AWSBaseCollector):
    """Collector for RDS database costs and optimization opportunities"""
    
    IDLE_CONNECTIONS_THRESHOLD = 1.0  # Connections < 1 = idle
    
    def __init__(self, **kwargs):
        """Initialize RDS cost collector"""
        super().__init__(**kwargs)
        self.rds_client = self.get_client('rds')
        self.cloudwatch_client = self.get_client('cloudwatch')
    
    def collect_rds_costs(
        self,
        include_utilization: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect per-instance RDS costs.
        
        Args:
            include_utilization: Include CloudWatch metrics
        
        Returns:
            List of RDS instance cost data
        """
        try:
            instances = self._get_all_db_instances()
            logger.info(f"Found {len(instances)} RDS instances")
            
            rds_costs = []
            
            for instance in instances:
                db_id = instance['DBInstanceIdentifier']
                db_class = instance['DBInstanceClass']
                engine = instance['Engine']
                status = instance['DBInstanceStatus']
                
                # Estimate cost
                monthly_cost = self._estimate_db_cost(instance)
                
                instance_data = {
                    'db_instance_id': db_id,
                    'db_class': db_class,
                    'engine': engine,
                    'engine_version': instance.get('EngineVersion'),
                    'status': status,
                    'multi_az': instance.get('MultiAZ', False),
                    'storage_gb': instance.get('AllocatedStorage', 0),
                    'storage_type': instance.get('StorageType', 'gp2'),
                    'monthly_cost': monthly_cost,
                    'region': self.region
                }
                
                # Add utilization if requested
                if include_utilization and status == 'available':
                    utilization = self._get_db_utilization(db_id)
                    instance_data['utilization'] = utilization
                    instance_data['optimization'] = self._analyze_db_instance(
                        instance_data,
                        utilization
                    )
                
                rds_costs.append(instance_data)
            
            logger.info(f"Collected cost data for {len(rds_costs)} RDS instances")
            return rds_costs
            
        except Exception as e:
            logger.error(f"Failed to collect RDS costs: {e}")
            raise
    
    def identify_idle_databases(
        self,
        lookback_days: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Identify idle RDS databases.
        
        Args:
            lookback_days: Days to analyze
        
        Returns:
            List of idle databases
        """
        try:
            instances = self._get_all_db_instances()
            idle_databases = []
            
            for instance in instances:
                if instance['DBInstanceStatus'] != 'available':
                    continue
                
                db_id = instance['DBInstanceIdentifier']
                utilization = self._get_db_utilization(db_id, lookback_days)
                
                # Check if idle (no connections)
                if utilization['connections_avg'] < self.IDLE_CONNECTIONS_THRESHOLD:
                    idle_databases.append({
                        'db_instance_id': db_id,
                        'db_class': instance['DBInstanceClass'],
                        'engine': instance['Engine'],
                        'monthly_cost': self._estimate_db_cost(instance),
                        'utilization': utilization,
                        'idle_duration_days': lookback_days,
                        'recommendation': 'terminate'
                    })
            
            logger.info(f"Identified {len(idle_databases)} idle databases")
            return idle_databases
            
        except Exception as e:
            logger.error(f"Failed to identify idle databases: {e}")
            return []
    
    def analyze_storage_costs(self) -> Dict[str, Any]:
        """
        Analyze RDS storage costs.
        
        Returns:
            Storage cost breakdown
        """
        try:
            instances = self._get_all_db_instances()
            
            total_storage_cost = 0.0
            total_iops_cost = 0.0
            total_backup_cost = 0.0
            
            for instance in instances:
                storage_gb = instance.get('AllocatedStorage', 0)
                storage_type = instance.get('StorageType', 'gp2')
                iops = instance.get('Iops', 0)
                
                # Storage cost
                storage_cost = self._estimate_storage_cost(storage_gb, storage_type)
                total_storage_cost += storage_cost
                
                # IOPS cost (for io1/io2)
                if storage_type in ['io1', 'io2'] and iops:
                    iops_cost = iops * 0.10  # $0.10 per provisioned IOPS
                    total_iops_cost += iops_cost
                
                # Backup cost (estimate)
                backup_cost = storage_gb * 0.095  # Approximate
                total_backup_cost += backup_cost
            
            return {
                'total_storage_cost': round(total_storage_cost, 2),
                'total_iops_cost': round(total_iops_cost, 2),
                'total_backup_cost': round(total_backup_cost, 2),
                'total_cost': round(
                    total_storage_cost + total_iops_cost + total_backup_cost,
                    2
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze storage costs: {e}")
            return {}
    
    def identify_multi_az_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify databases that could be converted to single-AZ.
        
        Returns:
            List of multi-AZ conversion opportunities
        """
        try:
            instances = self._get_all_db_instances()
            opportunities = []
            
            for instance in instances:
                if not instance.get('MultiAZ', False):
                    continue
                
                # Check if it's a non-production database
                tags = self._get_db_tags(instance['DBInstanceArn'])
                env = tags.get('Environment', '').lower()
                
                if env in ['dev', 'development', 'test', 'staging']:
                    current_cost = self._estimate_db_cost(instance)
                    single_az_cost = current_cost * 0.5  # Multi-AZ is ~2x cost
                    
                    opportunities.append({
                        'db_instance_id': instance['DBInstanceIdentifier'],
                        'environment': env,
                        'current_cost': current_cost,
                        'single_az_cost': single_az_cost,
                        'estimated_savings': current_cost - single_az_cost,
                        'recommendation': 'convert_to_single_az'
                    })
            
            logger.info(f"Identified {len(opportunities)} multi-AZ opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify multi-AZ opportunities: {e}")
            return []
    
    def _get_all_db_instances(self) -> List[Dict[str, Any]]:
        """Get all RDS instances"""
        try:
            self.log_api_call('rds', 'DescribeDBInstances')
            
            instances = self.paginate_results(
                self.rds_client,
                'describe_db_instances',
                'DBInstances'
            )
            
            return instances
            
        except Exception as e:
            logger.error(f"Failed to get RDS instances: {e}")
            return []
    
    def _get_db_utilization(
        self,
        db_instance_id: str,
        lookback_days: int = 14
    ) -> Dict[str, float]:
        """Get database utilization metrics from CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)
            
            # Get database connections
            connections = self._get_cloudwatch_metric(
                db_instance_id,
                'DatabaseConnections',
                start_time,
                end_time
            )
            
            # Get CPU utilization
            cpu = self._get_cloudwatch_metric(
                db_instance_id,
                'CPUUtilization',
                start_time,
                end_time
            )
            
            # Get read/write IOPS
            read_iops = self._get_cloudwatch_metric(
                db_instance_id,
                'ReadIOPS',
                start_time,
                end_time
            )
            
            write_iops = self._get_cloudwatch_metric(
                db_instance_id,
                'WriteIOPS',
                start_time,
                end_time
            )
            
            return {
                'connections_avg': round(connections.get('Average', 0.0), 2),
                'connections_max': round(connections.get('Maximum', 0.0), 2),
                'cpu_avg': round(cpu.get('Average', 0.0), 2),
                'read_iops_avg': round(read_iops.get('Average', 0.0), 2),
                'write_iops_avg': round(write_iops.get('Average', 0.0), 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get utilization for {db_instance_id}: {e}")
            return {
                'connections_avg': 0.0,
                'connections_max': 0.0,
                'cpu_avg': 0.0,
                'read_iops_avg': 0.0,
                'write_iops_avg': 0.0
            }
    
    def _get_cloudwatch_metric(
        self,
        db_instance_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Get CloudWatch metric statistics for RDS"""
        try:
            self.log_api_call('cloudwatch', 'GetMetricStatistics')
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            datapoints = response.get('Datapoints', [])
            
            if not datapoints:
                return {'Average': 0.0, 'Maximum': 0.0}
            
            avg = sum(d['Average'] for d in datapoints) / len(datapoints)
            max_val = max(d['Maximum'] for d in datapoints)
            
            return {'Average': avg, 'Maximum': max_val}
            
        except Exception as e:
            logger.warning(f"Failed to get CloudWatch metric {metric_name}: {e}")
            return {'Average': 0.0, 'Maximum': 0.0}
    
    def _estimate_db_cost(self, instance: Dict[str, Any]) -> float:
        """Estimate monthly cost for RDS instance"""
        db_class = instance['DBInstanceClass']
        multi_az = instance.get('MultiAZ', False)
        storage_gb = instance.get('AllocatedStorage', 0)
        storage_type = instance.get('StorageType', 'gp2')
        
        # Instance cost (simplified pricing)
        instance_cost = self._estimate_instance_cost_by_class(db_class)
        
        # Multi-AZ doubles the cost
        if multi_az:
            instance_cost *= 2
        
        # Storage cost
        storage_cost = self._estimate_storage_cost(storage_gb, storage_type)
        
        return round(instance_cost + storage_cost, 2)
    
    def _estimate_instance_cost_by_class(self, db_class: str) -> float:
        """Estimate monthly instance cost by class"""
        # Rough pricing estimates (on-demand, us-east-1)
        pricing = {
            'db.t3.micro': 12.0,
            'db.t3.small': 24.0,
            'db.t3.medium': 48.0,
            'db.t3.large': 96.0,
            'db.m5.large': 110.0,
            'db.m5.xlarge': 220.0,
            'db.m5.2xlarge': 440.0,
            'db.r5.large': 165.0,
            'db.r5.xlarge': 330.0,
            'db.r5.2xlarge': 660.0,
        }
        
        return pricing.get(db_class, 150.0)
    
    def _estimate_storage_cost(self, size_gb: int, storage_type: str) -> float:
        """Estimate monthly storage cost"""
        pricing_per_gb = {
            'gp2': 0.115,
            'gp3': 0.092,
            'io1': 0.125,
            'io2': 0.125,
            'magnetic': 0.10
        }
        
        price_per_gb = pricing_per_gb.get(storage_type, 0.115)
        return size_gb * price_per_gb
    
    def _analyze_db_instance(
        self,
        instance_data: Dict[str, Any],
        utilization: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze database for optimization opportunities"""
        connections_avg = utilization['connections_avg']
        cpu_avg = utilization['cpu_avg']
        
        is_idle = connections_avg < self.IDLE_CONNECTIONS_THRESHOLD
        is_underutilized = cpu_avg < 20.0 and not is_idle
        
        return {
            'is_idle': is_idle,
            'is_underutilized': is_underutilized,
            'recommendation': 'terminate' if is_idle else ('downsize' if is_underutilized else 'none')
        }
    
    def _get_db_tags(self, db_arn: str) -> Dict[str, str]:
        """Get tags for RDS instance"""
        try:
            response = self.rds_client.list_tags_for_resource(
                ResourceName=db_arn
            )
            tags = response.get('TagList', [])
            return {tag['Key']: tag['Value'] for tag in tags}
        except Exception as e:
            logger.warning(f"Failed to get tags for {db_arn}: {e}")
            return {}

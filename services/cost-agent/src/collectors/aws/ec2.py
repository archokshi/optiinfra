"""
AWS EC2 Cost Collector

Collects EC2 instance costs, identifies idle and underutilized instances,
and finds spot migration opportunities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.collectors.aws.base import AWSBaseCollector

logger = logging.getLogger(__name__)


class EC2CostCollector(AWSBaseCollector):
    """Collector for EC2 instance costs and optimization opportunities"""
    
    # Thresholds for idle/underutilized detection
    IDLE_CPU_THRESHOLD = 5.0  # CPU < 5% = idle
    IDLE_NETWORK_THRESHOLD = 1.0  # Network < 1MB/day = idle
    UNDERUTILIZED_CPU_THRESHOLD = 20.0  # CPU < 20% = underutilized
    
    def __init__(self, **kwargs):
        """Initialize EC2 cost collector"""
        super().__init__(**kwargs)
        self.ec2_client = self.get_client('ec2')
        self.cloudwatch_client = self.get_client('cloudwatch')
    
    def collect_instance_costs(
        self,
        start_date: str,
        end_date: str,
        include_utilization: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect per-instance cost breakdown.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            include_utilization: Include CloudWatch metrics
        
        Returns:
            List of instance cost data
        """
        try:
            # Get all instances
            instances = self._get_all_instances()
            logger.info(f"Found {len(instances)} EC2 instances")
            
            instance_costs = []
            
            for instance in instances:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                state = instance['State']['Name']
                
                # Skip terminated instances
                if state == 'terminated':
                    continue
                
                # Get instance cost (estimated from pricing)
                monthly_cost = self._estimate_instance_cost(instance)
                
                instance_data = {
                    'instance_id': instance_id,
                    'instance_type': instance_type,
                    'region': self.region,
                    'state': state,
                    'monthly_cost': monthly_cost,
                    'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                    'tags': self._extract_tags(instance.get('Tags', []))
                }
                
                # Add utilization metrics if requested
                if include_utilization and state == 'running':
                    utilization = self._get_instance_utilization(instance_id)
                    instance_data['utilization'] = utilization
                    
                    # Determine optimization opportunities
                    instance_data['optimization'] = self._analyze_instance(
                        instance_data,
                        utilization
                    )
                
                instance_costs.append(instance_data)
            
            logger.info(f"Collected cost data for {len(instance_costs)} instances")
            return instance_costs
            
        except Exception as e:
            logger.error(f"Failed to collect instance costs: {e}")
            raise
    
    def identify_idle_instances(
        self,
        lookback_days: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Identify idle EC2 instances.
        
        Args:
            lookback_days: Days to analyze (default: 14)
        
        Returns:
            List of idle instances
        """
        try:
            instances = self._get_all_instances()
            idle_instances = []
            
            for instance in instances:
                if instance['State']['Name'] != 'running':
                    continue
                
                instance_id = instance['InstanceId']
                utilization = self._get_instance_utilization(
                    instance_id,
                    lookback_days
                )
                
                # Check if idle
                if (utilization['cpu_avg'] < self.IDLE_CPU_THRESHOLD and
                    utilization['network_mb_day'] < self.IDLE_NETWORK_THRESHOLD):
                    
                    idle_instances.append({
                        'instance_id': instance_id,
                        'instance_type': instance['InstanceType'],
                        'monthly_cost': self._estimate_instance_cost(instance),
                        'utilization': utilization,
                        'idle_duration_days': lookback_days,
                        'recommendation': 'terminate',
                        'tags': self._extract_tags(instance.get('Tags', []))
                    })
            
            logger.info(f"Identified {len(idle_instances)} idle instances")
            return idle_instances
            
        except Exception as e:
            logger.error(f"Failed to identify idle instances: {e}")
            return []
    
    def identify_underutilized_instances(
        self,
        lookback_days: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Identify underutilized EC2 instances.
        
        Args:
            lookback_days: Days to analyze (default: 14)
        
        Returns:
            List of underutilized instances
        """
        try:
            instances = self._get_all_instances()
            underutilized = []
            
            for instance in instances:
                if instance['State']['Name'] != 'running':
                    continue
                
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                utilization = self._get_instance_utilization(
                    instance_id,
                    lookback_days
                )
                
                # Check if underutilized (not idle, but low usage)
                if (utilization['cpu_avg'] < self.UNDERUTILIZED_CPU_THRESHOLD and
                    utilization['cpu_avg'] >= self.IDLE_CPU_THRESHOLD):
                    
                    # Suggest smaller instance type
                    recommended_type = self._suggest_rightsizing(
                        instance_type,
                        utilization['cpu_avg']
                    )
                    
                    current_cost = self._estimate_instance_cost(instance)
                    recommended_cost = self._estimate_cost_by_type(recommended_type)
                    
                    underutilized.append({
                        'instance_id': instance_id,
                        'instance_type': instance_type,
                        'recommended_instance_type': recommended_type,
                        'current_monthly_cost': current_cost,
                        'recommended_monthly_cost': recommended_cost,
                        'estimated_savings': current_cost - recommended_cost,
                        'utilization': utilization,
                        'tags': self._extract_tags(instance.get('Tags', []))
                    })
            
            logger.info(f"Identified {len(underutilized)} underutilized instances")
            return underutilized
            
        except Exception as e:
            logger.error(f"Failed to identify underutilized instances: {e}")
            return []
    
    def get_spot_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify instances eligible for spot migration.
        
        Returns:
            List of spot-eligible instances
        """
        try:
            instances = self._get_all_instances()
            spot_opportunities = []
            
            for instance in instances:
                if instance['State']['Name'] != 'running':
                    continue
                
                # Skip if already spot
                if instance.get('InstanceLifecycle') == 'spot':
                    continue
                
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                
                # Check if workload is suitable for spot
                tags = self._extract_tags(instance.get('Tags', []))
                workload_type = self._determine_workload_type(tags)
                
                if self._is_spot_eligible(workload_type):
                    current_cost = self._estimate_instance_cost(instance)
                    spot_cost = current_cost * 0.65  # Approximate 35% savings
                    
                    spot_opportunities.append({
                        'instance_id': instance_id,
                        'instance_type': instance_type,
                        'current_cost': current_cost,
                        'spot_cost': spot_cost,
                        'monthly_savings': current_cost - spot_cost,
                        'savings_percentage': 35.0,
                        'workload_type': workload_type,
                        'spot_eligible': True,
                        'interruption_rate': '< 5%',  # Would need historical data
                        'tags': tags
                    })
            
            logger.info(f"Identified {len(spot_opportunities)} spot opportunities")
            return spot_opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify spot opportunities: {e}")
            return []
    
    def get_ebs_costs(self) -> Dict[str, Any]:
        """
        Get EBS volume costs.
        
        Returns:
            EBS cost breakdown
        """
        try:
            volumes = self._get_all_volumes()
            
            total_cost = 0.0
            attached_cost = 0.0
            unattached_cost = 0.0
            unattached_volumes = []
            
            for volume in volumes:
                volume_id = volume['VolumeId']
                size_gb = volume['Size']
                volume_type = volume['VolumeType']
                state = volume['State']
                
                # Estimate cost (rough approximation)
                monthly_cost = self._estimate_volume_cost(size_gb, volume_type)
                total_cost += monthly_cost
                
                if state == 'available':  # Unattached
                    unattached_cost += monthly_cost
                    unattached_volumes.append({
                        'volume_id': volume_id,
                        'size_gb': size_gb,
                        'volume_type': volume_type,
                        'monthly_cost': monthly_cost,
                        'create_time': volume.get('CreateTime').isoformat() if volume.get('CreateTime') else None
                    })
                else:
                    attached_cost += monthly_cost
            
            return {
                'total_ebs_cost': round(total_cost, 2),
                'attached_cost': round(attached_cost, 2),
                'unattached_cost': round(unattached_cost, 2),
                'unattached_count': len(unattached_volumes),
                'unattached_volumes': unattached_volumes
            }
            
        except Exception as e:
            logger.error(f"Failed to get EBS costs: {e}")
            return {}
    
    def _get_all_instances(self) -> List[Dict[str, Any]]:
        """Get all EC2 instances in region"""
        try:
            self.log_api_call('ec2', 'DescribeInstances')
            
            instances = self.paginate_results(
                self.ec2_client,
                'describe_instances',
                'Reservations'
            )
            
            # Flatten reservations to instances
            all_instances = []
            for reservation in instances:
                all_instances.extend(reservation.get('Instances', []))
            
            return all_instances
            
        except Exception as e:
            logger.error(f"Failed to get instances: {e}")
            return []
    
    def _get_all_volumes(self) -> List[Dict[str, Any]]:
        """Get all EBS volumes in region"""
        try:
            self.log_api_call('ec2', 'DescribeVolumes')
            
            response = self.ec2_client.describe_volumes()
            return response.get('Volumes', [])
            
        except Exception as e:
            logger.error(f"Failed to get volumes: {e}")
            return []
    
    def _get_instance_utilization(
        self,
        instance_id: str,
        lookback_days: int = 14
    ) -> Dict[str, float]:
        """
        Get instance utilization metrics from CloudWatch.
        
        Args:
            instance_id: EC2 instance ID
            lookback_days: Days to analyze
        
        Returns:
            Utilization metrics
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)
            
            # Get CPU utilization
            cpu_stats = self._get_cloudwatch_metric(
                instance_id,
                'CPUUtilization',
                start_time,
                end_time
            )
            
            # Get network in/out
            network_in = self._get_cloudwatch_metric(
                instance_id,
                'NetworkIn',
                start_time,
                end_time
            )
            
            network_out = self._get_cloudwatch_metric(
                instance_id,
                'NetworkOut',
                start_time,
                end_time
            )
            
            # Calculate averages
            cpu_avg = cpu_stats.get('Average', 0.0)
            network_mb_day = (
                (network_in.get('Average', 0.0) + network_out.get('Average', 0.0))
                / (1024 * 1024)  # Convert to MB
            )
            
            return {
                'cpu_avg': round(cpu_avg, 2),
                'cpu_max': round(cpu_stats.get('Maximum', 0.0), 2),
                'network_mb_day': round(network_mb_day, 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get utilization for {instance_id}: {e}")
            return {
                'cpu_avg': 0.0,
                'cpu_max': 0.0,
                'network_mb_day': 0.0
            }
    
    def _get_cloudwatch_metric(
        self,
        instance_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Get CloudWatch metric statistics"""
        try:
            self.log_api_call('cloudwatch', 'GetMetricStatistics')
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average', 'Maximum']
            )
            
            datapoints = response.get('Datapoints', [])
            
            if not datapoints:
                return {'Average': 0.0, 'Maximum': 0.0}
            
            # Calculate average across all datapoints
            avg = sum(d['Average'] for d in datapoints) / len(datapoints)
            max_val = max(d['Maximum'] for d in datapoints)
            
            return {
                'Average': avg,
                'Maximum': max_val
            }
            
        except Exception as e:
            logger.warning(f"Failed to get CloudWatch metric {metric_name}: {e}")
            return {'Average': 0.0, 'Maximum': 0.0}
    
    def _estimate_instance_cost(self, instance: Dict[str, Any]) -> float:
        """Estimate monthly cost for instance (simplified)"""
        instance_type = instance['InstanceType']
        return self._estimate_cost_by_type(instance_type)
    
    def _estimate_cost_by_type(self, instance_type: str) -> float:
        """
        Estimate monthly cost by instance type.
        This is a simplified estimation. In production, use AWS Pricing API.
        """
        # Rough pricing estimates (on-demand, us-east-1)
        pricing = {
            't3.micro': 7.5,
            't3.small': 15.0,
            't3.medium': 30.0,
            't3.large': 60.0,
            't3.xlarge': 120.0,
            'm5.large': 70.0,
            'm5.xlarge': 140.0,
            'm5.2xlarge': 280.0,
            'm5.4xlarge': 560.0,
            'c5.large': 62.0,
            'c5.xlarge': 124.0,
            'c5.2xlarge': 248.0,
            'r5.large': 91.0,
            'r5.xlarge': 182.0,
            'r5.2xlarge': 364.0,
        }
        
        return pricing.get(instance_type, 100.0)  # Default estimate
    
    def _estimate_volume_cost(self, size_gb: int, volume_type: str) -> float:
        """Estimate monthly cost for EBS volume"""
        # Rough pricing (per GB per month)
        pricing_per_gb = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.015,
            'standard': 0.05
        }
        
        price_per_gb = pricing_per_gb.get(volume_type, 0.10)
        return size_gb * price_per_gb
    
    def _analyze_instance(
        self,
        instance_data: Dict[str, Any],
        utilization: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze instance for optimization opportunities"""
        cpu_avg = utilization['cpu_avg']
        network_mb = utilization['network_mb_day']
        
        # Check if idle
        is_idle = (cpu_avg < self.IDLE_CPU_THRESHOLD and
                   network_mb < self.IDLE_NETWORK_THRESHOLD)
        
        # Check if underutilized
        is_underutilized = (cpu_avg < self.UNDERUTILIZED_CPU_THRESHOLD and
                           not is_idle)
        
        # Check spot eligibility
        tags = instance_data.get('tags', {})
        workload_type = self._determine_workload_type(tags)
        spot_eligible = self._is_spot_eligible(workload_type)
        
        # Rightsizing recommendation
        rightsizing_rec = None
        estimated_savings = 0.0
        
        if is_underutilized:
            current_type = instance_data['instance_type']
            recommended_type = self._suggest_rightsizing(current_type, cpu_avg)
            current_cost = instance_data['monthly_cost']
            recommended_cost = self._estimate_cost_by_type(recommended_type)
            
            rightsizing_rec = recommended_type
            estimated_savings = current_cost - recommended_cost
        
        return {
            'is_idle': is_idle,
            'is_underutilized': is_underutilized,
            'spot_eligible': spot_eligible,
            'rightsizing_recommendation': rightsizing_rec,
            'estimated_savings': round(estimated_savings, 2)
        }
    
    def _suggest_rightsizing(self, instance_type: str, cpu_avg: float) -> str:
        """Suggest smaller instance type based on utilization"""
        # Simple logic: if CPU < 10%, go down 2 sizes; if < 20%, go down 1 size
        family = instance_type.split('.')[0]  # e.g., 'm5' from 'm5.2xlarge'
        size = instance_type.split('.')[1] if '.' in instance_type else 'large'
        
        size_order = ['nano', 'micro', 'small', 'medium', 'large', 'xlarge', '2xlarge', '4xlarge', '8xlarge']
        
        try:
            current_index = size_order.index(size)
            
            if cpu_avg < 10:
                new_index = max(0, current_index - 2)
            else:
                new_index = max(0, current_index - 1)
            
            return f"{family}.{size_order[new_index]}"
        except (ValueError, IndexError):
            return instance_type  # Return original if can't determine
    
    def _determine_workload_type(self, tags: Dict[str, str]) -> str:
        """Determine workload type from tags"""
        # Check common tag patterns
        env = tags.get('Environment', '').lower()
        workload = tags.get('Workload', '').lower()
        
        if 'batch' in workload or 'processing' in workload:
            return 'batch_processing'
        elif 'dev' in env or 'test' in env:
            return 'development'
        elif 'prod' in env:
            return 'production'
        else:
            return 'unknown'
    
    def _is_spot_eligible(self, workload_type: str) -> bool:
        """Determine if workload is suitable for spot instances"""
        spot_suitable = ['batch_processing', 'development', 'testing']
        return workload_type in spot_suitable
    
    def _extract_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """Convert AWS tag format to dict"""
        return {tag['Key']: tag['Value'] for tag in tags}

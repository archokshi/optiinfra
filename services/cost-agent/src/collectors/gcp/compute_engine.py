"""
GCP Compute Engine Cost Collector

Collects GCE instance costs, identifies idle and underutilized instances,
and finds preemptible migration opportunities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google.cloud import compute_v1
from google.cloud import monitoring_v3

from src.collectors.gcp.base import GCPBaseCollector

logger = logging.getLogger(__name__)


class ComputeEngineCostCollector(GCPBaseCollector):
    """Collector for Compute Engine instance costs and optimization opportunities"""
    
    # Thresholds for idle/underutilized detection
    IDLE_CPU_THRESHOLD = 5.0  # CPU < 5% = idle
    IDLE_NETWORK_THRESHOLD = 1.0  # Network < 1GB/day = idle
    UNDERUTILIZED_CPU_THRESHOLD = 20.0  # CPU < 20% = underutilized
    
    def __init__(self, **kwargs):
        """Initialize Compute Engine cost collector"""
        super().__init__(**kwargs)
        self.compute_client = self.get_client(compute_v1.InstancesClient)
        self.monitoring_client = self.get_client(monitoring_v3.MetricServiceClient)
    
    def collect_instance_costs(
        self,
        include_utilization: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect per-instance cost breakdown.
        
        Args:
            include_utilization: Include Cloud Monitoring metrics
        
        Returns:
            List of instance cost data
        """
        try:
            # Get all instances across all zones
            instances = self._get_all_instances()
            logger.info(f"Found {len(instances)} GCE instances")
            
            instance_costs = []
            
            for instance in instances:
                instance_name = instance.name
                machine_type = instance.machine_type.split('/')[-1]
                zone = instance.zone.split('/')[-1]
                status = instance.status
                
                # Skip terminated instances
                if status == 'TERMINATED':
                    continue
                
                # Estimate instance cost
                monthly_cost = self._estimate_instance_cost(instance)
                
                instance_data = {
                    'instance_id': str(instance.id),
                    'instance_name': instance_name,
                    'machine_type': machine_type,
                    'zone': zone,
                    'region': '-'.join(zone.split('-')[:-1]),
                    'status': status,
                    'monthly_cost': monthly_cost,
                    'preemptible': instance.scheduling.preemptible,
                    'labels': self._extract_labels(instance.labels)
                }
                
                # Add utilization metrics if requested
                if include_utilization and status == 'RUNNING':
                    utilization = self._get_instance_utilization(instance_name, zone)
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
        Identify idle GCE instances.
        
        Args:
            lookback_days: Days to analyze (default: 14)
        
        Returns:
            List of idle instances
        """
        try:
            instances = self._get_all_instances()
            idle_instances = []
            
            for instance in instances:
                if instance.status != 'RUNNING':
                    continue
                
                instance_name = instance.name
                zone = instance.zone.split('/')[-1]
                
                utilization = self._get_instance_utilization(
                    instance_name,
                    zone,
                    lookback_days
                )
                
                # Check if idle
                if (utilization['cpu_avg'] < self.IDLE_CPU_THRESHOLD and
                    utilization['network_gb_day'] < self.IDLE_NETWORK_THRESHOLD):
                    
                    idle_instances.append({
                        'instance_id': str(instance.id),
                        'instance_name': instance_name,
                        'machine_type': instance.machine_type.split('/')[-1],
                        'zone': zone,
                        'monthly_cost': self._estimate_instance_cost(instance),
                        'utilization': utilization,
                        'idle_duration_days': lookback_days,
                        'recommendation': 'terminate',
                        'labels': self._extract_labels(instance.labels)
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
        Identify underutilized GCE instances.
        
        Args:
            lookback_days: Days to analyze (default: 14)
        
        Returns:
            List of underutilized instances
        """
        try:
            instances = self._get_all_instances()
            underutilized = []
            
            for instance in instances:
                if instance.status != 'RUNNING':
                    continue
                
                instance_name = instance.name
                zone = instance.zone.split('/')[-1]
                machine_type = instance.machine_type.split('/')[-1]
                
                utilization = self._get_instance_utilization(
                    instance_name,
                    zone,
                    lookback_days
                )
                
                # Check if underutilized (not idle, but low usage)
                if (utilization['cpu_avg'] < self.UNDERUTILIZED_CPU_THRESHOLD and
                    utilization['cpu_avg'] >= self.IDLE_CPU_THRESHOLD):
                    
                    # Suggest smaller machine type
                    recommended_type = self._suggest_rightsizing(
                        machine_type,
                        utilization['cpu_avg']
                    )
                    
                    current_cost = self._estimate_instance_cost(instance)
                    recommended_cost = self._estimate_cost_by_type(recommended_type)
                    
                    underutilized.append({
                        'instance_id': str(instance.id),
                        'instance_name': instance_name,
                        'machine_type': machine_type,
                        'recommended_machine_type': recommended_type,
                        'zone': zone,
                        'current_monthly_cost': current_cost,
                        'recommended_monthly_cost': recommended_cost,
                        'estimated_savings': current_cost - recommended_cost,
                        'utilization': utilization,
                        'labels': self._extract_labels(instance.labels)
                    })
            
            logger.info(f"Identified {len(underutilized)} underutilized instances")
            return underutilized
            
        except Exception as e:
            logger.error(f"Failed to identify underutilized instances: {e}")
            return []
    
    def get_preemptible_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify instances eligible for preemptible migration.
        
        Returns:
            List of preemptible-eligible instances
        """
        try:
            instances = self._get_all_instances()
            preemptible_opportunities = []
            
            for instance in instances:
                if instance.status != 'RUNNING':
                    continue
                
                # Skip if already preemptible
                if instance.scheduling.preemptible:
                    continue
                
                instance_name = instance.name
                machine_type = instance.machine_type.split('/')[-1]
                zone = instance.zone.split('/')[-1]
                
                # Check if workload is suitable for preemptible
                labels = self._extract_labels(instance.labels)
                workload_type = self._determine_workload_type(labels)
                
                if self._is_preemptible_eligible(workload_type):
                    current_cost = self._estimate_instance_cost(instance)
                    preemptible_cost = current_cost * 0.20  # Preemptible saves ~80%
                    
                    preemptible_opportunities.append({
                        'instance_id': str(instance.id),
                        'instance_name': instance_name,
                        'machine_type': machine_type,
                        'zone': zone,
                        'current_cost': current_cost,
                        'preemptible_cost': preemptible_cost,
                        'monthly_savings': current_cost - preemptible_cost,
                        'savings_percentage': 80.0,
                        'workload_type': workload_type,
                        'preemptible_eligible': True,
                        'labels': labels
                    })
            
            logger.info(f"Identified {len(preemptible_opportunities)} preemptible opportunities")
            return preemptible_opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify preemptible opportunities: {e}")
            return []
    
    def get_persistent_disk_costs(self) -> Dict[str, Any]:
        """
        Get persistent disk costs.
        
        Returns:
            Disk cost breakdown
        """
        try:
            disks_client = self.get_client(compute_v1.DisksClient)
            
            # Get all disks across all zones
            all_disks = []
            zones = self._get_all_zones()
            
            for zone in zones:
                request = compute_v1.ListDisksRequest(
                    project=self.project_id,
                    zone=zone
                )
                disks = list(disks_client.list(request=request))
                all_disks.extend(disks)
            
            total_cost = 0.0
            attached_cost = 0.0
            unattached_cost = 0.0
            unattached_disks = []
            
            for disk in all_disks:
                size_gb = disk.size_gb
                disk_type = disk.type.split('/')[-1]
                
                # Estimate cost
                monthly_cost = self._estimate_disk_cost(size_gb, disk_type)
                total_cost += monthly_cost
                
                if not disk.users:  # Unattached
                    unattached_cost += monthly_cost
                    unattached_disks.append({
                        'disk_name': disk.name,
                        'size_gb': size_gb,
                        'disk_type': disk_type,
                        'zone': disk.zone.split('/')[-1],
                        'monthly_cost': monthly_cost
                    })
                else:
                    attached_cost += monthly_cost
            
            return {
                'total_disk_cost': round(total_cost, 2),
                'attached_cost': round(attached_cost, 2),
                'unattached_cost': round(unattached_cost, 2),
                'unattached_count': len(unattached_disks),
                'unattached_disks': unattached_disks
            }
            
        except Exception as e:
            logger.error(f"Failed to get disk costs: {e}")
            return {}
    
    def _get_all_instances(self) -> List[Any]:
        """Get all GCE instances across all zones"""
        try:
            all_instances = []
            zones = self._get_all_zones()
            
            for zone in zones:
                request = compute_v1.ListInstancesRequest(
                    project=self.project_id,
                    zone=zone
                )
                instances = list(self.compute_client.list(request=request))
                all_instances.extend(instances)
            
            return all_instances
            
        except Exception as e:
            logger.error(f"Failed to get instances: {e}")
            return []
    
    def _get_all_zones(self) -> List[str]:
        """Get all available zones"""
        try:
            zones_client = self.get_client(compute_v1.ZonesClient)
            request = compute_v1.ListZonesRequest(project=self.project_id)
            zones = list(zones_client.list(request=request))
            return [zone.name for zone in zones if zone.status == 'UP']
        except Exception as e:
            logger.warning(f"Failed to list zones: {e}")
            return ['us-central1-a']  # Fallback
    
    def _get_instance_utilization(
        self,
        instance_name: str,
        zone: str,
        lookback_days: int = 14
    ) -> Dict[str, float]:
        """
        Get instance utilization metrics from Cloud Monitoring.
        
        Args:
            instance_name: Instance name
            zone: Zone
            lookback_days: Days to analyze
        
        Returns:
            Utilization metrics
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)
            
            # Get CPU utilization
            cpu_stats = self._get_monitoring_metric(
                instance_name,
                zone,
                'compute.googleapis.com/instance/cpu/utilization',
                start_time,
                end_time
            )
            
            # Get network sent/received
            network_sent = self._get_monitoring_metric(
                instance_name,
                zone,
                'compute.googleapis.com/instance/network/sent_bytes_count',
                start_time,
                end_time
            )
            
            network_received = self._get_monitoring_metric(
                instance_name,
                zone,
                'compute.googleapis.com/instance/network/received_bytes_count',
                start_time,
                end_time
            )
            
            # Calculate averages
            cpu_avg = cpu_stats.get('average', 0.0) * 100  # Convert to percentage
            network_gb_day = (
                (network_sent.get('average', 0.0) + network_received.get('average', 0.0))
                / (1024**3)  # Convert to GB
            )
            
            return {
                'cpu_avg': round(cpu_avg, 2),
                'cpu_max': round(cpu_stats.get('maximum', 0.0) * 100, 2),
                'network_gb_day': round(network_gb_day, 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get utilization for {instance_name}: {e}")
            return {
                'cpu_avg': 0.0,
                'cpu_max': 0.0,
                'network_gb_day': 0.0
            }
    
    def _get_monitoring_metric(
        self,
        instance_name: str,
        zone: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Get Cloud Monitoring metric statistics"""
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
                f'AND resource.labels.instance_id = "{instance_name}" '
                f'AND resource.labels.zone = "{zone}"'
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
                return {'average': 0.0, 'maximum': 0.0}
            
            return {
                'average': sum(values) / len(values),
                'maximum': max(values)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get monitoring metric {metric_type}: {e}")
            return {'average': 0.0, 'maximum': 0.0}
    
    def _estimate_instance_cost(self, instance: Any) -> float:
        """Estimate monthly cost for instance"""
        machine_type = instance.machine_type.split('/')[-1]
        is_preemptible = instance.scheduling.preemptible
        
        base_cost = self._estimate_cost_by_type(machine_type)
        
        if is_preemptible:
            return base_cost * 0.20  # Preemptible is ~80% cheaper
        
        return base_cost
    
    def _estimate_cost_by_type(self, machine_type: str) -> float:
        """Estimate monthly cost by machine type (simplified)"""
        # Rough pricing estimates (on-demand, us-central1)
        pricing = {
            'e2-micro': 6.0,
            'e2-small': 12.0,
            'e2-medium': 24.0,
            'n1-standard-1': 25.0,
            'n1-standard-2': 50.0,
            'n1-standard-4': 100.0,
            'n2-standard-2': 65.0,
            'n2-standard-4': 130.0,
            'n2-standard-8': 260.0,
            'c2-standard-4': 145.0,
            'c2-standard-8': 290.0,
        }
        
        return pricing.get(machine_type, 100.0)
    
    def _estimate_disk_cost(self, size_gb: int, disk_type: str) -> float:
        """Estimate monthly cost for persistent disk"""
        # Rough pricing (per GB per month)
        pricing_per_gb = {
            'pd-standard': 0.040,
            'pd-balanced': 0.100,
            'pd-ssd': 0.170,
            'pd-extreme': 0.125,
        }
        
        price_per_gb = pricing_per_gb.get(disk_type, 0.100)
        return size_gb * price_per_gb
    
    def _analyze_instance(
        self,
        instance_data: Dict[str, Any],
        utilization: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze instance for optimization opportunities"""
        cpu_avg = utilization['cpu_avg']
        network_gb = utilization['network_gb_day']
        
        is_idle = (cpu_avg < self.IDLE_CPU_THRESHOLD and
                   network_gb < self.IDLE_NETWORK_THRESHOLD)
        
        is_underutilized = (cpu_avg < self.UNDERUTILIZED_CPU_THRESHOLD and
                           not is_idle)
        
        labels = instance_data.get('labels', {})
        workload_type = self._determine_workload_type(labels)
        preemptible_eligible = self._is_preemptible_eligible(workload_type)
        
        rightsizing_rec = None
        estimated_savings = 0.0
        
        if is_underutilized:
            current_type = instance_data['machine_type']
            recommended_type = self._suggest_rightsizing(current_type, cpu_avg)
            current_cost = instance_data['monthly_cost']
            recommended_cost = self._estimate_cost_by_type(recommended_type)
            
            rightsizing_rec = recommended_type
            estimated_savings = current_cost - recommended_cost
        
        return {
            'is_idle': is_idle,
            'is_underutilized': is_underutilized,
            'preemptible_eligible': preemptible_eligible,
            'rightsizing_recommendation': rightsizing_rec,
            'estimated_savings': round(estimated_savings, 2)
        }
    
    def _suggest_rightsizing(self, machine_type: str, cpu_avg: float) -> str:
        """Suggest smaller machine type based on utilization"""
        # Extract family and size
        parts = machine_type.split('-')
        if len(parts) < 2:
            return machine_type
        
        family = parts[0]  # e.g., 'n2'
        size = parts[-1]   # e.g., '4'
        
        try:
            current_size = int(size)
            
            if cpu_avg < 10:
                new_size = max(1, current_size // 4)
            else:
                new_size = max(1, current_size // 2)
            
            return f"{family}-standard-{new_size}"
        except ValueError:
            return machine_type
    
    def _determine_workload_type(self, labels: Dict[str, str]) -> str:
        """Determine workload type from labels"""
        env = labels.get('environment', '').lower()
        workload = labels.get('workload', '').lower()
        
        if 'batch' in workload or 'processing' in workload:
            return 'batch_processing'
        elif 'dev' in env or 'test' in env:
            return 'development'
        elif 'prod' in env:
            return 'production'
        else:
            return 'unknown'
    
    def _is_preemptible_eligible(self, workload_type: str) -> bool:
        """Determine if workload is suitable for preemptible instances"""
        preemptible_suitable = ['batch_processing', 'development', 'testing']
        return workload_type in preemptible_suitable

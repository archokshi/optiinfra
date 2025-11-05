"""
GCP Cloud SQL Cost Collector

Collects Cloud SQL database costs and identifies idle/underutilized databases.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from google.cloud import monitoring_v3

try:
    from google.cloud.sql.v1 import SqlInstancesServiceClient
except ImportError as exc:  # pragma: no cover - optional dependency
    SqlInstancesServiceClient = None  # type: ignore
    _sql_client_import_error = exc
else:
    _sql_client_import_error = None

from src.collectors.gcp.base import GCPBaseCollector

logger = logging.getLogger(__name__)


class CloudSQLCostCollector(GCPBaseCollector):
    """Collector for Cloud SQL database costs and optimization opportunities"""
    
    IDLE_CONNECTIONS_THRESHOLD = 1.0  # Connections < 1 = idle
    
    def __init__(self, **kwargs):
        """Initialize Cloud SQL cost collector"""
        super().__init__(**kwargs)
        if SqlInstancesServiceClient is None:
            logger.warning(
                "google-cloud-sql not installed; Cloud SQL metrics disabled: %s",
                _sql_client_import_error,
            )
            self.sql_client = None
        else:
            self.sql_client = self.get_client(SqlInstancesServiceClient)
        self.monitoring_client = self.get_client(monitoring_v3.MetricServiceClient)
    
    def collect_sql_costs(
        self,
        include_utilization: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect per-instance Cloud SQL costs.
        
        Args:
            include_utilization: Include Cloud Monitoring metrics
        
        Returns:
            List of Cloud SQL instance cost data
        """
        try:
            instances = self._get_all_sql_instances()
            logger.info(f"Found {len(instances)} Cloud SQL instances")
            
            sql_costs = []
            
            for instance in instances:
                instance_name = instance.name
                tier = instance.settings.tier
                database_version = instance.database_version
                state = instance.state.name
                
                # Estimate cost
                monthly_cost = self._estimate_sql_cost(instance)
                
                instance_data = {
                    'instance_name': instance_name,
                    'tier': tier,
                    'database_version': database_version,
                    'state': state,
                    'region': instance.region,
                    'availability_type': instance.settings.availability_type.name,
                    'storage_gb': instance.settings.data_disk_size_gb,
                    'monthly_cost': monthly_cost
                }
                
                # Add utilization if requested
                if include_utilization and state == 'RUNNABLE':
                    utilization = self._get_sql_utilization(instance_name)
                    instance_data['utilization'] = utilization
                    instance_data['optimization'] = self._analyze_sql_instance(
                        instance_data,
                        utilization
                    )
                
                sql_costs.append(instance_data)
            
            logger.info(f"Collected cost data for {len(sql_costs)} Cloud SQL instances")
            return sql_costs
            
        except Exception as e:
            logger.error(f"Failed to collect Cloud SQL costs: {e}")
            raise
    
    def identify_idle_databases(
        self,
        lookback_days: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Identify idle Cloud SQL databases.
        
        Args:
            lookback_days: Days to analyze
        
        Returns:
            List of idle databases
        """
        try:
            instances = self._get_all_sql_instances()
            idle_databases = []
            
            for instance in instances:
                if instance.state.name != 'RUNNABLE':
                    continue
                
                instance_name = instance.name
                utilization = self._get_sql_utilization(instance_name, lookback_days)
                
                # Check if idle (no connections)
                if utilization['connections_avg'] < self.IDLE_CONNECTIONS_THRESHOLD:
                    idle_databases.append({
                        'instance_name': instance_name,
                        'tier': instance.settings.tier,
                        'database_version': instance.database_version,
                        'monthly_cost': self._estimate_sql_cost(instance),
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
        Analyze Cloud SQL storage costs.
        
        Returns:
            Storage cost breakdown
        """
        try:
            instances = self._get_all_sql_instances()
            
            total_storage_cost = 0.0
            total_backup_cost = 0.0
            
            for instance in instances:
                storage_gb = instance.settings.data_disk_size_gb
                
                # Storage cost (simplified)
                storage_cost = storage_gb * 0.17  # $0.17 per GB/month (SSD)
                total_storage_cost += storage_cost
                
                # Backup cost (estimate)
                backup_cost = storage_gb * 0.08  # Approximate
                total_backup_cost += backup_cost
            
            return {
                'total_storage_cost': round(total_storage_cost, 2),
                'total_backup_cost': round(total_backup_cost, 2),
                'total_cost': round(total_storage_cost + total_backup_cost, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze storage costs: {e}")
            return {}
    
    def identify_high_availability_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify databases that could be converted to zonal (from regional).
        
        Returns:
            List of HA conversion opportunities
        """
        try:
            instances = self._get_all_sql_instances()
            opportunities = []
            
            for instance in instances:
                # Check if regional (high availability)
                if instance.settings.availability_type.name == 'REGIONAL':
                    # Check labels for environment
                    labels = instance.settings.user_labels
                    env = labels.get('environment', '').lower() if labels else ''
                    
                    if env in ['dev', 'development', 'test', 'staging']:
                        current_cost = self._estimate_sql_cost(instance)
                        zonal_cost = current_cost * 0.5  # Regional is ~2x cost
                        
                        opportunities.append({
                            'instance_name': instance.name,
                            'environment': env,
                            'current_cost': current_cost,
                            'zonal_cost': zonal_cost,
                            'estimated_savings': current_cost - zonal_cost,
                            'recommendation': 'convert_to_zonal'
                        })
            
            logger.info(f"Identified {len(opportunities)} HA conversion opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify HA opportunities: {e}")
            return []
    
    def _get_all_sql_instances(self) -> List[Any]:
        """Get all Cloud SQL instances"""
        if self.sql_client is None:
            logger.debug("Cloud SQL client unavailable; skipping instance listing")
            return []
        try:
            from google.cloud.sql.v1 import ListInstancesRequest
            
            request = ListInstancesRequest(project=f"projects/{self.project_id}")
            
            self.log_api_call()
            response = self.sql_client.list(request=request)
            
            return list(response)
            
        except Exception as e:
            logger.error(f"Failed to get Cloud SQL instances: {e}")
            return []
    
    def _get_sql_utilization(
        self,
        instance_name: str,
        lookback_days: int = 14
    ) -> Dict[str, float]:
        """Get Cloud SQL utilization metrics from Cloud Monitoring"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)
            
            # Get database connections
            connections = self._get_monitoring_metric(
                instance_name,
                'cloudsql.googleapis.com/database/network/connections',
                start_time,
                end_time
            )
            
            # Get CPU utilization
            cpu = self._get_monitoring_metric(
                instance_name,
                'cloudsql.googleapis.com/database/cpu/utilization',
                start_time,
                end_time
            )
            
            # Get memory utilization
            memory = self._get_monitoring_metric(
                instance_name,
                'cloudsql.googleapis.com/database/memory/utilization',
                start_time,
                end_time
            )
            
            return {
                'connections_avg': round(connections.get('average', 0.0), 2),
                'connections_max': round(connections.get('maximum', 0.0), 2),
                'cpu_avg': round(cpu.get('average', 0.0) * 100, 2),
                'memory_avg': round(memory.get('average', 0.0) * 100, 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get utilization for {instance_name}: {e}")
            return {
                'connections_avg': 0.0,
                'connections_max': 0.0,
                'cpu_avg': 0.0,
                'memory_avg': 0.0
            }
    
    def _get_monitoring_metric(
        self,
        instance_name: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Get Cloud Monitoring metric statistics for Cloud SQL"""
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
                f'AND resource.labels.database_id = "{self.project_id}:{instance_name}"'
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
    
    def _estimate_sql_cost(self, instance: Any) -> float:
        """Estimate monthly cost for Cloud SQL instance"""
        tier = instance.settings.tier
        is_regional = instance.settings.availability_type.name == 'REGIONAL'
        storage_gb = instance.settings.data_disk_size_gb
        
        # Instance cost (simplified pricing)
        instance_cost = self._estimate_instance_cost_by_tier(tier)
        
        # Regional doubles the cost
        if is_regional:
            instance_cost *= 2
        
        # Storage cost
        storage_cost = storage_gb * 0.17  # $0.17 per GB/month (SSD)
        
        return round(instance_cost + storage_cost, 2)
    
    def _estimate_instance_cost_by_tier(self, tier: str) -> float:
        """Estimate monthly instance cost by tier"""
        # Rough pricing estimates (on-demand)
        pricing = {
            'db-f1-micro': 7.0,
            'db-g1-small': 25.0,
            'db-n1-standard-1': 50.0,
            'db-n1-standard-2': 100.0,
            'db-n1-standard-4': 200.0,
            'db-n1-highmem-2': 120.0,
            'db-n1-highmem-4': 240.0,
        }
        
        return pricing.get(tier, 100.0)
    
    def _analyze_sql_instance(
        self,
        instance_data: Dict[str, Any],
        utilization: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze Cloud SQL instance for optimization opportunities"""
        connections_avg = utilization['connections_avg']
        cpu_avg = utilization['cpu_avg']
        
        is_idle = connections_avg < self.IDLE_CONNECTIONS_THRESHOLD
        is_underutilized = cpu_avg < 20.0 and not is_idle
        
        return {
            'is_idle': is_idle,
            'is_underutilized': is_underutilized,
            'recommendation': 'terminate' if is_idle else ('downsize' if is_underutilized else 'none')
        }

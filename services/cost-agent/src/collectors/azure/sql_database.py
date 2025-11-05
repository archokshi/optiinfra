"""
Azure SQL Database Cost Collector

Collects SQL Database costs, utilization metrics, and identifies optimization opportunities.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from .base import AzureBaseCollector
from .cost_management_client import AzureCostManagementClient


class AzureSQLDatabaseCollector(AzureBaseCollector):
    """Collector for Azure SQL Database"""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        super().__init__(subscription_id, tenant_id, client_id, client_secret)
        self.sql_client = SqlManagementClient(self.credentials, subscription_id)
        self.monitor_client = MonitorManagementClient(self.credentials, subscription_id)
        self.cost_client = AzureCostManagementClient(subscription_id, tenant_id, client_id, client_secret)
        
        # Thresholds
        self.idle_connections_threshold = 1.0  # connections/day
        self.underutilized_dtu_threshold = 20.0  # %
        
        self.logger = logging.getLogger(__name__)
    
    async def collect_all(
        self,
        lookback_days: int = 30
    ) -> Dict:
        """
        Collect all SQL database data and costs
        
        Args:
            lookback_days: Days to look back for metrics
            
        Returns:
            Dictionary with database data, costs, and opportunities
        """
        start_date = datetime.utcnow() - timedelta(days=lookback_days)
        end_date = datetime.utcnow()
        
        self.logger.info(f"Collecting Azure SQL Database data for {lookback_days} days")
        
        # List all databases
        databases = await self._list_databases()
        self.logger.info(f"Found {len(databases)} SQL databases")
        
        # Collect costs and metrics for each database
        db_details = []
        for db in databases:
            try:
                db_data = await self._collect_database_data(
                    database=db,
                    start_date=start_date,
                    end_date=end_date
                )
                db_details.append(db_data)
            except Exception as e:
                self.logger.error(f"Failed to collect data for database {db['name']}: {str(e)}")
        
        # Calculate totals
        total_databases = len(db_details)
        total_cost = sum(db.get('monthly_cost', 0) for db in db_details)
        
        # Identify opportunities
        opportunities = self._identify_opportunities(db_details)
        
        return {
            "total_databases": total_databases,
            "total_monthly_cost": total_cost,
            "databases": db_details,
            "opportunities": opportunities,
            "collected_at": datetime.utcnow().isoformat()
        }
    
    async def _list_databases(self) -> List[Dict]:
        """List all SQL databases in subscription"""
        databases = []
        
        try:
            # List all SQL servers
            servers = await self._make_request(
                self.sql_client.servers,
                "list"
            )
            
            # For each server, list databases
            for server in servers:
                resource_group = self._get_resource_group_from_id(server.id)
                
                try:
                    dbs = await self._make_request(
                        self.sql_client.databases,
                        "list_by_server",
                        resource_group_name=resource_group,
                        server_name=server.name
                    )
                    
                    for db in dbs:
                        # Skip master database
                        if db.name.lower() != 'master':
                            databases.append({
                                "id": db.id,
                                "name": db.name,
                                "server_name": server.name,
                                "resource_group": resource_group,
                                "location": db.location,
                                "sku": db.sku.name if db.sku else "Unknown",
                                "tier": db.sku.tier if db.sku else "Unknown",
                                "capacity": db.sku.capacity if db.sku else 0,
                                "max_size_bytes": db.max_size_bytes,
                                "tags": db.tags or {}
                            })
                except Exception as e:
                    self.logger.error(f"Failed to list databases for server {server.name}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to list SQL servers: {str(e)}")
            raise
        
        return databases
    
    async def _collect_database_data(
        self,
        database: Dict,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Collect comprehensive data for a single database"""
        
        # Get costs
        monthly_cost = await self._get_database_costs(database['id'], start_date, end_date)
        
        # Get metrics
        metrics = await self._get_database_metrics(database['id'], start_date, end_date)
        
        # Analyze utilization
        utilization_analysis = self._analyze_database_utilization(database, metrics, monthly_cost)
        
        return {
            **database,
            "monthly_cost": monthly_cost,
            "metrics": metrics,
            "utilization_analysis": utilization_analysis
        }
    
    async def _get_database_costs(
        self,
        database_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Get costs for specific database"""
        try:
            daily_costs = await self.cost_client.get_resource_costs(
                resource_id=database_id,
                start_date=start_date,
                end_date=end_date
            )
            
            total_cost = sum(day['cost'] for day in daily_costs)
            days = (end_date - start_date).days or 1
            monthly_cost = (total_cost / days) * 30
            
            return monthly_cost
        except Exception as e:
            self.logger.error(f"Failed to get costs for database {database_id}: {str(e)}")
            return 0.0
    
    async def _get_database_metrics(
        self,
        database_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get connection, DTU, storage metrics from Azure Monitor"""
        metrics_to_collect = {
            "connection_successful": "connections",
            "dtu_consumption_percent": "dtu_percent",
            "cpu_percent": "cpu_percent",
            "storage_percent": "storage_percent",
            "deadlock": "deadlocks"
        }
        
        collected_metrics = {}
        
        for metric_name, metric_key in metrics_to_collect.items():
            try:
                metric_data = await self._make_request(
                    self.monitor_client.metrics,
                    "list",
                    resource_uri=database_id,
                    timespan=f"{start_date.isoformat()}/{end_date.isoformat()}",
                    interval='PT1H',
                    metricnames=metric_name,
                    aggregation='Average,Maximum,Total'
                )
                
                values = []
                total = 0
                for item in metric_data.value:
                    for timeseries in item.timeseries:
                        for data in timeseries.data:
                            if data.average is not None:
                                values.append(data.average)
                            if data.total is not None:
                                total += data.total
                
                if values:
                    collected_metrics[metric_key] = {
                        "average": sum(values) / len(values),
                        "max": max(values),
                        "total": total
                    }
            except Exception as e:
                self.logger.warning(f"Failed to collect metric {metric_name}: {str(e)}")
        
        return collected_metrics
    
    def _analyze_database_utilization(
        self,
        database: Dict,
        metrics: Dict,
        monthly_cost: float
    ) -> Dict:
        """Analyze database utilization and identify issues"""
        analysis = {
            "is_idle": False,
            "is_underutilized": False,
            "recommendations": []
        }
        
        # Check if idle (no connections)
        if 'connections' in metrics:
            total_connections = metrics['connections'].get('total', 0)
            days = 30  # Approximate
            connections_per_day = total_connections / days
            
            if connections_per_day < self.idle_connections_threshold:
                analysis['is_idle'] = True
                analysis['recommendations'].append({
                    "type": "idle_database",
                    "reason": f"Database has {connections_per_day:.1f} connections/day (threshold: {self.idle_connections_threshold})",
                    "action": "Consider pausing or deleting this database",
                    "estimated_savings": monthly_cost * 0.95
                })
        
        # Check DTU/CPU utilization
        dtu_avg = None
        if 'dtu_percent' in metrics:
            dtu_avg = metrics['dtu_percent']['average']
        elif 'cpu_percent' in metrics:
            dtu_avg = metrics['cpu_percent']['average']
        
        if dtu_avg is not None and dtu_avg < self.underutilized_dtu_threshold:
            analysis['is_underutilized'] = True
            # Recommend tier downgrade
            current_tier = database.get('tier', 'Unknown')
            recommended_tier = self._recommend_lower_tier(current_tier, database.get('sku'))
            
            if recommended_tier:
                analysis['recommendations'].append({
                    "type": "tier_downgrade",
                    "reason": f"DTU/CPU utilization is {dtu_avg:.1f}% (threshold: {self.underutilized_dtu_threshold}%)",
                    "action": f"Downgrade from {database.get('sku')} to {recommended_tier}",
                    "estimated_savings": monthly_cost * 0.40
                })
        
        # Check for elastic pool opportunity
        if database.get('tier') in ['Standard', 'Premium'] and monthly_cost > 50:
            analysis['recommendations'].append({
                "type": "elastic_pool",
                "reason": "Database is suitable for elastic pool consolidation",
                "action": "Consider moving to elastic pool",
                "estimated_savings": monthly_cost * 0.25
            })
        
        return analysis
    
    def _recommend_lower_tier(self, current_tier: str, current_sku: str) -> Optional[str]:
        """Recommend a lower tier/SKU"""
        # Simplified tier downgrade mapping
        tier_map = {
            "S2": "S1",
            "S3": "S2",
            "S4": "S3",
            "P1": "S3",
            "P2": "P1",
            "P4": "P2"
        }
        
        return tier_map.get(current_sku)
    
    def _identify_opportunities(self, db_details: List[Dict]) -> List[Dict]:
        """Identify all optimization opportunities"""
        opportunities = []
        
        for db in db_details:
            if db.get('utilization_analysis', {}).get('recommendations'):
                for rec in db['utilization_analysis']['recommendations']:
                    opportunities.append({
                        "service": "SQL Database",
                        "resource_id": db['id'],
                        "resource_name": db['name'],
                        **rec
                    })
        
        return opportunities

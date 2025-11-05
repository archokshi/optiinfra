"""
Azure Metrics Storage

Stores Azure cost metrics in ClickHouse for time-series analysis.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from clickhouse_driver import Client


class AzureMetricsStorage:
    """Storage layer for Azure metrics in ClickHouse"""
    
    def __init__(self, clickhouse_client: Client):
        self.client = clickhouse_client
        self.logger = logging.getLogger(__name__)
    
    async def create_tables(self):
        """Create all Azure metrics tables"""
        tables = [
            self._create_cost_metrics_table(),
            self._create_vm_metrics_table(),
            self._create_sql_metrics_table(),
            self._create_function_metrics_table(),
            self._create_storage_metrics_table(),
            self._create_opportunities_table()
        ]
        
        for table_sql in tables:
            try:
                self.client.execute(table_sql)
                self.logger.info(f"Created table successfully")
            except Exception as e:
                self.logger.error(f"Failed to create table: {str(e)}")
    
    def _create_cost_metrics_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS cost_agent.azure_cost_metrics (
            date Date,
            subscription_id String,
            service String,
            resource_group String,
            location String,
            cost Float64,
            currency String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (subscription_id, service, date)
        """
    
    def _create_vm_metrics_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS cost_agent.azure_vm_metrics (
            date Date,
            subscription_id String,
            vm_id String,
            vm_name String,
            resource_group String,
            location String,
            vm_size String,
            power_state String,
            monthly_cost Float64,
            disk_cost Float64,
            cpu_avg Float64,
            memory_avg Float64,
            network_in_gb Float64,
            network_out_gb Float64,
            is_idle Boolean,
            is_underutilized Boolean,
            spot_eligible Boolean,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (subscription_id, vm_id, date)
        """
    
    def _create_sql_metrics_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS cost_agent.azure_sql_metrics (
            date Date,
            subscription_id String,
            database_id String,
            database_name String,
            server_name String,
            resource_group String,
            tier String,
            sku String,
            monthly_cost Float64,
            connections_avg Float64,
            dtu_avg Float64,
            storage_percent Float64,
            is_idle Boolean,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (subscription_id, database_id, date)
        """
    
    def _create_function_metrics_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS cost_agent.azure_function_metrics (
            date Date,
            subscription_id String,
            function_app_id String,
            function_app_name String,
            resource_group String,
            plan_type String,
            monthly_cost Float64,
            executions_total Int64,
            memory_avg Float64,
            is_over_provisioned Boolean,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (subscription_id, function_app_id, date)
        """
    
    def _create_storage_metrics_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS cost_agent.azure_storage_metrics (
            date Date,
            subscription_id String,
            storage_account_id String,
            storage_account_name String,
            resource_group String,
            sku String,
            monthly_cost Float64,
            capacity_gb Float64,
            transactions_total Int64,
            egress_gb Float64,
            has_lifecycle_policy Boolean,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (subscription_id, storage_account_id, date)
        """
    
    def _create_opportunities_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS cost_agent.azure_opportunities (
            date Date,
            subscription_id String,
            service String,
            opportunity_type String,
            resource_id String,
            resource_name String,
            estimated_savings Float64,
            priority String,
            confidence Float64,
            reason String,
            action String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (subscription_id, service, date, estimated_savings DESC)
        """
    
    async def store_cost_metrics(
        self,
        subscription_id: str,
        metrics: List[Dict]
    ):
        """Store daily cost metrics"""
        if not metrics:
            return
        
        data = [
            (
                metric['date'],
                subscription_id,
                metric.get('service', 'Unknown'),
                metric.get('resource_group', 'Unknown'),
                metric.get('location', 'Unknown'),
                metric.get('cost', 0.0),
                metric.get('currency', 'USD')
            )
            for metric in metrics
        ]
        
        try:
            self.client.execute(
                """
                INSERT INTO cost_agent.azure_cost_metrics 
                (date, subscription_id, service, resource_group, location, cost, currency)
                VALUES
                """,
                data
            )
            self.logger.info(f"Stored {len(data)} cost metrics")
        except Exception as e:
            self.logger.error(f"Failed to store cost metrics: {str(e)}")
    
    async def store_vm_metrics(
        self,
        subscription_id: str,
        vms: List[Dict]
    ):
        """Store VM metrics"""
        if not vms:
            return
        
        data = [
            (
                datetime.utcnow().date(),
                subscription_id,
                vm['id'],
                vm['name'],
                vm.get('resource_group', 'Unknown'),
                vm.get('location', 'Unknown'),
                vm.get('vm_size', 'Unknown'),
                vm.get('power_state', 'unknown'),
                vm.get('monthly_cost', 0.0),
                vm.get('disk_cost', 0.0),
                vm.get('metrics', {}).get('cpu', {}).get('average', 0.0),
                vm.get('metrics', {}).get('memory', {}).get('average', 0.0),
                vm.get('metrics', {}).get('network_in', {}).get('total', 0.0) / (1024**3),  # Convert to GB
                vm.get('metrics', {}).get('network_out', {}).get('total', 0.0) / (1024**3),
                vm.get('utilization_analysis', {}).get('is_idle', False),
                vm.get('utilization_analysis', {}).get('is_underutilized', False),
                vm.get('utilization_analysis', {}).get('spot_eligible', False)
            )
            for vm in vms
        ]
        
        try:
            self.client.execute(
                """
                INSERT INTO cost_agent.azure_vm_metrics 
                (date, subscription_id, vm_id, vm_name, resource_group, location, vm_size, 
                 power_state, monthly_cost, disk_cost, cpu_avg, memory_avg, network_in_gb, 
                 network_out_gb, is_idle, is_underutilized, spot_eligible)
                VALUES
                """,
                data
            )
            self.logger.info(f"Stored {len(data)} VM metrics")
        except Exception as e:
            self.logger.error(f"Failed to store VM metrics: {str(e)}")
    
    async def store_opportunities(
        self,
        subscription_id: str,
        opportunities: List[Dict]
    ):
        """Store optimization opportunities"""
        if not opportunities:
            return
        
        data = [
            (
                datetime.utcnow().date(),
                subscription_id,
                opp.get('service', 'Unknown'),
                opp.get('type', 'Unknown'),
                opp.get('resource_id', ''),
                opp.get('resource_name', ''),
                opp.get('estimated_savings', 0.0),
                opp.get('priority', 'low'),
                opp.get('confidence', 0.0),
                opp.get('reason', ''),
                opp.get('action', '')
            )
            for opp in opportunities
        ]
        
        try:
            self.client.execute(
                """
                INSERT INTO cost_agent.azure_opportunities 
                (date, subscription_id, service, opportunity_type, resource_id, resource_name,
                 estimated_savings, priority, confidence, reason, action)
                VALUES
                """,
                data
            )
            self.logger.info(f"Stored {len(data)} opportunities")
        except Exception as e:
            self.logger.error(f"Failed to store opportunities: {str(e)}")
    
    async def query_costs(
        self,
        subscription_id: str,
        start_date: datetime,
        end_date: datetime,
        service: Optional[str] = None
    ) -> List[Dict]:
        """Query cost metrics"""
        query = """
        SELECT date, service, resource_group, location, SUM(cost) as total_cost
        FROM cost_agent.azure_cost_metrics
        WHERE subscription_id = %(subscription_id)s
          AND date >= %(start_date)s
          AND date <= %(end_date)s
        """
        
        params = {
            'subscription_id': subscription_id,
            'start_date': start_date.date(),
            'end_date': end_date.date()
        }
        
        if service:
            query += " AND service = %(service)s"
            params['service'] = service
        
        query += " GROUP BY date, service, resource_group, location ORDER BY date DESC"
        
        try:
            result = self.client.execute(query, params)
            return [
                {
                    "date": row[0].isoformat(),
                    "service": row[1],
                    "resource_group": row[2],
                    "location": row[3],
                    "cost": row[4]
                }
                for row in result
            ]
        except Exception as e:
            self.logger.error(f"Failed to query costs: {str(e)}")
            return []
    
    async def query_opportunities(
        self,
        subscription_id: str,
        min_savings: float = 0,
        limit: int = 100
    ) -> List[Dict]:
        """Query optimization opportunities"""
        query = """
        SELECT service, opportunity_type, resource_name, estimated_savings, 
               priority, confidence, reason, action
        FROM cost_agent.azure_opportunities
        WHERE subscription_id = %(subscription_id)s
          AND date = today()
          AND estimated_savings >= %(min_savings)s
        ORDER BY estimated_savings DESC
        LIMIT %(limit)s
        """
        
        params = {
            'subscription_id': subscription_id,
            'min_savings': min_savings,
            'limit': limit
        }
        
        try:
            result = self.client.execute(query, params)
            return [
                {
                    "service": row[0],
                    "type": row[1],
                    "resource_name": row[2],
                    "estimated_savings": row[3],
                    "priority": row[4],
                    "confidence": row[5],
                    "reason": row[6],
                    "action": row[7]
                }
                for row in result
            ]
        except Exception as e:
            self.logger.error(f"Failed to query opportunities: {str(e)}")
            return []

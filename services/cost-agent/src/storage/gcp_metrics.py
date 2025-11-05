"""
GCP Metrics Storage

ClickHouse storage layer for GCP cost metrics and optimization opportunities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from clickhouse_driver import Client

logger = logging.getLogger(__name__)


class GCPMetricsStorage:
    """Storage layer for GCP cost metrics in ClickHouse"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 9000,
        database: str = 'cost_agent',
        **kwargs
    ):
        """
        Initialize GCP metrics storage.
        
        Args:
            host: ClickHouse host
            port: ClickHouse port
            database: Database name
            **kwargs: Additional ClickHouse client arguments
        """
        self.client = Client(host=host, port=port, **kwargs)
        self.database = database
        
        # Create tables if they don't exist
        self._create_tables()
        
        logger.info(f"Initialized GCP metrics storage: {host}:{port}/{database}")
    
    def _create_tables(self):
        """Create ClickHouse tables for GCP metrics"""
        
        # GCP cost metrics table
        self.client.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.database}.gcp_cost_metrics (
            timestamp DateTime,
            project_id String,
            service String,
            region String,
            cost Float64,
            currency String DEFAULT 'USD',
            date Date
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (project_id, service, timestamp)
        """)
        
        # GCP Compute Engine instance metrics
        self.client.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.database}.gcp_compute_metrics (
            timestamp DateTime,
            project_id String,
            instance_id String,
            instance_name String,
            machine_type String,
            zone String,
            region String,
            status String,
            cpu_avg Float64,
            cpu_max Float64,
            network_gb_day Float64,
            monthly_cost Float64,
            preemptible UInt8,
            date Date
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (project_id, instance_id, timestamp)
        """)
        
        # GCP Cloud SQL metrics
        self.client.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.database}.gcp_sql_metrics (
            timestamp DateTime,
            project_id String,
            instance_name String,
            tier String,
            database_version String,
            region String,
            availability_type String,
            storage_gb Int32,
            connections_avg Float64,
            cpu_avg Float64,
            memory_avg Float64,
            monthly_cost Float64,
            date Date
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (project_id, instance_name, timestamp)
        """)
        
        # GCP Cloud Functions metrics
        self.client.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.database}.gcp_functions_metrics (
            timestamp DateTime,
            project_id String,
            function_name String,
            memory_mb Int32,
            runtime String,
            region String,
            invocations Int64,
            execution_time_avg Float64,
            monthly_cost Float64,
            date Date
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (project_id, function_name, timestamp)
        """)
        
        # GCP Cloud Storage metrics
        self.client.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.database}.gcp_storage_metrics (
            timestamp DateTime,
            project_id String,
            bucket_name String,
            location String,
            storage_class String,
            size_gb Float64,
            object_count Int64,
            monthly_cost Float64,
            date Date
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (project_id, bucket_name, timestamp)
        """)
        
        # GCP optimization opportunities
        self.client.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.database}.gcp_opportunities (
            timestamp DateTime,
            project_id String,
            service String,
            opportunity_type String,
            resource_id String,
            estimated_savings Float64,
            recommendation String,
            details String,
            date Date
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (project_id, service, timestamp)
        """)
        
        logger.info("GCP tables created/verified")
    
    def store_cost_metrics(
        self,
        project_id: str,
        cost_data: Dict[str, Any]
    ):
        """
        Store GCP cost metrics.
        
        Args:
            project_id: GCP project ID
            cost_data: Cost data from billing
        """
        try:
            timestamp = datetime.utcnow()
            date = timestamp.date()
            
            rows = []
            
            # Store service costs
            by_service = cost_data.get('by_service', {})
            for service, cost in by_service.items():
                rows.append((
                    timestamp,
                    project_id,
                    service,
                    '',  # region
                    cost,
                    'USD',
                    date
                ))
            
            if rows:
                self.client.execute(
                    f'INSERT INTO {self.database}.gcp_cost_metrics VALUES',
                    rows
                )
                logger.info(f"Stored {len(rows)} cost metrics for {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to store cost metrics: {e}")
            raise
    
    def store_compute_metrics(
        self,
        project_id: str,
        instances: List[Dict[str, Any]]
    ):
        """
        Store Compute Engine instance metrics.
        
        Args:
            project_id: GCP project ID
            instances: List of instance data
        """
        try:
            timestamp = datetime.utcnow()
            date = timestamp.date()
            
            rows = []
            
            for instance in instances:
                utilization = instance.get('utilization', {})
                
                rows.append((
                    timestamp,
                    project_id,
                    instance.get('instance_id', ''),
                    instance.get('instance_name', ''),
                    instance.get('machine_type', ''),
                    instance.get('zone', ''),
                    instance.get('region', ''),
                    instance.get('status', ''),
                    utilization.get('cpu_avg', 0.0),
                    utilization.get('cpu_max', 0.0),
                    utilization.get('network_gb_day', 0.0),
                    instance.get('monthly_cost', 0.0),
                    1 if instance.get('preemptible', False) else 0,
                    date
                ))
            
            if rows:
                self.client.execute(
                    f'INSERT INTO {self.database}.gcp_compute_metrics VALUES',
                    rows
                )
                logger.info(f"Stored {len(rows)} Compute Engine metrics")
            
        except Exception as e:
            logger.error(f"Failed to store Compute Engine metrics: {e}")
            raise
    
    def store_sql_metrics(
        self,
        project_id: str,
        instances: List[Dict[str, Any]]
    ):
        """
        Store Cloud SQL metrics.
        
        Args:
            project_id: GCP project ID
            instances: List of Cloud SQL instance data
        """
        try:
            timestamp = datetime.utcnow()
            date = timestamp.date()
            
            rows = []
            
            for instance in instances:
                utilization = instance.get('utilization', {})
                
                rows.append((
                    timestamp,
                    project_id,
                    instance.get('instance_name', ''),
                    instance.get('tier', ''),
                    instance.get('database_version', ''),
                    instance.get('region', ''),
                    instance.get('availability_type', ''),
                    instance.get('storage_gb', 0),
                    utilization.get('connections_avg', 0.0),
                    utilization.get('cpu_avg', 0.0),
                    utilization.get('memory_avg', 0.0),
                    instance.get('monthly_cost', 0.0),
                    date
                ))
            
            if rows:
                self.client.execute(
                    f'INSERT INTO {self.database}.gcp_sql_metrics VALUES',
                    rows
                )
                logger.info(f"Stored {len(rows)} Cloud SQL metrics")
            
        except Exception as e:
            logger.error(f"Failed to store Cloud SQL metrics: {e}")
            raise
    
    def store_functions_metrics(
        self,
        project_id: str,
        functions: List[Dict[str, Any]]
    ):
        """
        Store Cloud Functions metrics.
        
        Args:
            project_id: GCP project ID
            functions: List of function data
        """
        try:
            timestamp = datetime.utcnow()
            date = timestamp.date()
            
            rows = []
            
            for function in functions:
                metrics = function.get('metrics', {})
                
                rows.append((
                    timestamp,
                    project_id,
                    function.get('function_name', ''),
                    function.get('memory_mb', 0),
                    function.get('runtime', ''),
                    function.get('region', ''),
                    metrics.get('invocations', 0),
                    metrics.get('execution_time_avg', 0.0),
                    function.get('monthly_cost', 0.0),
                    date
                ))
            
            if rows:
                self.client.execute(
                    f'INSERT INTO {self.database}.gcp_functions_metrics VALUES',
                    rows
                )
                logger.info(f"Stored {len(rows)} Cloud Functions metrics")
            
        except Exception as e:
            logger.error(f"Failed to store Cloud Functions metrics: {e}")
            raise
    
    def store_storage_metrics(
        self,
        project_id: str,
        buckets: List[Dict[str, Any]]
    ):
        """
        Store Cloud Storage metrics.
        
        Args:
            project_id: GCP project ID
            buckets: List of bucket data
        """
        try:
            timestamp = datetime.utcnow()
            date = timestamp.date()
            
            rows = []
            
            for bucket in buckets:
                rows.append((
                    timestamp,
                    project_id,
                    bucket.get('bucket_name', ''),
                    bucket.get('location', ''),
                    bucket.get('storage_class', ''),
                    bucket.get('size_gb', 0.0),
                    bucket.get('object_count', 0),
                    bucket.get('monthly_cost', 0.0),
                    date
                ))
            
            if rows:
                self.client.execute(
                    f'INSERT INTO {self.database}.gcp_storage_metrics VALUES',
                    rows
                )
                logger.info(f"Stored {len(rows)} Cloud Storage metrics")
            
        except Exception as e:
            logger.error(f"Failed to store Cloud Storage metrics: {e}")
            raise
    
    def store_opportunities(
        self,
        project_id: str,
        opportunities: List[Dict[str, Any]]
    ):
        """
        Store optimization opportunities.
        
        Args:
            project_id: GCP project ID
            opportunities: List of opportunities
        """
        try:
            timestamp = datetime.utcnow()
            date = timestamp.date()
            
            rows = []
            
            for opp in opportunities:
                import json
                
                rows.append((
                    timestamp,
                    project_id,
                    opp.get('service', ''),
                    opp.get('type', ''),
                    opp.get('resource_id', ''),
                    opp.get('estimated_savings', 0.0),
                    opp.get('recommendation', ''),
                    json.dumps(opp.get('details', {})),
                    date
                ))
            
            if rows:
                self.client.execute(
                    f'INSERT INTO {self.database}.gcp_opportunities VALUES',
                    rows
                )
                logger.info(f"Stored {len(rows)} optimization opportunities")
            
        except Exception as e:
            logger.error(f"Failed to store opportunities: {e}")
            raise
    
    def query_cost_trends(
        self,
        project_id: str,
        days: int = 30,
        service: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query cost trends.
        
        Args:
            project_id: GCP project ID
            days: Days to query
            service: Optional service filter
        
        Returns:
            Cost trend data
        """
        try:
            where_clause = f"project_id = '{project_id}' AND date >= today() - {days}"
            if service:
                where_clause += f" AND service = '{service}'"
            
            query = f"""
            SELECT
                toDate(timestamp) as date,
                service,
                sum(cost) as total_cost
            FROM {self.database}.gcp_cost_metrics
            WHERE {where_clause}
            GROUP BY date, service
            ORDER BY date DESC
            """
            
            result = self.client.execute(query)
            
            trends = []
            for row in result:
                trends.append({
                    'date': str(row[0]),
                    'service': row[1],
                    'cost': round(row[2], 2)
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to query cost trends: {e}")
            return []
    
    def query_top_opportunities(
        self,
        project_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query top optimization opportunities.
        
        Args:
            project_id: GCP project ID
            limit: Max results
        
        Returns:
            Top opportunities
        """
        try:
            query = f"""
            SELECT
                service,
                opportunity_type,
                resource_id,
                estimated_savings,
                recommendation,
                details
            FROM {self.database}.gcp_opportunities
            WHERE project_id = '{project_id}'
            AND date = today()
            ORDER BY estimated_savings DESC
            LIMIT {limit}
            """
            
            result = self.client.execute(query)
            
            import json
            opportunities = []
            for row in result:
                opportunities.append({
                    'service': row[0],
                    'type': row[1],
                    'resource_id': row[2],
                    'estimated_savings': round(row[3], 2),
                    'recommendation': row[4],
                    'details': json.loads(row[5]) if row[5] else {}
                })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to query opportunities: {e}")
            return []

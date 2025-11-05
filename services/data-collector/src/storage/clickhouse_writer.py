"""
ClickHouse writer for metrics data
"""
from typing import List, Dict, Any
import logging
from datetime import datetime

from clickhouse_driver import Client

from ..config import config
from ..models.metrics import CostMetric, PerformanceMetric, ResourceMetric, ApplicationMetric

logger = logging.getLogger(__name__)


class ClickHouseWriter:
    """
    Writes metrics data to ClickHouse
    """
    
    def __init__(self):
        """Initialize ClickHouse writer"""
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to ClickHouse"""
        try:
            self.client = Client(
                host=config.CLICKHOUSE_HOST,
                port=config.CLICKHOUSE_PORT,
                database=config.CLICKHOUSE_DATABASE,
                user=config.CLICKHOUSE_USER,
                password=config.CLICKHOUSE_PASSWORD
            )
            logger.info(f"Connected to ClickHouse at {config.CLICKHOUSE_HOST}:{config.CLICKHOUSE_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise
    
    def write_cost_metrics(self, metrics: List[CostMetric]) -> int:
        """
        Write cost metrics to ClickHouse
        
        Args:
            metrics: List of CostMetric objects
        
        Returns:
            Number of records written
        """
        if not metrics:
            return 0
        
        try:
            # Prepare data for batch insert
            data = []
            for metric in metrics:
                data.append((
                    metric.timestamp,
                    metric.customer_id,
                    metric.provider,
                    metric.instance_id or '',
                    metric.cost_type,
                    metric.amount,
                    metric.currency
                ))
            
            # Insert into ClickHouse
            query = """
                INSERT INTO cost_metrics 
                (timestamp, customer_id, provider, instance_id, cost_type, amount, currency)
                VALUES
            """
            
            self.client.execute(query, data)
            logger.info(f"Wrote {len(data)} cost metrics to ClickHouse")
            return len(data)
            
        except Exception as e:
            logger.error(f"Failed to write cost metrics: {e}")
            raise
    
    def write_performance_metrics(self, metrics: List[PerformanceMetric]) -> int:
        """
        Write performance metrics to ClickHouse (Phase 6.4 Enhanced)
        
        Args:
            metrics: List of PerformanceMetric objects
        
        Returns:
            Number of records written
        """
        if not metrics:
            return 0
        
        try:
            data = []
            for metric in metrics:
                # Convert metadata dict to JSON string if it's a dict
                metadata_str = ''
                if metric.metadata:
                    import json
                    metadata_str = json.dumps(metric.metadata)
                
                data.append((
                    metric.timestamp,
                    metric.customer_id,
                    metric.provider,
                    metric.metric_type,
                    metric.resource_id,
                    metric.resource_name,
                    metric.metric_name,
                    metric.metric_value,
                    metric.unit,
                    metadata_str,
                    metric.workload_type or ''
                ))
            
            query = """
                INSERT INTO performance_metrics 
                (timestamp, customer_id, provider, metric_type, resource_id, resource_name, 
                 metric_name, metric_value, unit, metadata, workload_type)
                VALUES
            """
            
            self.client.execute(query, data)
            logger.info(f"Wrote {len(data)} performance metrics to ClickHouse")
            return len(data)
            
        except Exception as e:
            logger.error(f"Failed to write performance metrics: {e}")
            raise
    
    def write_resource_metrics(self, metrics: List[ResourceMetric]) -> int:
        """
        Write resource metrics to ClickHouse (Phase 6.4 Enhanced)
        
        Args:
            metrics: List of ResourceMetric objects
        
        Returns:
            Number of records written
        """
        if not metrics:
            return 0
        
        try:
            data = []
            for metric in metrics:
                data.append((
                    metric.timestamp,
                    metric.customer_id,
                    metric.provider,
                    metric.metric_type,
                    metric.resource_id,
                    metric.resource_name,
                    metric.resource_type,
                    metric.status,
                    metric.region,
                    metric.utilization,
                    metric.capacity,
                    metric.unit,
                    metric.metadata or ''
                ))
            
            query = """
                INSERT INTO resource_metrics 
                (timestamp, customer_id, provider, metric_type, resource_id, resource_name,
                 resource_type, status, region, utilization, capacity, unit, metadata)
                VALUES
            """
            
            self.client.execute(query, data)
            logger.info(f"Wrote {len(data)} resource metrics to ClickHouse")
            return len(data)
            
        except Exception as e:
            logger.error(f"Failed to write resource metrics: {e}")
            raise
    
    def write_application_metrics(self, metrics: List[ApplicationMetric]) -> int:
        """
        Write application metrics to ClickHouse (Phase 6.5 Enhanced)
        
        Args:
            metrics: List of ApplicationMetric objects
        
        Returns:
            Number of records written
        """
        if not metrics:
            return 0
        
        try:
            data = []
            for metric in metrics:
                # Convert metadata dict to JSON string if it's a dict
                metadata_str = ''
                if metric.metadata:
                    import json
                    metadata_str = json.dumps(metric.metadata)
                
                data.append((
                    metric.timestamp,
                    metric.customer_id,
                    metric.provider,
                    metric.application_id,
                    metric.application_name,
                    metric.metric_type,
                    metric.score,
                    metric.details or '',
                    metric.model_name,
                    metric.prompt_text or '',
                    metric.response_text or '',
                    metadata_str
                ))
            
            query = """
                INSERT INTO application_metrics 
                (timestamp, customer_id, provider, application_id, application_name,
                 metric_type, score, details, model_name, prompt_text, response_text, metadata)
                VALUES
            """
            
            self.client.execute(query, data)
            logger.info(f"Wrote {len(data)} application metrics to ClickHouse")
            return len(data)
            
        except Exception as e:
            logger.error(f"Failed to write application metrics: {e}")
            raise
    
    def close(self):
        """Close ClickHouse connection"""
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from ClickHouse")

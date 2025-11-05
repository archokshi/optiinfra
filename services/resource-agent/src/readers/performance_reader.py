"""
Performance Metrics Reader
Phase 6.5: Performance Agent Refactor
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .clickhouse_reader import ClickHouseReader

logger = logging.getLogger(__name__)


class PerformanceReader:
    """
    Reader for performance metrics from ClickHouse
    
    Provides methods to query and aggregate performance data
    """
    
    def __init__(self):
        """Initialize performance reader"""
        self.reader = ClickHouseReader()
        self.logger = logging.getLogger(f"{__name__}.PerformanceReader")
    
    def get_metrics(
        self,
        customer_id: str,
        provider: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metric_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider (vultr, aws, gcp, azure)
            start_date: Start date for filtering
            end_date: End date for filtering
            metric_type: Filter by metric type (compute, memory, storage, network)
            resource_id: Filter by specific resource
        
        Returns:
            List of performance metric dictionaries
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        # Build query
        query = """
            SELECT
                timestamp,
                provider,
                metric_type,
                resource_id,
                resource_name,
                metric_name,
                metric_value,
                unit,
                metadata,
                workload_type
            FROM performance_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
              AND timestamp <= %(end_date)s
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': start_date,
            'end_date': end_date
        }
        
        if metric_type:
            query += " AND metric_type = %(metric_type)s"
            params['metric_type'] = metric_type
        
        if resource_id:
            query += " AND resource_id = %(resource_id)s"
            params['resource_id'] = resource_id
        
        query += " ORDER BY timestamp DESC"
        
        return self.reader.execute_query(query, params)
    
    def get_average_metrics(
        self,
        customer_id: str,
        provider: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get average performance metrics over time period
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            hours: Number of hours to look back
        
        Returns:
            List of aggregated metrics
        """
        start_date = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT
                metric_type,
                metric_name,
                AVG(metric_value) as avg_value,
                MAX(metric_value) as max_value,
                MIN(metric_value) as min_value,
                unit,
                COUNT(*) as sample_count
            FROM performance_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
            GROUP BY metric_type, metric_name, unit
            ORDER BY metric_type, metric_name
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': start_date
        }
        
        return self.reader.execute_query(query, params)
    
    def get_resource_performance(
        self,
        customer_id: str,
        provider: str,
        resource_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics for a specific resource
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            resource_id: Resource identifier
            hours: Number of hours to look back
        
        Returns:
            List of performance metrics
        """
        start_date = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT
                timestamp,
                metric_name,
                metric_value,
                unit
            FROM performance_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND resource_id = %(resource_id)s
              AND timestamp >= %(start_date)s
            ORDER BY timestamp ASC
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'resource_id': resource_id,
            'start_date': start_date
        }
        
        return self.reader.execute_query(query, params)
    
    def get_performance_summary(
        self,
        customer_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Get performance summary for a provider
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
        
        Returns:
            Summary dictionary
        """
        # Get latest metrics
        latest_query = """
            SELECT
                metric_type,
                COUNT(DISTINCT resource_id) as resource_count,
                AVG(metric_value) as avg_value
            FROM performance_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
            GROUP BY metric_type
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': datetime.now() - timedelta(hours=1)
        }
        
        metrics = self.reader.execute_query(latest_query, params)
        
        return {
            'provider': provider,
            'metrics_by_type': metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    def close(self):
        """Close ClickHouse connection"""
        self.reader.close()

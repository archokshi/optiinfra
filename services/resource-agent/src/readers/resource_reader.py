"""
Resource Metrics Reader
Phase 6.5: Resource Agent Refactor
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .clickhouse_reader import ClickHouseReader

logger = logging.getLogger(__name__)


class ResourceReader:
    """
    Reader for resource metrics from ClickHouse
    
    Provides methods to query and aggregate resource inventory data
    """
    
    def __init__(self):
        """Initialize resource reader"""
        self.reader = ClickHouseReader()
        self.logger = logging.getLogger(f"{__name__}.ResourceReader")
    
    def get_inventory(
        self,
        customer_id: str,
        provider: str,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get resource inventory
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider (vultr, aws, gcp, azure)
            resource_type: Filter by resource type
            status: Filter by status
            region: Filter by region
        
        Returns:
            List of resource inventory items
        """
        query = """
            SELECT
                timestamp,
                provider,
                metric_type,
                resource_id,
                resource_name,
                resource_type,
                status,
                region,
                utilization,
                capacity,
                unit,
                metadata
            FROM resource_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider
        }
        
        if resource_type:
            query += " AND resource_type = %(resource_type)s"
            params['resource_type'] = resource_type
        
        if status:
            query += " AND status = %(status)s"
            params['status'] = status
        
        if region:
            query += " AND region = %(region)s"
            params['region'] = region
        
        query += " ORDER BY timestamp DESC LIMIT 1000"
        
        return self.reader.execute_query(query, params)
    
    def get_resource_changes(
        self,
        customer_id: str,
        provider: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get resource changes over time period
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            hours: Number of hours to look back
        
        Returns:
            List of resource changes
        """
        start_date = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT
                timestamp,
                resource_id,
                resource_name,
                resource_type,
                status,
                region
            FROM resource_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
            ORDER BY timestamp DESC
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': start_date
        }
        
        return self.reader.execute_query(query, params)
    
    def get_resource_summary(
        self,
        customer_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Get resource summary for a provider
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
        
        Returns:
            Summary dictionary
        """
        # Get counts by type and status
        summary_query = """
            SELECT
                resource_type,
                status,
                COUNT(*) as count
            FROM resource_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
            GROUP BY resource_type, status
            ORDER BY resource_type, status
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'start_date': datetime.now() - timedelta(hours=1)
        }
        
        summary = self.reader.execute_query(summary_query, params)
        
        # Get total count
        total_query = """
            SELECT COUNT(DISTINCT resource_id) as total_resources
            FROM resource_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
        """
        
        total_result = self.reader.execute_query(total_query, params)
        total_count = total_result[0]['total_resources'] if total_result else 0
        
        return {
            'provider': provider,
            'total_resources': total_count,
            'by_type_and_status': summary,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_resource_by_id(
        self,
        customer_id: str,
        provider: str,
        resource_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific resource details
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            resource_id: Resource identifier
        
        Returns:
            Resource details or None
        """
        query = """
            SELECT *
            FROM resource_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND resource_id = %(resource_id)s
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        params = {
            'customer_id': customer_id,
            'provider': provider,
            'resource_id': resource_id
        }
        
        results = self.reader.execute_query(query, params)
        return results[0] if results else None
    
    def close(self):
        """Close ClickHouse connection"""
        self.reader.close()

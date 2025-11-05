"""
Cost Reader - Read cost metrics from ClickHouse
Phase 6.3: Cost Agent Refactor

This replaces the direct cloud API collectors with ClickHouse readers
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .clickhouse_reader import ClickHouseReader

logger = logging.getLogger(__name__)


class CostReader:
    """
    Read cost metrics from ClickHouse
    
    This class provides a unified interface to read cost data
    that was collected by the data-collector service
    """
    
    def __init__(self):
        self.reader = ClickHouseReader()
        self.table_name = "cost_metrics"
    
    @staticmethod
    def _format_datetime(dt) -> str:
        """Convert datetime to ClickHouse-compatible string format"""
        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(dt, str):
            return dt
        return str(dt)
    
    def get_cost_metrics(
        self,
        customer_id: str,
        provider: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metric_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cost metrics for a customer and provider
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider (vultr, aws, gcp, azure)
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            metric_type: Optional metric type filter
        
        Returns:
            List of cost metrics
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        query = f"""
            SELECT
                timestamp,
                customer_id,
                provider,
                cost_type as metric_type,
                instance_id as resource_id,
                instance_id as resource_name,
                amount as cost,
                currency
            FROM {self.table_name}
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
              AND timestamp <= %(end_date)s
        """
        
        params = {
            "customer_id": customer_id,
            "provider": provider,
            "start_date": self._format_datetime(start_date),
            "end_date": self._format_datetime(end_date)
        }
        
        if metric_type:
            query += " AND cost_type = %(metric_type)s"
            params["metric_type"] = metric_type
        
        query += " ORDER BY timestamp DESC"
        
        try:
            results = self.reader.execute_query(query, params)
            logger.info(f"Retrieved {len(results)} cost metrics for {customer_id}/{provider}")
            return results
        except Exception as e:
            logger.error(f"Failed to get cost metrics: {e}", exc_info=True)
            return []
    
    def get_latest_costs(
        self,
        customer_id: str,
        provider: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get the most recent cost metrics
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            limit: Maximum number of records to return
        
        Returns:
            List of latest cost metrics
        """
        query = f"""
            SELECT
                timestamp,
                customer_id,
                provider,
                cost_type as metric_type,
                instance_id as resource_id,
                instance_id as resource_name,
                amount as cost,
                currency
            FROM {self.table_name}
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
            ORDER BY timestamp DESC
            LIMIT %(limit)s
        """
        
        params = {
            "customer_id": customer_id,
            "provider": provider,
            "limit": limit
        }
        
        try:
            results = self.reader.execute_query(query, params)
            logger.info(f"Retrieved {len(results)} latest costs for {customer_id}/{provider}")
            return results
        except Exception as e:
            logger.error(f"Failed to get latest costs: {e}", exc_info=True)
            return []
    
    def get_cost_trends(
        self,
        customer_id: str,
        provider: str,
        days: int = 30,
        group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get cost trends aggregated by time period
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            days: Number of days to look back
            group_by: Grouping period (day, week, month)
        
        Returns:
            List of aggregated cost trends
        """
        start_date = self._format_datetime(datetime.now() - timedelta(days=days))
        
        # Determine date truncation based on group_by
        if group_by == "day":
            date_trunc = "toDate(timestamp)"
        elif group_by == "week":
            date_trunc = "toMonday(timestamp)"
        elif group_by == "month":
            date_trunc = "toStartOfMonth(timestamp)"
        else:
            date_trunc = "toDate(timestamp)"
        
        query = f"""
            SELECT
                {date_trunc} as period,
                sum(amount) as total_cost,
                count() as metric_count,
                uniq(instance_id) as unique_resources,
                currency
            FROM {self.table_name}
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
            GROUP BY period, currency
            ORDER BY period DESC
        """
        
        params = {
            "customer_id": customer_id,
            "provider": provider,
            "start_date": start_date
        }
        
        try:
            results = self.reader.execute_query(query, params)
            logger.info(f"Retrieved cost trends for {customer_id}/{provider} ({days} days)")
            return results
        except Exception as e:
            logger.error(f"Failed to get cost trends: {e}", exc_info=True)
            return []
    
    def get_cost_by_resource(
        self,
        customer_id: str,
        provider: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get costs grouped by resource
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
        
        Returns:
            List of costs grouped by resource
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        query = f"""
            SELECT
                instance_id as resource_id,
                instance_id as resource_name,
                cost_type as metric_type,
                sum(amount) as total_cost,
                avg(amount) as avg_cost,
                count() as metric_count,
                currency
            FROM {self.table_name}
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
              AND timestamp <= %(end_date)s
            GROUP BY instance_id, cost_type, currency
            ORDER BY total_cost DESC
        """
        
        params = {
            "customer_id": customer_id,
            "provider": provider,
            "start_date": self._format_datetime(start_date),
            "end_date": self._format_datetime(end_date)
        }
        
        try:
            results = self.reader.execute_query(query, params)
            logger.info(f"Retrieved costs by resource for {customer_id}/{provider}")
            return results
        except Exception as e:
            logger.error(f"Failed to get costs by resource: {e}", exc_info=True)
            return []
    
    def get_cost_by_type(
        self,
        customer_id: str,
        provider: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get costs grouped by metric type
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
        
        Returns:
            List of costs grouped by type
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        query = f"""
            SELECT
                cost_type as metric_type,
                sum(amount) as total_cost,
                avg(amount) as avg_cost,
                count() as metric_count,
                uniq(instance_id) as unique_resources,
                currency
            FROM {self.table_name}
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
              AND timestamp <= %(end_date)s
            GROUP BY cost_type, currency
            ORDER BY total_cost DESC
        """
        
        params = {
            "customer_id": customer_id,
            "provider": provider,
            "start_date": self._format_datetime(start_date),
            "end_date": self._format_datetime(end_date)
        }
        
        try:
            results = self.reader.execute_query(query, params)
            logger.info(f"Retrieved costs by type for {customer_id}/{provider}")
            return results
        except Exception as e:
            logger.error(f"Failed to get costs by type: {e}", exc_info=True)
            return []
    
    def get_total_cost(
        self,
        customer_id: str,
        provider: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get total cost for a period
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            days: Number of days to look back (alternative to start_date)
        
        Returns:
            Dict with total cost information
        """
        if days:
            start_date = datetime.now() - timedelta(days=days)
            end_date = datetime.now()
        elif not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        query = f"""
            SELECT
                sum(amount) as total_cost,
                count() as metric_count,
                uniq(instance_id) as unique_resources,
                min(timestamp) as first_metric,
                max(timestamp) as last_metric,
                currency
            FROM {self.table_name}
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= %(start_date)s
              AND timestamp <= %(end_date)s
            GROUP BY currency
        """
        
        params = {
            "customer_id": customer_id,
            "provider": provider,
            "start_date": self._format_datetime(start_date),
            "end_date": self._format_datetime(end_date)
        }
        
        try:
            results = self.reader.execute_query(query, params)
            if results:
                result = results[0]
                logger.info(f"Total cost for {customer_id}/{provider}: {result.get('total_cost')} {result.get('currency')}")
                return result
            else:
                return {
                    "total_cost": 0,
                    "metric_count": 0,
                    "unique_resources": 0,
                    "first_metric": None,
                    "last_metric": None,
                    "currency": "USD"
                }
        except Exception as e:
            logger.error(f"Failed to get total cost: {e}", exc_info=True)
            return {
                "total_cost": 0,
                "metric_count": 0,
                "unique_resources": 0,
                "first_metric": None,
                "last_metric": None,
                "currency": "USD"
            }
    
    def close(self):
        """Close the ClickHouse connection"""
        self.reader.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

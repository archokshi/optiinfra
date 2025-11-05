"""
ClickHouse Reader - Base class for reading from ClickHouse
Phase 6.3: Cost Agent Refactor
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from clickhouse_driver import Client

logger = logging.getLogger(__name__)


class ClickHouseReader:
    """
    Base reader for ClickHouse database
    
    Provides common functionality for reading metrics from ClickHouse
    """
    
    def __init__(self):
        self.host = os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
        self.user = os.getenv("CLICKHOUSE_USER", "default")
        self.password = os.getenv("CLICKHOUSE_PASSWORD", "")
        self.database = os.getenv("CLICKHOUSE_DB", "optiinfra_metrics")
        
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to ClickHouse"""
        try:
            self.client = Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logger.info(f"Connected to ClickHouse at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}", exc_info=True)
            raise
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as list of dicts
        
        Args:
            query: SQL query string
            params: Optional query parameters
        
        Returns:
            List of dictionaries with query results
        """
        try:
            if params:
                result = self.client.execute(query, params, with_column_types=True)
            else:
                result = self.client.execute(query, with_column_types=True)
            
            # result is a tuple: (rows, column_info)
            rows, columns = result
            column_names = [col[0] for col in columns]
            
            # Convert to list of dicts
            return [dict(zip(column_names, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            logger.error(f"Query: {query}")
            raise
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get information about a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            List of column information
        """
        query = f"DESCRIBE TABLE {table_name}"
        return self.execute_query(query)
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists
        
        Args:
            table_name: Name of the table
        
        Returns:
            True if table exists, False otherwise
        """
        query = """
            SELECT count() as count
            FROM system.tables
            WHERE database = %(database)s AND name = %(table)s
        """
        params = {"database": self.database, "table": table_name}
        result = self.execute_query(query, params)
        return result[0]["count"] > 0 if result else False
    
    def get_date_range(self, table_name: str, date_column: str = "timestamp") -> Dict[str, Optional[datetime]]:
        """
        Get the date range of data in a table
        
        Args:
            table_name: Name of the table
            date_column: Name of the date/timestamp column
        
        Returns:
            Dict with min_date and max_date
        """
        query = f"""
            SELECT
                min({date_column}) as min_date,
                max({date_column}) as max_date
            FROM {table_name}
        """
        result = self.execute_query(query)
        return result[0] if result else {"min_date": None, "max_date": None}
    
    def get_row_count(self, table_name: str, where_clause: str = "") -> int:
        """
        Get row count for a table
        
        Args:
            table_name: Name of the table
            where_clause: Optional WHERE clause (without WHERE keyword)
        
        Returns:
            Number of rows
        """
        query = f"SELECT count() as count FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        result = self.execute_query(query)
        return result[0]["count"] if result else 0
    
    def close(self):
        """Close the ClickHouse connection"""
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from ClickHouse")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

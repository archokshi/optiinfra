"""
PostgreSQL writer for metadata
"""
import logging
from typing import Dict, Any
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from ..config import config

logger = logging.getLogger(__name__)


class PostgresWriter:
    """
    Writes metadata to PostgreSQL
    """
    
    def __init__(self):
        """Initialize PostgreSQL writer"""
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(config.get_postgres_url())
            logger.info(f"Connected to PostgreSQL at {config.POSTGRES_HOST}:{config.POSTGRES_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def write_collection_history(
        self,
        customer_id: str,
        provider: str,
        task_id: str,
        status: str,
        started_at: datetime,
        completed_at: datetime,
        metrics_collected: int,
        error_message: str = None
    ) -> int:
        """
        Write collection history record
        
        Args:
            customer_id: Customer ID
            provider: Cloud provider
            task_id: Task ID
            status: Collection status
            started_at: Start timestamp
            completed_at: Completion timestamp
            metrics_collected: Number of metrics collected
            error_message: Error message if failed
        
        Returns:
            Record ID
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO collection_history 
                    (customer_id, provider, task_id, status, started_at, completed_at, metrics_collected, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                cur.execute(
                    query,
                    (customer_id, provider, task_id, status, started_at, completed_at, metrics_collected, error_message)
                )
                record_id = cur.fetchone()[0]
                self.conn.commit()
                logger.info(f"Wrote collection history record: {record_id}")
                return record_id
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to write collection history: {e}")
            raise
    
    def close(self):
        """Close PostgreSQL connection"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from PostgreSQL")

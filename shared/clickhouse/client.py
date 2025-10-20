"""
ClickHouse client for high-frequency time-series metrics.
Provides easy-to-use interface for inserting and querying metrics.

Usage:
    from shared.clickhouse.client import get_clickhouse_client
    
    client = get_clickhouse_client()
    
    # Insert cost metrics
    client.insert_cost_metrics([
        {
            'timestamp': datetime.now(),
            'customer_id': '123e4567-e89b-12d3-a456-426614174000',
            'cloud_provider': 'aws',
            'service_name': 'ec2',
            'instance_id': 'i-1234567',
            'instance_type': 'm5.xlarge',
            'region': 'us-east-1',
            'cost_per_hour': 0.192,
            'utilization_percent': 45.5,
            'is_spot': 0,
            'is_reserved': 0
        }
    ])
    
    # Query hourly costs
    results = client.query_cost_hourly(
        customer_id='123e4567-e89b-12d3-a456-426614174000',
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
"""

from clickhouse_driver import Client
from typing import Dict, List, Any, Optional
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Client for inserting and querying time-series metrics in ClickHouse."""
    
    def __init__(self):
        """Initialize ClickHouse client with connection parameters."""
        self.client = Client(
            host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
            port=int(os.getenv('CLICKHOUSE_PORT', 9000)),
            database=os.getenv('CLICKHOUSE_DB', 'optiinfra'),
            user=os.getenv('CLICKHOUSE_USER', 'optiinfra'),
            password=os.getenv('CLICKHOUSE_PASSWORD', 'optiinfra_dev_password')
        )
        logger.info(f"ClickHouse client initialized")
    
    def ping(self) -> bool:
        """
        Check if ClickHouse is accessible.
        
        Returns:
            bool: True if ClickHouse responds, False otherwise
        """
        try:
            result = self.client.execute('SELECT 1')
            return result[0][0] == 1
        except Exception as e:
            logger.error(f"ClickHouse ping failed: {e}")
            return False
    
    # ========================================================================
    # COST METRICS
    # ========================================================================
    
    def insert_cost_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """
        Insert cost metrics in batch.
        
        Args:
            metrics: List of cost metric dictionaries with keys:
                - timestamp (datetime)
                - customer_id (str UUID)
                - cloud_provider (str)
                - service_name (str)
                - instance_id (str)
                - instance_type (str)
                - region (str)
                - cost_per_hour (float)
                - utilization_percent (float)
                - is_spot (int: 0 or 1)
                - is_reserved (int: 0 or 1)
        
        Returns:
            int: Number of rows inserted
        
        Example:
            client.insert_cost_metrics([
                {
                    'timestamp': datetime.now(),
                    'customer_id': '123e4567-e89b-12d3-a456-426614174000',
                    'cloud_provider': 'aws',
                    'service_name': 'ec2',
                    'instance_id': 'i-1234567',
                    'instance_type': 'm5.xlarge',
                    'region': 'us-east-1',
                    'cost_per_hour': 0.192,
                    'utilization_percent': 45.5,
                    'is_spot': 0,
                    'is_reserved': 0
                }
            ])
        """
        if not metrics:
            return 0
        
        query = """
        INSERT INTO cost_metrics_ts 
        (timestamp, customer_id, cloud_provider, service_name, instance_id, 
         instance_type, region, cost_per_hour, utilization_percent, is_spot, is_reserved)
        VALUES
        """
        
        self.client.execute(query, metrics)
        logger.info(f"Inserted {len(metrics)} cost metrics")
        return len(metrics)
    
    def query_cost_hourly(
        self, 
        customer_id: str, 
        start_date: datetime, 
        end_date: datetime,
        cloud_provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query hourly cost aggregations.
        
        Args:
            customer_id: Customer UUID
            start_date: Start datetime
            end_date: End datetime
            cloud_provider: Optional filter by cloud provider
        
        Returns:
            List of dictionaries with hourly cost data
        
        Example:
            results = client.query_cost_hourly(
                customer_id='123e4567-e89b-12d3-a456-426614174000',
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now(),
                cloud_provider='aws'
            )
        """
        query = """
        SELECT 
            hour,
            cloud_provider,
            service_name,
            total_cost,
            avg_utilization,
            sample_count
        FROM cost_metrics_hourly_mv
        WHERE customer_id = %(customer_id)s
          AND hour >= %(start_date)s
          AND hour < %(end_date)s
        """
        
        params = {
            'customer_id': customer_id,
            'start_date': start_date,
            'end_date': end_date
        }
        
        if cloud_provider:
            query += " AND cloud_provider = %(cloud_provider)s"
            params['cloud_provider'] = cloud_provider
        
        query += " ORDER BY hour"
        
        result = self.client.execute(query, params)
        
        return [
            {
                'hour': row[0],
                'cloud_provider': row[1],
                'service_name': row[2],
                'total_cost': row[3],
                'avg_utilization': row[4],
                'sample_count': row[5]
            }
            for row in result
        ]
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    def insert_performance_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """
        Insert performance metrics in batch.
        
        Args:
            metrics: List of performance metric dictionaries
        
        Returns:
            int: Number of rows inserted
        """
        if not metrics:
            return 0
        
        query = """
        INSERT INTO performance_metrics_ts 
        (timestamp, customer_id, service_id, service_type, model_name, request_id,
         latency_ms, throughput_tokens_per_sec, gpu_utilization, kv_cache_utilization,
         batch_size, prompt_tokens, completion_tokens, total_tokens)
        VALUES
        """
        
        self.client.execute(query, metrics)
        logger.info(f"Inserted {len(metrics)} performance metrics")
        return len(metrics)
    
    def query_performance_p95(
        self,
        customer_id: str,
        service_id: str,
        hours: int = 24
    ) -> Dict[str, float]:
        """
        Query P95 latency over last N hours.
        
        Args:
            customer_id: Customer UUID
            service_id: Service UUID
            hours: Number of hours to query (default 24)
        
        Returns:
            Dictionary with performance metrics
        
        Example:
            results = client.query_performance_p95(
                customer_id='123e4567-e89b-12d3-a456-426614174000',
                service_id='456e7890-e89b-12d3-a456-426614174000',
                hours=24
            )
            # Returns: {'avg_latency_ms': 245.3, 'p95_latency_ms': 450.2, ...}
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        query = """
        SELECT 
            avgMerge(avg_latency) as avg_latency,
            quantileMerge(0.95)(p95_latency) as p95_latency,
            quantileMerge(0.99)(p99_latency) as p99_latency,
            avgMerge(avg_throughput) as avg_throughput,
            sum(request_count) as total_requests
        FROM performance_metrics_hourly_mv
        WHERE customer_id = %(customer_id)s
          AND service_id = %(service_id)s
          AND hour >= %(start_time)s
          AND hour < %(end_time)s
        """
        
        result = self.client.execute(query, {
            'customer_id': customer_id,
            'service_id': service_id,
            'start_time': start_time,
            'end_time': end_time
        })
        
        if not result:
            return {}
        
        row = result[0]
        return {
            'avg_latency_ms': row[0],
            'p95_latency_ms': row[1],
            'p99_latency_ms': row[2],
            'avg_throughput': row[3],
            'total_requests': row[4]
        }
    
    # ========================================================================
    # RESOURCE METRICS
    # ========================================================================
    
    def insert_resource_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """Insert resource metrics in batch."""
        if not metrics:
            return 0
        
        query = """
        INSERT INTO resource_metrics_ts 
        (timestamp, customer_id, instance_id, instance_type, gpu_index,
         gpu_utilization, gpu_memory_used_mb, gpu_memory_total_mb, gpu_temperature,
         cpu_utilization, memory_used_gb, memory_total_gb, network_rx_mbps, network_tx_mbps)
        VALUES
        """
        
        self.client.execute(query, metrics)
        logger.info(f"Inserted {len(metrics)} resource metrics")
        return len(metrics)
    
    def query_resource_utilization(
        self,
        customer_id: str,
        instance_id: str,
        hours: int = 24
    ) -> Dict[str, float]:
        """Query resource utilization over last N hours."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        query = """
        SELECT 
            avgMerge(avg_gpu_util) as avg_gpu_util,
            maxMerge(max_gpu_util) as max_gpu_util,
            avgMerge(avg_gpu_memory) as avg_gpu_memory,
            avgMerge(avg_cpu_util) as avg_cpu_util
        FROM resource_metrics_hourly_mv
        WHERE customer_id = %(customer_id)s
          AND instance_id = %(instance_id)s
          AND hour >= %(start_time)s
          AND hour < %(end_time)s
        """
        
        result = self.client.execute(query, {
            'customer_id': customer_id,
            'instance_id': instance_id,
            'start_time': start_time,
            'end_time': end_time
        })
        
        if not result:
            return {}
        
        row = result[0]
        return {
            'avg_gpu_utilization': row[0],
            'max_gpu_utilization': row[1],
            'avg_gpu_memory_mb': row[2],
            'avg_cpu_utilization': row[3]
        }
    
    # ========================================================================
    # QUALITY METRICS
    # ========================================================================
    
    def insert_quality_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """Insert quality metrics in batch."""
        if not metrics:
            return 0
        
        query = """
        INSERT INTO quality_metrics_ts 
        (timestamp, customer_id, service_id, request_id, model_name,
         relevance_score, coherence_score, factuality_score, hallucination_detected,
         toxicity_score, overall_quality_score, prompt_hash, latency_ms)
        VALUES
        """
        
        self.client.execute(query, metrics)
        logger.info(f"Inserted {len(metrics)} quality metrics")
        return len(metrics)
    
    def query_quality_trends(
        self,
        customer_id: str,
        service_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Query quality trends over last N hours."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        query = """
        SELECT 
            hour,
            avgMerge(avg_quality) as avg_quality,
            avgMerge(avg_relevance) as avg_relevance,
            avgMerge(avg_coherence) as avg_coherence,
            avgMerge(avg_factuality) as avg_factuality,
            sum(hallucination_count) as hallucinations,
            sum(request_count) as total_requests
        FROM quality_metrics_hourly_mv
        WHERE customer_id = %(customer_id)s
          AND service_id = %(service_id)s
          AND hour >= %(start_time)s
          AND hour < %(end_time)s
        GROUP BY hour
        ORDER BY hour
        """
        
        result = self.client.execute(query, {
            'customer_id': customer_id,
            'service_id': service_id,
            'start_time': start_time,
            'end_time': end_time
        })
        
        return [
            {
                'hour': row[0],
                'avg_quality': row[1],
                'avg_relevance': row[2],
                'avg_coherence': row[3],
                'avg_factuality': row[4],
                'hallucinations': row[5],
                'total_requests': row[6]
            }
            for row in result
        ]


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_clickhouse_client = None

def get_clickhouse_client() -> ClickHouseClient:
    """
    Get singleton ClickHouse client instance.
    
    Returns:
        ClickHouseClient: Singleton client instance
    
    Example:
        client = get_clickhouse_client()
        if client.ping():
            print("ClickHouse is ready!")
    """
    global _clickhouse_client
    if _clickhouse_client is None:
        _clickhouse_client = ClickHouseClient()
    return _clickhouse_client

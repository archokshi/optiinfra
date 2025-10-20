"""
ClickHouse time-series database package.

Provides high-performance storage and querying for:
- Cost metrics (hourly cloud spending)
- Performance metrics (per-request LLM latency)
- Resource metrics (GPU/CPU utilization)
- Quality metrics (LLM output quality scores)

Usage:
    from shared.clickhouse import get_clickhouse_client
    
    client = get_clickhouse_client()
    
    # Insert metrics
    client.insert_cost_metrics([...])
    
    # Query aggregations
    results = client.query_cost_hourly(...)
"""

from shared.clickhouse.client import (
    ClickHouseClient,
    get_clickhouse_client
)

__all__ = [
    'ClickHouseClient',
    'get_clickhouse_client'
]

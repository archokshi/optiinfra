# ClickHouse Time-Series Database

High-performance time-series storage for OptiInfra metrics.

## Overview

ClickHouse stores high-frequency metrics that would overwhelm PostgreSQL:
- **1M+ inserts/second** vs PostgreSQL's ~10K/second
- **10-20x compression** vs PostgreSQL's 2-3x
- **Millisecond queries** vs PostgreSQL's seconds

## Architecture

### Tables
1. **cost_metrics_ts** - Cloud costs (1-hour granularity, 90-day retention)
2. **performance_metrics_ts** - LLM latency (per-request, 30-day retention)
3. **resource_metrics_ts** - GPU/CPU utilization (1-minute, 90-day retention)
4. **quality_metrics_ts** - Quality scores (per-request, 30-day retention)

### Materialized Views
Pre-aggregated hourly rollups for fast dashboard queries:
- cost_metrics_hourly_mv
- performance_metrics_hourly_mv
- resource_metrics_hourly_mv
- quality_metrics_hourly_mv

## Usage

### Initialize Database

```bash
# Run initialization script
docker exec -i optiinfra-clickhouse clickhouse-client < shared/clickhouse/migrations/init.sql
```

### Python Client

```python
from shared.clickhouse import get_clickhouse_client
from datetime import datetime, timedelta

# Get client
client = get_clickhouse_client()

# Check connection
if client.ping():
    print("✅ ClickHouse connected!")

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

for row in results:
    print(f"{row['hour']}: ${row['total_cost']:.2f}")
```

### Performance Metrics

```python
# Insert performance metrics
client.insert_performance_metrics([
    {
        'timestamp': datetime.now(),
        'customer_id': '123e4567-e89b-12d3-a456-426614174000',
        'service_id': '456e7890-e89b-12d3-a456-426614174000',
        'service_type': 'vllm',
        'model_name': 'llama-2-70b',
        'request_id': '789e0123-e89b-12d3-a456-426614174000',
        'latency_ms': 245.3,
        'throughput_tokens_per_sec': 125.5,
        'gpu_utilization': 85.2,
        'kv_cache_utilization': 72.1,
        'batch_size': 8,
        'prompt_tokens': 150,
        'completion_tokens': 300,
        'total_tokens': 450
    }
])

# Query P95 latency
stats = client.query_performance_p95(
    customer_id='123e4567-e89b-12d3-a456-426614174000',
    service_id='456e7890-e89b-12d3-a456-426614174000',
    hours=24
)

print(f"P95 Latency: {stats['p95_latency_ms']:.2f}ms")
print(f"Total Requests: {stats['total_requests']}")
```

### Resource Metrics

```python
# Insert resource metrics
client.insert_resource_metrics([
    {
        'timestamp': datetime.now(),
        'customer_id': '123e4567-e89b-12d3-a456-426614174000',
        'instance_id': 'i-gpu-001',
        'instance_type': 'p4d.24xlarge',
        'gpu_index': 0,
        'gpu_utilization': 92.5,
        'gpu_memory_used_mb': 38400,
        'gpu_memory_total_mb': 40960,
        'gpu_temperature': 72.0,
        'cpu_utilization': 45.2,
        'memory_used_gb': 120.5,
        'memory_total_gb': 1152.0,
        'network_rx_mbps': 1250.0,
        'network_tx_mbps': 850.0
    }
])

# Query utilization
util = client.query_resource_utilization(
    customer_id='123e4567-e89b-12d3-a456-426614174000',
    instance_id='i-gpu-001',
    hours=24
)

print(f"Avg GPU Util: {util['avg_gpu_utilization']:.1f}%")
print(f"Max GPU Util: {util['max_gpu_utilization']:.1f}%")
```

### Quality Metrics

```python
# Insert quality metrics
client.insert_quality_metrics([
    {
        'timestamp': datetime.now(),
        'customer_id': '123e4567-e89b-12d3-a456-426614174000',
        'service_id': '456e7890-e89b-12d3-a456-426614174000',
        'request_id': '789e0123-e89b-12d3-a456-426614174000',
        'model_name': 'gpt-4',
        'relevance_score': 0.92,
        'coherence_score': 0.95,
        'factuality_score': 0.88,
        'hallucination_detected': 0,
        'toxicity_score': 0.02,
        'overall_quality_score': 0.91,
        'prompt_hash': 'abc123def456',
        'latency_ms': 1250
    }
])

# Query quality trends
trends = client.query_quality_trends(
    customer_id='123e4567-e89b-12d3-a456-426614174000',
    service_id='456e7890-e89b-12d3-a456-426614174000',
    hours=24
)

for trend in trends:
    print(f"{trend['hour']}: Quality={trend['avg_quality']:.2f}, Hallucinations={trend['hallucinations']}")
```

## Data Retention

- **cost_metrics_ts**: 90 days (automatic TTL cleanup)
- **performance_metrics_ts**: 30 days
- **resource_metrics_ts**: 90 days
- **quality_metrics_ts**: 30 days

Data older than TTL is automatically deleted by ClickHouse.

## Performance

### Insertion Speed
- Batch inserts: 1M+ rows/second
- Single inserts: 10K+ rows/second

### Query Speed
- Materialized views: <10ms for hourly aggregations
- Raw data queries: <100ms for 24-hour windows

### Storage Efficiency
- 10-20x compression vs PostgreSQL
- Automatic partitioning by month
- Efficient columnar storage

## Monitoring

### Check Table Sizes

```bash
docker exec optiinfra-clickhouse clickhouse-client --database=optiinfra --query="
SELECT 
    table,
    formatReadableSize(total_bytes) as size,
    total_rows as rows
FROM system.tables
WHERE database = 'optiinfra'
ORDER BY total_bytes DESC
"
```

### Check Partitions

```bash
docker exec optiinfra-clickhouse clickhouse-client --database=optiinfra --query="
SELECT 
    table,
    partition,
    formatReadableSize(bytes_on_disk) as size,
    rows
FROM system.parts
WHERE database = 'optiinfra' AND active
ORDER BY table, partition
"
```

## Troubleshooting

### Connection Issues

```python
from shared.clickhouse import get_clickhouse_client

client = get_clickhouse_client()
if not client.ping():
    print("❌ ClickHouse not responding")
    print("   Check: docker ps | grep clickhouse")
else:
    print("✅ ClickHouse connected")
```

### Check Logs

```bash
docker logs optiinfra-clickhouse --tail 100
```

### Restart ClickHouse

```bash
docker-compose restart clickhouse
```

## Best Practices

1. **Batch Inserts**: Always insert in batches (100-1000 rows) for best performance
2. **Use Materialized Views**: Query hourly views instead of raw tables when possible
3. **Monitor TTL**: Ensure old data is being cleaned up automatically
4. **Partition by Month**: Tables are partitioned by month for efficient queries
5. **Index Granularity**: Default 8192 provides good balance of speed and storage

## Integration with PostgreSQL

ClickHouse complements PostgreSQL:
- **PostgreSQL**: Structured data, transactions, relationships (customers, agents, configs)
- **ClickHouse**: High-frequency metrics, time-series, analytics

Use customer_id and service_id from PostgreSQL as foreign keys in ClickHouse queries.

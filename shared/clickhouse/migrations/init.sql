-- ============================================================================
-- OptiInfra ClickHouse Time-Series Database
-- Foundation Phase 0.3
-- ============================================================================

-- Create database
CREATE DATABASE IF NOT EXISTS optiinfra;
USE optiinfra;

-- ============================================================================
-- TABLE 1: cost_metrics_ts
-- Purpose: Track cloud costs per instance per hour
-- Retention: 90 days
-- Granularity: 1 hour
-- ============================================================================

CREATE TABLE IF NOT EXISTS cost_metrics_ts (
    timestamp DateTime,
    customer_id UUID,
    cloud_provider String,        -- 'aws', 'gcp', 'azure'
    service_name String,           -- 'ec2', 'compute-engine', 'vm'
    instance_id String,
    instance_type String,          -- 'm5.xlarge', 'n1-standard-4'
    region String,                 -- 'us-east-1', 'us-central1'
    cost_per_hour Float64,
    utilization_percent Float32,
    is_spot UInt8,                 -- 0 or 1 (boolean)
    is_reserved UInt8              -- 0 or 1 (boolean)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, cloud_provider, timestamp)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- ============================================================================
-- TABLE 2: performance_metrics_ts
-- Purpose: Track LLM inference performance per request
-- Retention: 30 days
-- Granularity: 1 second (per request)
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_metrics_ts (
    timestamp DateTime,
    customer_id UUID,
    service_id UUID,
    service_type String,                -- 'vllm', 'tgi', 'sglang'
    model_name String,                  -- 'gpt-4', 'llama-2-70b'
    request_id UUID,
    latency_ms Float32,
    throughput_tokens_per_sec Float32,
    gpu_utilization Float32,
    kv_cache_utilization Float32,
    batch_size UInt32,
    prompt_tokens UInt32,
    completion_tokens UInt32,
    total_tokens UInt32
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, service_id, timestamp)
TTL timestamp + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;

-- ============================================================================
-- TABLE 3: resource_metrics_ts
-- Purpose: Track GPU/CPU utilization per minute
-- Retention: 90 days
-- Granularity: 1 minute
-- ============================================================================

CREATE TABLE IF NOT EXISTS resource_metrics_ts (
    timestamp DateTime,
    customer_id UUID,
    instance_id String,
    instance_type String,
    gpu_index UInt8,                    -- 0-7 (which GPU on instance)
    gpu_utilization Float32,            -- 0-100%
    gpu_memory_used_mb Float32,
    gpu_memory_total_mb Float32,
    gpu_temperature Float32,
    cpu_utilization Float32,            -- 0-100%
    memory_used_gb Float32,
    memory_total_gb Float32,
    network_rx_mbps Float32,
    network_tx_mbps Float32
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, instance_id, timestamp)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- ============================================================================
-- TABLE 4: quality_metrics_ts
-- Purpose: Track LLM output quality per request
-- Retention: 30 days
-- Granularity: Per request
-- ============================================================================

CREATE TABLE IF NOT EXISTS quality_metrics_ts (
    timestamp DateTime,
    customer_id UUID,
    service_id UUID,
    request_id UUID,
    model_name String,
    relevance_score Float32,            -- 0-1
    coherence_score Float32,            -- 0-1
    factuality_score Float32,           -- 0-1
    hallucination_detected UInt8,       -- 0 or 1
    toxicity_score Float32,             -- 0-1
    overall_quality_score Float32,      -- weighted average
    prompt_hash String,                 -- for grouping similar prompts
    latency_ms UInt32
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, service_id, timestamp)
TTL timestamp + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;

-- ============================================================================
-- MATERIALIZED VIEW 1: cost_metrics_hourly_mv
-- Purpose: Pre-aggregate cost data by hour for fast dashboard queries
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS cost_metrics_hourly_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (customer_id, cloud_provider, hour)
POPULATE
AS SELECT
    toStartOfHour(timestamp) as hour,
    customer_id,
    cloud_provider,
    service_name,
    sum(cost_per_hour) as total_cost,
    avg(utilization_percent) as avg_utilization,
    count() as sample_count
FROM cost_metrics_ts
GROUP BY hour, customer_id, cloud_provider, service_name;

-- ============================================================================
-- MATERIALIZED VIEW 2: performance_metrics_hourly_mv
-- Purpose: Pre-aggregate latency P95/P99 by hour
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS performance_metrics_hourly_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (customer_id, service_id, hour)
POPULATE
AS SELECT
    toStartOfHour(timestamp) as hour,
    customer_id,
    service_id,
    service_type,
    avgState(latency_ms) as avg_latency,
    quantileState(0.95)(latency_ms) as p95_latency,
    quantileState(0.99)(latency_ms) as p99_latency,
    avgState(throughput_tokens_per_sec) as avg_throughput,
    avgState(gpu_utilization) as avg_gpu_util,
    count() as request_count
FROM performance_metrics_ts
GROUP BY hour, customer_id, service_id, service_type;

-- ============================================================================
-- MATERIALIZED VIEW 3: resource_metrics_hourly_mv
-- Purpose: Pre-aggregate GPU utilization by hour
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS resource_metrics_hourly_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (customer_id, instance_id, hour)
POPULATE
AS SELECT
    toStartOfHour(timestamp) as hour,
    customer_id,
    instance_id,
    instance_type,
    avgState(gpu_utilization) as avg_gpu_util,
    maxState(gpu_utilization) as max_gpu_util,
    avgState(gpu_memory_used_mb) as avg_gpu_memory,
    avgState(cpu_utilization) as avg_cpu_util,
    count() as sample_count
FROM resource_metrics_ts
GROUP BY hour, customer_id, instance_id, instance_type;

-- ============================================================================
-- MATERIALIZED VIEW 4: quality_metrics_hourly_mv
-- Purpose: Pre-aggregate quality scores by hour
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS quality_metrics_hourly_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (customer_id, service_id, hour)
POPULATE
AS SELECT
    toStartOfHour(timestamp) as hour,
    customer_id,
    service_id,
    model_name,
    avgState(overall_quality_score) as avg_quality,
    avgState(relevance_score) as avg_relevance,
    avgState(coherence_score) as avg_coherence,
    avgState(factuality_score) as avg_factuality,
    sumState(hallucination_detected) as hallucination_count,
    count() as request_count
FROM quality_metrics_ts
GROUP BY hour, customer_id, service_id, model_name;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show all tables
SHOW TABLES;

-- Check table row counts
SELECT 
    database,
    table,
    formatReadableSize(total_bytes) as size,
    total_rows as rows
FROM system.tables
WHERE database = 'optiinfra'
ORDER BY table;

-- OptiInfra ClickHouse Schema
-- Initial schema for metrics storage

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS optiinfra_metrics;

USE optiinfra_metrics;

-- ============================================
-- Cost Metrics Table
-- ============================================
CREATE TABLE IF NOT EXISTS cost_metrics (
    timestamp DateTime DEFAULT now(),
    customer_id String,
    provider LowCardinality(String),
    instance_id Nullable(String),
    cost_type LowCardinality(String),
    amount Decimal(18, 6),
    currency LowCardinality(String) DEFAULT 'USD',
    metadata String DEFAULT '{}',
    INDEX idx_customer customer_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_provider provider TYPE set(0) GRANULARITY 1,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 1
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- ============================================
-- Performance Metrics Table
-- ============================================
CREATE TABLE IF NOT EXISTS performance_metrics (
    timestamp DateTime DEFAULT now(),
    customer_id String,
    provider LowCardinality(String),
    metric_type LowCardinality(String),
    resource_id String,
    resource_name String,
    metric_name LowCardinality(String),
    metric_value Float64,
    unit LowCardinality(String),
    metadata String DEFAULT '{}',
    workload_type Nullable(LowCardinality(String)),
    INDEX idx_customer customer_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_provider provider TYPE set(0) GRANULARITY 1,
    INDEX idx_metric_name metric_name TYPE set(0) GRANULARITY 1,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 1
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, resource_id, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- ============================================
-- Resource Metrics Table
-- ============================================
CREATE TABLE IF NOT EXISTS resource_metrics (
    timestamp DateTime DEFAULT now(),
    customer_id String,
    provider LowCardinality(String),
    metric_type LowCardinality(String),
    resource_id String,
    resource_name String,
    resource_type LowCardinality(String),
    status LowCardinality(String),
    region LowCardinality(String),
    utilization Float64 DEFAULT 0.0,
    capacity Float64 DEFAULT 0.0,
    unit LowCardinality(String) DEFAULT '',
    metadata String DEFAULT '{}',
    INDEX idx_customer customer_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_provider provider TYPE set(0) GRANULARITY 1,
    INDEX idx_resource_type resource_type TYPE set(0) GRANULARITY 1,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 1
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, resource_id, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- ============================================
-- Application Metrics Table
-- ============================================
CREATE TABLE IF NOT EXISTS application_metrics (
    timestamp DateTime DEFAULT now(),
    customer_id String,
    provider LowCardinality(String),
    application_id String,
    application_name String,
    metric_type LowCardinality(String),
    score Float64,
    details Nullable(String),
    model_name String,
    prompt_text Nullable(String),
    response_text Nullable(String),
    metadata String DEFAULT '{}',
    INDEX idx_customer customer_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_provider provider TYPE set(0) GRANULARITY 1,
    INDEX idx_application application_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 1
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, application_id, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- ============================================
-- Provider Metadata Table (Phase 6.6.5)
-- ============================================
CREATE TABLE IF NOT EXISTS provider_metadata (
    customer_id String,
    provider LowCardinality(String),
    provider_type LowCardinality(String), -- dedicated, generic
    category LowCardinality(String), -- gpu_cloud, general_compute, self_hosted
    enabled Boolean DEFAULT true,
    prometheus_url Nullable(String),
    dcgm_url Nullable(String),
    api_url Nullable(String),
    api_type Nullable(LowCardinality(String)), -- rest, graphql, sdk, kubernetes
    last_collection_at Nullable(DateTime),
    last_collection_status LowCardinality(String) DEFAULT 'pending',
    total_collections UInt64 DEFAULT 0,
    successful_collections UInt64 DEFAULT 0,
    failed_collections UInt64 DEFAULT 0,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now(),
    metadata String DEFAULT '{}'
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (customer_id, provider);

-- ============================================
-- Collection History Table
-- ============================================
CREATE TABLE IF NOT EXISTS collection_history (
    task_id String,
    customer_id String,
    provider LowCardinality(String),
    data_type LowCardinality(String),
    status LowCardinality(String),
    started_at DateTime,
    completed_at DateTime,
    duration_seconds UInt32,
    records_collected UInt64,
    error_message Nullable(String),
    metadata String DEFAULT '{}',
    INDEX idx_customer customer_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_provider provider TYPE set(0) GRANULARITY 1,
    INDEX idx_status status TYPE set(0) GRANULARITY 1,
    INDEX idx_started_at started_at TYPE minmax GRANULARITY 1
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(started_at)
ORDER BY (customer_id, provider, started_at)
TTL started_at + INTERVAL 180 DAY;

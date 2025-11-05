-- ClickHouse Schemas for OptiInfra Metrics
-- Phase 6.1: Data Collector Service

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS optiinfra_metrics;

USE optiinfra_metrics;

-- ============================================================
-- COST METRICS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS cost_metrics (
    timestamp DateTime,
    customer_id String,
    provider String,
    instance_id String,
    cost_type String,
    amount Float64,
    currency String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, timestamp)
SETTINGS index_granularity = 8192;

-- ============================================================
-- PERFORMANCE METRICS TABLE (Phase 6.4 Enhanced)
-- ============================================================
CREATE TABLE IF NOT EXISTS performance_metrics (
    timestamp DateTime,
    customer_id String,
    provider String,
    metric_type String,
    resource_id String,
    resource_name String,
    metric_name String,
    metric_value Float64,
    unit String,
    metadata String,
    workload_type String,
    collected_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, resource_id, timestamp)
SETTINGS index_granularity = 8192;

-- ============================================================
-- RESOURCE METRICS TABLE (Phase 6.4 Enhanced)
-- ============================================================
CREATE TABLE IF NOT EXISTS resource_metrics (
    timestamp DateTime,
    customer_id String,
    provider String,
    metric_type String,
    resource_id String,
    resource_name String,
    resource_type String,
    status String,
    region String,
    utilization Float64,
    capacity Float64,
    unit String,
    metadata String,
    collected_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, resource_id, timestamp)
SETTINGS index_granularity = 8192;

-- ============================================================
-- APPLICATION METRICS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS application_metrics (
    timestamp DateTime,
    customer_id String,
    application_id String,
    metric_type String,
    score Float64,
    details String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, application_id, timestamp)
SETTINGS index_granularity = 8192;

-- ============================================================
-- INDEXES FOR BETTER QUERY PERFORMANCE
-- ============================================================

-- Cost metrics indexes
ALTER TABLE cost_metrics ADD INDEX IF NOT EXISTS idx_provider provider TYPE minmax GRANULARITY 4;
ALTER TABLE cost_metrics ADD INDEX IF NOT EXISTS idx_cost_type cost_type TYPE set(100) GRANULARITY 4;

-- Performance metrics indexes (Phase 6.4 Enhanced)
ALTER TABLE performance_metrics ADD INDEX IF NOT EXISTS idx_provider provider TYPE minmax GRANULARITY 4;
ALTER TABLE performance_metrics ADD INDEX IF NOT EXISTS idx_metric_type metric_type TYPE set(100) GRANULARITY 4;
ALTER TABLE performance_metrics ADD INDEX IF NOT EXISTS idx_metric_name metric_name TYPE set(100) GRANULARITY 4;
ALTER TABLE performance_metrics ADD INDEX IF NOT EXISTS idx_workload workload_type TYPE set(10) GRANULARITY 4;

-- Resource metrics indexes (Phase 6.4 Enhanced)
ALTER TABLE resource_metrics ADD INDEX IF NOT EXISTS idx_provider provider TYPE minmax GRANULARITY 4;
ALTER TABLE resource_metrics ADD INDEX IF NOT EXISTS idx_resource_type resource_type TYPE set(50) GRANULARITY 4;
ALTER TABLE resource_metrics ADD INDEX IF NOT EXISTS idx_status status TYPE set(20) GRANULARITY 4;
ALTER TABLE resource_metrics ADD INDEX IF NOT EXISTS idx_region region TYPE set(50) GRANULARITY 4;

-- Application metrics indexes
ALTER TABLE application_metrics ADD INDEX IF NOT EXISTS idx_app_metric_type metric_type TYPE set(50) GRANULARITY 4;

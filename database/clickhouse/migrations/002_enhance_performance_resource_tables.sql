-- Migration: Enhance Performance and Resource Tables for Phase 6.4
-- Date: October 30, 2025

USE optiinfra_metrics;

-- Drop existing tables (backup data first if needed)
DROP TABLE IF EXISTS performance_metrics;
DROP TABLE IF EXISTS resource_metrics;

-- Recreate Performance Metrics Table with enhanced schema
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

-- Recreate Resource Metrics Table with enhanced schema
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

-- Add indexes for Performance Metrics
ALTER TABLE performance_metrics ADD INDEX IF NOT EXISTS idx_provider provider TYPE minmax GRANULARITY 4;
ALTER TABLE performance_metrics ADD INDEX IF NOT EXISTS idx_metric_type metric_type TYPE set(100) GRANULARITY 4;
ALTER TABLE performance_metrics ADD INDEX IF NOT EXISTS idx_metric_name metric_name TYPE set(100) GRANULARITY 4;
ALTER TABLE performance_metrics ADD INDEX IF NOT EXISTS idx_workload workload_type TYPE set(10) GRANULARITY 4;

-- Add indexes for Resource Metrics
ALTER TABLE resource_metrics ADD INDEX IF NOT EXISTS idx_provider provider TYPE minmax GRANULARITY 4;
ALTER TABLE resource_metrics ADD INDEX IF NOT EXISTS idx_resource_type resource_type TYPE set(50) GRANULARITY 4;
ALTER TABLE resource_metrics ADD INDEX IF NOT EXISTS idx_status status TYPE set(20) GRANULARITY 4;
ALTER TABLE resource_metrics ADD INDEX IF NOT EXISTS idx_region region TYPE set(50) GRANULARITY 4;

-- Migration: RunPod staging tables for Phase 1 integration
-- Date: November 2025

USE optiinfra_metrics;

-- RunPod pod snapshots ------------------------------------------------------
CREATE TABLE IF NOT EXISTS runpod_pods (
    snapshot_ts DateTime,
    customer_id String,
    pod_id String,
    gpu_type_id String,
    gpu_count UInt32,
    vcpu_count UInt32,
    memory_gb Float64,
    region String,
    status String,
    uptime_seconds UInt64,
    cost_per_hour Float64,
    metadata_json String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(snapshot_ts)
ORDER BY (customer_id, pod_id, snapshot_ts)
SETTINGS index_granularity = 8192;

-- RunPod serverless endpoint inventory --------------------------------------
CREATE TABLE IF NOT EXISTS runpod_endpoints (
    snapshot_ts DateTime,
    customer_id String,
    endpoint_id String,
    name String,
    compute_type String,
    gpu_type_ids Array(String),
    workers_min UInt32,
    workers_max UInt32,
    scaler_type String,
    idle_timeout UInt32,
    execution_timeout_ms UInt64,
    metadata_json String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(snapshot_ts)
ORDER BY (customer_id, endpoint_id, snapshot_ts)
SETTINGS index_granularity = 8192;

-- RunPod job telemetry ------------------------------------------------------
CREATE TABLE IF NOT EXISTS runpod_jobs (
    observed_ts DateTime,
    customer_id String,
    endpoint_id String,
    job_id String,
    status String,
    delay_ms UInt64,
    execution_ms UInt64,
    input_tokens UInt64,
    output_tokens UInt64,
    throughput Float64,
    metadata_json String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(observed_ts)
ORDER BY (customer_id, endpoint_id, observed_ts, job_id)
SETTINGS index_granularity = 8192;

-- RunPod endpoint health polling -------------------------------------------
CREATE TABLE IF NOT EXISTS runpod_endpoint_health (
    observed_ts DateTime,
    customer_id String,
    endpoint_id String,
    jobs_completed UInt64,
    jobs_failed UInt64,
    jobs_in_progress UInt64,
    jobs_in_queue UInt64,
    workers_idle UInt64,
    workers_running UInt64,
    workers_throttled UInt64,
    metadata_json String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(observed_ts)
ORDER BY (customer_id, endpoint_id, observed_ts)
SETTINGS index_granularity = 8192;

-- RunPod billing snapshots --------------------------------------------------
CREATE TABLE IF NOT EXISTS runpod_billing_snapshots (
    snapshot_ts DateTime,
    customer_id String,
    current_spend_per_hr Float64,
    lifetime_spend Float64,
    balance Float64,
    spend_breakdown_json String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(snapshot_ts)
ORDER BY (customer_id, snapshot_ts)
SETTINGS index_granularity = 8192;

-- Migration: Enhance Application Metrics Table for Phase 6.5
-- Date: October 30, 2025

USE optiinfra_metrics;

-- Drop existing application_metrics table
DROP TABLE IF EXISTS application_metrics;

-- Recreate Application Metrics Table with enhanced schema
CREATE TABLE IF NOT EXISTS application_metrics (
    timestamp DateTime,
    customer_id String,
    provider String,
    application_id String,
    application_name String,
    metric_type String,  -- quality, hallucination, toxicity, latency, etc.
    score Float64,
    details String,
    model_name String,
    prompt_text String,
    response_text String,
    metadata String,
    collected_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, application_id, timestamp)
SETTINGS index_granularity = 8192;

-- Add indexes for Application Metrics
ALTER TABLE application_metrics ADD INDEX IF NOT EXISTS idx_provider provider TYPE minmax GRANULARITY 4;
ALTER TABLE application_metrics ADD INDEX IF NOT EXISTS idx_metric_type metric_type TYPE set(100) GRANULARITY 4;
ALTER TABLE application_metrics ADD INDEX IF NOT EXISTS idx_model_name model_name TYPE set(50) GRANULARITY 4;
ALTER TABLE application_metrics ADD INDEX IF NOT EXISTS idx_application_name application_name TYPE set(100) GRANULARITY 4;

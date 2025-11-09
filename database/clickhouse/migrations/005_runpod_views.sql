-- Migration: RunPod analytics views for Phase 2 integration
-- Date: November 2025

USE optiinfra_metrics;

-- Daily billing roll-up per customer
CREATE VIEW IF NOT EXISTS runpod_billing_daily AS
SELECT
    customer_id,
    toDate(snapshot_ts) AS snapshot_date,
    avg(current_spend_per_hr) AS avg_spend_per_hr,
    max(lifetime_spend) AS lifetime_spend,
    anyLast(balance) AS balance,
    anyLast(spend_breakdown_json) AS spend_breakdown_json
FROM runpod_billing_snapshots
GROUP BY customer_id, snapshot_date;

-- Latest pod snapshot per pod/customer combination
CREATE VIEW IF NOT EXISTS runpod_pods_latest AS
SELECT
    customer_id,
    pod_id,
    argMax(snapshot_ts, snapshot_ts) AS snapshot_ts,
    argMax(gpu_type_id, snapshot_ts) AS gpu_type_id,
    argMax(gpu_count, snapshot_ts) AS gpu_count,
    argMax(vcpu_count, snapshot_ts) AS vcpu_count,
    argMax(memory_gb, snapshot_ts) AS memory_gb,
    argMax(region, snapshot_ts) AS region,
    argMax(status, snapshot_ts) AS status,
    argMax(uptime_seconds, snapshot_ts) AS uptime_seconds,
    argMax(cost_per_hour, snapshot_ts) AS cost_per_hour,
    argMax(metadata_json, snapshot_ts) AS metadata_json
FROM runpod_pods
GROUP BY customer_id, pod_id;

-- Latest endpoint health per endpoint/customer combination
CREATE VIEW IF NOT EXISTS runpod_endpoint_health_latest AS
SELECT
    customer_id,
    endpoint_id,
    argMax(observed_ts, observed_ts) AS observed_ts,
    argMax(jobs_completed, observed_ts) AS jobs_completed,
    argMax(jobs_failed, observed_ts) AS jobs_failed,
    argMax(jobs_in_progress, observed_ts) AS jobs_in_progress,
    argMax(jobs_in_queue, observed_ts) AS jobs_in_queue,
    argMax(workers_idle, observed_ts) AS workers_idle,
    argMax(workers_running, observed_ts) AS workers_running,
    argMax(workers_throttled, observed_ts) AS workers_throttled,
    argMax(metadata_json, observed_ts) AS metadata_json
FROM runpod_endpoint_health
GROUP BY customer_id, endpoint_id;

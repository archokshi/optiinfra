# RunPod Integration – Phase 1 Design

This document captures the concrete deliverables for the first implementation
phase that brings real RunPod data into OptiInfra.  The scope focuses on
laying the foundation that every agent can share for later phases.

The objective for Phase 1 is to ship structural changes (schemas, configs, and
collector scaffolding) without yet implementing the full data ingestion logic.

---

## 1. Storage Layer

Create RunPod‑specific staging tables and supporting analytics views.  These
tables live alongside the existing shared `*_metrics` tables so that later
phases can ETL into the dashboards without breaking current queries.

### ClickHouse (new migration `004_runpod_staging.sql`)

| Table | Purpose | Key Columns |
| ----- | ------- | ----------- |
| `runpod_pods` | Snapshots of pod inventory + telemetry metadata | `snapshot_ts, pod_id, customer_id, gpu_type_id, gpu_count, vcpu_count, memory_gb, region, status, uptime_seconds, cost_per_hour, metadata_json` |
| `runpod_endpoints` | Serverless endpoint inventory/config | `snapshot_ts, endpoint_id, customer_id, name, compute_type, gpu_type_ids, workers_min/max, scaler_type, idle_timeout, execution_timeout_ms, metadata_json` |
| `runpod_jobs` | Job level telemetry (sync/async/stream) | `observed_ts, endpoint_id, job_id, customer_id, status, delay_ms, execution_ms, input_tokens, output_tokens, throughput, metadata_json` |
| `runpod_endpoint_health` | Poll results from `/health` | `observed_ts, endpoint_id, customer_id, jobs_completed, jobs_failed, jobs_in_progress, jobs_in_queue, workers_idle, workers_running, workers_throttled, metadata_json` |
| `runpod_billing_snapshots` | Aggregated spend pulled from `myself` | `snapshot_ts, customer_id, current_spend_per_hr, lifetime_spend, balance, spend_breakdown_json` |

All tables use `MergeTree` engines with monthly partitions, ordered by
`(customer_id, endpoint_id/pod_id, observed_ts)` as appropriate.  The schema
should keep JSON metadata columns (`String`) for forward compatibility.

### Postgres

No Postgres schema changes are required in Phase 1.  If we later persist
roll‑ups here, it will happen in Phase 2 ETL tasks.

---

## 2. Configuration & Secrets

Update the collector service configuration to make RunPod endpoints explicit
and to control polling cadence.

Add the following environment variables to `services/data-collector/src/config.py`:

- `RUNPOD_GRAPHQL_URL` (default `https://api.runpod.io/graphql`)
- `RUNPOD_REST_URL` (default `https://rest.runpod.io/v1`)
- `RUNPOD_SERVERLESS_URL` (default `https://api.runpod.ai/v2`)
- `RUNPOD_COLLECTION_INTERVAL_SECONDS` (default `300`)
- `RUNPOD_HEALTH_POLL_SECONDS` (default `120`)
- `RUNPOD_JOB_RETENTION_DAYS` (default `90`)

Expose matching entries in `.env.example`, `docker-compose.yml`, and service
charts so the credentials (API key) and cadence can be supplied per
environment.

---

## 3. Collector Scaffolding

Introduce new modules that will be filled out in Phase 2.  Phase 1 is only
responsible for the structure and wiring so the rest of the stack can import
them without runtime errors.

### Shared Client

- `services/data-collector/src/collectors/providers/runpod_client.py`
  - Async client wrapping GraphQL and REST requests.
  - Handles authentication headers, rate limiting backoff, and GraphQL errors.
  - Expose helper methods with type hints for:
    - `fetch_gpu_catalog()`
    - `fetch_myself()`
    - `fetch_pods()` / `fetch_pod(pod_id)`
    - `fetch_endpoints()`
    - `fetch_endpoint_health(endpoint_id)`
    - `fetch_job_status(endpoint_id, job_id)`
    - `fetch_stream_metrics(endpoint_id, job_id)`
  - For now, method bodies return `NotImplementedError` placeholders or simple
    `...` statements with TODO comments.

### Agent Collectors

Create skeleton collectors that plug into the existing scheduling framework:

- `services/data-collector/src/collectors/runpod/cost_collector.py`
- `services/data-collector/src/collectors/runpod/resource_collector.py`
- `services/data-collector/src/collectors/runpod/performance_collector.py`
- `services/data-collector/src/collectors/runpod/application_collector.py`

Each class should:

1. Accept RunPod config settings (API key, URLs, cadence) and store a
   `RunPodClient` instance.
2. Expose `collect()` / `collect_async()` methods that currently log a
   “not implemented” warning and return empty `CollectionResult` objects.
3. Include docstrings describing the metrics they will emit in Phase 2.

### Registration

- Update `services/data-collector/src/collectors/__init__.py` and any loader
  logic to recognise the new RunPod collectors.
- Ensure feature flags (`RUNPOD_ENABLED`) wire up these collectors instead of
  pointing at the simulator.

---

## 4. Portal & API Placeholders

While Phase 1 does not change the front‑end behaviour, add clearly labelled
placeholders in the Cost Agent dashboard route indicating which RunPod
datasets it will consume once populated.  This can be done with TODO comments
and lightweight helper functions that are currently no‑ops.

---

## 5. Testing & Tooling

Provide scaffolding tests so that future PRs can add fixtures without new
setup boilerplate:

- `tests/fixtures/runpod_examples/` with placeholder JSON files for each API
  call.
- Unit test modules (one per collector + client) that currently assert the
  classes initialises correctly and raise `NotImplementedError` for
  collection.

Ensure CI loads the new tests without failing (i.e., mark them with
`xfail(strict=False)` or equivalent until real implementations land).

---

## 6. Follow‑Up (Phase 2 Preview)

After Phase 1 is merged, Phase 2 will focus on:

1. Implementing the RunPod client calls and serializers.
2. Writing to the staging tables and building ETL pipelines into the shared
   metrics tables.
3. Updating the portal and agent readers to surface the new metrics.
4. Adding recorded fixtures and live smoke tests using the cadence defined
   above.

This staged approach keeps the initial PR manageable while signalling the
complete path to production RunPod telemetry.

---

## Appendix A – Phase 3 Portal Integration Checklist

With Phase 3 we replaced the placeholders described above with working API and
UI surfaces.  Use this checklist to verify the RunPod flow end-to-end.

- The Cost Agent `/api/v1/dashboard` route now attaches a `metrics.runpod`
  section containing `billing`, `endpoint_health`, and `pods` arrays.  Each
  entry normalises timestamps to ISO strings and parses JSON metadata into
  Python dictionaries.
- The Next.js edge route `portal/app/api/dashboard/route.ts` forwards requests
  to `COST_AGENT_URL` and defaults the `provider` query string to `runpod`.
- The Cost dashboard (`portal/app/(dashboard)/cost/page.tsx`) renders RunPod
  analytics: high-level spend cards, spend-breakdown tiles, billing history,
  endpoint health, and pod inventory tables, including graceful placeholders
  when data has not arrived yet.
- The Performance, Resource, and Application dashboards now surface dedicated
  RunPod sections (job telemetry, GPU inventory, workflow status) sourced from
  the shared runpod helper module.
- Portal type definitions now model the RunPod section and placeholder status
  payload so that future schema adjustments remain type-safe.
- New unit coverage (`services/cost-agent/tests/api/test_dashboard_runpod.py`)
  exercises the helper responsible for shaping RunPod data: targeted scenarios
  for cost, performance, resource, and application agents plus a combined
  integration-style check across all metrics.

### Operational Notes

- When developing locally, expose the Cost Agent URL via
  `COST_AGENT_URL=http://localhost:8001` (or the appropriate compose service).
- The dashboard route preserves the default provider override; other providers
  continue using the existing cost metrics pipeline.

### Validation Steps

1. Populate the RunPod staging tables (e.g., via the data collector's `runpod`
   collectors) for the target customer ID.
2. Hit `GET /api/v1/dashboard?provider=runpod` on the Cost Agent and confirm
   the response includes the `runpod` section with populated arrays.
3. Run `npm run dev` within the `portal` workspace and load the Cost dashboard
   to observe the RunPod tables and charts.
4. Optional: execute `pytest services/cost-agent/tests/api/test_dashboard_runpod.py`
   once Python dependencies are available to verify helper behaviour.

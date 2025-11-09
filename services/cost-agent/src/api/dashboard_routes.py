"""Portal dashboard aggregation routes."""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

import json

from shared.database.connections import get_postgres_cursor
from src.readers.cost_reader import CostReader
from src.readers.clickhouse_reader import ClickHouseReader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["dashboard"])

DEFAULT_CUSTOMER_ID = os.getenv(
    "DEFAULT_CUSTOMER_ID",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
)
DEFAULT_PROVIDER = os.getenv("DEFAULT_DASHBOARD_PROVIDER", "vultr")
RUNPOD_JOB_LOOKBACK_HOURS = int(os.getenv("RUNPOD_JOB_LOOKBACK_HOURS", "6"))
AGENT_HEARTBEAT_STALE_SECONDS = int(
    os.getenv("AGENT_HEARTBEAT_STALE_SECONDS", "300"),
)


class AgentPayload(BaseModel):
    agent_id: str
    agent_name: str
    agent_type: str
    version: Optional[str]
    status: str
    last_heartbeat: Optional[str]
    capabilities: List[str] = Field(default_factory=list)
    host: Optional[str]
    port: Optional[int]


class CostMetricsPayload(BaseModel):
    total_cost: float = 0.0
    daily_cost: float = 0.0
    monthly_cost: float = 0.0
    cost_trend: float = 0.0
    savings_potential: float = 0.0
    currency: str = "USD"


class PerformanceMetricsPayload(BaseModel):
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    throughput: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0


class ResourceMetricsPayload(BaseModel):
    gpu_utilization: float = 0.0
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    gpu_memory_used: float = 0.0
    gpu_memory_total: float = 0.0


class QualityMetricsPayload(BaseModel):
    quality_score: float = 0.0
    relevance_score: float = 0.0
    coherence_score: float = 0.0
    hallucination_rate: float = 0.0
    toxicity_score: float = 0.0


class RecommendationPayload(BaseModel):
    id: str
    agent_type: str
    type: str
    title: str
    description: Optional[str]
    estimated_savings: Optional[float]
    estimated_improvement: Optional[float]
    risk_level: str
    status: str
    created_at: str
    updated_at: Optional[str]


class ExecutionPayload(BaseModel):
    id: str
    recommendation_id: str
    agent_type: str
    type: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    actual_savings: Optional[float]
    actual_improvement: Optional[float]
    error_message: Optional[str]


class TimeseriesPointPayload(BaseModel):
    timestamp: str
    cost: Optional[float] = None
    latency: Optional[float] = None
    gpu: Optional[float] = None
    quality: Optional[float] = None


class DashboardPayload(BaseModel):
    agents: List[AgentPayload]
    metrics: Dict[str, Any]
    timeseries: List[TimeseriesPointPayload] = Field(default_factory=list)
    recommendations: List[RecommendationPayload] = Field(default_factory=list)
    recent_executions: List[ExecutionPayload] = Field(default_factory=list)


def _decimal_to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _to_float(value: Any) -> Optional[float]:
    """Best-effort conversion of ClickHouse values (floats, Decimals, strings) to float."""
    if value is None:
        return None
    if isinstance(value, float):
        return value
    if isinstance(value, (int, Decimal)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _map_agent_status(status: str) -> str:
    normalized = (status or "").lower()
    mapping = {
        "healthy": "active",
        "starting": "inactive",
        "degraded": "degraded",
        "failed": "error",
        "stopped": "inactive",
    }
    return mapping.get(normalized, "inactive")


def _parse_endpoint(endpoint: Optional[str]) -> Dict[str, Optional[Any]]:
    if not endpoint:
        return {"host": None, "port": None}
    parsed = urlparse(endpoint)
    return {"host": parsed.hostname or None, "port": parsed.port}


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _load_json_field(raw_value: Any) -> Dict[str, Any]:
    if not raw_value:
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return {}
    return {}


def _build_runpod_dashboard_section(reader: CostReader, customer_id: str) -> Dict[str, Any]:
    billing = reader.get_runpod_billing_summary(customer_id, days=30)
    for row in billing:
        snapshot_date = row.get("snapshot_date")
        if hasattr(snapshot_date, "isoformat"):
            row["snapshot_date"] = snapshot_date.isoformat()
        row["avg_spend_per_hr"] = _to_float(row.get("avg_spend_per_hr")) or 0.0
        row["lifetime_spend"] = _to_float(row.get("lifetime_spend")) or 0.0
        row["balance"] = _to_float(row.get("balance")) or 0.0

    endpoint_query = """
        SELECT
            endpoint_id,
            observed_ts,
            jobs_completed,
            jobs_failed,
            jobs_in_progress,
            jobs_in_queue,
            workers_idle,
            workers_running,
            workers_throttled,
            metadata_json
        FROM runpod_endpoint_health_latest
        WHERE customer_id = %(customer_id)s
    """
    endpoint_rows = reader.reader.execute_query(endpoint_query, {"customer_id": customer_id})
    for row in endpoint_rows:
        row["metadata"] = _load_json_field(row.pop("metadata_json", ""))
        ts = row.get("observed_ts")
        if hasattr(ts, "isoformat"):
            row["observed_ts"] = ts.isoformat()

    pods_query = """
        SELECT
            pod_id,
            snapshot_ts,
            status,
            gpu_type_id,
            gpu_count,
            vcpu_count,
            memory_gb,
            cost_per_hour,
            metadata_json
        FROM runpod_pods_latest
        WHERE customer_id = %(customer_id)s
    """
    pod_rows = reader.reader.execute_query(pods_query, {"customer_id": customer_id})
    for row in pod_rows:
        row["metadata"] = _load_json_field(row.pop("metadata_json", ""))
        ts = row.get("snapshot_ts")
        if hasattr(ts, "isoformat"):
            row["snapshot_ts"] = ts.isoformat()

    job_stats, job_series, application_summary = _build_runpod_job_sections(reader, customer_id)
    resource_summary = _summarize_runpod_resources(pod_rows)

    return {
        "billing": billing,
        "endpoint_health": endpoint_rows,
        "pods": pod_rows,
        "job_stats": job_stats,
        "job_timeseries": job_series,
        "application_summary": application_summary,
        "resource_summary": resource_summary,
    }


def _build_runpod_job_sections(
    reader: CostReader,
    customer_id: str,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Aggregate RunPod job telemetry for performance/application dashboards."""
    lookback_start = (datetime.utcnow() - timedelta(hours=RUNPOD_JOB_LOOKBACK_HOURS)).strftime(
        "%Y-%m-%d %H:%M:%S",
    )
    params = {
        "customer_id": customer_id,
        "start": lookback_start,
    }

    stats_query = """
        SELECT
            endpoint_id,
            max(observed_ts) AS last_observed,
            count() AS total_jobs,
            countIf(lower(status) IN ('failed', 'error')) AS failed_jobs,
            avgOrNull(execution_ms) AS avg_execution_ms,
            quantileExactOrNull(0.95)(execution_ms) AS p95_execution_ms,
            avgOrNull(throughput) AS avg_throughput,
            sum(input_tokens) AS total_input_tokens,
            sum(output_tokens) AS total_output_tokens
        FROM runpod_jobs
        WHERE customer_id = %(customer_id)s
          AND observed_ts >= %(start)s
        GROUP BY endpoint_id
        ORDER BY endpoint_id
    """
    stats_rows = reader.reader.execute_query(stats_query, params)

    job_stats: List[Dict[str, Any]] = []
    latest_observed: Optional[datetime] = None
    for row in stats_rows:
        observed_ts = row.get("last_observed")
        if isinstance(observed_ts, datetime):
            row["last_observed"] = observed_ts.isoformat()
            if latest_observed is None or observed_ts > latest_observed:
                latest_observed = observed_ts
        else:
            row["last_observed"] = None

        row["avg_execution_ms"] = _to_float(row.get("avg_execution_ms")) or 0.0
        row["p95_execution_ms"] = _to_float(row.get("p95_execution_ms")) or 0.0
        row["avg_throughput"] = _to_float(row.get("avg_throughput")) or 0.0
        row["total_input_tokens"] = int(row.get("total_input_tokens") or 0)
        row["total_output_tokens"] = int(row.get("total_output_tokens") or 0)
        row["total_jobs"] = int(row.get("total_jobs") or 0)
        row["failed_jobs"] = int(row.get("failed_jobs") or 0)
        job_stats.append(row)

    series_query = """
        SELECT
            endpoint_id,
            toStartOfFiveMinute(observed_ts) AS bucket,
            count() AS total_jobs,
            countIf(lower(status) IN ('failed', 'error')) AS failed_jobs,
            avgOrNull(throughput) AS avg_throughput
        FROM runpod_jobs
        WHERE customer_id = %(customer_id)s
          AND observed_ts >= %(start)s
        GROUP BY endpoint_id, bucket
        ORDER BY bucket, endpoint_id
    """
    series_rows = reader.reader.execute_query(series_query, params)
    job_series: List[Dict[str, Any]] = []
    for row in series_rows:
        bucket = row.get("bucket")
        if isinstance(bucket, datetime):
            row["timestamp"] = bucket.isoformat()
        else:
            row["timestamp"] = str(bucket)
        row.pop("bucket", None)
        row["total_jobs"] = int(row.get("total_jobs") or 0)
        row["failed_jobs"] = int(row.get("failed_jobs") or 0)
        row["avg_throughput"] = _to_float(row.get("avg_throughput")) or 0.0
        job_series.append(row)

    status_query = """
        SELECT
            lower(status) AS status,
            count() AS job_count
        FROM runpod_jobs
        WHERE customer_id = %(customer_id)s
          AND observed_ts >= %(start)s
        GROUP BY status
    """
    status_rows = reader.reader.execute_query(status_query, params)
    status_counts = {
        (row.get("status") or "unknown"): int(row.get("job_count") or 0)
        for row in status_rows
    }

    failed_jobs = sum(
        count for status, count in status_counts.items() if status in {"failed", "error"}
    )

    application_summary = {
        "status_counts": status_counts,
        "total_jobs": sum(status_counts.values()),
        "failed_jobs": failed_jobs,
        "active_endpoints": len(job_stats),
        "last_updated": latest_observed.isoformat() if latest_observed else None,
    }

    return job_stats, job_series, application_summary


def _summarize_runpod_resources(pod_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarise RunPod pod inventory for the resource dashboard."""
    if not pod_rows:
        return {
            "total_pods": 0,
            "total_gpus": 0,
            "total_vcpus": 0,
            "total_memory_gb": 0.0,
            "pods_by_status": {},
            "gpu_types": [],
        }

    pods_by_status: Dict[str, int] = {}
    gpu_types: Dict[str, Dict[str, Any]] = {}
    total_gpus = 0
    total_vcpus = 0
    total_memory = 0.0

    for row in pod_rows:
        status = str(row.get("status") or "unknown").lower()
        pods_by_status[status] = pods_by_status.get(status, 0) + 1

        gpu_count = int(row.get("gpu_count") or 0)
        vcpu_count = int(row.get("vcpu_count") or 0)
        memory_gb = _to_float(row.get("memory_gb")) or 0.0
        cost_per_hour = _to_float(row.get("cost_per_hour")) or 0.0
        gpu_type = row.get("gpu_type_id") or "unknown"

        total_gpus += gpu_count
        total_vcpus += vcpu_count
        total_memory += memory_gb

        entry = gpu_types.setdefault(
            gpu_type,
            {"gpu_type_id": gpu_type, "pods": 0, "gpus": 0, "cost_per_hour": 0.0},
        )
        entry["pods"] += 1
        entry["gpus"] += gpu_count
        entry["cost_per_hour"] += cost_per_hour

    for entry in gpu_types.values():
        entry["cost_per_hour"] = round(entry["cost_per_hour"], 4)

    return {
        "total_pods": len(pod_rows),
        "total_gpus": total_gpus,
        "total_vcpus": total_vcpus,
        "total_memory_gb": round(total_memory, 2),
        "pods_by_status": pods_by_status,
        "gpu_types": sorted(gpu_types.values(), key=lambda item: item["gpu_type_id"]),
    }


def _runpod_dashboard_placeholder(note: str = "RunPod metrics unavailable.") -> Dict[str, Any]:
    return {
        "status": "pending_ingestion",
        "note": note,
    }


def _fetch_agents() -> List[AgentPayload]:
    query = """
        SELECT id, type, name, version, status, endpoint, capabilities, last_heartbeat
        FROM agents
        ORDER BY type
    """
    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

    agents: List[AgentPayload] = []
    for row in rows:
        data = dict(zip(columns, row))
        endpoint_parts = _parse_endpoint(data.get("endpoint"))
        agents.append(
            AgentPayload(
                agent_id=str(data.get("id")),
                agent_name=data.get("name"),
                agent_type=str(data.get("type") or "").lower(),
                version=data.get("version"),
                status=_map_agent_status(data.get("status")),
                last_heartbeat=(
                    data.get("last_heartbeat").isoformat()
                    if data.get("last_heartbeat")
                    else None
                ),
                capabilities=list(data.get("capabilities") or []),
                host=endpoint_parts["host"],
                port=endpoint_parts["port"],
            )
        )
    return agents


async def _refresh_agent_heartbeats(agents: List[AgentPayload]) -> None:
    """Update stale agent heartbeats by probing their health endpoints."""
    now = datetime.utcnow()
    candidates: List[AgentPayload] = []

    for agent in agents:
        if not agent.host or not agent.port:
            continue
        last_seen = _parse_iso_datetime(agent.last_heartbeat)
        if (
            last_seen is None
            or (now - last_seen).total_seconds() > AGENT_HEARTBEAT_STALE_SECONDS
        ):
            candidates.append(agent)

    if not candidates:
        return

    async with httpx.AsyncClient(timeout=2.0) as client:
        tasks = [_probe_agent_health(client, agent) for agent in candidates]
        await asyncio.gather(*tasks, return_exceptions=True)


async def _probe_agent_health(client: httpx.AsyncClient, agent: AgentPayload) -> None:
    url = f"http://{agent.host}:{agent.port}/api/v1/health"
    try:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
        timestamp = payload.get("timestamp")
        status = payload.get("status")
        if timestamp:
            agent.last_heartbeat = timestamp
        if status:
            agent.status = _map_agent_status(str(status))
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Failed health probe for %s: %s", agent.agent_name, exc)
        agent.status = "inactive"


def _fetch_recommendations(customer_id: str) -> List[RecommendationPayload]:
    query = """
        SELECT
            r.id,
            a.type AS agent_type,
            r.type,
            r.title,
            r.description,
            r.estimated_savings,
            r.estimated_improvement,
            r.priority,
            r.status,
            r.created_at,
            r.updated_at,
            r.data
        FROM recommendations r
        JOIN agents a ON r.agent_id = a.id
        WHERE r.customer_id = %s
        ORDER BY r.created_at DESC
    """

    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, (customer_id,))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

    risk_map = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "high",
    }

    recommendations: List[RecommendationPayload] = []
    for row in rows:
        data = dict(zip(columns, row))
        metadata = data.get("data") or {}
        risk = metadata.get("risk_level") or risk_map.get(
            str(data.get("priority") or "").lower(),
            "medium",
        )
        recommendations.append(
            RecommendationPayload(
                id=str(data.get("id")),
                agent_type=str(data.get("agent_type") or "").lower(),
                type=data.get("type") or "unknown",
                title=data.get("title") or "",
                description=data.get("description"),
                estimated_savings=_decimal_to_float(data.get("estimated_savings")),
                estimated_improvement=_decimal_to_float(data.get("estimated_improvement")),
                risk_level=risk,
                status=str(data.get("status") or "pending").lower(),
                created_at=(
                    data.get("created_at").isoformat()
                    if data.get("created_at")
                    else datetime.utcnow().isoformat()
                ),
                updated_at=(
                    data.get("updated_at").isoformat()
                    if data.get("updated_at")
                    else None
                ),
            )
        )
    return recommendations


def _fetch_recent_executions(customer_id: str) -> List[ExecutionPayload]:
    query = """
        SELECT
            o.id,
            o.recommendation_id,
            a.type AS agent_type,
            r.type AS recommendation_type,
            o.status,
            o.started_at,
            o.completed_at,
            o.actual_savings,
            o.actual_improvement,
            o.error
        FROM optimizations o
        JOIN agents a ON o.agent_id = a.id
        JOIN recommendations r ON o.recommendation_id = r.id
        WHERE o.customer_id = %s
        ORDER BY COALESCE(o.completed_at, o.started_at, NOW()) DESC
        LIMIT 10
    """

    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, (customer_id,))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

    executions: List[ExecutionPayload] = []
    for row in rows:
        data = dict(zip(columns, row))
        executions.append(
            ExecutionPayload(
                id=str(data.get("id")),
                recommendation_id=str(data.get("recommendation_id")),
                agent_type=str(data.get("agent_type") or "").lower(),
                type=data.get("recommendation_type") or "unknown",
                status=str(data.get("status") or "queued").lower(),
                started_at=(
                    data.get("started_at").isoformat()
                    if data.get("started_at")
                    else None
                ),
                completed_at=(
                    data.get("completed_at").isoformat()
                    if data.get("completed_at")
                    else None
                ),
                actual_savings=_decimal_to_float(data.get("actual_savings")),
                actual_improvement=_decimal_to_float(data.get("actual_improvement")),
                error_message=data.get("error"),
            )
        )
    return executions


def _lookup_primary_provider(reader: CostReader, customer_id: str) -> Optional[str]:
    query = """
        SELECT provider, count() AS samples
        FROM cost_metrics
        WHERE customer_id = %(customer_id)s
        GROUP BY provider
        ORDER BY samples DESC
        LIMIT 1
    """
    try:
        results = reader.reader.execute_query(query, {"customer_id": customer_id})
        if results:
            return results[0].get("provider")
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Provider lookup failed: %s", exc)
    return None


def _fetch_cost_timeseries(
    reader: CostReader,
    customer_id: str,
    provider: str,
    hours: int = 24,
) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    start = now - timedelta(hours=hours)
    query = """
        SELECT
            toStartOfHour(timestamp) AS period,
            sum(amount) AS total_cost
        FROM cost_metrics
        WHERE customer_id = %(customer_id)s
          AND provider = %(provider)s
          AND timestamp >= %(start)s
          AND timestamp <= %(end)s
        GROUP BY period
        ORDER BY period
    """
    params = {
        "customer_id": customer_id,
        "provider": provider,
        "start": start.strftime('%Y-%m-%d %H:%M:%S'),
        "end": now.strftime('%Y-%m-%d %H:%M:%S'),
    }
    try:
        return reader.reader.execute_query(query, params)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Cost timeseries query failed: %s", exc)
        return []


def _calculate_cost_metrics(
    customer_id: str,
    provider: Optional[str],
) -> tuple[CostMetricsPayload, List[TimeseriesPointPayload]]:
    """Calculate cost metrics for dashboard"""
    logger.info(f"Calculating cost metrics for customer: {customer_id}, provider: {provider}")
    metrics = CostMetricsPayload()
    timeseries: Dict[str, TimeseriesPointPayload] = {}

    try:
        with CostReader() as reader:
            selected_provider = provider or _lookup_primary_provider(reader, customer_id)
            logger.info(f"Selected provider: {selected_provider}")
            if not selected_provider:
                logger.debug("No cost provider found for customer %s", customer_id)
                return metrics, []

            total_cost = reader.get_total_cost(customer_id, selected_provider, days=30)
            metrics.total_cost = _decimal_to_float(total_cost.get("total_cost")) or 0.0
            metrics.monthly_cost = metrics.total_cost
            metrics.currency = total_cost.get("currency") or "USD"

            latest_costs = reader.get_latest_costs(customer_id, selected_provider, limit=24)
            if latest_costs:
                recent_sum = sum(_decimal_to_float(item.get("cost")) or 0.0 for item in latest_costs[:24])
                metrics.daily_cost = recent_sum

            trends = reader.get_cost_trends(customer_id, selected_provider, days=30, group_by="day")
            if len(trends) >= 2:
                latest = _decimal_to_float(trends[0].get("total_cost")) or 0.0
                previous = _decimal_to_float(trends[1].get("total_cost")) or 0.0
                if previous > 0:
                    metrics.cost_trend = ((latest - previous) / previous) * 100

            cost_series = _fetch_cost_timeseries(reader, customer_id, selected_provider)
            for item in cost_series:
                period = item.get("period")
                key = period.isoformat() if isinstance(period, datetime) else str(period)
                point = timeseries.setdefault(key, TimeseriesPointPayload(timestamp=key))
                point.cost = _decimal_to_float(item.get("total_cost"))

    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Cost metric calculation failed: %s", exc)

    return metrics, list(sorted(timeseries.values(), key=lambda p: p.timestamp))


def _calculate_performance_metrics(customer_id: str, provider: Optional[str]) -> PerformanceMetricsPayload:
    metrics = PerformanceMetricsPayload()
    
    try:
        reader = ClickHouseReader()
        query = """
            SELECT
                metric_name,
                argMax(metric_value, timestamp) AS metric_value,
                argMax(metadata, timestamp) AS metadata
            FROM performance_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= now() - INTERVAL 1 HOUR
            GROUP BY metric_name
        """
        params = {
            "customer_id": customer_id,
            "provider": provider or DEFAULT_PROVIDER,
        }
        rows = reader.execute_query(query, params)
        if not rows:
            return metrics
        
        data: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            meta = row.get("metadata")
            metadata: Dict[str, Any] = {}
            if isinstance(meta, str) and meta:
                try:
                    metadata = json.loads(meta)
                except json.JSONDecodeError:
                    metadata = {}
            data[row["metric_name"]] = {
                "value": row.get("metric_value"),
                "metadata": metadata,
            }
        
        def _value(name: str) -> Optional[float]:
            return _to_float(data.get(name, {}).get("value"))
        
        latency_p50 = _value("latency_p50")
        if latency_p50 is not None:
            metrics.latency_p50 = latency_p50
        latency_p95 = _value("latency_p95")
        if latency_p95 is not None:
            metrics.latency_p95 = latency_p95
        latency_p99 = _value("latency_p99")
        if latency_p99 is not None:
            metrics.latency_p99 = latency_p99
        
        requests_per_second = _value("requests_per_second")
        if requests_per_second is not None:
            metrics.requests_per_second = requests_per_second
            metrics.throughput = requests_per_second
        
        token_throughput = _value("token_throughput")
        if token_throughput is not None:
            metrics.throughput = token_throughput
        
        error_rate = _value("error_rate")
        if error_rate is not None:
            metrics.error_rate = error_rate * 100 if error_rate < 1 else error_rate
        
    except Exception as e:
        logger.warning(f"Failed to calculate performance metrics from ClickHouse: {e}")
    
    return metrics


def _calculate_resource_metrics(customer_id: str, provider: Optional[str]) -> ResourceMetricsPayload:
    metrics = ResourceMetricsPayload()
    try:
        reader = ClickHouseReader()
        query = """
            SELECT
                resource_type,
                JSONExtractString(metadata, 'metric_name') AS metric_name,
                argMax(utilization, timestamp) AS utilization,
                argMax(capacity, timestamp) AS capacity,
                argMax(metadata, timestamp) AS metadata
            FROM resource_metrics
            WHERE customer_id = %(customer_id)s
              AND provider = %(provider)s
              AND timestamp >= now() - INTERVAL 1 HOUR
            GROUP BY resource_type, metric_name
        """
        params = {
            "customer_id": customer_id,
            "provider": provider or DEFAULT_PROVIDER,
        }
        rows = reader.execute_query(query, params)
        if not rows:
            return metrics
        
        for row in rows:
            resource_type = row.get("resource_type")
            metric_name = row.get("metric_name")
            value = _to_float(row.get("utilization"))
            capacity = _to_float(row.get("capacity"))
            metadata_raw = row.get("metadata")
            metadata: Dict[str, Any] = {}
            if isinstance(metadata_raw, str) and metadata_raw:
                try:
                    metadata = json.loads(metadata_raw)
                except json.JSONDecodeError:
                    metadata = {}
            
            if resource_type == "gpu":
                if metric_name == "gpu_utilization":
                    if value is not None:
                        metrics.gpu_utilization = value
                    used_value = _to_float(metadata.get("gpu_memory_used_gb"))
                    total_value = _to_float(metadata.get("gpu_memory_total_gb"))
                    if used_value is not None:
                        metrics.gpu_memory_used = used_value
                    if total_value is not None:
                        metrics.gpu_memory_total = total_value
                elif metric_name == "gpu_memory_used":
                    if capacity is not None:
                        metrics.gpu_memory_used = capacity
                    total_value = _to_float(metadata.get("gpu_memory_total_gb"))
                    if total_value is not None:
                        metrics.gpu_memory_total = total_value
            elif resource_type == "cpu" and metric_name == "cpu_utilization":
                if value is not None:
                    metrics.cpu_utilization = value
            elif resource_type == "memory" and metric_name == "memory_utilization":
                if value is not None:
                    metrics.memory_utilization = value
        return metrics
    except Exception as exc:
        logger.warning("Failed to calculate resource metrics from ClickHouse: %s", exc)
        return metrics


def _calculate_quality_metrics(customer_id: str) -> QualityMetricsPayload:
    metrics = QualityMetricsPayload()
    query = """
        SELECT
            AVG(overall_quality_score) AS quality,
            AVG(relevance_score) AS relevance,
            AVG(coherence_score) AS coherence,
            AVG(toxicity_score) AS toxicity,
            AVG(CASE WHEN hallucination_detected THEN 1 ELSE 0 END) * 100 AS hallucinations
        FROM quality_metrics
        WHERE customer_id = %s
    """

    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, (customer_id,))
        row = cursor.fetchone()

    if not row:
        return metrics

    metrics.quality_score = _decimal_to_float(row[0]) or 0.0
    metrics.relevance_score = _decimal_to_float(row[1]) or 0.0
    metrics.coherence_score = _decimal_to_float(row[2]) or 0.0
    metrics.toxicity_score = _decimal_to_float(row[3]) or 0.0
    metrics.hallucination_rate = _decimal_to_float(row[4]) or 0.0
    return metrics


def _fetch_latency_series(customer_id: str) -> Dict[str, float]:
    query = """
        SELECT
            date_trunc('hour', timestamp) AS bucket,
            AVG(latency_ms) AS latency
        FROM quality_metrics
        WHERE customer_id = %s
          AND timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY bucket
        ORDER BY bucket
    """
    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, (customer_id,))
        rows = cursor.fetchall()
    if not rows:
        return {}
    return {
        bucket.isoformat(): _decimal_to_float(latency) or 0.0
        for bucket, latency in rows
        if bucket
    }


def _fetch_gpu_series(customer_id: str, provider: Optional[str]) -> Dict[str, float]:
    query = """
        SELECT
            toStartOfHour(timestamp) AS bucket,
            avg(utilization) AS gpu_util
        FROM resource_metrics
        WHERE customer_id = %(customer_id)s
          AND provider = %(provider)s
          AND resource_type = 'gpu'
          AND JSONExtractString(metadata, 'metric_name') = 'gpu_utilization'
          AND timestamp >= now() - INTERVAL 24 HOUR
        GROUP BY bucket
        ORDER BY bucket
    """
    try:
        reader = ClickHouseReader()
        rows = reader.execute_query(query, {
            "customer_id": customer_id,
            "provider": provider or DEFAULT_PROVIDER,
        })
    except Exception as exc:
        logger.debug("GPU series query failed: %s", exc)
        return {}
    if not rows:
        return {}
    series: Dict[str, float] = {}
    for row in rows:
        bucket = row.get("bucket")
        value = _to_float(row.get("gpu_util"))
        if bucket and value is not None:
            if isinstance(bucket, datetime):
                series[bucket.isoformat()] = value
            else:
                series[str(bucket)] = value
    return series


def _fetch_quality_series(customer_id: str) -> Dict[str, float]:
    query = """
        SELECT
            date_trunc('hour', timestamp) AS bucket,
            AVG(overall_quality_score) AS quality
        FROM quality_metrics
        WHERE customer_id = %s
          AND timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY bucket
        ORDER BY bucket
    """
    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, (customer_id,))
        rows = cursor.fetchall()
    if not rows:
        return {}
    return {
        bucket.isoformat(): ((_decimal_to_float(value) or 0.0) * 100)
        for bucket, value in rows
        if bucket
    }


async def _build_dashboard_payload(
    customer_id: str,
    provider: Optional[str],
) -> DashboardPayload:
    agents = await run_in_threadpool(_fetch_agents)
    await _refresh_agent_heartbeats(agents)
    recommendations = await run_in_threadpool(_fetch_recommendations, customer_id)
    executions = await run_in_threadpool(_fetch_recent_executions, customer_id)

    cost_metrics, cost_series = await run_in_threadpool(
        _calculate_cost_metrics,
        customer_id,
        provider,
    )

    performance_metrics = await run_in_threadpool(
        _calculate_performance_metrics,
        customer_id,
        provider,
    )
    resource_metrics = await run_in_threadpool(
        _calculate_resource_metrics,
        customer_id,
        provider,
    )
    quality_metrics = await run_in_threadpool(
        _calculate_quality_metrics,
        customer_id,
    )

    latency_series, gpu_series, quality_series = await asyncio.gather(
        run_in_threadpool(_fetch_latency_series, customer_id),
        run_in_threadpool(_fetch_gpu_series, customer_id, provider),
        run_in_threadpool(_fetch_quality_series, customer_id),
    )

    series_map: Dict[str, TimeseriesPointPayload] = {
        point.timestamp: point for point in cost_series
    }

    for timestamp, latency in latency_series.items():
        series_map.setdefault(timestamp, TimeseriesPointPayload(timestamp=timestamp)).latency = latency

    for timestamp, gpu in gpu_series.items():
        series_map.setdefault(timestamp, TimeseriesPointPayload(timestamp=timestamp)).gpu = gpu

    for timestamp, quality in quality_series.items():
        series_map.setdefault(timestamp, TimeseriesPointPayload(timestamp=timestamp)).quality = quality

    sorted_series = sorted(series_map.values(), key=lambda p: p.timestamp)

    metrics_payload = {
        "cost": cost_metrics.model_dump(),
        "performance": performance_metrics.model_dump(),
        "resource": resource_metrics.model_dump(),
        "quality": quality_metrics.model_dump(),
    }
    try:
        with CostReader() as reader:
            metrics_payload["runpod"] = _build_runpod_dashboard_section(reader, customer_id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("RunPod dashboard section unavailable: %s", exc)
        metrics_payload["runpod"] = _runpod_dashboard_placeholder(str(exc))

    potential = sum(
        rec.estimated_savings or 0.0
        for rec in recommendations
        if rec.status == "pending" and rec.estimated_savings
    )
    metrics_payload["cost"]["savings_potential"] = potential

    return DashboardPayload(
        agents=agents,
        metrics=metrics_payload,
        timeseries=sorted_series[-12:],
        recommendations=recommendations,
        recent_executions=executions,
    )


@router.get("/dashboard", response_model=DashboardPayload)
async def get_dashboard(  # pragma: no cover - exercised in integration
    customer_id: Optional[str] = Query(None, description="Customer identifier"),
    provider: Optional[str] = Query(None, description="Preferred cost provider"),
):
    active_customer = customer_id or DEFAULT_CUSTOMER_ID
    active_provider = provider or DEFAULT_PROVIDER
    try:
        return await _build_dashboard_payload(active_customer, active_provider)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to build dashboard for %s: %s", active_customer, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to build dashboard payload")

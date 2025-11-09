"""
Dashboard API - Aggregates data from ClickHouse and PostgreSQL for Portal UI

This module aligns the API response with the Portal dashboard contract so
OptiInfra agents appear with real-time status updates and metrics.
"""
from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import psycopg2
from clickhouse_driver import Client
from fastapi import APIRouter, HTTPException, Query
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field

from ..config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, handling Decimal/None gracefully."""
    if value is None:
        return default
    if isinstance(value, Decimal):
        value = float(value)
    try:
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


class Agent(BaseModel):
    agent_id: str
    agent_name: str
    agent_type: str
    version: Optional[str] = None
    status: str
    last_heartbeat: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    host: Optional[str] = None
    port: Optional[int] = None


class CostMetrics(BaseModel):
    total_cost: float = 0.0
    daily_cost: float = 0.0
    monthly_cost: float = 0.0
    cost_trend: float = 0.0
    savings_potential: float = 0.0
    currency: str = "USD"


class PerformanceMetrics(BaseModel):
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    throughput: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0


class ResourceMetrics(BaseModel):
    gpu_utilization: float = 0.0
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    gpu_memory_used: float = 0.0
    gpu_memory_total: float = 0.0


class QualityMetrics(BaseModel):
    quality_score: float = 0.0
    relevance_score: float = 0.0
    coherence_score: float = 0.0
    hallucination_rate: float = 0.0
    toxicity_score: float = 0.0


class DashboardMetrics(BaseModel):
    cost: CostMetrics
    performance: PerformanceMetrics
    resource: ResourceMetrics
    quality: QualityMetrics


class DashboardTimeseriesPoint(BaseModel):
    timestamp: str
    cost: Optional[float] = None
    latency: Optional[float] = None
    gpu: Optional[float] = None
    quality: Optional[float] = None


class DashboardData(BaseModel):
    agents: List[Agent]
    metrics: DashboardMetrics
    timeseries: List[DashboardTimeseriesPoint] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    recent_executions: List[Dict[str, Any]] = Field(default_factory=list)


def get_clickhouse_client() -> Client:
    """Create ClickHouse client connection."""
    try:
        return Client(
            host=config.CLICKHOUSE_HOST,
            port=config.CLICKHOUSE_PORT,
            database=config.CLICKHOUSE_DATABASE,
            user=config.CLICKHOUSE_USER,
            password=config.CLICKHOUSE_PASSWORD,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to connect to ClickHouse: %s", exc)
        raise HTTPException(status_code=500, detail=f"Database connection failed: {exc}")


def get_postgres_connection():
    """Create PostgreSQL connection."""
    try:
        return psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            dbname=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to connect to PostgreSQL: %s", exc)
        raise HTTPException(status_code=500, detail=f"Metadata connection failed: {exc}")


def _map_agent_status(status: Optional[Any]) -> str:
    mapping = {
        "healthy": "active",
        "starting": "inactive",
        "degraded": "degraded",
        "failed": "error",
        "stopped": "inactive",
    }
    if status is None:
        return "inactive"
    normalized = str(status).lower()
    return mapping.get(normalized, "inactive")


def _parse_capabilities(raw: Any) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
            return [str(parsed)]
        except json.JSONDecodeError:
            return [raw]
    return [str(raw)]


def _parse_endpoint(endpoint: Optional[str]) -> Dict[str, Optional[Any]]:
    if not endpoint:
        return {"host": None, "port": None}
    parsed = urlparse(endpoint)
    return {
        "host": parsed.hostname or None,
        "port": parsed.port,
    }


def fetch_agents(conn) -> List[Agent]:
    """Fetch registered agents from PostgreSQL."""
    query = """
        SELECT id, type, name, version, status, endpoint, capabilities, last_heartbeat
        FROM agents
        ORDER BY type
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to fetch agents: %s", exc)
        return []

    agents: List[Agent] = []
    for row in rows:
        endpoint_parts = _parse_endpoint(row.get("endpoint"))
        last_heartbeat = row.get("last_heartbeat")
        if last_heartbeat is not None:
            last_heartbeat = last_heartbeat.isoformat()
        agents.append(
            Agent(
                agent_id=str(row.get("id")),
                agent_name=row.get("name") or "unknown-agent",
                agent_type=str(row.get("type") or "unknown").lower(),
                version=row.get("version"),
                status=_map_agent_status(row.get("status")),
                last_heartbeat=last_heartbeat,
                capabilities=_parse_capabilities(row.get("capabilities")),
                host=endpoint_parts["host"],
                port=endpoint_parts["port"],
            )
        )
    return agents


def build_fallback_agents() -> List[Agent]:
    """Return fallback agents when database has no records."""
    now = datetime.utcnow()
    return [
        Agent(
            agent_id="fallback-cost",
            agent_name="Cost Agent",
            agent_type="cost",
            version="1.0.0",
            status="inactive",
            last_heartbeat=now.isoformat(),
            capabilities=["cost_tracking", "optimization"],
            host="localhost",
            port=8001,
        ),
        Agent(
            agent_id="fallback-performance",
            agent_name="Performance Agent",
            agent_type="performance",
            version="1.0.0",
            status="inactive",
            last_heartbeat=now.isoformat(),
            capabilities=["performance_monitoring"],
            host="localhost",
            port=8002,
        ),
        Agent(
            agent_id="fallback-resource",
            agent_name="Resource Agent",
            agent_type="resource",
            version="1.0.0",
            status="inactive",
            last_heartbeat=now.isoformat(),
            capabilities=["resource_monitoring"],
            host="localhost",
            port=8003,
        ),
        Agent(
            agent_id="fallback-application",
            agent_name="Application Agent",
            agent_type="application",
            version="1.0.0",
            status="inactive",
            last_heartbeat=now.isoformat(),
            capabilities=["quality_monitoring"],
            host="localhost",
            port=8004,
        ),
    ]


def _provider_clause(provider: Optional[str]) -> str:
    return "AND provider = %(provider)s" if provider else ""


def _with_provider(params: Dict[str, Any], provider: Optional[str]) -> Dict[str, Any]:
    if provider:
        params = dict(params)
        params["provider"] = provider
    return params


def fetch_cost_sum(
    client: Client,
    customer_id: str,
    provider: Optional[str],
    start: datetime,
    end: datetime,
) -> float:
    query = f"""
        SELECT sum(amount)
        FROM optiinfra_metrics.cost_metrics
        WHERE customer_id = %(customer_id)s
          AND timestamp >= %(start)s
          AND timestamp <= %(end)s
          {_provider_clause(provider)}
    """
    params = _with_provider({"customer_id": customer_id, "start": start, "end": end}, provider)
    result = client.execute(query, params)
    if result and result[0][0] is not None:
        return safe_float(result[0][0])
    return 0.0


def fetch_cost_metrics(
    client: Client,
    customer_id: str,
    provider: Optional[str],
    start: datetime,
    end: datetime,
    hours: int,
) -> tuple[CostMetrics, List[DashboardTimeseriesPoint]]:
    query = f"""
        SELECT
            toStartOfHour(timestamp) AS hour,
            SUM(amount) AS total_cost
        FROM optiinfra_metrics.cost_metrics
        WHERE customer_id = %(customer_id)s
          AND timestamp >= %(start)s
          AND timestamp <= %(end)s
          {_provider_clause(provider)}
        GROUP BY hour
        ORDER BY hour ASC
    """
    params = _with_provider({"customer_id": customer_id, "start": start, "end": end}, provider)
    rows = client.execute(query, params)

    cost_series: List[DashboardTimeseriesPoint] = []
    for hour, total in rows:
        if hour:
            cost_series.append(
                DashboardTimeseriesPoint(
                    timestamp=hour.isoformat(),
                    cost=safe_float(total),
                )
            )

    if not cost_series:
        logger.warning("No cost data found for customer %s", customer_id)
        step = max(1, hours // 6) or 1
        fallback_start = start
        for offset in range(0, hours, step):
            timestamp = (fallback_start + timedelta(hours=offset)).isoformat()
            cost_series.append(DashboardTimeseriesPoint(timestamp=timestamp, cost=0.0))

    daily_cost = fetch_cost_sum(client, customer_id, provider, end - timedelta(hours=24), end)
    previous_day_cost = fetch_cost_sum(
        client,
        customer_id,
        provider,
        end - timedelta(hours=48),
        end - timedelta(hours=24),
    )
    monthly_cost = fetch_cost_sum(client, customer_id, provider, end - timedelta(days=30), end)

    total_cost = monthly_cost or sum(point.cost or 0.0 for point in cost_series)
    cost_trend = 0.0
    if previous_day_cost > 0:
        cost_trend = ((daily_cost - previous_day_cost) / previous_day_cost) * 100

    metrics = CostMetrics(
        total_cost=total_cost,
        daily_cost=daily_cost,
        monthly_cost=monthly_cost or total_cost,
        cost_trend=cost_trend,
        savings_potential=0.0,
        currency="USD",
    )
    return metrics, cost_series


def fetch_performance_metrics(
    client: Client,
    customer_id: str,
    provider: Optional[str],
    start: datetime,
    end: datetime,
) -> PerformanceMetrics:
    query = f"""
        SELECT
            quantileIf(0.5)(metric_value, metric_name = 'latency') AS latency_p50,
            quantileIf(0.95)(metric_value, metric_name = 'latency') AS latency_p95,
            quantileIf(0.99)(metric_value, metric_name = 'latency') AS latency_p99,
            avgIf(metric_value, metric_name = 'throughput') AS throughput,
            avgIf(metric_value, metric_name = 'requests_per_second') AS requests_per_second,
            avgIf(metric_value, metric_name = 'error_rate') AS error_rate
        FROM optiinfra_metrics.performance_metrics
        WHERE customer_id = %(customer_id)s
          AND timestamp >= %(start)s
          AND timestamp <= %(end)s
          {_provider_clause(provider)}
    """
    params = _with_provider({"customer_id": customer_id, "start": start, "end": end}, provider)
    result = client.execute(query, params)

    metrics = PerformanceMetrics()
    if result:
        row = result[0]
        metrics.latency_p50 = safe_float(row[0])
        metrics.latency_p95 = safe_float(row[1]) or metrics.latency_p50
        metrics.latency_p99 = safe_float(row[2]) or metrics.latency_p95
        metrics.throughput = safe_float(row[3])
        metrics.requests_per_second = safe_float(row[4])
        metrics.error_rate = safe_float(row[5])
    return metrics


def fetch_resource_metrics(
    client: Client,
    customer_id: str,
    provider: Optional[str],
    start: datetime,
    end: datetime,
) -> ResourceMetrics:
    query = f"""
        SELECT
            avgIf(metric_value, metric_name IN ('gpu_utilization')) AS gpu_utilization,
            avgIf(metric_value, metric_name IN ('cpu_usage', 'cpu_utilization')) AS cpu_utilization,
            avgIf(metric_value, metric_name IN ('memory_usage', 'memory_utilization')) AS memory_utilization,
            avgIf(metric_value, metric_name IN ('gpu_memory_used', 'gpu_memory_used_gb')) AS gpu_memory_used,
            avgIf(metric_value, metric_name IN ('gpu_memory_total', 'gpu_memory_total_gb')) AS gpu_memory_total
        FROM optiinfra_metrics.performance_metrics
        WHERE customer_id = %(customer_id)s
          AND timestamp >= %(start)s
          AND timestamp <= %(end)s
          {_provider_clause(provider)}
    """
    params = _with_provider({"customer_id": customer_id, "start": start, "end": end}, provider)
    result = client.execute(query, params)

    metrics = ResourceMetrics()
    if result:
        row = result[0]
        metrics.gpu_utilization = safe_float(row[0])
        metrics.cpu_utilization = safe_float(row[1])
        metrics.memory_utilization = safe_float(row[2])
        metrics.gpu_memory_used = safe_float(row[3])
        metrics.gpu_memory_total = safe_float(row[4])
    return metrics


def _normalize_quality(value: float) -> float:
    if value <= 1.0:
        return value * 100.0
    return value


def fetch_quality_metrics(
    client: Client,
    customer_id: str,
    provider: Optional[str],
    start: datetime,
    end: datetime,
) -> QualityMetrics:
    query = f"""
        SELECT
            avgIf(score, metric_type IN ('quality', 'quality_score')) AS quality_score,
            avgIf(score, metric_type IN ('relevance', 'relevance_score')) AS relevance_score,
            avgIf(score, metric_type IN ('coherence', 'coherence_score')) AS coherence_score,
            avgIf(score, metric_type IN ('toxicity', 'toxicity_score')) AS toxicity_score,
            avgIf(score, metric_type IN ('hallucination', 'hallucination_rate')) AS hallucination_rate
        FROM optiinfra_metrics.application_metrics
        WHERE customer_id = %(customer_id)s
          AND timestamp >= %(start)s
          AND timestamp <= %(end)s
          {_provider_clause(provider)}
    """
    params = _with_provider({"customer_id": customer_id, "start": start, "end": end}, provider)
    result = client.execute(query, params)

    metrics = QualityMetrics()
    if result:
        row = result[0]
        metrics.quality_score = _normalize_quality(safe_float(row[0]))
        metrics.relevance_score = _normalize_quality(safe_float(row[1]))
        metrics.coherence_score = _normalize_quality(safe_float(row[2]))
        metrics.toxicity_score = _normalize_quality(safe_float(row[3]))
        metrics.hallucination_rate = _normalize_quality(safe_float(row[4]))
    return metrics


def fetch_latency_series(
    client: Client,
    customer_id: str,
    provider: Optional[str],
    start: datetime,
    end: datetime,
) -> Dict[str, float]:
    query = f"""
        SELECT
            toStartOfHour(timestamp) AS hour,
            quantileIf(0.95)(metric_value, metric_name = 'latency') AS latency
        FROM optiinfra_metrics.performance_metrics
        WHERE customer_id = %(customer_id)s
          AND timestamp >= %(start)s
          AND timestamp <= %(end)s
          {_provider_clause(provider)}
        GROUP BY hour
        ORDER BY hour ASC
    """
    params = _with_provider({"customer_id": customer_id, "start": start, "end": end}, provider)
    rows = client.execute(query, params)

    series: Dict[str, float] = {}
    for hour, latency in rows:
        if hour is not None and latency is not None:
            series[hour.isoformat()] = safe_float(latency)
    return series


def fetch_gpu_series(
    client: Client,
    customer_id: str,
    provider: Optional[str],
    start: datetime,
    end: datetime,
) -> Dict[str, float]:
    query = f"""
        SELECT
            toStartOfHour(timestamp) AS hour,
            avgIf(metric_value, metric_name IN ('gpu_utilization')) AS gpu
        FROM optiinfra_metrics.performance_metrics
        WHERE customer_id = %(customer_id)s
          AND timestamp >= %(start)s
          AND timestamp <= %(end)s
          {_provider_clause(provider)}
        GROUP BY hour
        ORDER BY hour ASC
    """
    params = _with_provider({"customer_id": customer_id, "start": start, "end": end}, provider)
    rows = client.execute(query, params)

    series: Dict[str, float] = {}
    for hour, gpu in rows:
        if hour is not None and gpu is not None:
            series[hour.isoformat()] = safe_float(gpu)
    return series


def merge_timeseries(
    cost_series: List[DashboardTimeseriesPoint],
    latency_series: Dict[str, float],
    gpu_series: Dict[str, float],
) -> List[DashboardTimeseriesPoint]:
    merged: Dict[str, DashboardTimeseriesPoint] = {
        point.timestamp: DashboardTimeseriesPoint(**point.model_dump()) for point in cost_series
    }

    for timestamp, latency in latency_series.items():
        merged.setdefault(timestamp, DashboardTimeseriesPoint(timestamp=timestamp)).latency = latency

    for timestamp, gpu in gpu_series.items():
        merged.setdefault(timestamp, DashboardTimeseriesPoint(timestamp=timestamp)).gpu = gpu

    return sorted(merged.values(), key=lambda item: item.timestamp)


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    customer_id: str = Query(default="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    hours: int = Query(default=24, description="Number of hours to look back"),
    provider: Optional[str] = Query(default=None, description="Filter by provider (e.g., runpod, vultr)"),
):
    """Return dashboard data aligned with Portal expectations."""
    hours = max(1, hours)
    logger.info(
        "Dashboard data requested for customer: %s, hours: %s, provider: %s",
        customer_id,
        hours,
        provider,
    )

    clickhouse_client = get_clickhouse_client()
    postgres_conn = None
    try:
        postgres_conn = get_postgres_connection()
    except HTTPException:
        clickhouse_client.disconnect()
        raise

    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        agents = fetch_agents(postgres_conn)
        if not agents:
            agents = build_fallback_agents()

        cost_metrics, cost_series = fetch_cost_metrics(
            clickhouse_client,
            customer_id,
            provider,
            start_time,
            end_time,
            hours,
        )
        performance_metrics = fetch_performance_metrics(
            clickhouse_client,
            customer_id,
            provider,
            start_time,
            end_time,
        )
        resource_metrics = fetch_resource_metrics(
            clickhouse_client,
            customer_id,
            provider,
            start_time,
            end_time,
        )
        quality_metrics = fetch_quality_metrics(
            clickhouse_client,
            customer_id,
            provider,
            start_time,
            end_time,
        )

        latency_series = fetch_latency_series(
            clickhouse_client,
            customer_id,
            provider,
            start_time,
            end_time,
        )
        gpu_series = fetch_gpu_series(
            clickhouse_client,
            customer_id,
            provider,
            start_time,
            end_time,
        )

        timeseries = merge_timeseries(cost_series, latency_series, gpu_series)

        metrics = DashboardMetrics(
            cost=cost_metrics,
            performance=performance_metrics,
            resource=resource_metrics,
            quality=quality_metrics,
        )

        return DashboardData(
            agents=agents,
            metrics=metrics,
            timeseries=timeseries,
            recommendations=[],
            recent_executions=[],
        )

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to generate dashboard data: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard data: {exc}")
    finally:
        clickhouse_client.disconnect()
        if postgres_conn:
            postgres_conn.close()


@router.get("/dashboard/providers")
async def get_provider_summary(
    customer_id: str = Query(default="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
):
    """Return summary of providers with available cost data."""
    client = get_clickhouse_client()
    try:
        query = """
            SELECT
                provider,
                SUM(amount) AS total_cost,
                COUNT(DISTINCT instance_id) AS instances,
                MAX(timestamp) AS last_collection
            FROM optiinfra_metrics.cost_metrics
            WHERE customer_id = %(customer_id)s
            GROUP BY provider
            ORDER BY total_cost DESC
        """
        rows = client.execute(query, {"customer_id": customer_id})

        providers: List[Dict[str, Any]] = []
        for provider, total_cost, instances, last_collection in rows:
            providers.append(
                {
                    "provider": provider,
                    "total_cost": safe_float(total_cost),
                    "instances": int(instances or 0),
                    "last_collection": last_collection.isoformat() if last_collection else None,
                    "status": "connected" if last_collection else "not_configured",
                }
            )

        return {
            "customer_id": customer_id,
            "providers": providers,
            "total_providers": len(providers),
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to get provider summary: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get provider summary: {exc}")
    finally:
        client.disconnect()

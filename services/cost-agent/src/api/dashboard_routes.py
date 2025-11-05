"""Portal dashboard aggregation routes."""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

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


def _calculate_performance_metrics(customer_id: str) -> PerformanceMetricsPayload:
    metrics = PerformanceMetricsPayload()
    
    try:
        reader = ClickHouseReader()
        query = """
            SELECT
                quantile(0.5)(metric_value) AS latency_p50,
                quantile(0.95)(metric_value) AS latency_p95,
                quantile(0.99)(metric_value) AS latency_p99,
                count() AS total,
                max(timestamp) - min(timestamp) AS window_seconds
            FROM performance_metrics
            WHERE customer_id = %(customer_id)s 
            AND metric_name = 'latency'
            AND timestamp >= now() - INTERVAL 1 HOUR
        """
        
        results = reader.execute_query(query, {"customer_id": customer_id})
        
        if not results or not results[0].get("latency_p50"):
            return metrics
        
        row = results[0]
        metrics.latency_p50 = float(row["latency_p50"])
        metrics.latency_p95 = float(row["latency_p95"]) if row["latency_p95"] else metrics.latency_p50
        metrics.latency_p99 = float(row["latency_p99"]) if row["latency_p99"] else metrics.latency_p95
        
        total_requests = row["total"] or 0
        window_seconds = row["window_seconds"] or 0
        if window_seconds > 0 and total_requests > 0:
            metrics.requests_per_second = total_requests / window_seconds
            metrics.throughput = metrics.requests_per_second * 60
        
    except Exception as e:
        logger.warning(f"Failed to calculate performance metrics from ClickHouse: {e}")
    
    return metrics


def _calculate_resource_metrics(customer_id: str) -> ResourceMetricsPayload:
    metrics = ResourceMetricsPayload()
    query = """
        SELECT
            AVG(CASE WHEN resource_type = 'gpu' AND metric_name = 'utilization' THEN metric_value END) AS gpu_util,
            AVG(CASE WHEN resource_type = 'cpu' AND metric_name = 'utilization' THEN metric_value END) AS cpu_util,
            AVG(CASE WHEN resource_type = 'memory' AND metric_name = 'used' THEN (metadata->>'utilization_percent')::numeric END) AS mem_util,
            AVG(CASE WHEN resource_type = 'gpu' AND metric_name = 'utilization' THEN (metadata->>'gpu_memory_used_gb')::numeric END) AS gpu_mem_used,
            AVG(CASE WHEN resource_type = 'gpu' AND metric_name = 'utilization' THEN (metadata->>'gpu_memory_total_gb')::numeric END) AS gpu_mem_total
        FROM resource_metrics
        WHERE customer_id = %s
    """

    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, (customer_id,))
        row = cursor.fetchone()

    if not row:
        return metrics

    metrics.gpu_utilization = _decimal_to_float(row[0]) or 0.0
    metrics.cpu_utilization = _decimal_to_float(row[1]) or 0.0
    metrics.memory_utilization = _decimal_to_float(row[2]) or 0.0
    metrics.gpu_memory_used = _decimal_to_float(row[3]) or 0.0
    metrics.gpu_memory_total = _decimal_to_float(row[4]) or 0.0
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


def _fetch_gpu_series(customer_id: str) -> Dict[str, float]:
    query = """
        SELECT
            date_trunc('hour', timestamp) AS bucket,
            AVG(metric_value) AS gpu_util
        FROM resource_metrics
        WHERE customer_id = %s
          AND resource_type = 'gpu'
          AND metric_name = 'utilization'
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
        bucket.isoformat(): _decimal_to_float(value) or 0.0
        for bucket, value in rows
        if bucket
    }


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
    )
    resource_metrics = await run_in_threadpool(
        _calculate_resource_metrics,
        customer_id,
    )
    quality_metrics = await run_in_threadpool(
        _calculate_quality_metrics,
        customer_id,
    )

    latency_series, gpu_series, quality_series = await asyncio.gather(
        run_in_threadpool(_fetch_latency_series, customer_id),
        run_in_threadpool(_fetch_gpu_series, customer_id),
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

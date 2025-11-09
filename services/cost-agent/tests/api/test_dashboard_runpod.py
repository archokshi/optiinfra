"""Tests for RunPod dashboard helpers."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pytest

from src.api.dashboard_routes import (
    _build_runpod_dashboard_section,
    _runpod_dashboard_placeholder,
)


class _FakeCostReader:
    """Minimal stub that mimics CostReader for RunPod helpers."""

    def __init__(
        self,
        billing_rows: List[Dict[str, Any]],
        endpoint_rows: List[Dict[str, Any]],
        pod_rows: List[Dict[str, Any]],
        job_stats_rows: Optional[List[Dict[str, Any]]] = None,
        job_series_rows: Optional[List[Dict[str, Any]]] = None,
        job_status_rows: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        # The helpers mutate the rows, so work with shallow copies per call.
        self._billing_rows = billing_rows
        self._endpoint_rows = endpoint_rows
        self._pod_rows = pod_rows
        self._job_stats_rows = job_stats_rows or []
        self._job_series_rows = job_series_rows or []
        self._job_status_rows = job_status_rows or []
        self.reader = self

    def get_runpod_billing_summary(self, customer_id: str, days: int = 30):
        return [row.copy() for row in self._billing_rows]

    def execute_query(self, query: str, params: Dict[str, Any]):
        if "runpod_endpoint_health_latest" in query:
            return [row.copy() for row in self._endpoint_rows]
        if "runpod_pods_latest" in query:
            return [row.copy() for row in self._pod_rows]
        lowered = query.lower()
        if "quantileexact" in lowered or "avgornull" in lowered:
            return [row.copy() for row in self._job_stats_rows]
        if "tostartoffiveminute" in lowered:
            return [row.copy() for row in self._job_series_rows]
        if "group by status" in lowered and "runpod_jobs" in lowered:
            return [row.copy() for row in self._job_status_rows]
        return []


def test_runpod_billing_section_cost_agent():
    """Ensure helper flattens and normalises cost-facing RunPod data."""
    reader = _FakeCostReader(
        billing_rows=[
            {
                "snapshot_date": date(2024, 5, 1),
                "avg_spend_per_hr": Decimal("1.25"),
                "lifetime_spend": "42.5",
                "balance": Decimal("7.0"),
                "spend_breakdown": {"gpuCloud": {"totalSpend": 12}},
            }
        ],
        endpoint_rows=[
            {
                "endpoint_id": "endpoint-1",
                "observed_ts": datetime(2024, 5, 1, 12, 30, tzinfo=timezone.utc),
                "jobs_completed": 5,
                "jobs_failed": 1,
                "jobs_in_progress": 2,
                "jobs_in_queue": 0,
                "workers_idle": 1,
                "workers_running": 2,
                "workers_throttled": 0,
                "metadata_json": '{"region": "ams1"}',
            }
        ],
        pod_rows=[
            {
                "pod_id": "pod-1",
                "snapshot_ts": datetime(2024, 5, 1, 13, 0, tzinfo=timezone.utc),
                "status": "running",
                "gpu_type_id": "24gb",
                "gpu_count": 1,
                "vcpu_count": 8,
                "memory_gb": 24,
                "cost_per_hour": Decimal("3.5"),
                "metadata_json": "not-json",
            }
        ],
    )

    section = _build_runpod_dashboard_section(reader, "customer-123")

    assert section["billing"][0]["snapshot_date"] == "2024-05-01"
    assert section["billing"][0]["avg_spend_per_hr"] == 1.25
    assert section["billing"][0]["lifetime_spend"] == 42.5
    assert section["billing"][0]["balance"] == 7.0
    assert section["billing"][0]["spend_breakdown"] == {"gpuCloud": {"totalSpend": 12}}

    endpoint = section["endpoint_health"][0]
    assert endpoint["observed_ts"] == "2024-05-01T12:30:00+00:00"
    assert endpoint["metadata"] == {"region": "ams1"}

    pod = section["pods"][0]
    assert pod["snapshot_ts"] == "2024-05-01T13:00:00+00:00"
    assert pod["metadata"] == {}
    assert pod["cost_per_hour"] == Decimal("3.5")

    assert section["job_stats"] == []
    assert section["job_timeseries"] == []
    assert section["application_summary"] == {
        "status_counts": {},
        "total_jobs": 0,
        "failed_jobs": 0,
        "active_endpoints": 0,
        "last_updated": None,
    }
    assert section["resource_summary"]["total_pods"] == 1
    assert section["resource_summary"]["total_gpus"] == 1


@pytest.mark.parametrize(
    "note",
    [
        None,
        "No RunPod metrics yet",
    ],
)
def test_runpod_dashboard_placeholder(note: str | None):
    """Placeholder helper should return a lightweight status payload."""
    payload = _runpod_dashboard_placeholder(note or "RunPod metrics unavailable.")
    assert payload["status"] == "pending_ingestion"
    if note:
        assert payload["note"] == note
    else:
        assert payload["note"] == "RunPod metrics unavailable."


def test_runpod_performance_section_job_metrics():
    """RunPod job sections should aggregate throughput and job stats."""
    reader = _FakeCostReader(
        billing_rows=[],
        endpoint_rows=[],
        pod_rows=[],
        job_stats_rows=[
            {
                "endpoint_id": "endpoint-1",
                "last_observed": datetime(2024, 5, 1, 15, 0, tzinfo=timezone.utc),
                "total_jobs": 8,
                "failed_jobs": 2,
                "avg_execution_ms": Decimal("120.5"),
                "p95_execution_ms": Decimal("250.0"),
                "avg_throughput": 1.25,
                "total_input_tokens": 3200,
                "total_output_tokens": 2100,
            }
        ],
        job_series_rows=[
            {
                "endpoint_id": "endpoint-1",
                "bucket": datetime(2024, 5, 1, 14, 55, tzinfo=timezone.utc),
                "total_jobs": 5,
                "failed_jobs": 1,
                "avg_throughput": 1.3,
            }
        ],
        job_status_rows=[
            {"status": "completed", "job_count": 6},
            {"status": "failed", "job_count": 2},
        ],
    )

    section = _build_runpod_dashboard_section(reader, "customer-123")
    stats = section["job_stats"][0]
    assert stats["endpoint_id"] == "endpoint-1"
    assert stats["total_jobs"] == 8
    assert stats["failed_jobs"] == 2
    assert stats["avg_execution_ms"] == 120.5
    assert stats["p95_execution_ms"] == 250.0
    assert stats["avg_throughput"] == 1.25
    assert stats["total_output_tokens"] == 2100
    assert stats["last_observed"] == "2024-05-01T15:00:00+00:00"

    series = section["job_timeseries"][0]
    assert series["total_jobs"] == 5
    assert series["failed_jobs"] == 1
    assert series["avg_throughput"] == 1.3

    summary = section["application_summary"]
    assert summary["total_jobs"] == 8
    assert summary["failed_jobs"] == 2
    assert summary["active_endpoints"] == 1
    assert summary["status_counts"] == {"completed": 6, "failed": 2}


def test_runpod_resource_section_summary():
    """Resource summary should aggregate pod inventory and GPU totals."""
    reader = _FakeCostReader(
        billing_rows=[],
        endpoint_rows=[],
        pod_rows=[
            {
                "pod_id": "pod-1",
                "snapshot_ts": datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc),
                "status": "running",
                "gpu_type_id": "A100",
                "gpu_count": 2,
                "vcpu_count": 16,
                "memory_gb": 48,
                "cost_per_hour": Decimal("4.5"),
                "metadata_json": "{}",
            },
            {
                "pod_id": "pod-2",
                "snapshot_ts": datetime(2024, 5, 1, 12, 5, tzinfo=timezone.utc),
                "status": "stopped",
                "gpu_type_id": "A100",
                "gpu_count": 1,
                "vcpu_count": 8,
                "memory_gb": 24,
                "cost_per_hour": Decimal("2.5"),
                "metadata_json": "{}",
            },
            {
                "pod_id": "pod-3",
                "snapshot_ts": datetime(2024, 5, 1, 12, 10, tzinfo=timezone.utc),
                "status": "running",
                "gpu_type_id": "H100",
                "gpu_count": 4,
                "vcpu_count": 32,
                "memory_gb": 64,
                "cost_per_hour": Decimal("10.0"),
                "metadata_json": "{}",
            },
        ],
    )

    section = _build_runpod_dashboard_section(reader, "customer-123")
    summary = section["resource_summary"]
    assert summary["total_pods"] == 3
    assert summary["total_gpus"] == 7
    assert summary["total_vcpus"] == 56
    assert summary["total_memory_gb"] == 136.0
    assert summary["pods_by_status"]["running"] == 2
    assert summary["pods_by_status"]["stopped"] == 1

    gpu_types = {item["gpu_type_id"]: item for item in summary["gpu_types"]}
    assert gpu_types["A100"]["pods"] == 2
    assert gpu_types["A100"]["gpus"] == 3
    assert gpu_types["H100"]["pods"] == 1
    assert gpu_types["H100"]["gpus"] == 4


def test_runpod_application_status_counts():
    """Application summary should capture status distribution."""
    reader = _FakeCostReader(
        billing_rows=[],
        endpoint_rows=[
            {
                "endpoint_id": "endpoint-1",
                "observed_ts": datetime(2024, 5, 1, 12, 20, tzinfo=timezone.utc),
                "jobs_completed": 10,
                "jobs_failed": 1,
                "jobs_in_progress": 2,
                "jobs_in_queue": 0,
                "workers_idle": 1,
                "workers_running": 2,
                "workers_throttled": 0,
                "metadata_json": "{}",
            }
        ],
        pod_rows=[],
        job_status_rows=[
            {"status": "completed", "job_count": 10},
            {"status": "queued", "job_count": 3},
            {"status": "failed", "job_count": 1},
        ],
    )

    section = _build_runpod_dashboard_section(reader, "customer-123")
    summary = section["application_summary"]
    assert summary["status_counts"] == {"completed": 10, "queued": 3, "failed": 1}
    assert summary["total_jobs"] == 14
    assert summary["failed_jobs"] == 1


def test_runpod_dashboard_section_all_agents():
    """Combined scenario covering billing, performance, resource, and application shapes."""
    reader = _FakeCostReader(
        billing_rows=[
            {
                "snapshot_date": date(2024, 5, 1),
                "avg_spend_per_hr": Decimal("3.0"),
                "lifetime_spend": Decimal("120.0"),
                "balance": Decimal("42.0"),
                "spend_breakdown": {"serverless": {"totalSpend": 80}},
            }
        ],
        endpoint_rows=[
            {
                "endpoint_id": "endpoint-1",
                "observed_ts": datetime(2024, 5, 1, 12, 25, tzinfo=timezone.utc),
                "jobs_completed": 12,
                "jobs_failed": 2,
                "jobs_in_progress": 1,
                "jobs_in_queue": 0,
                "workers_idle": 0,
                "workers_running": 3,
                "workers_throttled": 0,
                "metadata_json": '{"region":"iad"}',
            }
        ],
        pod_rows=[
            {
                "pod_id": "pod-1",
                "snapshot_ts": datetime(2024, 5, 1, 12, 30, tzinfo=timezone.utc),
                "status": "running",
                "gpu_type_id": "A100",
                "gpu_count": 2,
                "vcpu_count": 16,
                "memory_gb": 48,
                "cost_per_hour": Decimal("5.0"),
                "metadata_json": "{}",
            }
        ],
        job_stats_rows=[
            {
                "endpoint_id": "endpoint-1",
                "last_observed": datetime(2024, 5, 1, 12, 28, tzinfo=timezone.utc),
                "total_jobs": 14,
                "failed_jobs": 2,
                "avg_execution_ms": Decimal("110.0"),
                "p95_execution_ms": Decimal("200.0"),
                "avg_throughput": 1.5,
                "total_input_tokens": 3500,
                "total_output_tokens": 2100,
            }
        ],
        job_series_rows=[
            {
                "endpoint_id": "endpoint-1",
                "bucket": datetime(2024, 5, 1, 12, 20, tzinfo=timezone.utc),
                "total_jobs": 7,
                "failed_jobs": 1,
                "avg_throughput": 1.4,
            }
        ],
        job_status_rows=[
            {"status": "completed", "job_count": 12},
            {"status": "failed", "job_count": 2},
        ],
    )

    section = _build_runpod_dashboard_section(reader, "customer-123")

    assert section["billing"][0]["avg_spend_per_hr"] == 3.0
    assert section["job_stats"][0]["total_jobs"] == 14
    assert section["resource_summary"]["total_pods"] == 1
    assert section["application_summary"]["total_jobs"] == 14

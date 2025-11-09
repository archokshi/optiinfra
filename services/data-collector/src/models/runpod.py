"""Data models describing RunPod staging table payloads."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def _json_dump(payload: Dict[str, Any]) -> str:
    if not payload:
        return "{}"
    try:
        return json.dumps(payload, default=str)
    except (TypeError, ValueError):
        return "{}"


@dataclass
class RunPodPodSnapshot:
    snapshot_ts: datetime
    customer_id: str
    pod_id: str
    gpu_type_id: Optional[str]
    gpu_count: int
    vcpu_count: int
    memory_gb: float
    region: Optional[str]
    status: str
    uptime_seconds: int
    cost_per_hour: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> tuple:
        return (
            self.snapshot_ts,
            self.customer_id,
            self.pod_id,
            self.gpu_type_id or "",
            int(self.gpu_count),
            int(self.vcpu_count),
            float(self.memory_gb),
            self.region or "",
            self.status,
            int(self.uptime_seconds),
            float(self.cost_per_hour),
            _json_dump(self.metadata),
        )


@dataclass
class RunPodEndpointConfig:
    snapshot_ts: datetime
    customer_id: str
    endpoint_id: str
    name: str
    compute_type: Optional[str]
    gpu_type_ids: List[str]
    workers_min: int
    workers_max: int
    scaler_type: Optional[str]
    idle_timeout: Optional[int]
    execution_timeout_ms: Optional[int]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> tuple:
        return (
            self.snapshot_ts,
            self.customer_id,
            self.endpoint_id,
            self.name,
            self.compute_type or "",
            self.gpu_type_ids,
            int(self.workers_min),
            int(self.workers_max),
            self.scaler_type or "",
            int(self.idle_timeout or 0),
            int(self.execution_timeout_ms or 0),
            _json_dump(self.metadata),
        )


@dataclass
class RunPodJobTelemetry:
    observed_ts: datetime
    customer_id: str
    endpoint_id: str
    job_id: str
    status: str
    delay_ms: Optional[int]
    execution_ms: Optional[int]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    throughput: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> tuple:
        return (
            self.observed_ts,
            self.customer_id,
            self.endpoint_id,
            self.job_id,
            self.status,
            int(self.delay_ms or 0),
            int(self.execution_ms or 0),
            int(self.input_tokens or 0),
            int(self.output_tokens or 0),
            float(self.throughput or 0.0),
            _json_dump(self.metadata),
        )


@dataclass
class RunPodEndpointHealthSnapshot:
    observed_ts: datetime
    customer_id: str
    endpoint_id: str
    jobs_completed: int
    jobs_failed: int
    jobs_in_progress: int
    jobs_in_queue: int
    workers_idle: int
    workers_running: int
    workers_throttled: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> tuple:
        return (
            self.observed_ts,
            self.customer_id,
            self.endpoint_id,
            int(self.jobs_completed),
            int(self.jobs_failed),
            int(self.jobs_in_progress),
            int(self.jobs_in_queue),
            int(self.workers_idle),
            int(self.workers_running),
            int(self.workers_throttled),
            _json_dump(self.metadata),
        )


@dataclass
class RunPodBillingSnapshot:
    snapshot_ts: datetime
    customer_id: str
    current_spend_per_hr: float
    lifetime_spend: float
    balance: float
    spend_breakdown: Dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> tuple:
        return (
            self.snapshot_ts,
            self.customer_id,
            float(self.current_spend_per_hr),
            float(self.lifetime_spend),
            float(self.balance),
            _json_dump(self.spend_breakdown),
        )

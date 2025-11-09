"""Collect RunPod endpoint health telemetry."""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

from ...models.metrics import CollectionResult, Provider
from ...models.runpod import RunPodEndpointHealthSnapshot
from .base import RunPodCollectorBase, RunPodCollectorSettings


class RunPodPerformanceCollector(RunPodCollectorBase):
    """
    Collects RunPod job telemetry and endpoint health information.

    Phase 2 will populate `runpod_jobs` and `runpod_endpoint_health` using
    data sourced from the RunPod GraphQL and serverless APIs.
    """

    def __init__(self, settings: RunPodCollectorSettings):
        super().__init__(settings)

    def get_provider_name(self) -> str:
        return "runpod"

    def get_data_type(self) -> str:
        return "performance"

    def collect(self) -> CollectionResult:
        self.reset_staging_buffers()
        self.log_collection_start()
        started_at = datetime.now(timezone.utc)

        try:
            endpoints = asyncio.run(self.client.fetch_endpoints())
            health_snapshots = asyncio.run(self._fetch_health(endpoints))
        except Exception as exc:  # pragma: no cover - network/runtime error
            return self.handle_error(exc)

        self.get_endpoint_health_snapshots().extend(health_snapshots)

        metadata = {
            "endpoint_health_rows": len(health_snapshots),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }

        result = CollectionResult(
            customer_id=self.customer_id,
            provider=Provider.RUNPOD,
            data_type=self.get_data_type(),
            success=True,
            records_collected=len(health_snapshots),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.log_collection_end(result)
        return result

    async def _fetch_health(self, endpoints: List[Dict[str, Any]]) -> List[RunPodEndpointHealthSnapshot]:
        observed_at = datetime.now(timezone.utc)
        snapshots: List[RunPodEndpointHealthSnapshot] = []

        async def _fetch(endpoint_id: str) -> Dict[str, Any]:
            return await self.client.fetch_endpoint_health(endpoint_id)

        tasks = [
            _fetch(endpoint.get("id"))
            for endpoint in endpoints
            if endpoint.get("id")
        ]
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for endpoint, payload in zip([e for e in endpoints if e.get("id")], results):
            if isinstance(payload, Exception):
                self.logger.warning(
                    "Failed to fetch health for endpoint %s: %s", endpoint.get("id"), payload
                )
                continue

            jobs = payload.get("jobs", {}) if isinstance(payload, dict) else {}
            workers = payload.get("workers", {}) if isinstance(payload, dict) else {}
            metadata = {k: v for k, v in payload.items() if k not in {"jobs", "workers"}}

            snapshot = RunPodEndpointHealthSnapshot(
                observed_ts=observed_at,
                customer_id=self.customer_id,
                endpoint_id=endpoint.get("id"),
                jobs_completed=int(jobs.get("completed") or 0),
                jobs_failed=int(jobs.get("failed") or 0),
                jobs_in_progress=int(jobs.get("inProgress") or 0),
                jobs_in_queue=int(jobs.get("inQueue") or 0),
                workers_idle=int(workers.get("idle") or 0),
                workers_running=int(workers.get("running") or 0),
                workers_throttled=int(workers.get("throttled") or 0),
                metadata=metadata,
            )
            snapshots.append(snapshot)

        return snapshots

"""Collect RunPod job telemetry for application insights."""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from ...models.metrics import CollectionResult, Provider
from ...models.runpod import RunPodJobTelemetry
from .base import RunPodCollectorBase, RunPodCollectorSettings


class RunPodApplicationCollector(RunPodCollectorBase):
    """
    Collects higher level application metrics derived from RunPod jobs.

    Phase 2 will translate serverless telemetry into insights for the portal's
    dashboard, but Phase 1 keeps the implementation as a placeholder.
    """

    def __init__(self, settings: RunPodCollectorSettings):
        super().__init__(settings)

    def get_provider_name(self) -> str:
        return "runpod"

    def get_data_type(self) -> str:
        return "application"

    def collect(self) -> CollectionResult:
        self.reset_staging_buffers()
        self.log_collection_start()
        started_at = datetime.now(timezone.utc)

        job_pairs = self._parse_tracked_job_ids()
        if not job_pairs:
            metadata = {
                "job_rows": 0,
                "captured_at": started_at.isoformat(),
                "note": "No RUNPOD job IDs configured; skipping telemetry pull.",
            }
            result = CollectionResult(
                customer_id=self.customer_id,
                provider=Provider.RUNPOD,
                data_type=self.get_data_type(),
                success=True,
                records_collected=0,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                metadata=metadata,
            )
            self.log_collection_end(result)
            return result

        try:
            telemetry = asyncio.run(self._fetch_job_telemetry(job_pairs))
        except Exception as exc:  # pragma: no cover - network/runtime error
            return self.handle_error(exc)

        self.get_job_telemetry().extend(telemetry)

        metadata = {
            "job_rows": len(telemetry),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }

        result = CollectionResult(
            customer_id=self.customer_id,
            provider=Provider.RUNPOD,
            data_type=self.get_data_type(),
            success=True,
            records_collected=len(telemetry),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.log_collection_end(result)
        return result

    def _parse_tracked_job_ids(self) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for token in self.settings.tracked_job_ids:
            if not token or ":" not in token:
                continue
            endpoint_id, job_id = token.split(":", 1)
            endpoint_id = endpoint_id.strip()
            job_id = job_id.strip()
            if endpoint_id and job_id:
                pairs.append((endpoint_id, job_id))
        return pairs

    async def _fetch_job_telemetry(
        self, pairs: List[Tuple[str, str]]
    ) -> List[RunPodJobTelemetry]:
        observed_ts = datetime.now(timezone.utc)
        telemetry: List[RunPodJobTelemetry] = []

        async def _fetch(endpoint_id: str, job_id: str) -> Tuple[str, str, Dict[str, Any], List[Dict[str, Any]]]:
            status = await self.client.fetch_job_status(endpoint_id, job_id)
            stream = await self.client.fetch_stream_metrics(endpoint_id, job_id)
            return endpoint_id, job_id, status, stream

        tasks = [_fetch(endpoint_id, job_id) for endpoint_id, job_id in pairs]
        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for pair, payload in zip(pairs, results):
            endpoint_id, job_id = pair
            if isinstance(payload, Exception):
                self.logger.warning(
                    "Failed to fetch job telemetry for %s:%s: %s", endpoint_id, job_id, payload
                )
                continue

            _, _, status_data, stream_data = payload
            output = status_data.get("output", {}) if isinstance(status_data, dict) else {}
            metrics = self._extract_stream_metrics(stream_data)

            telemetry.append(
                RunPodJobTelemetry(
                    observed_ts=observed_ts,
                    customer_id=self.customer_id,
                    endpoint_id=endpoint_id,
                    job_id=job_id,
                    status=status_data.get("status", "unknown"),
                    delay_ms=status_data.get("delayTime"),
                    execution_ms=status_data.get("executionTime"),
                    input_tokens=output.get("input_tokens"),
                    output_tokens=output.get("output_tokens"),
                    throughput=metrics.get("avg_gen_throughput"),
                    metadata={
                        "output": output,
                        "stream_metrics": stream_data,
                    },
                )
            )

        return telemetry

    def _extract_stream_metrics(self, stream_data: Any) -> Dict[str, Any]:
        if isinstance(stream_data, list) and stream_data:
            metrics = stream_data[-1].get("metrics") if isinstance(stream_data[-1], dict) else None
            if isinstance(metrics, dict):
                return metrics
        return {}

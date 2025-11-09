"""
Shared helpers for RunPod collectors.

Phase 1 introduces placeholder collectors that expose the wiring required for
future implementation work. The real ingestion logic will be added in Phase 2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..base import BaseCollector
from ...models.metrics import CollectionResult, Provider
from ...config import config
from ..providers.runpod_client import RunPodClient
from ...models.runpod import (
    RunPodBillingSnapshot,
    RunPodEndpointConfig,
    RunPodEndpointHealthSnapshot,
    RunPodJobTelemetry,
    RunPodPodSnapshot,
)


@dataclass
class RunPodCollectorSettings:
    """Container for the configuration shared by RunPod collectors."""

    api_key: str
    customer_id: str
    graphql_url: str
    rest_url: str
    serverless_url: str
    collection_interval_seconds: int
    health_poll_seconds: int
    job_retention_days: int
    timeout: int = 30
    tracked_job_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_sources(
        cls,
        customer_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> "RunPodCollectorSettings":
        """
        Build settings using stored customer credentials with environment
        variables as sensible defaults.
        """
        creds = credentials or {}

        api_key = creds.get("api_key") or creds.get("RUNPOD_API_KEY") or config.RUNPOD_API_KEY
        if not api_key:
            raise ValueError(
                "RunPod API key not configured. "
                "Please add credentials in the dashboard or set RUNPOD_API_KEY."
            )

        def _resolve(key: str, default: Any) -> Any:
            return creds.get(key) or creds.get(key.upper()) or default

        timeout_value = int(creds.get("timeout")) if creds.get("timeout") else 30

        tracked_job_ids: List[str] = []
        raw_job_ids = creds.get("job_ids") or creds.get("RUNPOD_JOB_IDS")
        if isinstance(raw_job_ids, str):
            tracked_job_ids = [item.strip() for item in raw_job_ids.split(",") if item.strip()]
        elif isinstance(raw_job_ids, list):
            tracked_job_ids = [str(item).strip() for item in raw_job_ids if str(item).strip()]

        return cls(
            api_key=api_key,
            customer_id=customer_id,
            graphql_url=_resolve("graphql_url", config.RUNPOD_GRAPHQL_URL),
            rest_url=_resolve("rest_url", config.RUNPOD_REST_URL),
            serverless_url=_resolve("serverless_url", config.RUNPOD_SERVERLESS_URL),
            collection_interval_seconds=int(
                creds.get("collection_interval_seconds") or config.RUNPOD_COLLECTION_INTERVAL_SECONDS
            ),
            health_poll_seconds=int(
                creds.get("health_poll_seconds") or config.RUNPOD_HEALTH_POLL_SECONDS
            ),
            job_retention_days=int(
                creds.get("job_retention_days") or config.RUNPOD_JOB_RETENTION_DAYS
            ),
            timeout=timeout_value,
            tracked_job_ids=tracked_job_ids,
        )


class RunPodCollectorBase(BaseCollector):
    """Base class that handles shared RunPod collector behaviour."""

    def __init__(self, settings: RunPodCollectorSettings):
        super().__init__(api_key=settings.api_key, customer_id=settings.customer_id)
        self.settings = settings
        self.client = RunPodClient(
            api_key=settings.api_key,
            graphql_url=settings.graphql_url,
            rest_url=settings.rest_url,
            serverless_url=settings.serverless_url,
            timeout=settings.timeout,
        )
        self._pod_snapshots: List[RunPodPodSnapshot] = []
        self._endpoint_configs: List[RunPodEndpointConfig] = []
        self._job_telemetry: List[RunPodJobTelemetry] = []
        self._endpoint_health: List[RunPodEndpointHealthSnapshot] = []
        self._billing_snapshots: List[RunPodBillingSnapshot] = []

    def validate_credentials(self) -> bool:
        """Phase 1 placeholder; Phase 2 will verify connectivity with RunPod APIs."""
        self.logger.info("RunPod credential validation is deferred to Phase 2.")
        return True

    def _placeholder_result(
        self,
        data_type: str,
        started_at: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CollectionResult:
        """
        Return a CollectionResult indicating that concrete logic is pending.
        """
        result = CollectionResult(
            customer_id=self.customer_id,
            provider=Provider.RUNPOD,
            data_type=data_type,
            success=True,
            records_collected=0,
            started_at=started_at,
            completed_at=datetime.now(),
            metadata=metadata
            or {
                "status": "placeholder",
                "phase": "runpod-phase-1",
            },
        )
        self.log_collection_end(result)
        return result

    def get_metrics(self) -> List[Any]:
        """No metrics are produced in Phase 1."""
        return []

    def get_collected_metrics(self) -> List[Any]:
        """Alias for cost collectors that expect this method."""
        return []

    # ------------------------------------------------------------------
    # RunPod staging accessors
    # ------------------------------------------------------------------

    def get_pod_snapshots(self) -> List[RunPodPodSnapshot]:
        return self._pod_snapshots

    def get_endpoint_configs(self) -> List[RunPodEndpointConfig]:
        return self._endpoint_configs

    def get_job_telemetry(self) -> List[RunPodJobTelemetry]:
        return self._job_telemetry

    def get_endpoint_health_snapshots(self) -> List[RunPodEndpointHealthSnapshot]:
        return self._endpoint_health

    def get_billing_snapshots(self) -> List[RunPodBillingSnapshot]:
        return self._billing_snapshots

    def reset_staging_buffers(self) -> None:
        self._pod_snapshots.clear()
        self._endpoint_configs.clear()
        self._job_telemetry.clear()
        self._endpoint_health.clear()
        self._billing_snapshots.clear()

    async def collect_async(self) -> CollectionResult:
        """
        Async convenience method for future collectors. It currently delegates
        to the synchronous collect implementation.
        """
        return self.collect()

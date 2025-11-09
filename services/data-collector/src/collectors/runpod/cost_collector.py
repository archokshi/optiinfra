"""Collect RunPod billing data into staging tables."""
from datetime import datetime, timezone
import asyncio

from ...models.metrics import CollectionResult, Provider
from ...models.runpod import RunPodBillingSnapshot
from .base import RunPodCollectorBase, RunPodCollectorSettings


class RunPodCostCollector(RunPodCollectorBase):
    """
    Collects aggregated spend from the RunPod GraphQL `myself` endpoint.

    Future implementation will translate daily/hourly spend and balance
    snapshots into ClickHouse staging rows (`runpod_billing_snapshots`).
    """

    def __init__(self, settings: RunPodCollectorSettings):
        super().__init__(settings)

    def get_provider_name(self) -> str:
        return "runpod"

    def get_data_type(self) -> str:
        return "cost"

    def collect(self) -> CollectionResult:
        self.reset_staging_buffers()
        self.log_collection_start()
        started_at = datetime.now(timezone.utc)

        try:
            billing_payload = asyncio.run(self._fetch_billing_payload())
        except Exception as exc:  # pragma: no cover - network/runtime error
            return self.handle_error(exc)

        snapshot = RunPodBillingSnapshot(
            snapshot_ts=started_at,
            customer_id=self.customer_id,
            current_spend_per_hr=float(billing_payload.get("currentSpendPerHr") or 0.0),
            lifetime_spend=float(billing_payload.get("clientLifetimeSpend") or 0.0),
            balance=float(billing_payload.get("clientBalance") or 0.0),
            spend_breakdown={
                "billing": billing_payload.get("billing", {}),
                "spendDetails": billing_payload.get("spendDetails", []),
            },
        )

        self.get_billing_snapshots().append(snapshot)

        metadata = {
            "billing_rows": 1,
            "captured_at": started_at.isoformat(),
        }

        result = CollectionResult(
            customer_id=self.customer_id,
            provider=Provider.RUNPOD,
            data_type=self.get_data_type(),
            success=True,
            records_collected=1,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            metadata=metadata,
        )

        self.log_collection_end(result)
        return result

    async def _fetch_billing_payload(self) -> dict:
        billing, _ = await asyncio.gather(
            self.client.fetch_myself(),
            self.client.fetch_gpu_catalog(),  # Catalogue kept for downstream enrichment
        )
        return billing

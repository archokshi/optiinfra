"""Collect RunPod inventory snapshots."""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

from ...models.metrics import CollectionResult, Provider
from ...models.runpod import RunPodEndpointConfig, RunPodPodSnapshot
from .base import RunPodCollectorBase, RunPodCollectorSettings


class RunPodResourceCollector(RunPodCollectorBase):
    """
    Collects RunPod pod inventory and endpoint configuration.

    Future implementation will write to `runpod_pods` and `runpod_endpoints`
    staging tables using the shared RunPodClient.
    """

    def __init__(self, settings: RunPodCollectorSettings):
        super().__init__(settings)

    def get_provider_name(self) -> str:
        return "runpod"

    def get_data_type(self) -> str:
        return "resource"

    def collect(self) -> CollectionResult:
        self.reset_staging_buffers()
        self.log_collection_start()
        started_at = datetime.now(timezone.utc)

        try:
            pods, endpoints, detailed_pods = asyncio.run(self._fetch_resources())
        except Exception as exc:  # pragma: no cover - network/runtime error
            return self.handle_error(exc)

        snapshot_time = datetime.now(timezone.utc)

        pod_snapshots = self._build_pod_snapshots(snapshot_time, pods, detailed_pods)
        endpoint_configs = self._build_endpoint_configs(snapshot_time, endpoints)

        self.get_pod_snapshots().extend(pod_snapshots)
        self.get_endpoint_configs().extend(endpoint_configs)

        metadata = {
            "pods": len(pod_snapshots),
            "endpoints": len(endpoint_configs),
            "captured_at": snapshot_time.isoformat(),
        }

        result = CollectionResult(
            customer_id=self.customer_id,
            provider=Provider.RUNPOD,
            data_type=self.get_data_type(),
            success=True,
            records_collected=len(pod_snapshots) + len(endpoint_configs),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.log_collection_end(result)
        return result

    async def _fetch_resources(self):
        pods = await self.client.fetch_pods()
        endpoints = await self.client.fetch_endpoints()

        pod_ids = [pod.get("id") for pod in pods if pod.get("id")]
        detailed: Dict[str, Dict[str, any]] = {}
        if pod_ids:
            details = await asyncio.gather(
                *(self.client.fetch_pod(pod_id) for pod_id in pod_ids),
                return_exceptions=True,
            )
            for pod_id, info in zip(pod_ids, details):
                if isinstance(info, Exception) or not info:
                    continue
                detailed[pod_id] = info

        return pods, endpoints, detailed

    def _build_pod_snapshots(
        self,
        snapshot_ts: datetime,
        pods: List[Dict[str, Any]],
        detailed: Dict[str, Dict[str, Any]],
    ) -> List[RunPodPodSnapshot]:
        snapshots: List[RunPodPodSnapshot] = []
        for pod in pods:
            pod_id = pod.get("id")
            if not pod_id:
                continue

            detail = detailed.get(pod_id, {})
            combined = {**pod, **detail}

            status = combined.get("desiredStatus") or combined.get("status") or "unknown"
            metadata = {
                "name": combined.get("name"),
                "podType": combined.get("podType"),
                "dataCenterId": combined.get("dataCenterId"),
                "templateId": combined.get("templateId"),
                "imageName": combined.get("imageName"),
                "env": combined.get("env"),
                "runtime": combined.get("runtime"),
                "machine": combined.get("machine"),
            }

            snapshot = RunPodPodSnapshot(
                snapshot_ts=snapshot_ts,
                customer_id=self.customer_id,
                pod_id=pod_id,
                gpu_type_id=combined.get("gpuTypeId"),
                gpu_count=int(combined.get("gpuCount") or 0),
                vcpu_count=int(combined.get("vcpuCount") or 0),
                memory_gb=float(combined.get("memoryInGb") or 0.0),
                region=combined.get("dataCenterId"),
                status=status,
                uptime_seconds=int(combined.get("uptimeSeconds") or 0),
                cost_per_hour=float(
                    combined.get("adjustedCostPerHr")
                    or combined.get("costPerHr")
                    or 0.0
                ),
                metadata={k: v for k, v in metadata.items() if v is not None},
            )
            snapshots.append(snapshot)

        return snapshots

    def _build_endpoint_configs(
        self,
        snapshot_ts: datetime,
        endpoints: List[Dict[str, Any]],
    ) -> List[RunPodEndpointConfig]:
        configs: List[RunPodEndpointConfig] = []
        for endpoint in endpoints:
            endpoint_id = endpoint.get("id")
            if not endpoint_id:
                continue

            metadata = {
                "createdAt": endpoint.get("createdAt"),
                "networkVolumeId": endpoint.get("networkVolumeId"),
                "env": endpoint.get("env"),
                "userId": endpoint.get("userId"),
            }

            config = RunPodEndpointConfig(
                snapshot_ts=snapshot_ts,
                customer_id=self.customer_id,
                endpoint_id=endpoint_id,
                name=endpoint.get("name", ""),
                compute_type=endpoint.get("computeType"),
                gpu_type_ids=list(endpoint.get("gpuTypeIds") or []),
                workers_min=int(endpoint.get("workersMin") or 0),
                workers_max=int(endpoint.get("workersMax") or 0),
                scaler_type=endpoint.get("scalerType"),
                idle_timeout=int(endpoint.get("idleTimeout") or 0),
                execution_timeout_ms=int(endpoint.get("executionTimeoutMs") or 0),
                metadata={k: v for k, v in metadata.items() if v is not None},
            )
            configs.append(config)

        return configs

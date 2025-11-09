"""Tests for the RunPod resource collector."""
from datetime import datetime

import httpx
import pytest

from src.collectors.providers.runpod_client import RunPodClient
from src.collectors.runpod.base import RunPodCollectorSettings
from src.collectors.runpod.resource_collector import RunPodResourceCollector


@pytest.fixture
def runpod_settings() -> RunPodCollectorSettings:
    """Provide a basic settings object for collector tests."""
    return RunPodCollectorSettings(
        api_key="test-key",
        customer_id="cust-123",
        graphql_url="https://api.runpod.io/graphql",
        rest_url="https://rest.runpod.io/v1",
        serverless_url="https://api.runpod.ai/v2",
        collection_interval_seconds=300,
        health_poll_seconds=120,
        job_retention_days=90,
        tracked_job_ids=[],
    )


@pytest.fixture
def mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/pods"):
            return httpx.Response(
                200,
                json={
                    "pods": [
                        {
                            "id": "pod-1",
                            "name": "pod-a",
                            "gpuTypeId": "A100",
                            "gpuCount": 1,
                            "memoryInGb": 40,
                            "vcpuCount": 16,
                            "dataCenterId": "ams1",
                        }
                    ]
                },
            )
        if path.endswith("/endpoints"):
            return httpx.Response(
                200,
                json={
                    "endpoints": [
                        {
                            "id": "endpoint-1",
                            "name": "endpoint-a",
                            "computeType": "GPU",
                            "gpuTypeIds": ["A100"],
                            "workersMin": 1,
                            "workersMax": 3,
                            "idleTimeout": 120,
                            "executionTimeoutMs": 30000,
                        }
                    ]
                },
            )
        if path.endswith("/graphql"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "pod": {
                            "id": "pod-1",
                            "desiredStatus": "RUNNING",
                            "uptimeSeconds": 100,
                            "costPerHr": 2.5,
                            "adjustedCostPerHr": 2.0,
                            "runtime": {"ports": []},
                            "machine": {"podHostId": "ph-1"},
                        }
                    }
                },
            )
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_resource_collector_instantiation(runpod_settings):
    """Collector should store the incoming settings and client."""
    collector = RunPodResourceCollector(runpod_settings)
    assert collector.settings.customer_id == "cust-123"
    assert collector.client is not None


def test_resource_collect_builds_snapshots(runpod_settings, mock_transport):
    collector = RunPodResourceCollector(runpod_settings)
    collector.client = RunPodClient(
        api_key="test-key",
        graphql_url=collector.client.graphql_url,
        rest_url=collector.client.rest_url,
        serverless_url=collector.client.serverless_url,
        transport=mock_transport,
    )

    result = collector.collect()

    assert result.success is True
    assert collector.get_pod_snapshots()
    assert collector.get_endpoint_configs()

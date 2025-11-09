"""Tests for the RunPod performance collector."""
from datetime import datetime

import httpx
import pytest

from src.collectors.providers.runpod_client import RunPodClient
from src.collectors.runpod.base import RunPodCollectorSettings
from src.collectors.runpod.performance_collector import RunPodPerformanceCollector


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
        if request.url.path.endswith("/endpoints"):
            return httpx.Response(200, json={"endpoints": [{"id": "endpoint-1", "name": "ep"}]})
        if request.url.path.endswith("/health"):
            return httpx.Response(
                200,
                json={
                    "jobs": {"completed": 7, "failed": 1, "inProgress": 2, "inQueue": 3},
                    "workers": {"idle": 1, "running": 2, "throttled": 0},
                    "extra": {"latency_p95": 1200},
                },
            )
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_performance_collector_instantiation(runpod_settings):
    """Collector should store the incoming settings and client."""
    collector = RunPodPerformanceCollector(runpod_settings)
    assert collector.settings.graphql_url.endswith("/graphql")
    assert collector.client is not None


def test_performance_collects_health(runpod_settings, mock_transport):
    collector = RunPodPerformanceCollector(runpod_settings)
    collector.client = RunPodClient(
        api_key="test-key",
        graphql_url=collector.client.graphql_url,
        rest_url=collector.client.rest_url,
        serverless_url=collector.client.serverless_url,
        transport=mock_transport,
    )

    result = collector.collect()

    assert result.success is True
    snapshots = collector.get_endpoint_health_snapshots()
    assert len(snapshots) == 1
    assert snapshots[0].jobs_completed == 7

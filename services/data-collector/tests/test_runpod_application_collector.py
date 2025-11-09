"""Tests for the RunPod application collector."""
from datetime import datetime

import httpx
import pytest

from src.collectors.providers.runpod_client import RunPodClient
from src.collectors.runpod.application_collector import RunPodApplicationCollector
from src.collectors.runpod.base import RunPodCollectorSettings


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
        tracked_job_ids=["endpoint-1:job-1"],
    )


@pytest.fixture
def mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/status/" in path:
            return httpx.Response(
                200,
                json={
                    "id": "job-1",
                    "status": "COMPLETED",
                    "delayTime": 100,
                "executionTime": 500,
                    "output": {"input_tokens": 42, "output_tokens": 84},
                },
            )
        if "/stream/" in path:
            return httpx.Response(
                200,
                json=[{"metrics": {"avg_gen_throughput": 2.5, "output_tokens": 84}}],
            )
        if path.endswith("/endpoints"):
            return httpx.Response(200, json={"endpoints": [{"id": "endpoint-1"}]})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_application_collector_instantiation(runpod_settings):
    """Collector should store the incoming settings and client."""
    collector = RunPodApplicationCollector(runpod_settings)
    assert collector.settings.serverless_url.endswith("/v2")
    assert collector.client is not None


def test_application_collects_job_telemetry(runpod_settings, mock_transport):
    collector = RunPodApplicationCollector(runpod_settings)
    collector.client = RunPodClient(
        api_key="test-key",
        graphql_url=collector.client.graphql_url,
        rest_url=collector.client.rest_url,
        serverless_url=collector.client.serverless_url,
        transport=mock_transport,
    )

    result = collector.collect()

    assert result.success is True
    telemetry = collector.get_job_telemetry()
    assert len(telemetry) == 1
    assert telemetry[0].execution_ms == 500

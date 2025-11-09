"""Tests for the RunPod cost collector."""
from datetime import datetime
import json

import httpx
import pytest

from src.collectors.providers.runpod_client import RunPodClient
from src.collectors.runpod.base import RunPodCollectorSettings
from src.collectors.runpod.cost_collector import RunPodCostCollector


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
        if request.url.path.endswith("/graphql"):
            try:
                body = json.loads(request.content.decode())
            except json.JSONDecodeError:
                body = {}
            query = body.get("query", "")
            if "myself" in query:
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "myself": {
                                "currentSpendPerHr": 5.5,
                                "clientLifetimeSpend": 99.0,
                                "clientBalance": 10.0,
                                "billing": {"gpuCloud": {"totalSpend": 20}},
                                "spendDetails": [],
                            }
                        }
                    },
                )
            return httpx.Response(200, json={"data": {"gpuTypes": []}})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_cost_collector_instantiation(runpod_settings):
    """Collector should store the incoming settings and client."""
    collector = RunPodCostCollector(runpod_settings)
    assert collector.settings.api_key == "test-key"
    assert collector.client is not None

def test_cost_collect_writes_snapshot(runpod_settings, mock_transport):
    collector = RunPodCostCollector(runpod_settings)
    collector.client = RunPodClient(
        api_key="test-key",
        graphql_url=collector.client.graphql_url,
        rest_url=collector.client.rest_url,
        serverless_url=collector.client.serverless_url,
        transport=mock_transport,
    )

    result = collector.collect()

    assert result.success is True
    assert result.records_collected == 1
    assert collector.get_billing_snapshots()[0].current_spend_per_hr == 5.5
    assert isinstance(result.started_at, datetime)

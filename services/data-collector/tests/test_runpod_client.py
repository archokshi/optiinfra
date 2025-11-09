"""Runtime tests for the RunPod client."""
import json
from typing import Any

import httpx
import pytest

from src.collectors.providers.runpod_client import (
    RunPodClient,
    RunPodGraphQLError,
)


@pytest.fixture
def mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/graphql"):
            body = json.loads(request.content.decode())
            query = body.get("query", "")
            if "gpuTypes" in query:
                return httpx.Response(200, json={"data": {"gpuTypes": [{"id": "gpu-a", "securePrice": 1.23}]}})
            if "myself" in query:
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "myself": {
                                "currentSpendPerHr": 4.56,
                                "clientBalance": 12.34,
                                "clientLifetimeSpend": 78.9,
                                "billing": {
                                    "gpuCloud": {"totalSpend": 10, "totalUsageHours": 20},
                                    "serverless": {"totalSpend": 30, "totalRequests": 40, "totalComputeMs": 50},
                                    "storage": {"totalSpend": 5, "totalGbHours": 100},
                                },
                                "spendDetails": [
                                    {"product": "serverless", "spendPerHour": 2.0, "totalSpend": 10.0}
                                ],
                            }
                        }
                    },
                )
            # Force GraphQL error for other queries
            return httpx.Response(200, json={"errors": [{"message": "boom"}]})

        if path.endswith("/pods"):
            return httpx.Response(
                200,
                json={
                    "pods": [
                        {
                            "id": "pod-1",
                            "name": "pod-a",
                            "gpuTypeId": "24gb",
                            "gpuCount": 1,
                            "memoryInGb": 24,
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
                            "gpuTypeIds": ["24gb"],
                            "workersMin": 1,
                            "workersMax": 2,
                        }
                    ]
                },
            )

        if path.endswith("/health"):
            return httpx.Response(
                200,
                json={"jobs": {"completed": 5, "failed": 1, "inQueue": 2}, "workers": {"idle": 1, "running": 1}},
            )

        if "/status/" in path:
            return httpx.Response(200, json={"id": "job-123", "status": "COMPLETED", "executionTime": 1234})

        if "/stream/" in path:
            return httpx.Response(
                200,
                json=[
                    {
                        "metrics": {
                            "avg_gen_throughput": 1.0,
                            "output_tokens": 10,
                        }
                    }
                ],
            )

        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.fixture
def runpod_client(mock_transport: httpx.MockTransport) -> RunPodClient:
    return RunPodClient(
        api_key="test-key",
        graphql_url="https://api.runpod.io/graphql",
        rest_url="https://rest.runpod.io/v1",
        serverless_url="https://api.runpod.ai/v2",
        transport=mock_transport,
    )


@pytest.mark.asyncio
async def test_fetch_gpu_catalog(runpod_client: RunPodClient):
    catalog = await runpod_client.fetch_gpu_catalog()
    assert catalog[0]["id"] == "gpu-a"


@pytest.mark.asyncio
async def test_fetch_myself(runpod_client: RunPodClient):
    myself = await runpod_client.fetch_myself()
    assert myself["currentSpendPerHr"] == 4.56
    assert myself["billing"]["gpuCloud"]["totalSpend"] == 10


@pytest.mark.asyncio
async def test_fetch_pods_and_endpoints(runpod_client: RunPodClient):
    pods = await runpod_client.fetch_pods()
    endpoints = await runpod_client.fetch_endpoints()
    assert pods[0]["id"] == "pod-1"
    assert endpoints[0]["id"] == "endpoint-1"


@pytest.mark.asyncio
async def test_serverless_helpers(runpod_client: RunPodClient):
    health = await runpod_client.fetch_endpoint_health("endpoint-1")
    job = await runpod_client.fetch_job_status("endpoint-1", "job-1")
    stream = await runpod_client.fetch_stream_metrics("endpoint-1", "job-1")

    assert health["jobs"]["completed"] == 5
    assert job["status"] == "COMPLETED"
    assert stream[0]["metrics"]["output_tokens"] == 10


@pytest.mark.asyncio
async def test_graphql_errors_raise(runpod_client: RunPodClient):
    with pytest.raises(RunPodGraphQLError):
        await runpod_client.fetch_pod("pod-error")


def test_build_headers(runpod_client: RunPodClient):
    headers = runpod_client.build_headers({"Content-Type": "application/json"})
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["Content-Type"] == "application/json"

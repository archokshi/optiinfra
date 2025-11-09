"""Async client for interacting with RunPod APIs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


class RunPodClientError(Exception):
    """Base exception for RunPod client failures."""


class RunPodAuthenticationError(RunPodClientError):
    """Raised when RunPod returns an authentication/authorisation error."""


class RunPodGraphQLError(RunPodClientError):
    """Raised when the GraphQL endpoint reports execution errors."""


@dataclass
class GraphQLResponse:
    """Container for GraphQL responses so callers can inspect the payload."""

    data: Dict[str, Any]
    errors: Optional[List[Dict[str, Any]]] = None


class RunPodClient:
    """Lightweight async wrapper around RunPod GraphQL, REST, and serverless APIs."""

    def __init__(
        self,
        api_key: str,
        graphql_url: str,
        rest_url: str,
        serverless_url: str,
        timeout: float = 30.0,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.api_key = api_key
        self.graphql_url = graphql_url.rstrip("/")
        self.rest_url = rest_url.rstrip("/")
        self.serverless_url = serverless_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if extra:
            headers.update(extra)
        return headers

    # ------------------------------------------------------------------
    # GraphQL queries
    # ------------------------------------------------------------------
    async def fetch_gpu_catalog(self) -> List[Dict[str, Any]]:
        """Return the RunPod GPU catalog with price references."""

        query = """
        query gpuTypes($input: GpuTypeFilter) {
            gpuTypes(input: $input) {
                id
                displayName
                communityPrice
                securePrice
                communitySpotPrice
                secureSpotPrice
                oneWeekPrice
                oneMonthPrice
                threeMonthPrice
                sixMonthPrice
            }
        }
        """
        response = await self._execute_graphql(query, variables={"input": None})
        return response.data.get("gpuTypes", [])

    async def fetch_myself(self) -> Dict[str, Any]:
        """Return billing context for the authenticated user."""

        query = """
        query myselfBilling {
            myself {
                id
                email
                currentSpendPerHr
                clientBalance
                clientLifetimeSpend
                referralEarned
                spendDetails {
                    product
                    spendPerHour
                    totalSpend
                }
                billing {
                    gpuCloud {
                        totalSpend
                        totalUsageHours
                    }
                    serverless {
                        totalSpend
                        totalRequests
                        totalComputeMs
                    }
                    storage {
                        totalSpend
                        totalGbHours
                    }
                }
                teams {
                    id
                    name
                }
            }
        }
        """
        response = await self._execute_graphql(query)
        return response.data.get("myself", {})

    async def fetch_pod(self, pod_id: str) -> Dict[str, Any]:
        """Return detailed information for a single pod by ID."""

        query = """
        query podById($input: PodFilter) {
            pod(input: $input) {
                id
                name
                desiredStatus
                createdAt
                costPerHr
                adjustedCostPerHr
                gpuCount
                vcpuCount
                memoryInGb
                uptimeSeconds
                podType
                templateId
                volumeInGb
                gpuPowerLimitPercent
                dataCenterId
                imageName
                env
                endpoint {
                    id
                    name
                }
                runtime {
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                        type
                    }
                }
                latestTelemetry {
                    cpuUtilPercent
                    memoryUtilPercent
                    gpuUtilPercent
                    gpuMemoryUtilPercent
                    diskUtilPercent
                }
                machine {
                    podHostId
                    clusterId
                }
            }
        }
        """
        variables = {"input": {"podId": pod_id}}
        response = await self._execute_graphql(query, variables=variables)
        return response.data.get("pod", {})

    # ------------------------------------------------------------------
    # REST inventory endpoints
    # ------------------------------------------------------------------
    async def fetch_pods(self) -> List[Dict[str, Any]]:
        payload = await self._request_rest("GET", "/pods", params={"includeMachine": "true"})
        return payload.get("pods", [])

    async def fetch_endpoints(self) -> List[Dict[str, Any]]:
        payload = await self._request_rest("GET", "/endpoints")
        return payload.get("endpoints", [])

    # ------------------------------------------------------------------
    # Serverless telemetry endpoints
    # ------------------------------------------------------------------
    async def fetch_endpoint_health(self, endpoint_id: str) -> Dict[str, Any]:
        return await self._request_serverless("GET", endpoint_id, "/health")

    async def fetch_job_status(self, endpoint_id: str, job_id: str) -> Dict[str, Any]:
        return await self._request_serverless("GET", endpoint_id, f"/status/{job_id}")

    async def fetch_stream_metrics(self, endpoint_id: str, job_id: str) -> List[Dict[str, Any]]:
        response = await self._request_serverless("GET", endpoint_id, f"/stream/{job_id}")
        if isinstance(response, list):
            return response
        if isinstance(response, str):
            try:
                parsed = json.loads(response)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _execute_graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> GraphQLResponse:
        payload = {"query": query, "variables": variables or {}}
        headers = self.build_headers({"Content-Type": "application/json"})
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            try:
                response = await client.post(self.graphql_url, json=payload, headers=headers)
            except httpx.HTTPError as exc:  # pragma: no cover - network failure
                raise RunPodClientError(f"GraphQL request failed: {exc}") from exc

        if response.status_code in (401, 403):
            raise RunPodAuthenticationError("RunPod GraphQL API rejected the request")

        try:
            body = response.json()
        except json.JSONDecodeError as exc:
            raise RunPodClientError("Invalid JSON response from RunPod GraphQL API") from exc

        errors = body.get("errors")
        if errors:
            raise RunPodGraphQLError(str(errors))

        return GraphQLResponse(data=body.get("data", {}), errors=errors)

    async def _request_rest(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.rest_url}{path}"
        headers = self.build_headers({"Content-Type": "application/json"})
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            try:
                response = await client.request(method, url, params=params, json=json_body, headers=headers)
            except httpx.HTTPError as exc:  # pragma: no cover - network failure
                raise RunPodClientError(f"RunPod REST request failed: {exc}") from exc

        if response.status_code in (401, 403):
            raise RunPodAuthenticationError("RunPod REST API rejected the request")

        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise RunPodClientError("Invalid JSON response from RunPod REST API") from exc

    async def _request_serverless(
        self,
        method: str,
        endpoint_id: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        base = f"{self.serverless_url}/{endpoint_id.strip('/')}"
        url = f"{base}{path}"
        headers = self.build_headers({"Content-Type": "application/json"})
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            try:
                response = await client.request(method, url, params=params, json=json_body, headers=headers)
            except httpx.HTTPError as exc:  # pragma: no cover - network failure
                raise RunPodClientError(f"RunPod serverless request failed: {exc}") from exc

        if response.status_code in (401, 403):
            raise RunPodAuthenticationError("RunPod serverless API rejected the request")

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            try:
                return response.json()
            except json.JSONDecodeError as exc:
                raise RunPodClientError("Invalid JSON response from RunPod serverless API") from exc
        return response.text

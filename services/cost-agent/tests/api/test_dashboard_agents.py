"""Tests for agent heartbeat refresh logic."""

from datetime import datetime, timedelta

import pytest

from src.api import dashboard_routes as dashboard


class _MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _MockClient:
    def __init__(self, responses):
        self._responses = responses
        self.requested = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        self.requested.append(url)
        return self._responses[url]


class _ErrorClient(_MockClient):
    async def get(self, url):
        raise RuntimeError("boom")


def _make_agent(**overrides):
    defaults = dict(
        agent_id="agent-1",
        agent_name="cost-agent-1",
        agent_type="cost",
        version="0.1.0",
        status="active",
        last_heartbeat=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
        capabilities=[],
        host="cost-agent",
        port=8001,
    )
    defaults.update(overrides)
    return dashboard.AgentPayload(**defaults)


@pytest.mark.asyncio
async def test_refresh_agent_heartbeats_updates_stale(monkeypatch):
    """Stale agents should be probed and updated with fresh data."""
    agent = _make_agent()
    new_timestamp = "2024-05-05T12:00:00+00:00"

    monkeypatch.setattr(dashboard, "AGENT_HEARTBEAT_STALE_SECONDS", 0)
    mock_client = _MockClient(
        {
            "http://cost-agent:8001/api/v1/health": _MockResponse(
                {"status": "healthy", "timestamp": new_timestamp}
            )
        }
    )
    monkeypatch.setattr(dashboard.httpx, "AsyncClient", lambda timeout=2.0: mock_client)

    await dashboard._refresh_agent_heartbeats([agent])

    assert agent.last_heartbeat == new_timestamp
    assert agent.status == "active"
    assert mock_client.requested == ["http://cost-agent:8001/api/v1/health"]


@pytest.mark.asyncio
async def test_refresh_agent_heartbeats_marks_inactive_on_failure(monkeypatch):
    """Failed probes should flag the agent as inactive."""
    agent = _make_agent(last_heartbeat=None)

    monkeypatch.setattr(dashboard, "AGENT_HEARTBEAT_STALE_SECONDS", 0)
    error_client = _ErrorClient({})
    monkeypatch.setattr(dashboard.httpx, "AsyncClient", lambda timeout=2.0: error_client)

    await dashboard._refresh_agent_heartbeats([agent])

    assert agent.status == "inactive"

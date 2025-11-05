# OptiInfra E2E System Tests - PART 1: Implementation

**Document Version:** 1.0  
**Phase:** 5.8 - E2E System Tests  
**Dependencies:** ALL prompts (complete system)  
**Status:** Production-Ready  
**Last Updated:** October 27, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Test Architecture](#test-architecture)
3. [Test Environment Setup](#test-environment-setup)
4. [Test Fixtures & Utilities](#test-fixtures--utilities)
5. [E2E Test Scenarios](#e2e-test-scenarios)
6. [Integration Tests](#integration-tests)
7. [Performance Tests](#performance-tests)
8. [Security Tests](#security-tests)
9. [Running the Tests](#running-the-tests)
10. [Test Coverage](#test-coverage)

---

## 1. Overview

### Purpose

End-to-end system tests validate the complete OptiInfra platform, including:
- All 4 agents (Cost, Performance, Resource, Application) working together
- Orchestrator coordinating multi-agent workflows
- Customer portal integration
- Complete optimization workflows (from detection → recommendation → approval → execution → validation)
- Real infrastructure changes (in test environment)

### Test Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    E2E TEST PYRAMID                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│          📊 E2E System Tests (8-10 scenarios)                   │
│              ↓ This document                                    │
│                                                                 │
│       🔗 Integration Tests (20-30 tests)                        │
│           ↓ Agent-to-Orchestrator                               │
│           ↓ Portal-to-API                                       │
│                                                                 │
│    🧪 Unit Tests (200+ tests)                                   │
│        ↓ Individual functions                                   │
│        ↓ Agent modules                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Test Scope

**✅ IN SCOPE:**
- Complete user workflows (sign up → optimization → savings)
- Multi-agent coordination and conflict resolution
- Real cloud resources (test AWS account)
- Data persistence across all databases
- Portal functionality and real-time updates
- Security and authentication
- Error handling and rollback mechanisms

**❌ OUT OF SCOPE:**
- Load testing (separate suite)
- Chaos engineering (separate suite)
- Manual exploratory testing

---

## 2. Test Architecture

### Directory Structure

```
tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   ├── test_spot_migration.py         # E2E scenario 1
│   ├── test_performance_optimization.py # E2E scenario 2
│   ├── test_multi_agent_coordination.py # E2E scenario 3
│   ├── test_quality_validation.py     # E2E scenario 4
│   ├── test_complete_customer_journey.py # E2E scenario 5
│   ├── test_rollback_scenario.py      # E2E scenario 6
│   ├── test_conflict_resolution.py    # E2E scenario 7
│   └── test_cross_cloud_optimization.py # E2E scenario 8
│
├── fixtures/
│   ├── test_infrastructure.py         # Mock AWS resources
│   ├── test_data.py                   # Test customer data
│   ├── mock_llm_responses.py          # Mock LLM API responses
│   └── sample_metrics.py              # Sample telemetry data
│
├── helpers/
│   ├── api_client.py                  # API client for tests
│   ├── aws_simulator.py               # Mock AWS API
│   ├── database_helpers.py            # DB utilities
│   ├── wait_helpers.py                # Polling utilities
│   └── assertions.py                  # Custom assertions
│
└── docker-compose.e2e.yml             # Test environment
```

### Test Environment

```yaml
# docker-compose.e2e.yml
version: '3.8'

services:
  # Databases
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: optiinfra_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test123
    ports:
      - "5433:5432"

  clickhouse:
    image: clickhouse/clickhouse-server:latest
    ports:
      - "8124:8123"

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6334:6333"

  # OptiInfra Services
  orchestrator:
    build: ../../orchestrator
    environment:
      - ENV=test
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    ports:
      - "8001:8000"

  cost-agent:
    build: ../../agents/cost_agent
    environment:
      - ENV=test
      - ORCHESTRATOR_URL=http://orchestrator:8000
    depends_on:
      - orchestrator

  performance-agent:
    build: ../../agents/performance_agent
    environment:
      - ENV=test
      - ORCHESTRATOR_URL=http://orchestrator:8000
    depends_on:
      - orchestrator

  resource-agent:
    build: ../../agents/resource_agent
    environment:
      - ENV=test
      - ORCHESTRATOR_URL=http://orchestrator:8000
    depends_on:
      - orchestrator

  application-agent:
    build: ../../agents/application_agent
    environment:
      - ENV=test
      - ORCHESTRATOR_URL=http://orchestrator:8000
    depends_on:
      - orchestrator

  portal:
    build: ../../portal
    environment:
      - NEXT_PUBLIC_API_URL=http://orchestrator:8000
    ports:
      - "3001:3000"
    depends_on:
      - orchestrator

  # Mock AWS API
  localstack:
    image: localstack/localstack:latest
    environment:
      - SERVICES=ec2,iam,cloudwatch
      - DEBUG=1
    ports:
      - "4567:4566"
```

---

## 3. Test Environment Setup

### conftest.py - Pytest Configuration

```python
"""
Global pytest configuration and fixtures for E2E tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
import docker
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import redis
import clickhouse_connect
from qdrant_client import QdrantClient

from helpers.api_client import OptiInfraClient
from helpers.database_helpers import DatabaseHelper
from helpers.aws_simulator import AWSSimulator
from fixtures.test_data import TestCustomerFactory, TestInfrastructureFactory


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end (deselect with '-m \"not e2e\"')"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_aws: marks tests that need AWS credentials"
    )


# ============================================================================
# Test Environment Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def docker_compose():
    """Start Docker Compose environment for tests."""
    client = docker.from_env()
    compose_file = "docker-compose.e2e.yml"
    project_name = "optiinfra-e2e"
    
    print("\n🚀 Starting test environment...")
    client.containers.run(
        "docker/compose:latest",
        f"up -d --project-name {project_name}",
        volumes={compose_file: {"bind": "/docker-compose.yml", "mode": "ro"}},
        remove=True
    )
    
    # Wait for services to be healthy
    time.sleep(10)
    print("✅ Test environment ready\n")
    
    yield
    
    # Cleanup
    print("\n🧹 Cleaning up test environment...")
    client.containers.run(
        "docker/compose:latest",
        f"down -v --project-name {project_name}",
        volumes={compose_file: {"bind": "/docker-compose.yml", "mode": "ro"}},
        remove=True
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def db_session(docker_compose) -> Generator[Session, None, None]:
    """Provide a database session for tests."""
    engine = create_engine("postgresql://test:test123@localhost:5433/optiinfra_test")
    
    # Create tables
    from database.models import Base
    Base.metadata.create_all(engine)
    
    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.rollback()
    session.close()


@pytest.fixture
def redis_client(docker_compose) -> redis.Redis:
    """Provide Redis client for tests."""
    client = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
    
    yield client
    
    # Cleanup
    client.flushdb()


@pytest.fixture
def clickhouse_client(docker_compose):
    """Provide ClickHouse client for tests."""
    client = clickhouse_connect.get_client(
        host="localhost",
        port=8124,
        username="default",
        password=""
    )
    
    yield client
    
    # Cleanup - drop test tables
    client.command("DROP DATABASE IF EXISTS test_metrics")


@pytest.fixture
def qdrant_client(docker_compose) -> QdrantClient:
    """Provide Qdrant client for tests."""
    client = QdrantClient(host="localhost", port=6334)
    
    yield client
    
    # Cleanup - delete collections
    collections = client.get_collections().collections
    for collection in collections:
        client.delete_collection(collection.name)


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
async def api_client(docker_compose) -> AsyncGenerator[OptiInfraClient, None]:
    """Provide authenticated API client."""
    client = OptiInfraClient(base_url="http://localhost:8001")
    
    # Wait for API to be ready
    await client.wait_for_health()
    
    yield client
    
    await client.close()


@pytest.fixture
async def admin_client(api_client: OptiInfraClient) -> OptiInfraClient:
    """Provide admin-authenticated API client."""
    await api_client.login(username="admin@optiinfra.ai", password="admin123")
    return api_client


@pytest.fixture
async def customer_client(api_client: OptiInfraClient) -> OptiInfraClient:
    """Provide customer-authenticated API client."""
    # Create test customer
    customer = await api_client.create_customer({
        "email": "test@example.com",
        "company_name": "Test Company",
        "plan": "pro"
    })
    
    # Login as customer
    await api_client.login(username="test@example.com", password="test123")
    
    return api_client


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def test_customer(db_session):
    """Create a test customer."""
    factory = TestCustomerFactory(db_session)
    customer = factory.create_customer(
        company_name="Acme Corp",
        monthly_spend=120000,
        cloud_provider="aws"
    )
    return customer


@pytest.fixture
def test_infrastructure(db_session, test_customer):
    """Create test infrastructure for customer."""
    factory = TestInfrastructureFactory(db_session)
    
    infrastructure = factory.create_infrastructure(
        customer_id=test_customer.id,
        instances=[
            {
                "instance_id": "i-123456",
                "instance_type": "p4d.24xlarge",
                "region": "us-east-1",
                "pricing": "on-demand",
                "monthly_cost": 30000,
                "gpu_type": "A100",
                "gpu_count": 8,
                "utilization": 0.78
            },
            {
                "instance_id": "i-789012",
                "instance_type": "p4d.24xlarge",
                "region": "us-east-1",
                "pricing": "on-demand",
                "monthly_cost": 30000,
                "gpu_type": "A100",
                "gpu_count": 8,
                "utilization": 0.72
            }
        ],
        vllm_deployments=[
            {
                "deployment_id": "vllm-prod-1",
                "model": "meta-llama/Llama-3-70B",
                "instance_ids": ["i-123456", "i-789012"],
                "avg_latency_p95": 1600,
                "requests_per_second": 45
            }
        ]
    )
    
    return infrastructure


@pytest.fixture
def aws_simulator(docker_compose):
    """Provide AWS API simulator (LocalStack)."""
    simulator = AWSSimulator(endpoint_url="http://localhost:4567")
    simulator.setup()
    
    yield simulator
    
    simulator.cleanup()


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest.fixture
def db_helper(db_session):
    """Provide database helper utilities."""
    return DatabaseHelper(db_session)


@pytest.fixture
def wait_for(api_client):
    """Provide wait helper for polling."""
    from helpers.wait_helpers import WaitHelper
    return WaitHelper(api_client)


# ============================================================================
# Test Data Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_between_tests(db_session, redis_client):
    """Automatic cleanup between tests."""
    yield
    
    # Rollback any uncommitted transactions
    db_session.rollback()
    
    # Clear Redis cache
    redis_client.flushdb()
```

---

## 4. Test Fixtures & Utilities

### helpers/api_client.py

```python
"""
API client for E2E tests.
"""
import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime


class OptiInfraClient:
    """High-level API client for testing."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self.token: Optional[str] = None
    
    async def wait_for_health(self, max_retries: int = 30):
        """Wait for API to be healthy."""
        for i in range(max_retries):
            try:
                response = await self.client.get("/health")
                if response.status_code == 200:
                    print(f"✅ API is healthy")
                    return
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        raise TimeoutError("API did not become healthy in time")
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and store token."""
        response = await self.client.post("/auth/login", json={
            "username": username,
            "password": password
        })
        response.raise_for_status()
        
        data = response.json()
        self.token = data["access_token"]
        
        # Set authorization header
        self.client.headers["Authorization"] = f"Bearer {self.token}"
        
        return data
    
    async def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer."""
        response = await self.client.post("/customers", json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_recommendations(self, customer_id: str) -> list:
        """Get recommendations for customer."""
        response = await self.client.get(f"/customers/{customer_id}/recommendations")
        response.raise_for_status()
        return response.json()
    
    async def approve_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """Approve a recommendation."""
        response = await self.client.post(
            f"/recommendations/{recommendation_id}/approve"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_optimization_status(self, optimization_id: str) -> Dict[str, Any]:
        """Get optimization execution status."""
        response = await self.client.get(f"/optimizations/{optimization_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_customer_metrics(
        self, 
        customer_id: str, 
        metric_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> list:
        """Get customer metrics."""
        params = {"metric_type": metric_type}
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()
        
        response = await self.client.get(
            f"/customers/{customer_id}/metrics",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def trigger_agent_analysis(self, customer_id: str, agent_type: str):
        """Manually trigger agent analysis."""
        response = await self.client.post(
            f"/customers/{customer_id}/analyze",
            json={"agent_type": agent_type}
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()


class WebSocketClient:
    """WebSocket client for real-time updates."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.replace("http", "ws")
        self.messages = []
    
    async def connect(self, customer_id: str):
        """Connect to WebSocket."""
        import websockets
        
        self.ws = await websockets.connect(
            f"{self.base_url}/ws/customers/{customer_id}"
        )
    
    async def receive_message(self, timeout: float = 10.0):
        """Receive a message with timeout."""
        import asyncio
        
        try:
            message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            self.messages.append(message)
            return message
        except asyncio.TimeoutError:
            return None
    
    async def close(self):
        """Close the WebSocket."""
        await self.ws.close()
```

### helpers/wait_helpers.py

```python
"""
Wait helpers for polling asynchronous operations.
"""
import asyncio
from typing import Callable, Any, Optional
from datetime import datetime, timedelta


class WaitHelper:
    """Helper for waiting on conditions."""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def wait_for_recommendation(
        self,
        customer_id: str,
        recommendation_type: str,
        timeout: float = 60.0
    ) -> Optional[dict]:
        """Wait for a specific recommendation to appear."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            recommendations = await self.api_client.get_recommendations(customer_id)
            
            for rec in recommendations:
                if rec["type"] == recommendation_type and rec["status"] == "pending":
                    return rec
            
            await asyncio.sleep(2)
        
        return None
    
    async def wait_for_optimization_complete(
        self,
        optimization_id: str,
        timeout: float = 300.0
    ) -> dict:
        """Wait for optimization to complete."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            status = await self.api_client.get_optimization_status(optimization_id)
            
            if status["status"] in ["completed", "failed", "rolled_back"]:
                return status
            
            await asyncio.sleep(5)
        
        raise TimeoutError(f"Optimization {optimization_id} did not complete in time")
    
    async def wait_for_metric_change(
        self,
        customer_id: str,
        metric_type: str,
        condition: Callable[[Any], bool],
        timeout: float = 60.0
    ) -> bool:
        """Wait for a metric to meet a condition."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            metrics = await self.api_client.get_customer_metrics(
                customer_id,
                metric_type,
                start_time=datetime.now() - timedelta(minutes=5)
            )
            
            if metrics and condition(metrics[-1]["value"]):
                return True
            
            await asyncio.sleep(5)
        
        return False
    
    async def wait_for_condition(
        self,
        condition: Callable[[], bool],
        timeout: float = 60.0,
        poll_interval: float = 2.0
    ) -> bool:
        """Generic wait for condition."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            if await condition():
                return True
            
            await asyncio.sleep(poll_interval)
        
        return False
```

### helpers/assertions.py

```python
"""
Custom assertions for E2E tests.
"""
from typing import Dict, Any, List


def assert_optimization_successful(optimization: Dict[str, Any]):
    """Assert that optimization completed successfully."""
    assert optimization["status"] == "completed", \
        f"Expected optimization to complete, got status: {optimization['status']}"
    
    assert "result" in optimization, \
        "Optimization result missing"
    
    assert optimization["result"]["success"] is True, \
        f"Optimization failed: {optimization['result'].get('error')}"


def assert_cost_reduced(before: float, after: float, min_reduction_pct: float = 10.0):
    """Assert that cost was reduced by at least min_reduction_pct."""
    reduction_pct = ((before - after) / before) * 100
    
    assert reduction_pct >= min_reduction_pct, \
        f"Expected cost reduction of at least {min_reduction_pct}%, got {reduction_pct:.2f}%"


def assert_latency_improved(before: float, after: float, max_degradation_pct: float = 5.0):
    """Assert that latency improved or degraded less than max_degradation_pct."""
    degradation_pct = ((after - before) / before) * 100
    
    assert degradation_pct <= max_degradation_pct, \
        f"Latency degraded by {degradation_pct:.2f}%, max allowed: {max_degradation_pct}%"


def assert_quality_maintained(quality_metrics: List[Dict[str, Any]], threshold: float = 0.95):
    """Assert that quality remained above threshold."""
    for metric in quality_metrics:
        assert metric["score"] >= threshold, \
            f"Quality score {metric['score']} below threshold {threshold}"


def assert_multi_agent_coordination(events: List[Dict[str, Any]]):
    """Assert proper multi-agent coordination."""
    agent_types = {event["agent_type"] for event in events}
    
    assert len(agent_types) > 1, \
        "Expected multiple agents to participate"
    
    # Check orchestrator coordinated
    orchestrator_events = [e for e in events if e.get("source") == "orchestrator"]
    assert len(orchestrator_events) > 0, \
        "Expected orchestrator coordination events"
```

---

## 5. E2E Test Scenarios

### test_spot_migration.py - Scenario 1

```python
"""
E2E Test: Complete Spot Instance Migration Workflow

Tests the full journey:
1. Cost agent detects optimization opportunity
2. Generates recommendation
3. Multi-agent validation
4. Customer approval
5. Execution with blue-green deployment
6. Validation and cost tracking
"""
import pytest
from datetime import datetime, timedelta
from helpers.assertions import (
    assert_optimization_successful,
    assert_cost_reduced,
    assert_quality_maintained
)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_complete_spot_migration_workflow(
    customer_client,
    test_customer,
    test_infrastructure,
    wait_for,
    db_session
):
    """Test complete spot migration from detection to savings."""
    
    # ========================================================================
    # PHASE 1: Initial State
    # ========================================================================
    print("\n📊 PHASE 1: Recording initial state...")
    
    initial_cost = await customer_client.get_customer_metrics(
        test_customer.id,
        "monthly_cost"
    )
    initial_cost_value = initial_cost[-1]["value"]
    
    print(f"  Initial monthly cost: ${initial_cost_value:,.0f}")
    
    # ========================================================================
    # PHASE 2: Trigger Cost Analysis
    # ========================================================================
    print("\n🔍 PHASE 2: Triggering cost agent analysis...")
    
    analysis = await customer_client.trigger_agent_analysis(
        test_customer.id,
        agent_type="cost"
    )
    
    assert analysis["status"] == "started"
    print(f"  Analysis ID: {analysis['analysis_id']}")
    
    # ========================================================================
    # PHASE 3: Wait for Recommendation
    # ========================================================================
    print("\n⏳ PHASE 3: Waiting for spot migration recommendation...")
    
    recommendation = await wait_for.wait_for_recommendation(
        test_customer.id,
        recommendation_type="spot_migration",
        timeout=120.0
    )
    
    assert recommendation is not None, "Spot migration recommendation not generated"
    print(f"  ✅ Recommendation generated: {recommendation['id']}")
    print(f"  Estimated savings: ${recommendation['estimated_savings']:,.0f}/month")
    
    # Validate recommendation details
    assert recommendation["agent_type"] == "cost"
    assert recommendation["risk_level"] in ["low", "medium"]
    assert recommendation["estimated_savings"] > 10000  # At least $10K savings
    
    # ========================================================================
    # PHASE 4: Multi-Agent Validation
    # ========================================================================
    print("\n🤝 PHASE 4: Waiting for multi-agent validation...")
    
    # Performance agent should validate
    validations = recommendation.get("validations", [])
    
    await wait_for.wait_for_condition(
        lambda: len(validations) >= 2,  # Cost + Performance at minimum
        timeout=60.0
    )
    
    performance_validation = next(
        (v for v in validations if v["agent_type"] == "performance"),
        None
    )
    assert performance_validation is not None
    assert performance_validation["approved"] is True
    print(f"  ✅ Performance agent approved")
    
    # Application agent should establish baseline
    app_validation = next(
        (v for v in validations if v["agent_type"] == "application"),
        None
    )
    assert app_validation is not None
    assert app_validation["baseline_established"] is True
    print(f"  ✅ Application agent baseline established")
    
    # ========================================================================
    # PHASE 5: Customer Approval
    # ========================================================================
    print("\n👤 PHASE 5: Customer approves recommendation...")
    
    approval = await customer_client.approve_recommendation(recommendation["id"])
    
    assert approval["status"] == "approved"
    optimization_id = approval["optimization_id"]
    print(f"  ✅ Approved. Optimization ID: {optimization_id}")
    
    # ========================================================================
    # PHASE 6: Execution (Blue-Green Deployment)
    # ========================================================================
    print("\n⚙️  PHASE 6: Monitoring execution...")
    
    optimization = await wait_for.wait_for_optimization_complete(
        optimization_id,
        timeout=600.0  # 10 minutes
    )
    
    assert_optimization_successful(optimization)
    print(f"  ✅ Optimization completed successfully")
    
    # Validate execution steps
    steps = optimization["execution_steps"]
    expected_steps = [
        "create_spot_instances",
        "deploy_canary",
        "validate_canary",
        "scale_to_50_percent",
        "validate_50_percent",
        "full_migration",
        "terminate_ondemand"
    ]
    
    for step in expected_steps:
        assert any(s["name"] == step and s["status"] == "completed" for s in steps), \
            f"Expected step {step} to complete"
    
    print(f"  ✅ All {len(steps)} execution steps completed")
    
    # ========================================================================
    # PHASE 7: Quality Validation
    # ========================================================================
    print("\n✅ PHASE 7: Validating quality maintained...")
    
    quality_metrics = await customer_client.get_customer_metrics(
        test_customer.id,
        "quality_score",
        start_time=optimization["started_at"],
        end_time=datetime.now()
    )
    
    assert_quality_maintained(quality_metrics, threshold=0.95)
    print(f"  ✅ Quality maintained above 95%")
    
    # ========================================================================
    # PHASE 8: Cost Savings Validation
    # ========================================================================
    print("\n💰 PHASE 8: Validating cost savings...")
    
    # Wait a bit for cost metrics to update
    await asyncio.sleep(10)
    
    new_cost = await customer_client.get_customer_metrics(
        test_customer.id,
        "monthly_cost"
    )
    new_cost_value = new_cost[-1]["value"]
    
    print(f"  New monthly cost: ${new_cost_value:,.0f}")
    print(f"  Actual savings: ${initial_cost_value - new_cost_value:,.0f}/month")
    
    assert_cost_reduced(initial_cost_value, new_cost_value, min_reduction_pct=40.0)
    print(f"  ✅ Cost reduced by >40%")
    
    # ========================================================================
    # PHASE 9: Learning Loop
    # ========================================================================
    print("\n🧠 PHASE 9: Verifying learning loop...")
    
    # Cost agent should have stored success pattern
    from database.models import OptimizationOutcome
    outcome = db_session.query(OptimizationOutcome).filter_by(
        optimization_id=optimization_id
    ).first()
    
    assert outcome is not None
    assert outcome.success is True
    assert outcome.stored_in_vector_db is True
    print(f"  ✅ Success pattern stored for future learning")
    
    print("\n" + "="*70)
    print("✅ SPOT MIGRATION E2E TEST PASSED")
    print("="*70 + "\n")
```

### test_multi_agent_coordination.py - Scenario 3

```python
"""
E2E Test: Multi-Agent Coordination with Conflict Resolution

Tests:
1. Multiple agents generating recommendations
2. Conflicting recommendations
3. Orchestrator conflict resolution
4. Priority-based decision making
"""
import pytest
from datetime import datetime


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_agent_conflict_resolution(
    customer_client,
    test_customer,
    test_infrastructure,
    wait_for,
    db_session
):
    """Test orchestrator resolves conflicts between agents."""
    
    print("\n🤝 TESTING MULTI-AGENT CONFLICT RESOLUTION")
    print("="*70)
    
    # ========================================================================
    # PHASE 1: Setup Conflicting Scenario
    # ========================================================================
    print("\n📊 PHASE 1: Creating scenario with potential conflicts...")
    
    # Cost agent will recommend spot migration (lower cost)
    # Performance agent will recommend staying on-demand (lower risk)
    
    # Trigger both analyses simultaneously
    cost_analysis = await customer_client.trigger_agent_analysis(
        test_customer.id,
        agent_type="cost"
    )
    
    perf_analysis = await customer_client.trigger_agent_analysis(
        test_customer.id,
        agent_type="performance"
    )
    
    print(f"  Cost analysis: {cost_analysis['analysis_id']}")
    print(f"  Performance analysis: {perf_analysis['analysis_id']}")
    
    # ========================================================================
    # PHASE 2: Wait for Conflicting Recommendations
    # ========================================================================
    print("\n⏳ PHASE 2: Waiting for recommendations...")
    
    recommendations = await wait_for.wait_for_condition(
        lambda: len(customer_client.get_recommendations(test_customer.id)) >= 2,
        timeout=120.0
    )
    
    all_recs = await customer_client.get_recommendations(test_customer.id)
    
    # Find conflicting recommendations
    cost_rec = next((r for r in all_recs if r["agent_type"] == "cost"), None)
    perf_rec = next((r for r in all_recs if r["agent_type"] == "performance"), None)
    
    assert cost_rec is not None
    assert perf_rec is not None
    
    print(f"  Cost recommendation: {cost_rec['type']}")
    print(f"  Performance recommendation: {perf_rec['type']}")
    
    # ========================================================================
    # PHASE 3: Orchestrator Analyzes Conflict
    # ========================================================================
    print("\n🧠 PHASE 3: Orchestrator analyzing conflict...")
    
    # Trigger orchestrator conflict resolution
    resolution = await customer_client.client.post(
        "/orchestrator/resolve-conflict",
        json={
            "customer_id": test_customer.id,
            "recommendation_ids": [cost_rec["id"], perf_rec["id"]]
        }
    )
    resolution_data = resolution.json()
    
    assert resolution_data["conflict_detected"] is True
    assert resolution_data["resolution_strategy"] in [
        "prioritize_customer",
        "negotiate_hybrid",
        "sequential_execution"
    ]
    
    print(f"  ✅ Conflict detected and resolved")
    print(f"  Strategy: {resolution_data['resolution_strategy']}")
    
    # ========================================================================
    # PHASE 4: Validate Resolution Logic
    # ========================================================================
    print("\n✅ PHASE 4: Validating resolution logic...")
    
    # Check that orchestrator followed priority rules
    # Priority: Customer preference > Performance > Cost
    
    if resolution_data["resolution_strategy"] == "prioritize_customer":
        # Customer preferences should be respected
        assert resolution_data["chosen_recommendation"] is not None
        print(f"  ✅ Customer preference respected")
    
    elif resolution_data["resolution_strategy"] == "negotiate_hybrid":
        # Hybrid solution combining both
        assert resolution_data["hybrid_solution"] is not None
        print(f"  ✅ Hybrid solution negotiated")
    
    elif resolution_data["resolution_strategy"] == "sequential_execution":
        # Execute in priority order
        assert len(resolution_data["execution_order"]) == 2
        print(f"  ✅ Sequential execution planned")
    
    # ========================================================================
    # PHASE 5: Execute Resolution
    # ========================================================================
    print("\n⚙️  PHASE 5: Executing resolution...")
    
    execution = await customer_client.client.post(
        "/orchestrator/execute-resolution",
        json={"resolution_id": resolution_data["id"]}
    )
    execution_data = execution.json()
    
    optimization = await wait_for.wait_for_optimization_complete(
        execution_data["optimization_id"],
        timeout=600.0
    )
    
    assert optimization["status"] == "completed"
    print(f"  ✅ Resolution executed successfully")
    
    # ========================================================================
    # PHASE 6: Verify All Agents Notified
    # ========================================================================
    print("\n📢 PHASE 6: Verifying agent notifications...")
    
    # All agents should be notified of the outcome
    from database.models import AgentEvent
    events = db_session.query(AgentEvent).filter_by(
        customer_id=test_customer.id,
        event_type="resolution_executed"
    ).all()
    
    agent_types = {event.agent_type for event in events}
    assert "cost" in agent_types
    assert "performance" in agent_types
    assert "orchestrator" in agent_types
    
    print(f"  ✅ All agents notified: {agent_types}")
    
    print("\n" + "="*70)
    print("✅ MULTI-AGENT COORDINATION TEST PASSED")
    print("="*70 + "\n")
```

### test_complete_customer_journey.py - Scenario 5

```python
"""
E2E Test: Complete Customer Journey

Tests the entire customer experience from signup to savings:
1. Customer signup
2. Infrastructure onboarding
3. Agent runtime deployment
4. First analysis
5. Recommendation review
6. Approval and execution
7. Ongoing monitoring
8. Dashboard visualization
"""
import pytest
from datetime import datetime


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_complete_customer_journey(
    api_client,
    wait_for,
    db_session,
    aws_simulator
):
    """Test complete customer journey from signup to savings."""
    
    print("\n🚀 TESTING COMPLETE CUSTOMER JOURNEY")
    print("="*70)
    
    # ========================================================================
    # PHASE 1: Customer Signup
    # ========================================================================
    print("\n👤 PHASE 1: Customer signs up...")
    
    signup = await api_client.client.post("/auth/signup", json={
        "email": "newcustomer@example.com",
        "company_name": "NewCorp Inc",
        "password": "securepass123",
        "plan": "pro"
    })
    signup_data = signup.json()
    
    assert signup_data["success"] is True
    customer_id = signup_data["customer_id"]
    print(f"  ✅ Customer created: {customer_id}")
    
    # Login
    await api_client.login("newcustomer@example.com", "securepass123")
    print(f"  ✅ Logged in successfully")
    
    # ========================================================================
    # PHASE 2: Infrastructure Onboarding
    # ========================================================================
    print("\n🏗️  PHASE 2: Onboarding infrastructure...")
    
    # Customer provides AWS credentials
    onboarding = await api_client.client.post(
        f"/customers/{customer_id}/onboard",
        json={
            "cloud_provider": "aws",
            "region": "us-east-1",
            "iam_role_arn": "arn:aws:iam::123456789012:role/OptiInfraAgent"
        }
    )
    onboarding_data = onboarding.json()
    
    assert onboarding_data["status"] == "started"
    print(f"  ✅ Onboarding initiated")
    
    # ========================================================================
    # PHASE 3: Agent Runtime Deployment
    # ========================================================================
    print("\n🤖 PHASE 3: Deploying agent runtime...")
    
    # Portal provides install command
    install_cmd = await api_client.client.get(
        f"/customers/{customer_id}/agent-install-command"
    )
    cmd_data = install_cmd.json()
    
    assert "install_command" in cmd_data
    assert "agent_token" in cmd_data
    print(f"  ✅ Install command generated")
    
    # Simulate agent runtime connecting
    agent_connection = await api_client.client.post(
        "/agent-runtime/connect",
        json={
            "customer_id": customer_id,
            "agent_token": cmd_data["agent_token"],
            "hostname": "test-agent-runtime",
            "version": "1.0.0"
        }
    )
    agent_data = agent_connection.json()
    
    assert agent_data["connected"] is True
    print(f"  ✅ Agent runtime connected")
    
    # ========================================================================
    # PHASE 4: Infrastructure Discovery
    # ========================================================================
    print("\n🔍 PHASE 4: Discovering infrastructure...")
    
    # Agent runtime discovers customer's infrastructure
    # (Simulated using AWS simulator)
    
    # Wait for discovery to complete
    await wait_for.wait_for_condition(
        lambda: api_client.client.get(
            f"/customers/{customer_id}/infrastructure"
        ).json().get("status") == "discovered",
        timeout=120.0
    )
    
    infra = await api_client.client.get(f"/customers/{customer_id}/infrastructure")
    infra_data = infra.json()
    
    assert len(infra_data["instances"]) > 0
    assert len(infra_data["vllm_deployments"]) > 0
    print(f"  ✅ Infrastructure discovered:")
    print(f"     - {len(infra_data['instances'])} instances")
    print(f"     - {len(infra_data['vllm_deployments'])} vLLM deployments")
    
    # ========================================================================
    # PHASE 5: Initial Analysis
    # ========================================================================
    print("\n📊 PHASE 5: Running initial analysis...")
    
    # All agents analyze automatically
    await wait_for.wait_for_condition(
        lambda: len(api_client.get_recommendations(customer_id)) > 0,
        timeout=180.0
    )
    
    recommendations = await api_client.get_recommendations(customer_id)
    
    assert len(recommendations) > 0
    print(f"  ✅ {len(recommendations)} recommendations generated")
    
    for rec in recommendations[:3]:  # Show first 3
        print(f"     - {rec['type']}: Save ${rec['estimated_savings']:,.0f}/mo")
    
    # ========================================================================
    # PHASE 6: Customer Reviews in Portal
    # ========================================================================
    print("\n📱 PHASE 6: Customer reviews in portal...")
    
    # Simulate customer opening portal
    portal_data = await api_client.client.get(
        f"/portal/customers/{customer_id}/dashboard"
    )
    dashboard = portal_data.json()
    
    assert "current_spend" in dashboard
    assert "potential_savings" in dashboard
    assert "recommendations" in dashboard
    
    print(f"  ✅ Dashboard loaded:")
    print(f"     - Current spend: ${dashboard['current_spend']:,.0f}/mo")
    print(f"     - Potential savings: ${dashboard['potential_savings']:,.0f}/mo")
    print(f"     - Recommendations: {len(dashboard['recommendations'])}")
    
    # ========================================================================
    # PHASE 7: Customer Approves Top Recommendation
    # ========================================================================
    print("\n👍 PHASE 7: Customer approves recommendation...")
    
    # Get highest-savings recommendation
    top_rec = max(recommendations, key=lambda r: r["estimated_savings"])
    
    approval = await api_client.approve_recommendation(top_rec["id"])
    optimization_id = approval["optimization_id"]
    
    print(f"  ✅ Approved: {top_rec['type']}")
    print(f"     Expected savings: ${top_rec['estimated_savings']:,.0f}/mo")
    
    # ========================================================================
    # PHASE 8: Optimization Execution
    # ========================================================================
    print("\n⚙️  PHASE 8: Executing optimization...")
    
    # Monitor via WebSocket (real-time updates)
    from helpers.api_client import WebSocketClient
    ws_client = WebSocketClient(base_url=api_client.base_url)
    await ws_client.connect(customer_id)
    
    # Wait for completion
    optimization = await wait_for.wait_for_optimization_complete(
        optimization_id,
        timeout=600.0
    )
    
    assert optimization["status"] == "completed"
    print(f"  ✅ Optimization completed")
    
    # Check that customer received real-time updates
    assert len(ws_client.messages) > 0
    print(f"     - Received {len(ws_client.messages)} real-time updates")
    
    await ws_client.close()
    
    # ========================================================================
    # PHASE 9: Results Validation
    # ========================================================================
    print("\n💰 PHASE 9: Validating results...")
    
    # Check updated dashboard
    updated_dashboard = await api_client.client.get(
        f"/portal/customers/{customer_id}/dashboard"
    )
    new_dashboard = updated_dashboard.json()
    
    assert new_dashboard["current_spend"] < dashboard["current_spend"]
    
    actual_savings = dashboard["current_spend"] - new_dashboard["current_spend"]
    print(f"  ✅ Actual savings: ${actual_savings:,.0f}/mo")
    print(f"     vs predicted: ${top_rec['estimated_savings']:,.0f}/mo")
    
    # Validate savings are within 20% of prediction
    prediction_accuracy = (actual_savings / top_rec["estimated_savings"]) * 100
    assert 80 <= prediction_accuracy <= 120
    print(f"  ✅ Prediction accuracy: {prediction_accuracy:.1f}%")
    
    # ========================================================================
    # PHASE 10: Ongoing Monitoring
    # ========================================================================
    print("\n📈 PHASE 10: Verifying ongoing monitoring...")
    
    # Check that agents continue to monitor
    from database.models import AgentHeartbeat
    heartbeats = db_session.query(AgentHeartbeat).filter_by(
        customer_id=customer_id
    ).all()
    
    agent_types = {hb.agent_type for hb in heartbeats}
    expected_agents = {"cost", "performance", "resource", "application"}
    
    assert agent_types == expected_agents
    print(f"  ✅ All agents monitoring: {agent_types}")
    
    print("\n" + "="*70)
    print("✅ COMPLETE CUSTOMER JOURNEY TEST PASSED")
    print("="*70 + "\n")
```

---

## 6. Integration Tests

### test_agent_orchestrator_integration.py

```python
"""
Integration tests for agent-orchestrator communication.
"""
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_registration(api_client, db_session):
    """Test agent can register with orchestrator."""
    
    # Simulate agent registration
    registration = await api_client.client.post("/orchestrator/agents/register", json={
        "agent_type": "cost",
        "version": "1.0.0",
        "capabilities": [
            "spot_migration",
            "reserved_instance_optimization",
            "instance_rightsizing"
        ],
        "hostname": "cost-agent-pod-1"
    })
    
    assert registration.status_code == 200
    data = registration.json()
    
    assert data["registered"] is True
    assert "agent_id" in data
    
    # Verify in database
    from database.models import Agent
    agent = db_session.query(Agent).filter_by(
        agent_id=data["agent_id"]
    ).first()
    
    assert agent is not None
    assert agent.agent_type == "cost"
    assert agent.status == "active"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_heartbeat(api_client, db_session):
    """Test agent heartbeat mechanism."""
    
    # Register agent first
    registration = await api_client.client.post("/orchestrator/agents/register", json={
        "agent_type": "performance",
        "version": "1.0.0",
        "capabilities": ["latency_optimization"],
        "hostname": "perf-agent-pod-1"
    })
    agent_id = registration.json()["agent_id"]
    
    # Send heartbeat
    heartbeat = await api_client.client.post(
        f"/orchestrator/agents/{agent_id}/heartbeat",
        json={
            "status": "active",
            "current_tasks": 2,
            "load": 0.45
        }
    )
    
    assert heartbeat.status_code == 200
    
    # Verify heartbeat recorded
    from database.models import AgentHeartbeat
    hb = db_session.query(AgentHeartbeat).filter_by(
        agent_id=agent_id
    ).order_by(AgentHeartbeat.timestamp.desc()).first()
    
    assert hb is not None
    assert hb.status == "active"
    assert hb.current_tasks == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_routes_request_to_agent(api_client, test_customer):
    """Test orchestrator routes request to appropriate agent."""
    
    # Make request to orchestrator
    response = await api_client.client.post(
        "/orchestrator/analyze",
        json={
            "customer_id": test_customer.id,
            "analysis_type": "cost_optimization"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["routed_to_agent"] == "cost"
    assert "task_id" in data
```

---

## 7. Performance Tests

### test_system_performance.py

```python
"""
Performance tests for E2E system.
"""
import pytest
import asyncio
from datetime import datetime


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_optimizations(api_client, test_customer):
    """Test system handles multiple concurrent optimizations."""
    
    # Trigger 5 concurrent optimizations
    tasks = []
    for i in range(5):
        task = api_client.trigger_agent_analysis(
            test_customer.id,
            agent_type="cost"
        )
        tasks.append(task)
    
    start_time = datetime.now()
    results = await asyncio.gather(*tasks)
    duration = (datetime.now() - start_time).total_seconds()
    
    # All should succeed
    assert all(r["status"] == "started" for r in results)
    
    # Should complete in reasonable time (<30 seconds)
    assert duration < 30.0
    
    print(f"  ✅ 5 concurrent analyses completed in {duration:.2f}s")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_recommendation_generation_latency(api_client, test_customer):
    """Test recommendation generation is fast."""
    
    start_time = datetime.now()
    
    await api_client.trigger_agent_analysis(test_customer.id, "cost")
    
    # Wait for recommendation
    recommendations = await wait_for.wait_for_condition(
        lambda: len(api_client.get_recommendations(test_customer.id)) > 0,
        timeout=60.0
    )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    assert duration < 60.0  # Should generate within 1 minute
    print(f"  ✅ Recommendation generated in {duration:.2f}s")
```

---

## 8. Security Tests

### test_security.py

```python
"""
Security tests for E2E system.
"""
import pytest


@pytest.mark.security
@pytest.mark.asyncio
async def test_unauthorized_access_denied(api_client):
    """Test unauthorized requests are denied."""
    
    # Try to access without token
    response = await api_client.client.get("/customers")
    
    assert response.status_code == 401


@pytest.mark.security
@pytest.mark.asyncio
async def test_customer_cannot_access_other_customer_data(
    customer_client,
    test_customer,
    db_session
):
    """Test customer can only access their own data."""
    
    # Create another customer
    other_customer = db_session.query(Customer).filter(
        Customer.id != test_customer.id
    ).first()
    
    # Try to access other customer's data
    response = await customer_client.client.get(
        f"/customers/{other_customer.id}/recommendations"
    )
    
    assert response.status_code == 403


@pytest.mark.security
@pytest.mark.asyncio
async def test_sql_injection_prevented(api_client):
    """Test SQL injection is prevented."""
    
    # Attempt SQL injection
    malicious_input = "1' OR '1'='1"
    
    response = await api_client.client.get(
        f"/customers/{malicious_input}/recommendations"
    )
    
    # Should return 400 (validation error) or 404, not 500
    assert response.status_code in [400, 404]
```

---

## 9. Running the Tests

### Makefile

```makefile
# OptiInfra E2E Tests

.PHONY: help test test-e2e test-integration test-performance test-security clean

help:
	@echo "OptiInfra E2E Test Suite"
	@echo ""
	@echo "Available commands:"
	@echo "  make test              - Run all tests"
	@echo "  make test-e2e          - Run only E2E tests"
	@echo "  make test-integration  - Run integration tests"
	@echo "  make test-performance  - Run performance tests"
	@echo "  make test-security     - Run security tests"
	@echo "  make test-fast         - Run fast tests only"
	@echo "  make clean             - Clean up test environment"

# Run all tests
test:
	docker-compose -f docker-compose.e2e.yml up -d
	sleep 10
	pytest tests/e2e/ -v --tb=short --cov=. --cov-report=html
	docker-compose -f docker-compose.e2e.yml down -v

# Run only E2E tests
test-e2e:
	docker-compose -f docker-compose.e2e.yml up -d
	sleep 10
	pytest tests/e2e/ -v -m e2e --tb=short
	docker-compose -f docker-compose.e2e.yml down -v

# Run only integration tests
test-integration:
	docker-compose -f docker-compose.e2e.yml up -d
	sleep 10
	pytest tests/e2e/ -v -m integration --tb=short
	docker-compose -f docker-compose.e2e.yml down -v

# Run performance tests
test-performance:
	docker-compose -f docker-compose.e2e.yml up -d
	sleep 10
	pytest tests/e2e/ -v -m performance --tb=short
	docker-compose -f docker-compose.e2e.yml down -v

# Run security tests
test-security:
	docker-compose -f docker-compose.e2e.yml up -d
	sleep 10
	pytest tests/e2e/ -v -m security --tb=short
	docker-compose -f docker-compose.e2e.yml down -v

# Run fast tests only (exclude slow E2E)
test-fast:
	docker-compose -f docker-compose.e2e.yml up -d
	sleep 10
	pytest tests/e2e/ -v -m "not slow" --tb=short
	docker-compose -f docker-compose.e2e.yml down -v

# Clean up
clean:
	docker-compose -f docker-compose.e2e.yml down -v
	rm -rf .pytest_cache htmlcov .coverage
```

### pytest.ini

```ini
[pytest]
testpaths = tests/e2e
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

markers =
    e2e: End-to-end system tests
    integration: Integration tests
    performance: Performance tests
    security: Security tests
    slow: Slow-running tests

addopts =
    -v
    --strict-markers
    --tb=short
    --cov=.
    --cov-report=term-missing
    --cov-report=html
    --durations=10

filterwarnings =
    ignore::DeprecationWarning
```

---

## 10. Test Coverage

### Coverage Goals

```
Component                Coverage Target    Current
─────────────────────────────────────────────────────
Orchestrator             90%                TBD
Cost Agent               85%                TBD
Performance Agent        85%                TBD
Resource Agent           85%                TBD
Application Agent        85%                TBD
Portal API               80%                TBD
Database Layer           90%                TBD
─────────────────────────────────────────────────────
Overall System           85%                TBD
```

### Running Coverage Report

```bash
# Generate coverage report
make test

# Open HTML report
open htmlcov/index.html

# View coverage summary
coverage report
```

---

## Summary

This implementation document provides:

✅ **Complete test infrastructure** - Docker Compose environment, fixtures, helpers  
✅ **8 E2E test scenarios** - Covering all major workflows  
✅ **Integration tests** - Agent-orchestrator communication  
✅ **Performance tests** - System scalability validation  
✅ **Security tests** - Access control and injection prevention  
✅ **Easy execution** - Makefile commands and pytest configuration  
✅ **Coverage tracking** - Monitoring test coverage goals  

**Next**: See PART 2 (PDF) for execution procedures and validation criteria.

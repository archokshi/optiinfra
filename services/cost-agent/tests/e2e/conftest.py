"""
E2E Test Configuration and Fixtures.

Provides fixtures and configuration for end-to-end integration tests.
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime
from unittest.mock import MagicMock
import json
import os


# Test configuration
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/cost_agent_test")
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_database():
    """Set up test database."""
    db = {
        "url": TEST_DB_URL,
        "connected": True,
        "type": "postgresql"
    }
    
    yield db


@pytest.fixture(scope="session")
async def test_cache():
    """Set up test cache."""
    cache = {
        "url": TEST_REDIS_URL,
        "connected": True,
        "type": "redis"
    }
    
    yield cache


@pytest.fixture
async def clean_database(test_database):
    """Clean database before each test."""
    # Clean all tables before test
    yield
    # Cleanup after test


@pytest.fixture
def mock_aws_client():
    """Mock AWS client for E2E tests."""
    client = MagicMock()
    
    # Mock get_cost_and_usage
    client.get_cost_and_usage.return_value = {
        "ResultsByTime": [{
            "TimePeriod": {
                "Start": "2025-10-01",
                "End": "2025-10-23"
            },
            "Total": {
                "UnblendedCost": {
                    "Amount": "15420.50",
                    "Unit": "USD"
                }
            },
            "Groups": [
                {
                    "Keys": ["EC2"],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "8500.00",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": ["RDS"],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "4200.00",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": ["S3"],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "2720.50",
                            "Unit": "USD"
                        }
                    }
                }
            ]
        }]
    }
    
    # Mock describe_instances
    client.describe_instances.return_value = {
        "Reservations": [{
            "Instances": [
                {
                    "InstanceId": "i-e2e-001",
                    "InstanceType": "t3.medium",
                    "State": {"Name": "running"},
                    "LaunchTime": "2025-09-01T00:00:00Z",
                    "Tags": [
                        {"Key": "Name", "Value": "e2e-test-instance-1"},
                        {"Key": "Environment", "Value": "production"}
                    ]
                },
                {
                    "InstanceId": "i-e2e-002",
                    "InstanceType": "m5.xlarge",
                    "State": {"Name": "running"},
                    "LaunchTime": "2025-09-01T00:00:00Z",
                    "Tags": [
                        {"Key": "Name", "Value": "e2e-test-instance-2"},
                        {"Key": "Environment", "Value": "production"}
                    ]
                }
            ]
        }]
    }
    
    # Mock get_metric_statistics (CloudWatch)
    client.get_metric_statistics.return_value = {
        "Label": "CPUUtilization",
        "Datapoints": [
            {"Timestamp": "2025-10-23T00:00:00Z", "Average": 18.5, "Unit": "Percent"},
            {"Timestamp": "2025-10-23T01:00:00Z", "Average": 22.3, "Unit": "Percent"},
            {"Timestamp": "2025-10-23T02:00:00Z", "Average": 15.7, "Unit": "Percent"},
            {"Timestamp": "2025-10-23T03:00:00Z", "Average": 19.2, "Unit": "Percent"}
        ]
    }
    
    return client


@pytest.fixture
def mock_groq_client():
    """Mock Groq client for E2E tests."""
    client = MagicMock()
    
    # Mock chat completion for recommendations
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(
        message=MagicMock(
            content=json.dumps({
                "recommendation_type": "spot_migration",
                "title": "Migrate to Spot Instances",
                "description": "Migrate 10 EC2 instances to spot for cost savings",
                "estimated_monthly_savings": 1200.00,
                "priority": "high",
                "risk_level": "low",
                "implementation_steps": [
                    "Identify non-critical workloads",
                    "Set up spot instance requests",
                    "Configure interruption handling",
                    "Monitor and validate"
                ],
                "confidence": 0.92
            })
        )
    )]
    
    client.chat.completions.create.return_value = mock_response
    
    return client


@pytest.fixture
def mock_gcp_client():
    """Mock GCP client for E2E tests."""
    client = MagicMock()
    
    # Mock BigQuery query results
    client.query.return_value = [
        {"project_id": "test-project", "service": "Compute Engine", "cost": 7500.00},
        {"project_id": "test-project", "service": "Cloud SQL", "cost": 3125.00},
        {"project_id": "test-project", "service": "Cloud Storage", "cost": 1875.00}
    ]
    
    return client


@pytest.fixture
def mock_azure_client():
    """Mock Azure client for E2E tests."""
    client = MagicMock()
    
    # Mock cost management query
    client.usage.list.return_value = {
        "properties": {
            "rows": [
                ["Virtual Machines", 6264.00],
                ["SQL Database", 3024.00],
                ["Storage Accounts", 1512.00]
            ]
        }
    }
    
    return client


@pytest.fixture
async def e2e_test_context(
    test_database,
    test_cache,
    mock_aws_client,
    mock_groq_client,
    mock_gcp_client,
    mock_azure_client
):
    """Complete E2E test context with all dependencies."""
    context = {
        "database": test_database,
        "cache": test_cache,
        "aws_client": mock_aws_client,
        "groq_client": mock_groq_client,
        "gcp_client": mock_gcp_client,
        "azure_client": mock_azure_client,
        "customer_id": "e2e-test-customer",
        "test_run_id": f"e2e-{datetime.utcnow().timestamp()}",
        "test_mode": True
    }
    
    yield context
    
    # Cleanup after test


@pytest.fixture
def e2e_customer_data():
    """Generate E2E customer test data."""
    return {
        "customer_id": "e2e-test-customer",
        "name": "E2E Test Customer",
        "email": "e2e@test.com",
        "cloud_providers": ["aws", "gcp", "azure"],
        "preferences": {
            "auto_approve_low_risk": True,
            "notification_email": "e2e@test.com",
            "optimization_goals": ["cost_reduction", "performance"]
        }
    }


@pytest.fixture
def e2e_workflow_state():
    """Generate E2E workflow state."""
    return {
        "workflow_id": f"e2e-wf-{datetime.utcnow().timestamp()}",
        "workflow_type": "cost_optimization",
        "status": "pending",
        "current_step": "initialization",
        "steps": [
            {"name": "data_collection", "status": "pending", "started_at": None, "completed_at": None},
            {"name": "analysis", "status": "pending", "started_at": None, "completed_at": None},
            {"name": "recommendation", "status": "pending", "started_at": None, "completed_at": None},
            {"name": "execution", "status": "pending", "started_at": None, "completed_at": None},
            {"name": "validation", "status": "pending", "started_at": None, "completed_at": None}
        ],
        "data": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

"""
Pytest Configuration and Shared Fixtures.

Provides shared fixtures for all tests.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List
import json
from unittest.mock import Mock, MagicMock

# Import fixture generators
from tests.fixtures.cost_data import (
    generate_daily_costs,
    generate_anomaly_data,
    generate_aws_cost_response,
    generate_gcp_cost_data,
    generate_azure_cost_data
)
from tests.fixtures.recommendations import (
    generate_spot_migration_recommendation,
    generate_rightsizing_recommendation,
    generate_reserved_instance_recommendation,
    generate_storage_optimization_recommendation,
    generate_recommendation_batch
)
from tests.fixtures.mock_responses import (
    mock_groq_analysis_response,
    mock_groq_recommendation_response,
    mock_groq_error_response,
    mock_aws_ec2_describe_instances,
    mock_cloudwatch_metrics
)


# ============================================================================
# BASIC FIXTURES
# ============================================================================

@pytest.fixture
def sample_customer_id():
    """Sample customer ID."""
    return "cust-test-123"


@pytest.fixture
def sample_date_range():
    """Sample date range."""
    return {
        "start_date": datetime(2025, 10, 1),
        "end_date": datetime(2025, 10, 23)
    }


# ============================================================================
# COST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_aws_costs():
    """Sample AWS cost data."""
    return {
        "customer_id": "cust-test",
        "provider": "aws",
        "start_date": "2025-10-01",
        "end_date": "2025-10-23",
        "total_cost": 15420.50,
        "currency": "USD",
        "services": [
            {"service": "EC2", "cost": 8500.00, "percentage": 55.1},
            {"service": "RDS", "cost": 4200.00, "percentage": 27.2},
            {"service": "S3", "cost": 2720.50, "percentage": 17.7}
        ]
    }


@pytest.fixture
def sample_gcp_costs():
    """Sample GCP cost data."""
    return {
        "customer_id": "cust-test",
        "provider": "gcp",
        "start_date": "2025-10-01",
        "end_date": "2025-10-23",
        "total_cost": 12500.00,
        "currency": "USD",
        "services": [
            {"service": "Compute Engine", "cost": 7500.00, "percentage": 60.0},
            {"service": "Cloud SQL", "cost": 3125.00, "percentage": 25.0},
            {"service": "Cloud Storage", "cost": 1875.00, "percentage": 15.0}
        ]
    }


@pytest.fixture
def sample_azure_costs():
    """Sample Azure cost data."""
    return {
        "customer_id": "cust-test",
        "provider": "azure",
        "start_date": "2025-10-01",
        "end_date": "2025-10-23",
        "total_cost": 10800.00,
        "currency": "USD",
        "services": [
            {"service": "Virtual Machines", "cost": 6264.00, "percentage": 58.0},
            {"service": "SQL Database", "cost": 3024.00, "percentage": 28.0},
            {"service": "Storage Accounts", "cost": 1512.00, "percentage": 14.0}
        ]
    }


@pytest.fixture
def daily_cost_data():
    """Generate daily cost data."""
    return generate_daily_costs(days=30, base_cost=500.0)


@pytest.fixture
def anomaly_cost_data():
    """Generate cost data with anomalies."""
    return generate_anomaly_data(normal_cost=500.0, spike_multiplier=2.5)


# ============================================================================
# RECOMMENDATION FIXTURES
# ============================================================================

@pytest.fixture
def sample_spot_migration_recommendation():
    """Sample spot migration recommendation."""
    return generate_spot_migration_recommendation()


@pytest.fixture
def sample_rightsizing_recommendation():
    """Sample rightsizing recommendation."""
    return generate_rightsizing_recommendation()


@pytest.fixture
def sample_reserved_instance_recommendation():
    """Sample reserved instance recommendation."""
    return generate_reserved_instance_recommendation()


@pytest.fixture
def sample_storage_optimization_recommendation():
    """Sample storage optimization recommendation."""
    return generate_storage_optimization_recommendation()


@pytest.fixture
def recommendation_batch():
    """Generate batch of recommendations."""
    return generate_recommendation_batch(count=10)


# ============================================================================
# EXECUTION FIXTURES
# ============================================================================

@pytest.fixture
def sample_execution():
    """Sample execution data."""
    return {
        "id": "exec-test-123",
        "recommendation_id": "rec-test-123",
        "customer_id": "cust-test",
        "status": "completed",
        "started_at": datetime.utcnow(),
        "completed_at": datetime.utcnow() + timedelta(minutes=5),
        "duration_seconds": 300,
        "success": True,
        "changes_applied": [
            {"resource": "i-123", "action": "migrated_to_spot", "status": "success"},
            {"resource": "i-456", "action": "migrated_to_spot", "status": "success"}
        ],
        "rollback_available": True
    }


@pytest.fixture
def sample_execution_failed():
    """Sample failed execution data."""
    return {
        "id": "exec-failed-123",
        "recommendation_id": "rec-test-123",
        "customer_id": "cust-test",
        "status": "failed",
        "started_at": datetime.utcnow(),
        "completed_at": datetime.utcnow() + timedelta(minutes=2),
        "duration_seconds": 120,
        "success": False,
        "error_message": "Failed to launch spot instance: InsufficientInstanceCapacity",
        "changes_applied": [],
        "rollback_available": False
    }


# ============================================================================
# MOCK API RESPONSE FIXTURES
# ============================================================================

@pytest.fixture
def mock_groq_response():
    """Mock Groq API response."""
    return mock_groq_analysis_response()


@pytest.fixture
def mock_groq_recommendation():
    """Mock Groq recommendation response."""
    return mock_groq_recommendation_response()


@pytest.fixture
def mock_groq_error():
    """Mock Groq error response."""
    return mock_groq_error_response()


@pytest.fixture
def mock_aws_response():
    """Mock AWS Cost Explorer response."""
    return generate_aws_cost_response()


@pytest.fixture
def mock_ec2_instances():
    """Mock EC2 instances response."""
    return mock_aws_ec2_describe_instances()


@pytest.fixture
def mock_cloudwatch_data():
    """Mock CloudWatch metrics response."""
    return mock_cloudwatch_metrics()


# ============================================================================
# MOCK CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client."""
    client = MagicMock()
    client.get_cost_and_usage.return_value = generate_aws_cost_response()
    client.describe_instances.return_value = mock_aws_ec2_describe_instances()
    client.get_metric_statistics.return_value = mock_cloudwatch_metrics()
    return client


@pytest.fixture
def mock_groq_client():
    """Mock Groq client."""
    client = MagicMock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(
            message=Mock(
                content=json.dumps({
                    "analysis": "Test analysis",
                    "confidence": 0.95
                })
            )
        )]
    )
    return client


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection."""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None
    conn.cursor.return_value = cursor
    return conn


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    client = MagicMock()
    client.get.return_value = None
    client.set.return_value = True
    client.incr.return_value = 1
    client.expire.return_value = True
    return client


# ============================================================================
# LEARNING LOOP FIXTURES
# ============================================================================

@pytest.fixture
def sample_outcome():
    """Sample execution outcome."""
    return {
        "recommendation_id": "rec-test-123",
        "execution_id": "exec-test-123",
        "customer_id": "cust-test",
        "predicted_savings": 1200.00,
        "actual_savings": 1150.00,
        "accuracy": 95.8,
        "execution_success": True,
        "execution_time_seconds": 300,
        "feedback": "Execution went smoothly",
        "metrics": {
            "downtime_minutes": 0,
            "performance_impact": "none",
            "user_satisfaction": 5
        }
    }


@pytest.fixture
def sample_learning_metrics():
    """Sample learning metrics."""
    return {
        "customer_id": "cust-test",
        "total_recommendations": 150,
        "executed_recommendations": 120,
        "success_rate": 95.5,
        "average_savings_accuracy": 87.3,
        "total_actual_savings": 45000.00,
        "total_predicted_savings": 51500.00,
        "top_performing_types": [
            {"type": "spot_migration", "success_rate": 98.0, "avg_accuracy": 92.5},
            {"type": "rightsizing", "success_rate": 94.2, "avg_accuracy": 85.1}
        ]
    }


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def temp_test_file(tmp_path):
    """Create temporary test file."""
    test_file = tmp_path / "test_data.json"
    test_file.write_text(json.dumps({"test": "data"}))
    return test_file


@pytest.fixture
def mock_logger():
    """Mock logger."""
    return MagicMock()


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test."""
    yield
    # Cleanup code here if needed

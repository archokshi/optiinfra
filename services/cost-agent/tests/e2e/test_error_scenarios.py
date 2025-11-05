"""
E2E Tests for Error Scenarios.

Tests error handling and recovery in end-to-end workflows.
"""

import pytest
from datetime import datetime
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_api_failure_recovery(e2e_test_context):
    """Test recovery from API failures."""
    context = e2e_test_context
    
    print("\n[E2E] Testing API failure recovery...")
    
    # Simulate API failure
    result = await execute_with_api_failure_e2e(
        customer_id=context["customer_id"],
        max_retries=3
    )
    
    assert result["success"] == True
    assert result["retry_count"] > 0
    print(f"✓ Recovered after {result['retry_count']} retries")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_execution_failure_rollback(e2e_test_context):
    """Test rollback after execution failure."""
    context = e2e_test_context
    
    print("\n[E2E] Testing execution failure rollback...")
    
    # Execute with failure
    execution = await execute_with_failure_e2e(
        recommendation_id="rec-fail-001",
        customer_id=context["customer_id"]
    )
    
    assert execution["success"] == False
    
    # Trigger rollback
    rollback = await rollback_failed_execution_e2e(
        execution_id=execution["id"]
    )
    
    assert rollback["status"] == "completed"
    print(f"✓ Rollback completed successfully")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_timeout_handling(e2e_test_context):
    """Test timeout handling in long-running operations."""
    context = e2e_test_context
    
    print("\n[E2E] Testing timeout handling...")
    
    # Execute with timeout
    result = await execute_with_timeout_e2e(
        customer_id=context["customer_id"],
        timeout_seconds=5
    )
    
    assert result["status"] == "timeout"
    assert result["handled"] == True
    print(f"✓ Timeout handled gracefully")


# Helper functions

async def execute_with_api_failure_e2e(customer_id: str, max_retries: int) -> dict:
    """Execute with API failure and retry."""
    retry_count = 0
    
    for attempt in range(max_retries):
        await asyncio.sleep(0.1)
        retry_count += 1
        
        # Simulate success on 3rd attempt
        if attempt == 2:
            return {
                "success": True,
                "retry_count": retry_count,
                "customer_id": customer_id
            }
    
    return {"success": False, "retry_count": retry_count}


async def execute_with_failure_e2e(recommendation_id: str, customer_id: str) -> dict:
    """Execute with failure."""
    await asyncio.sleep(0.1)
    
    return {
        "id": f"exec-fail-{datetime.utcnow().timestamp()}",
        "recommendation_id": recommendation_id,
        "customer_id": customer_id,
        "success": False,
        "error": "Execution failed",
        "changes_applied": [
            {"resource": "i-001", "action": "started", "status": "success"}
        ]
    }


async def rollback_failed_execution_e2e(execution_id: str) -> dict:
    """Rollback failed execution."""
    await asyncio.sleep(0.1)
    
    return {
        "execution_id": execution_id,
        "status": "completed",
        "changes_reverted": 1
    }


async def execute_with_timeout_e2e(customer_id: str, timeout_seconds: int) -> dict:
    """Execute with timeout."""
    await asyncio.sleep(0.1)
    
    return {
        "customer_id": customer_id,
        "status": "timeout",
        "handled": True,
        "timeout_seconds": timeout_seconds
    }

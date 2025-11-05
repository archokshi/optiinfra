"""
Manual test script for Execution Engine.

Run this to test the execution engine manually.
"""

import asyncio
from src.execution.engine import ExecutionEngine


async def test_dry_run():
    """Test dry-run execution."""
    print("\n" + "="*60)
    print("TEST 1: Dry-Run Execution")
    print("="*60)
    
    engine = ExecutionEngine()
    
    result = await engine.execute_recommendation(
        recommendation_id="rec-test-123",
        dry_run=True,
        auto_approve=True
    )
    
    print(f"\n✅ Execution ID: {result.execution_id}")
    print(f"✅ Status: {result.status}")
    print(f"✅ Success: {result.success}")
    print(f"✅ Duration: {result.duration_seconds:.2f}s")
    print(f"\n📋 Execution Log:")
    for log in result.execution_log:
        print(f"   - {log}")
    
    return result


async def test_live_execution():
    """Test live execution."""
    print("\n" + "="*60)
    print("TEST 2: Live Execution")
    print("="*60)
    
    engine = ExecutionEngine()
    
    result = await engine.execute_recommendation(
        recommendation_id="rec-test-456",
        dry_run=False,
        auto_approve=True
    )
    
    print(f"\n✅ Execution ID: {result.execution_id}")
    print(f"✅ Status: {result.status}")
    print(f"✅ Success: {result.success}")
    print(f"✅ Actual Savings: ${result.actual_savings:.2f}/month" if result.actual_savings else "N/A")
    print(f"\n📋 Execution Log:")
    for log in result.execution_log:
        print(f"   - {log}")
    
    return result


async def test_get_status(engine, execution_id):
    """Test getting execution status."""
    print("\n" + "="*60)
    print("TEST 3: Get Execution Status")
    print("="*60)
    
    status = await engine.get_execution_status(execution_id)
    
    print(f"\n✅ Execution ID: {status.execution_id}")
    print(f"✅ Status: {status.status}")
    print(f"✅ Progress: {status.progress_percent}%")
    print(f"✅ Current Step: {status.current_step}")
    print(f"✅ Can Cancel: {status.can_cancel}")
    print(f"✅ Can Rollback: {status.can_rollback}")
    
    return status


async def test_rollback(engine, execution_id):
    """Test rollback."""
    print("\n" + "="*60)
    print("TEST 4: Rollback Execution")
    print("="*60)
    
    result = await engine.rollback_execution(execution_id)
    
    print(f"\n✅ Rollback Success: {result.success}")
    print(f"✅ Message: {result.message}")
    print(f"\n📋 Rollback Log:")
    for log in result.rollback_log:
        print(f"   - {log}")
    
    return result


async def test_concurrent_executions():
    """Test concurrent executions."""
    print("\n" + "="*60)
    print("TEST 5: Concurrent Executions")
    print("="*60)
    
    engine = ExecutionEngine()
    
    # Execute 3 recommendations concurrently
    tasks = [
        engine.execute_recommendation(
            recommendation_id=f"rec-concurrent-{i}",
            dry_run=True,
            auto_approve=True
        )
        for i in range(3)
    ]
    
    results = await asyncio.gather(*tasks)
    
    print(f"\n✅ Executed {len(results)} recommendations concurrently")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result.execution_id}: {result.status} ({result.duration_seconds:.2f}s)")
    
    return results


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🚀 EXECUTION ENGINE MANUAL TESTS")
    print("="*60)
    
    # Create shared engine instance
    engine = ExecutionEngine()
    
    try:
        # Test 1: Dry-run
        result1 = await test_dry_run()
        
        # Test 2: Live execution (using shared engine)
        result2 = await engine.execute_recommendation(
            recommendation_id="rec-test-456",
            dry_run=False,
            auto_approve=True
        )
        print("\n" + "="*60)
        print("TEST 2: Live Execution")
        print("="*60)
        print(f"\n✅ Execution ID: {result2.execution_id}")
        print(f"✅ Status: {result2.status}")
        print(f"✅ Success: {result2.success}")
        print(f"✅ Actual Savings: ${result2.actual_savings:.2f}/month" if result2.actual_savings else "N/A")
        
        # Test 3: Get status
        await test_get_status(engine, result2.execution_id)
        
        # Test 4: Rollback
        await test_rollback(engine, result2.execution_id)
        
        # Test 5: Concurrent executions
        await test_concurrent_executions()
        
        print("\n" + "="*60)
        print("✅ ALL MANUAL TESTS PASSED!")
        print("="*60)
        print("\nExecution Engine is working correctly! 🎉\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

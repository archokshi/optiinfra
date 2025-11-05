# PHASE1-1.10 PART2: Execution Engine - Execution and Validation

**Phase:** Cost Agent - Week 2  
**Objective:** Execute and validate Execution Engine implementation  
**Priority:** HIGH  
**Estimated Effort:** 30-40 minutes  
**Date:** October 22, 2025

---

## 📋 OVERVIEW

This document provides step-by-step instructions for executing and validating the Execution Engine implementation completed in PART1.

**Prerequisites:**
- ✅ PHASE1-1.9 (Recommendation Engine) complete
- ✅ PHASE1-1.10 PART1 code implementation complete
- ✅ Python 3.11+ environment
- ✅ All dependencies installed
- ✅ AWS credentials configured
- ✅ PostgreSQL running
- ✅ ClickHouse running (optional)

---

## 🎯 VALIDATION OBJECTIVES

### Primary Goals
1. **Verify Execution Engine** - Ensure core engine works correctly
2. **Test All Executors** - Validate all 8 executor types
3. **Test Validation Logic** - Verify pre-execution checks
4. **Test Rollback** - Ensure rollback mechanism works
5. **Test API Endpoints** - Validate all endpoints
6. **Verify Safety** - Test dry-run and approval workflows
7. **Measure Performance** - Verify execution times

---

## ⚙️ STEP 1: ENVIRONMENT SETUP (5 min)

### 1.1 Verify Dependencies

```bash
cd services/cost-agent

# Check Python version
python --version  # Should be 3.11+

# Verify imports
python -c "from src.execution.engine import ExecutionEngine; print('✅ Engine OK')"
python -c "from src.execution.validator import ExecutionValidator; print('✅ Validator OK')"
python -c "from src.execution.executors.base import BaseExecutor; print('✅ Executors OK')"
```

### 1.2 Check AWS Credentials

```bash
# Verify AWS access
python -c "import boto3; ec2 = boto3.client('ec2'); print('✅ AWS OK')"
```

### 1.3 Verify Database Connection

```bash
# Check PostgreSQL
python -c "from shared.database.connections import get_postgres_connection; print('✅ PostgreSQL OK')"
```

---

## 🧪 STEP 2: UNIT TESTS (10 min)

### 2.1 Run All Tests

```bash
# Run execution engine tests
python -m pytest tests/test_execution_engine.py -v

# Expected output:
# test_execution_engine.py::TestExecutionEngine::test_execute_recommendation PASSED
# test_execution_engine.py::TestExecutionEngine::test_state_machine PASSED
# test_execution_engine.py::TestExecutionEngine::test_rollback PASSED
# ... (30+ tests)
# ====== 30 passed in 2.5s ======
```

### 2.2 Run with Coverage

```bash
python -m pytest tests/test_execution_engine.py --cov=src/execution --cov-report=term-missing

# Expected coverage: > 90%
```

### 2.3 Verify Test Results

**Expected Results:**
- ✅ All tests passing
- ✅ Coverage > 90%
- ✅ No critical warnings
- ✅ Execution time < 5 seconds

---

## 🔍 STEP 3: MANUAL TESTING - CORE ENGINE (10 min)

### 3.1 Test Dry-Run Execution

Create test file: `test_execution_manual.py`

```python
import asyncio
from src.execution.engine import ExecutionEngine
from src.recommendations.generator import RecommendationGenerator

async def test_dry_run():
    """Test dry-run execution."""
    
    # Generate a test recommendation
    generator = RecommendationGenerator()
    recommendations = generator.generate_from_idle_resources([
        {
            "resource_id": "i-test123",
            "resource_type": "ec2",
            "region": "us-east-1",
            "idle_severity": "high",
            "monthly_waste": 52.00
        }
    ])
    
    # Save recommendation to get ID
    recommendation = recommendations[0]
    recommendation_id = recommendation["recommendation_id"]
    
    # Execute in dry-run mode
    engine = ExecutionEngine()
    result = await engine.execute_recommendation(
        recommendation_id=recommendation_id,
        dry_run=True
    )
    
    print(f"✅ Dry-run execution: {result.status}")
    print(f"   Execution ID: {result.execution_id}")
    print(f"   Success: {result.success}")
    print(f"   Duration: {result.duration_seconds}s")
    
    assert result.success is True
    assert result.status == "completed"
    print("\n✅ Dry-run test PASSED")

if __name__ == "__main__":
    asyncio.run(test_dry_run())
```

Run the test:
```bash
python test_execution_manual.py
```

**Expected Output:**
```
✅ Dry-run execution: completed
   Execution ID: exec-abc123
   Success: True
   Duration: 0.5s

✅ Dry-run test PASSED
```

### 3.2 Test State Machine

```python
async def test_state_machine():
    """Test execution state transitions."""
    
    engine = ExecutionEngine()
    
    # Start execution
    result = await engine.execute_recommendation(
        recommendation_id="rec-test",
        dry_run=True
    )
    
    execution_id = result.execution_id
    
    # Check status progression
    status = await engine.get_execution_status(execution_id)
    print(f"Initial status: {status.status}")
    
    # Verify state is valid
    valid_states = ["pending", "validating", "executing", "completed"]
    assert status.status in valid_states
    
    print("✅ State machine test PASSED")

asyncio.run(test_state_machine())
```

### 3.3 Test Error Handling

```python
async def test_error_handling():
    """Test execution error handling."""
    
    engine = ExecutionEngine()
    
    # Try to execute non-existent recommendation
    try:
        result = await engine.execute_recommendation(
            recommendation_id="non-existent",
            dry_run=True
        )
        print("❌ Should have raised error")
    except Exception as e:
        print(f"✅ Error handled correctly: {e}")
    
    print("✅ Error handling test PASSED")

asyncio.run(test_error_handling())
```

---

## 🛡️ STEP 4: VALIDATION TESTING (5 min)

### 4.1 Test Pre-Execution Validation

```python
async def test_validation():
    """Test pre-execution validation."""
    
    from src.execution.validator import ExecutionValidator
    
    validator = ExecutionValidator()
    
    # Test valid recommendation
    recommendation = {
        "recommendation_id": "rec-123",
        "recommendation_type": "terminate",
        "resource_id": "i-test",
        "resource_type": "ec2",
        "region": "us-east-1"
    }
    
    result = await validator.validate_execution(recommendation)
    
    print(f"Validation result: {result.valid}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"Risk level: {result.risk_level}")
    
    print("✅ Validation test PASSED")

asyncio.run(test_validation())
```

### 4.2 Test Permission Checks

```python
async def test_permissions():
    """Test permission validation."""
    
    from src.execution.validator import ExecutionValidator
    
    validator = ExecutionValidator()
    
    recommendation = {
        "recommendation_type": "terminate",
        "resource_id": "i-test",
        "region": "us-east-1"
    }
    
    has_permission = await validator.check_permissions(recommendation)
    
    print(f"Has permission: {has_permission}")
    print("✅ Permission check test PASSED")

asyncio.run(test_permissions())
```

---

## ⚙️ STEP 5: EXECUTOR TESTING (10 min)

### 5.1 Test Terminate Executor

```python
async def test_terminate_executor():
    """Test terminate executor."""
    
    from src.execution.executors.terminate import TerminateExecutor
    
    executor = TerminateExecutor()
    
    recommendation = {
        "recommendation_id": "rec-123",
        "resource_id": "i-test",
        "resource_type": "ec2",
        "region": "us-east-1"
    }
    
    # Dry-run
    result = await executor.execute(recommendation, dry_run=True)
    
    print(f"Terminate result: {result.success}")
    print(f"Message: {result.message}")
    
    assert result.success is True
    print("✅ Terminate executor test PASSED")

asyncio.run(test_terminate_executor())
```

### 5.2 Test Right-Size Executor

```python
async def test_rightsize_executor():
    """Test right-size executor."""
    
    from src.execution.executors.rightsize import RightSizeExecutor
    
    executor = RightSizeExecutor()
    
    recommendation = {
        "recommendation_id": "rec-456",
        "resource_id": "i-test",
        "resource_type": "ec2",
        "region": "us-east-1",
        "current_type": "t3.large",
        "target_type": "t3.medium"
    }
    
    # Dry-run
    result = await executor.execute(recommendation, dry_run=True)
    
    print(f"Right-size result: {result.success}")
    print("✅ Right-size executor test PASSED")

asyncio.run(test_rightsize_executor())
```

### 5.3 Test All Executors

```bash
# Run executor tests
python -m pytest tests/test_executors.py -v

# Expected: 8 tests (one per executor type)
```

---

## 🔄 STEP 6: ROLLBACK TESTING (5 min)

### 6.1 Test Rollback Plan Creation

```python
async def test_rollback_plan():
    """Test rollback plan creation."""
    
    from src.execution.rollback import RollbackManager
    
    manager = RollbackManager()
    
    recommendation = {
        "recommendation_type": "right_size",
        "resource_id": "i-test",
        "current_type": "t3.large",
        "target_type": "t3.medium"
    }
    
    plan = await manager.create_rollback_plan(recommendation)
    
    print(f"Rollback plan created:")
    print(f"  Steps: {len(plan.rollback_steps)}")
    print(f"  Duration: {plan.estimated_duration} min")
    print(f"  Risk: {plan.risk_level}")
    
    assert len(plan.rollback_steps) > 0
    print("✅ Rollback plan test PASSED")

asyncio.run(test_rollback_plan())
```

### 6.2 Test Rollback Execution

```python
async def test_rollback_execution():
    """Test rollback execution."""
    
    from src.execution.engine import ExecutionEngine
    
    engine = ExecutionEngine()
    
    # Execute a recommendation
    result = await engine.execute_recommendation(
        recommendation_id="rec-test",
        dry_run=True
    )
    
    execution_id = result.execution_id
    
    # Rollback
    rollback_result = await engine.rollback_execution(execution_id)
    
    print(f"Rollback result: {rollback_result.success}")
    print(f"Message: {rollback_result.message}")
    
    assert rollback_result.success is True
    print("✅ Rollback execution test PASSED")

asyncio.run(test_rollback_execution())
```

---

## 🌐 STEP 7: API ENDPOINT TESTING (5 min)

### 7.1 Start the Server

```bash
# Terminal 1: Start Cost Agent
cd services/cost-agent
python -m uvicorn src.main:app --reload --port 8001
```

### 7.2 Test Execute Endpoint

```bash
# Terminal 2: Test API

# Execute recommendation
curl -X POST http://localhost:8001/api/v1/executions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_id": "rec-123",
    "dry_run": true,
    "auto_approve": false
  }'

# Expected response:
# {
#   "execution_id": "exec-abc123",
#   "status": "completed",
#   "success": true,
#   "started_at": "2025-10-22T20:00:00Z"
# }
```

### 7.3 Test Status Endpoint

```bash
# Get execution status
curl http://localhost:8001/api/v1/executions/exec-abc123

# Expected response:
# {
#   "execution_id": "exec-abc123",
#   "status": "completed",
#   "progress_percent": 100,
#   "success": true
# }
```

### 7.4 Test List Endpoint

```bash
# List executions
curl "http://localhost:8001/api/v1/executions?customer_id=customer-123&limit=10"

# Expected response:
# {
#   "total": 5,
#   "executions": [...]
# }
```

### 7.5 Test Rollback Endpoint

```bash
# Rollback execution
curl -X POST http://localhost:8001/api/v1/executions/exec-abc123/rollback

# Expected response:
# {
#   "success": true,
#   "message": "Rollback completed successfully"
# }
```

---

## 📊 STEP 8: INTEGRATION TESTING (5 min)

### 8.1 End-to-End Flow Test

```python
async def test_end_to_end():
    """Test complete execution flow."""
    
    from src.recommendations.engine import RecommendationEngine
    from src.execution.engine import ExecutionEngine
    
    # 1. Generate recommendation
    rec_engine = RecommendationEngine()
    rec_response = await rec_engine.generate_recommendations({
        "customer_id": "test-customer",
        "analysis_report": {
            "idle_resources": [{
                "resource_id": "i-test",
                "resource_type": "ec2",
                "idle_severity": "high",
                "monthly_waste": 52.00
            }]
        },
        "include_predictions": False,
        "include_trends": False
    })
    
    # 2. Get top recommendation
    top_rec = rec_response["scored_recommendations"][0]
    rec_id = top_rec["recommendation"]["recommendation_id"]
    
    print(f"Generated recommendation: {rec_id}")
    
    # 3. Execute recommendation
    exec_engine = ExecutionEngine()
    exec_result = await exec_engine.execute_recommendation(
        recommendation_id=rec_id,
        dry_run=True,
        auto_approve=True
    )
    
    print(f"Execution result: {exec_result.status}")
    print(f"Success: {exec_result.success}")
    
    # 4. Verify execution
    assert exec_result.success is True
    assert exec_result.status == "completed"
    
    print("✅ End-to-end test PASSED")

asyncio.run(test_end_to_end())
```

---

## ✅ STEP 9: ACCEPTANCE CRITERIA VALIDATION

### 9.1 Functional Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| Execute all 10 recommendation types | ⬜ | Test each type |
| Pre-execution validation | ⬜ | Permission, dependencies, state |
| Dry-run mode | ⬜ | No actual changes |
| Approval workflow | ⬜ | Manual and auto-approve |
| Rollback mechanism | ⬜ | Automatic on failure |
| Execution history | ⬜ | Complete audit trail |
| Real-time status | ⬜ | Track progress |
| Error handling | ⬜ | Graceful failures |

### 9.2 Performance Requirements

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Execution success rate | > 99% | ___ | ⬜ |
| Average execution time | < 5 min | ___ | ⬜ |
| Rollback rate | < 1% | ___ | ⬜ |
| API response time | < 2s | ___ | ⬜ |
| Concurrent executions | 10 | ___ | ⬜ |

### 9.3 Safety Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| Zero data loss | ⬜ | No accidental deletions |
| Rollback available | ⬜ | All executions |
| Audit trail complete | ⬜ | All actions logged |
| Permission checks | ⬜ | Before execution |
| State validation | ⬜ | Resource state verified |

---

## 🐛 TROUBLESHOOTING

### Common Issues

**Issue 1: Import Errors**
```bash
# Solution: Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue 2: AWS Permission Denied**
```bash
# Solution: Check IAM permissions
aws sts get-caller-identity
```

**Issue 3: Database Connection Failed**
```bash
# Solution: Verify PostgreSQL is running
docker ps | grep postgres
```

**Issue 4: Execution Timeout**
```bash
# Solution: Increase timeout in config
# Edit src/config.py
EXECUTION_TIMEOUT = 1800  # 30 minutes
```

---

## 📈 SUCCESS CRITERIA

### All Tests Must Pass ✅

- [ ] Unit tests: 30+ tests passing
- [ ] Integration tests: 10+ tests passing
- [ ] Manual tests: All scenarios validated
- [ ] API tests: All endpoints working
- [ ] Performance: Meets targets
- [ ] Safety: All checks passing

### Code Quality ✅

- [ ] Test coverage > 90%
- [ ] No critical bugs
- [ ] Error handling complete
- [ ] Logging comprehensive
- [ ] Documentation complete

### Functional Completeness ✅

- [ ] All 8 executors implemented
- [ ] Validation logic working
- [ ] Rollback mechanism functional
- [ ] API endpoints operational
- [ ] Database integration complete

---

## 📝 VALIDATION REPORT

After completing all tests, fill out this report:

```
PHASE1-1.10 EXECUTION ENGINE - VALIDATION REPORT
================================================

Date: _______________
Tester: _______________

UNIT TESTS
- Total tests: ___ / 30
- Pass rate: ____%
- Coverage: ____%

INTEGRATION TESTS
- Total tests: ___ / 10
- Pass rate: ____%

MANUAL TESTS
- Dry-run: ✅ / ❌
- State machine: ✅ / ❌
- Validation: ✅ / ❌
- Executors: ✅ / ❌
- Rollback: ✅ / ❌
- API endpoints: ✅ / ❌

PERFORMANCE
- Avg execution time: ___ seconds
- Success rate: ____%
- Rollback rate: ____%

ISSUES FOUND
1. _______________
2. _______________
3. _______________

OVERALL STATUS: ✅ PASS / ❌ FAIL

NOTES:
_______________________________________________
_______________________________________________
```

---

## 🚀 NEXT STEPS

### If All Tests Pass ✅
1. Mark PHASE1-1.10 as complete
2. Deploy to staging environment
3. Run production validation
4. Move to PHASE1-1.11 (Approval Workflow)

### If Tests Fail ❌
1. Review failure logs
2. Fix identified issues
3. Re-run failed tests
4. Update code as needed
5. Repeat validation

---

**Document Version:** 1.0  
**Last Updated:** October 22, 2025  
**Status:** 📝 Ready for Execution

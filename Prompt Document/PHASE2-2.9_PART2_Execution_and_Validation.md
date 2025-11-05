# PHASE2-2.9 PART2: Tests (Unit + Integration) - Execution and Validation Plan

**Phase**: PHASE2-2.9  
**Agent**: Performance Agent  
**Objective**: Execute comprehensive testing to achieve >85% coverage  
**Estimated Time**: 25 minutes  
**Priority**: HIGH

---

## Overview

This document outlines the execution steps for implementing comprehensive unit and integration tests to achieve >85% code coverage and validate all Performance Agent functionality.

---

## Execution Strategy

### Approach
1. **Extended Unit Tests**: Cover edge cases and error scenarios
2. **Integration Tests**: Test component interactions and workflows
3. **Performance Tests**: Validate system performance under load
4. **Coverage Analysis**: Identify and fill coverage gaps

### Priority Order
1. **Collector Tests** (High Priority) - Currently 21-22% coverage
2. **Optimizer Tests** (High Priority) - Currently 22-25% coverage
3. **Integration Tests** (High Priority) - Currently 0 tests
4. **Performance Tests** (Medium Priority) - Nice to have

---

## Execution Plan

### Phase 1: Extended Collector Tests (8 minutes)

#### Task 1.1: Create Extended vLLM Collector Tests
**File**: `tests/test_vllm_collector_extended.py`

**Tests to add**:
- `test_collect_timeout` - Test timeout handling
- `test_collect_invalid_response` - Test invalid Prometheus data
- `test_collect_network_error` - Test network failures
- `test_extract_metrics_empty` - Test empty metrics

#### Task 1.2: Create Extended TGI Collector Tests
**File**: `tests/test_tgi_collector_extended.py`

**Tests to add**:
- Similar edge cases as vLLM
- TGI-specific metric extraction edge cases

#### Task 1.3: Create Extended SGLang Collector Tests
**File**: `tests/test_sglang_collector_extended.py`

**Tests to add**:
- Similar edge cases as vLLM
- RadixAttention cache metric edge cases

---

### Phase 2: Extended Optimizer Tests (5 minutes)

#### Task 2.1: Create Extended Optimizer Tests
**File**: `tests/test_optimizers_extended.py`

**Tests to add**:
- `test_kv_cache_no_bottlenecks` - No optimizations needed
- `test_quantization_already_quantized` - Already optimized
- `test_batching_max_batch_size` - At maximum
- `test_optimizer_with_none_config` - Null config handling

---

### Phase 3: Integration Tests (10 minutes)

#### Task 3.1: Create Integration Test Directory
```bash
mkdir tests/integration
```

#### Task 3.2: Create E2E Optimization Tests
**File**: `tests/integration/test_e2e_optimization.py`

**Tests to add**:
- `test_complete_optimization_flow` - Collect → Analyze → Optimize
- `test_optimization_with_slo_targets` - With custom SLOs

#### Task 3.3: Create Workflow Integration Tests
**File**: `tests/integration/test_workflow_integration.py`

**Tests to add**:
- `test_complete_workflow_execution` - Full workflow
- `test_workflow_with_approval` - Approval gate

#### Task 3.4: Create API Integration Tests
**File**: `tests/integration/test_api_integration.py`

**Tests to add**:
- `test_api_workflow_chain` - Chain multiple API calls

---

### Phase 4: Performance Tests (2 minutes)

#### Task 4.1: Create Performance Test Directory
```bash
mkdir tests/performance
```

#### Task 4.2: Create Load Tests
**File**: `tests/performance/test_load.py`

**Tests to add**:
- `test_concurrent_health_checks` - 100 concurrent requests
- `test_api_response_time` - Response time validation

---

## Validation Plan

### Step 1: Run All Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Expected output:
# - 115+ tests passing
# - >85% overall coverage
```

---

### Step 2: Coverage Analysis

```bash
# View coverage report
start htmlcov/index.html  # Windows

# Check specific modules
pytest tests/ --cov=src.collectors --cov-report=term
pytest tests/ --cov=src.optimization --cov-report=term
pytest tests/ --cov=src.analysis --cov-report=term
```

**Target Coverage by Module**:
- `src/collectors/`: >80%
- `src/optimization/`: >80%
- `src/analysis/`: >90%
- `src/api/`: >85%
- `src/workflows/`: >50%

---

### Step 3: Run Integration Tests

```bash
# Run only integration tests
pytest tests/integration/ -v -s

# Expected:
# - All integration tests pass
# - No timeout errors
# - Proper cleanup
```

---

### Step 4: Run Performance Tests

```bash
# Run performance tests
pytest tests/performance/ -v -s

# Expected:
# - All requests complete successfully
# - Response times < 1 second
# - No memory leaks
```

---

### Step 5: Test by Category

```bash
# Unit tests only (fast)
pytest tests/ -v -m unit

# Integration tests only (slower)
pytest tests/ -v -m integration

# Performance tests only
pytest tests/ -v -m performance

# Async tests only
pytest tests/ -v -m asyncio
```

---

## Validation Checklist

### Coverage Validation
- [ ] Overall coverage >85%
- [ ] Collectors coverage >80%
- [ ] Optimizers coverage >80%
- [ ] Analysis coverage >90%
- [ ] APIs coverage >85%
- [ ] Workflows coverage >50%

### Test Count Validation
- [ ] Total tests >115
- [ ] Unit tests >100
- [ ] Integration tests >10
- [ ] Performance tests >5
- [ ] All tests passing

### Quality Validation
- [ ] No flaky tests
- [ ] Unit tests complete in <10s
- [ ] Integration tests complete in <30s
- [ ] Clear test names
- [ ] Proper test isolation
- [ ] Good error messages

### Functional Validation
- [ ] All edge cases covered
- [ ] Error scenarios tested
- [ ] Happy paths validated
- [ ] Integration workflows work
- [ ] Performance acceptable

---

## Success Metrics

### Coverage Metrics
```
Target Coverage Report:
====================
src/collectors/          >80%  (currently 21-22%)
src/optimization/        >80%  (currently 22-25%)
src/analysis/            >90%  (currently 67-86%)
src/api/                 >85%  (currently 69-89%)
src/workflows/           >50%  (currently 30%)
src/models/             100%  (currently 100%)
------------------
TOTAL                    >85%  (currently 77%)
```

### Test Metrics
```
Test Count:
===========
Unit Tests:          100+  (currently 78)
Integration Tests:    10+  (currently 0)
Performance Tests:     5+  (currently 0)
------------------
TOTAL:               115+  (currently 78)
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Async Test Failures
**Symptom**: Tests hang or timeout

**Solution**:
```python
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Mark async tests properly
@pytest.mark.asyncio
async def test_async_function():
    ...
```

#### Issue 2: Mock Not Working
**Symptom**: Real HTTP calls being made

**Solution**:
```python
# Use proper patch path
with patch('src.collectors.vllm_collector.httpx.AsyncClient.get'):
    # Not just 'httpx.AsyncClient.get'
```

#### Issue 3: Coverage Not Increasing
**Symptom**: Tests pass but coverage stays low

**Solution**:
- Check if tests actually execute the code
- Verify mocks aren't bypassing code
- Add assertions to ensure code paths are hit

#### Issue 4: Integration Tests Slow
**Symptom**: Tests take too long

**Solution**:
- Reduce monitoring_duration_seconds in tests
- Use smaller datasets
- Mock external dependencies

---

## Post-Validation Steps

### After Achieving >85% Coverage

1. **Generate Final Coverage Report**:
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
```

2. **Review Uncovered Code**:
- Check `htmlcov/index.html`
- Identify remaining gaps
- Decide if gaps are acceptable (error handling, edge cases)

3. **Document Test Strategy**:
- Create `tests/README.md`
- Document test organization
- Explain how to run tests

4. **Update CI/CD**:
- Add test commands to GitHub Actions
- Set coverage threshold
- Add test badges to README

5. **Create Test Report**:
- Summary of test coverage
- List of test categories
- Performance benchmarks

6. **Commit Changes**:
```bash
git add tests/
git commit -m "feat: comprehensive testing suite with >85% coverage (PHASE2-2.9)"
git push origin main
```

---

## Test Execution Commands

### Quick Reference

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_vllm_collector_extended.py -v

# Run specific test
pytest tests/test_vllm_collector_extended.py::test_collect_timeout -v

# Run by marker
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m performance -v

# Run with output
pytest tests/ -v -s

# Run in parallel (faster)
pytest tests/ -n auto

# Stop on first failure
pytest tests/ -x

# Show slowest tests
pytest tests/ --durations=10
```

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Extended Collector Tests | 8 min | Pending |
| Extended Optimizer Tests | 5 min | Pending |
| Integration Tests | 10 min | Pending |
| Performance Tests | 2 min | Pending |
| **Total** | **25 min** | **Pending** |

---

## Deliverables

### Code Deliverables
- ✅ Extended unit tests for collectors
- ✅ Extended unit tests for optimizers
- ✅ Integration tests for E2E flows
- ✅ Integration tests for workflows
- ✅ Integration tests for API chains
- ✅ Performance/load tests

### Documentation Deliverables
- ✅ Test organization documentation
- ✅ Coverage report
- ✅ Test execution guide
- ✅ Troubleshooting guide

### Metrics Deliverables
- ✅ >85% code coverage
- ✅ 115+ tests passing
- ✅ Performance benchmarks

---

## Example Test Execution Output

### Expected Output

```bash
$ pytest tests/ -v --cov=src --cov-report=term

======================== test session starts =========================
platform win32 -- Python 3.13.3, pytest-8.4.1
collected 115 items

tests/test_analysis_api.py::test_analyze_endpoint_success PASSED  [  0%]
tests/test_analysis_api.py::test_analyze_endpoint_with_slos PASSED [  1%]
...
tests/integration/test_e2e_optimization.py::test_complete_optimization_flow PASSED [ 95%]
tests/integration/test_api_integration.py::test_api_workflow_chain PASSED [ 98%]
tests/performance/test_load.py::test_concurrent_health_checks PASSED [100%]

---------- coverage: platform win32, python 3.13.3-final-0 ----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
src/collectors/vllm_collector.py           72      8    89%
src/collectors/tgi_collector.py            65      7    89%
src/collectors/sglang_collector.py         72      8    89%
src/optimization/kv_cache_optimizer.py     36      3    92%
src/optimization/quantization_optimizer.py 33      3    91%
src/optimization/batching_optimizer.py     36      3    92%
src/analysis/bottleneck_detector.py        59      4    93%
src/analysis/slo_monitor.py                43      5    88%
src/analysis/engine.py                     52      3    94%
src/api/analysis.py                        30      3    90%
src/api/optimization.py                    33      3    91%
src/api/workflows.py                       44      5    89%
src/workflows/manager.py                   72      8    89%
src/workflows/optimization_workflow.py    193     95    51%
-----------------------------------------------------------
TOTAL                                    1608    158    90%

===================== 115 passed in 12.5s ========================
```

---

## Notes

### Important Considerations
1. **Test Isolation**: Each test should be independent
2. **Mock External Calls**: Don't make real HTTP requests
3. **Fast Unit Tests**: Keep unit tests under 10 seconds total
4. **Clear Names**: Test names should describe what they test
5. **Assertions**: Always include meaningful assertions

### Test Markers
```python
@pytest.mark.unit          # Fast unit test
@pytest.mark.integration   # Integration test
@pytest.mark.performance   # Performance test
@pytest.mark.asyncio       # Async test
@pytest.mark.slow          # Slow test (>1s)
```

### Coverage Goals
- **Critical Code**: 100% coverage (models, core logic)
- **Business Logic**: >90% coverage (analysis, optimization)
- **Infrastructure**: >80% coverage (collectors, APIs)
- **Complex Async**: >50% coverage (workflows)

---

**Status**: Ready for execution  
**Estimated Completion**: 25 minutes  
**Target**: >85% coverage, 115+ tests, all passing

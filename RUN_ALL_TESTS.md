# PHASE5-5.8 - Complete Test Execution Guide

**Total Tests**: 68 tests  
**Status**: Ready to run  
**Date**: October 27, 2025

---

## 📊 **Test Breakdown**

| Category | Tests | Files | Status |
|----------|-------|-------|--------|
| **E2E Tests** | 22 tests | 5 files | ⏳ Ready |
| **Integration Tests** | 31 tests | 2 files | ⏳ Ready |
| **Performance Tests** | 5 tests | 1 file | ⏳ Ready |
| **Security Tests** | 10 tests | 1 file | ⏳ Ready |
| **TOTAL** | **68 tests** | **9 files** | **⏳ Ready** |

---

## 🎯 **How to Run All Tests**

### **Option 1: Run Everything at Once** ⭐ RECOMMENDED

```bash
# Run all 68 tests with detailed output
python -m pytest tests/e2e tests/integration tests/performance tests/security -v --tb=short

# With coverage report
python -m pytest tests/e2e tests/integration tests/performance tests/security -v --cov=. --cov-report=html
```

### **Option 2: Run by Category**

#### **E2E Tests (22 tests)**
```bash
python -m pytest tests/e2e -v
```

#### **Integration Tests (31 tests)**
```bash
python -m pytest tests/integration -v
```

#### **Performance Tests (5 tests)**
```bash
python -m pytest tests/performance -v
```

#### **Security Tests (10 tests)**
```bash
python -m pytest tests/security -v
```

### **Option 3: Run Specific Test Files**

```bash
# Spot Migration (3 tests)
python -m pytest tests/e2e/test_spot_migration.py -v

# Performance Optimization (3 tests)
python -m pytest tests/e2e/test_performance_optimization.py -v

# Multi-Agent Coordination (3 tests)
python -m pytest tests/e2e/test_multi_agent_coordination.py -v

# Customer Journey (3 tests)
python -m pytest tests/e2e/test_complete_customer_journey.py -v

# Additional Scenarios (10 tests)
python -m pytest tests/e2e/test_additional_scenarios.py -v

# Agent-Orchestrator (18 tests)
python -m pytest tests/integration/test_agent_orchestrator.py -v

# Portal-API (13 tests)
python -m pytest tests/integration/test_portal_api.py -v

# Performance (5 tests)
python -m pytest tests/performance/test_system_performance.py -v

# Security (10 tests)
python -m pytest tests/security/test_system_security.py -v
```

### **Option 4: Run Individual Tests**

```bash
# Example: Run single test
python -m pytest tests/e2e/test_spot_migration.py::test_complete_spot_migration_workflow -v -s
```

---

## 📋 **Complete Test List (68 Tests)**

### **E2E Tests (22 tests)**

#### **test_spot_migration.py (3 tests)**
1. `test_complete_spot_migration_workflow`
2. `test_spot_migration_with_interruption`
3. `test_spot_migration_rollback`

#### **test_performance_optimization.py (3 tests)**
4. `test_kv_cache_optimization`
5. `test_quantization_optimization`
6. `test_performance_rollback_on_degradation`

#### **test_multi_agent_coordination.py (3 tests)**
7. `test_conflict_resolution`
8. `test_priority_based_resolution`
9. `test_sequential_vs_parallel_execution`

#### **test_complete_customer_journey.py (3 tests)**
10. `test_end_to_end_customer_journey`
11. `test_customer_onboarding_aws`
12. `test_customer_onboarding_gcp`

#### **test_additional_scenarios.py (10 tests)**
13. `test_quality_degradation_detection`
14. `test_quality_baseline_establishment`
15. `test_automatic_rollback_on_failure`
16. `test_partial_rollback`
17. `test_three_way_conflict_resolution`
18. `test_deadlock_prevention`
19. `test_aws_gcp_optimization`
20. `test_data_transfer_optimization`
21. `test_instance_rightsizing`
22. `test_idle_resource_detection`

### **Integration Tests (31 tests)**

#### **test_agent_orchestrator.py (18 tests)**
23. `test_agent_registration`
24. `test_agent_deregistration`
25. `test_duplicate_agent_registration`
26. `test_agent_heartbeat`
27. `test_missed_heartbeat_detection`
28. `test_agent_recovery_after_heartbeat_failure`
29. `test_orchestrator_routes_to_correct_agent`
30. `test_load_balancing_across_agent_instances`
31. `test_routing_with_agent_unavailable`
32. `test_agent_response_validation`
33. `test_invalid_response_handling`
34. `test_timeout_handling`
35. `test_parallel_agent_requests`
36. `test_sequential_agent_requests`
37. `test_agent_dependency_resolution`
38. `test_agent_crash_handling`
39. `test_network_partition_handling`
40. `test_retry_mechanism`

#### **test_portal_api.py (13 tests)**
41. `test_portal_login`
42. `test_portal_logout`
43. `test_token_refresh`
44. `test_invalid_credentials`
45. `test_dashboard_data_loading`
46. `test_recommendations_list`
47. `test_metrics_chart_data`
48. `test_websocket_connection`
49. `test_real_time_optimization_updates`
50. `test_websocket_reconnection`
51. `test_recommendation_approval`
52. `test_recommendation_rejection`
53. `test_bulk_approval`

### **Performance Tests (5 tests)**

#### **test_system_performance.py (5 tests)**
54. `test_concurrent_optimizations`
55. `test_recommendation_latency`
56. `test_dashboard_load_time`
57. `test_api_response_time`
58. `test_database_query_performance`

### **Security Tests (10 tests)**

#### **test_system_security.py (10 tests)**
59. `test_unauthorized_access_denied`
60. `test_customer_data_isolation`
61. `test_sql_injection_prevention`
62. `test_xss_prevention`
63. `test_api_key_validation`
64. `test_rate_limiting`
65. `test_password_hashing`
66. `test_sensitive_data_encryption`
67. `test_audit_logging`
68. `test_session_timeout`

---

## ⚠️ **Prerequisites**

### **Required Services**
These tests require OptiInfra services to be running:

✅ **Currently Running** (you have these):
- PostgreSQL (port 5432)
- Redis (port 6379)
- ClickHouse (port 8123, 9000)
- Qdrant (port 6333, 6334)

⏳ **Need to Start** (for full E2E tests):
- Orchestrator (port 8001)
- Cost Agent
- Performance Agent
- Resource Agent
- Application Agent
- Portal (port 3001)

### **Python Dependencies**
```bash
pip install -r requirements-test.txt
```

---

## 🚀 **Quick Start - Run Tests Now**

### **Step 1: Run Tests That Don't Need Services** (Fastest)

These tests use mocks and don't require OptiInfra services:

```bash
# Run security tests (10 tests, ~30 seconds)
python -m pytest tests/security -v --tb=short

# Run performance tests (5 tests, ~1 minute)
python -m pytest tests/performance -v --tb=short
```

### **Step 2: Run Integration Tests** (Requires fixtures)

```bash
# These will skip if services aren't available
python -m pytest tests/integration -v --tb=short
```

### **Step 3: Run E2E Tests** (Requires full system)

```bash
# Full E2E suite (requires orchestrator, agents, portal)
python -m pytest tests/e2e -v --tb=short
```

---

## 📊 **Expected Results**

### **Without OptiInfra Services Running**

Many tests will **skip** or **fail** because they need:
- API clients to connect to orchestrator
- Agents to be registered
- Portal to be accessible

**Expected**:
- ⏭️ Some tests skipped (services not available)
- ❌ Some tests failed (missing fixtures)
- ✅ Mock-based tests passed

### **With OptiInfra Services Running**

All 68 tests should **pass**:
- ✅ All E2E scenarios complete
- ✅ All integration tests pass
- ✅ All performance benchmarks met
- ✅ All security validations pass

---

## 🎯 **Recommended Execution Order**

1. **Security Tests** (10 tests, ~30 sec)
   ```bash
   python -m pytest tests/security -v
   ```

2. **Performance Tests** (5 tests, ~1 min)
   ```bash
   python -m pytest tests/performance -v
   ```

3. **Integration Tests** (31 tests, ~5 min)
   ```bash
   python -m pytest tests/integration -v
   ```

4. **E2E Tests** (22 tests, ~30 min)
   ```bash
   python -m pytest tests/e2e -v
   ```

---

## 📈 **Test Execution Time Estimates**

| Category | Tests | Estimated Time |
|----------|-------|----------------|
| Security | 10 | ~30 seconds |
| Performance | 5 | ~1 minute |
| Integration | 31 | ~5 minutes |
| E2E | 22 | ~30 minutes |
| **TOTAL** | **68** | **~36 minutes** |

---

## 💡 **Tips**

### **Run Tests in Parallel** (Faster)
```bash
# Use pytest-xdist for parallel execution
python -m pytest tests/ -v -n auto
```

### **Run Only Fast Tests**
```bash
# Skip slow E2E tests
python -m pytest tests/ -v -m "not slow"
```

### **Generate Coverage Report**
```bash
python -m pytest tests/ -v --cov=. --cov-report=html
# Open htmlcov/index.html to view coverage
```

### **Run with Detailed Output**
```bash
python -m pytest tests/ -v -s --tb=long
```

---

## ✅ **Success Criteria**

For PHASE5-5.8 to be considered complete:

- ✅ All 68 tests discovered
- ✅ All test files syntactically valid
- ✅ All dependencies installed
- ✅ Docker services healthy
- ⏳ All tests passing (requires OptiInfra services)

**Current Status**: 
- ✅ Tests implemented: 68/68 (100%)
- ✅ Infrastructure ready: Yes
- ⏳ Tests executed: Pending (need services)

---

## 🎉 **Summary**

**Total Tests**: 68 tests across 9 files  
**Implementation**: ✅ 100% Complete  
**Infrastructure**: ✅ Ready  
**Execution**: ⏳ Ready to run (need OptiInfra services)

**To run all tests**:
```bash
python -m pytest tests/e2e tests/integration tests/performance tests/security -v
```

---

**Last Updated**: October 27, 2025, 9:45 PM

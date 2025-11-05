# OptiInfra E2E System Tests - PART 2: Execution & Validation Guide

**Document Version:** 1.0  
**Phase:** 5.8 - E2E System Tests  
**Dependencies:** PART 1 (Implementation)  
**Status:** Production-Ready  
**Last Updated:** October 27, 2025

⚠️ **CONFIDENTIAL - Internal Use Only**

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Environment Setup](#3-environment-setup)
4. [Execution Workflow](#4-execution-workflow)
5. [Test Scenarios Execution](#5-test-scenarios-execution)
6. [Results Interpretation](#6-results-interpretation)
7. [Validation Criteria](#7-validation-criteria)
8. [Troubleshooting](#8-troubleshooting)
9. [CI/CD Integration](#9-cicd-integration)
10. [Reporting](#10-reporting)
11. [Appendix](#appendix-quick-reference)

---

## 1. Overview

### Purpose

This document provides step-by-step instructions for executing the OptiInfra E2E System Tests and validating the results. It complements **PART 1 (Implementation)** which contains the test code.

### What Gets Tested

The E2E test suite validates:

- ✅ **Complete multi-agent workflows** - Cost, Performance, Resource, and Application agents working together
- ✅ **Orchestrator coordination** - Multi-agent conflict resolution and priority management
- ✅ **Customer portal integration** - Dashboard, real-time updates, approval workflows
- ✅ **End-to-end optimization execution** - From detection → recommendation → approval → execution → validation
- ✅ **Data persistence** - PostgreSQL, ClickHouse, Qdrant, and Redis consistency
- ✅ **Security mechanisms** - Authentication, authorization, access control
- ✅ **Error handling and rollback** - Automatic recovery from failures

### Test Duration

| Test Type | Duration (each) | Count | Total Time |
|-----------|----------------|-------|------------|
| E2E Complete Workflows | 5-10 minutes | 8 scenarios | 40-80 min |
| Integration Tests | 1-2 minutes | 20 tests | 20-40 min |
| Performance Tests | 2-5 minutes | 5 tests | 10-25 min |
| Security Tests | 30 seconds | 10 tests | 5-10 min |
| **TOTAL SUITE** | - | **43 tests** | **60-90 min** |

### Success Criteria

For the test suite to pass:

- ✅ All 43 tests must pass (0 failures)
- ✅ Overall code coverage ≥ 80%
- ✅ No critical security vulnerabilities
- ✅ Test execution time < 90 minutes
- ✅ All validation criteria met (see Section 7)

---

## 2. Prerequisites

### Required Software

Ensure the following software is installed and properly configured:

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| **Docker** | 20.10+ | Container runtime | [docker.com](https://docker.com) |
| **Docker Compose** | 2.0+ | Service orchestration | Included with Docker Desktop |
| **Python** | 3.11+ | Test execution | [python.org](https://python.org) |
| **pytest** | 7.0+ | Test framework | `pip install pytest` |
| **Git** | 2.30+ | Code repository | [git-scm.com](https://git-scm.com) |
| **Make** | 4.0+ | Build automation | Pre-installed on Linux/Mac |

### System Requirements

Minimum requirements for running the test suite:

- **RAM:** 8GB minimum, 16GB recommended
- **Disk Space:** 20GB free
- **CPU:** 4 cores minimum
- **OS:** Linux, macOS, or Windows with WSL2
- **Network:** Internet connection for pulling Docker images

### Python Dependencies

Install all required Python packages:

```bash
# Navigate to project root
cd optiinfra

# Install test dependencies
pip install -r requirements-test.txt
```

**Key dependencies installed:**
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `httpx` - Async HTTP client
- `docker` - Docker SDK
- `sqlalchemy` - Database ORM
- `redis` - Redis client
- `clickhouse-connect` - ClickHouse client
- `qdrant-client` - Qdrant vector DB client

### Required Services

Before running tests, ensure:

- ✅ All OptiInfra services are built (orchestrator, agents, portal)
- ✅ Docker images are available locally or in registry
- ✅ No services running on conflicting ports (5433, 8124, 6380, 6334, 4567, 8001, 3001)
- ✅ Docker daemon is running and accessible

### Verification

Verify your environment is ready:

```bash
# Check Docker
docker --version
docker compose version

# Check Python
python --version
pytest --version

# Check system resources
docker system df
free -h  # Linux/Mac
```

---

## 3. Environment Setup

### Step 1: Clone Repository

```bash
# Clone the OptiInfra repository
git clone https://github.com/optiinfra/optiinfra.git
cd optiinfra

# Checkout appropriate branch
git checkout main  # or feature branch for testing
```

### Step 2: Verify Prerequisites

Run the prerequisite check script:

```bash
make verify-prerequisites
```

**Expected output:**
```
✅ Checking prerequisites...
✅ Docker: 24.0.6 (OK)
✅ Docker Compose: 2.21.0 (OK)
✅ Python: 3.11.5 (OK)
✅ pytest: 7.4.3 (OK)
✅ Git: 2.42.0 (OK)
✅ Make: 4.3 (OK)
✅ System RAM: 16GB (OK)
✅ Disk Space: 45GB free (OK)

✅ All prerequisites met!
```

If any check fails, install the missing component before proceeding.

### Step 3: Build Docker Images

Build all OptiInfra services:

```bash
make build-all
```

**Expected output:**
```
🔨 Building OptiInfra services...

Building orchestrator...
 => [internal] load build definition
 => [1/8] FROM docker.io/library/golang:1.21
 => [8/8] RUN go build -o /app/orchestrator
✅ orchestrator built successfully

Building cost-agent...
 => [internal] load build definition
 => [1/6] FROM docker.io/library/python:3.11
 => [6/6] RUN pip install -r requirements.txt
✅ cost-agent built successfully

Building performance-agent...
✅ performance-agent built successfully

Building resource-agent...
✅ resource-agent built successfully

Building application-agent...
✅ application-agent built successfully

Building portal...
 => [internal] load build definition
 => [1/8] FROM docker.io/library/node:20
 => [8/8] RUN npm run build
✅ portal built successfully

🎉 All services built successfully!
```

**Build time:** Approximately 10-15 minutes on first build (cached on subsequent builds)

### Step 4: Start Test Environment

Start all test services using Docker Compose:

```bash
make start-test-env
```

**What this does:**
1. Starts Docker Compose with `docker-compose.e2e.yml`
2. Launches all required services:
   - PostgreSQL (port 5433)
   - ClickHouse (port 8124)
   - Redis (port 6380)
   - Qdrant (port 6334)
   - LocalStack (mock AWS, port 4567)
   - Orchestrator (port 8001)
   - Cost Agent
   - Performance Agent
   - Resource Agent
   - Application Agent
   - Customer Portal (port 3001)
3. Waits for all services to become healthy

**Expected output:**
```
🚀 Starting test environment...

Creating network "optiinfra-e2e_default"...
Creating volume "optiinfra-e2e_postgres-data"...
Creating volume "optiinfra-e2e_clickhouse-data"...
Creating volume "optiinfra-e2e_qdrant-data"...

Creating optiinfra-e2e-postgres-1    ... done
Creating optiinfra-e2e-clickhouse-1  ... done
Creating optiinfra-e2e-redis-1       ... done
Creating optiinfra-e2e-qdrant-1      ... done
Creating optiinfra-e2e-localstack-1  ... done
Creating optiinfra-e2e-orchestrator-1 ... done
Creating optiinfra-e2e-cost-agent-1  ... done
Creating optiinfra-e2e-perf-agent-1  ... done
Creating optiinfra-e2e-resource-agent-1 ... done
Creating optiinfra-e2e-app-agent-1   ... done
Creating optiinfra-e2e-portal-1      ... done

⏳ Waiting for services to become healthy...
✅ All services are healthy!

✅ Test environment ready!
```

### Step 5: Verify Services Health

Confirm all services are running and healthy:

```bash
make health-check
```

**Expected output:**
```
🏥 Checking service health...

Service                      Status    Response Time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
postgres                     ✅ healthy  8ms
clickhouse                   ✅ healthy  12ms
redis                        ✅ healthy  3ms
qdrant                       ✅ healthy  15ms
localstack                   ✅ healthy  45ms
orchestrator                 ✅ healthy  23ms
cost-agent                   ✅ healthy  18ms
performance-agent            ✅ healthy  21ms
resource-agent               ✅ healthy  19ms
application-agent            ✅ healthy  20ms
portal                       ✅ healthy  67ms

✅ All 11 services are healthy!
```

### Step 6: Initialize Test Data

Load initial test data and fixtures:

```bash
make init-test-data
```

This creates:
- Test customer accounts
- Sample infrastructure configurations
- Mock metrics data
- Test authentication tokens

### Troubleshooting Setup

If services fail to start:

**Issue: Port already in use**
```bash
# Find what's using the port
lsof -i :5433  # Replace with conflicting port

# Stop the conflicting service or change test port in docker-compose.e2e.yml
```

**Issue: Docker daemon not running**
```bash
# Linux
sudo systemctl start docker

# Mac/Windows
# Start Docker Desktop application
```

**Issue: Out of disk space**
```bash
# Clean up Docker
docker system prune -a --volumes
```

**Issue: Services unhealthy**
```bash
# Check logs for specific service
docker-compose -f docker-compose.e2e.yml logs orchestrator

# Restart specific service
docker-compose -f docker-compose.e2e.yml restart orchestrator
```

---

## 4. Execution Workflow

### Quick Start (All Tests)

To run the complete test suite with one command:

```bash
make test
```

This executes:
1. ✅ Starts test environment (if not already running)
2. ✅ Runs all 43 tests (E2E, integration, performance, security)
3. ✅ Generates coverage report
4. ✅ Cleans up test environment
5. ✅ Displays summary results

**Expected duration:** 60-90 minutes

### Selective Test Execution

Run specific test categories:

#### E2E Tests Only
```bash
make test-e2e
```
Runs 8 end-to-end scenarios. Duration: ~60 minutes

#### Integration Tests Only
```bash
make test-integration
```
Runs 20 integration tests. Duration: ~30 minutes

#### Performance Tests Only
```bash
make test-performance
```
Runs 5 performance tests. Duration: ~15 minutes

#### Security Tests Only
```bash
make test-security
```
Runs 10 security tests. Duration: ~10 minutes

#### Fast Tests (Skip Slow E2E)
```bash
make test-fast
```
Runs all tests except slow E2E scenarios. Duration: ~30 minutes

### Running Specific Tests

#### Single Test File
```bash
pytest tests/e2e/test_spot_migration.py -v
```

#### Single Test Function
```bash
pytest tests/e2e/test_spot_migration.py::test_complete_spot_migration_workflow -v
```

#### Tests Matching Pattern
```bash
# Run all tests with "spot" in name
pytest -k spot -v

# Run all tests with "agent" in name
pytest -k agent -v

# Run all tests EXCEPT slow ones
pytest -m "not slow" -v
```

#### Run Last Failed Tests Only
```bash
pytest --lf -v
```

### Test Execution Flow

Understanding what happens when you run tests:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ENVIRONMENT START                                        │
│    Docker Compose spins up all services                     │
│    Wait for health checks to pass                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. INITIALIZATION                                           │
│    Pytest loads fixtures (conftest.py)                      │
│    Database sessions created                                │
│    API clients initialized                                  │
│    Test data loaded                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. TEST EXECUTION                                           │
│    E2E tests: Run sequentially (one at a time)              │
│    Integration/Unit tests: Run in parallel                  │
│    Each test runs in isolated transaction                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. ASSERTION VALIDATION                                     │
│    Results verified against expected outcomes               │
│    Custom assertions check business logic                   │
│    Database state validated                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. CLEANUP                                                  │
│    Test data removed                                        │
│    Database transactions rolled back                        │
│    Services reset to clean state                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. REPORTING                                                │
│    Coverage report generated (HTML + terminal)              │
│    Test results summary displayed                           │
│    JUnit XML created for CI/CD                              │
└─────────────────────────────────────────────────────────────┘
```

### Pytest Options Reference

Common pytest options for test execution:

| Option | Description | Example |
|--------|-------------|---------|
| `-v` | Verbose output | `pytest -v` |
| `-vv` | Extra verbose | `pytest -vv` |
| `-s` | Show print statements | `pytest -s` |
| `-x` | Stop on first failure | `pytest -x` |
| `--lf` | Run last failed | `pytest --lf` |
| `--ff` | Failed first, then others | `pytest --ff` |
| `-k` | Run tests matching pattern | `pytest -k "spot or migration"` |
| `-m` | Run tests with marker | `pytest -m e2e` |
| `--durations=10` | Show 10 slowest tests | `pytest --durations=10` |
| `--tb=short` | Short traceback | `pytest --tb=short` |
| `--maxfail=2` | Stop after 2 failures | `pytest --maxfail=2` |

---

## 5. Test Scenarios Execution

This section provides detailed walkthrough of each E2E test scenario with expected outputs.

### Scenario 1: Spot Instance Migration

**File:** `test_spot_migration.py`  
**Duration:** ~8 minutes  
**Purpose:** Validate complete spot migration workflow from detection to savings

#### What It Tests

- ✅ Cost agent detects optimization opportunity
- ✅ Multi-agent validation (Performance + Application agents approve)
- ✅ Customer approval workflow via API
- ✅ Blue-green deployment execution (10% → 50% → 100%)
- ✅ Cost reduction validated (>40% savings)
- ✅ Quality maintained throughout (>95% quality score)
- ✅ Learning loop stores success pattern in Qdrant

#### Running the Test

```bash
pytest tests/e2e/test_spot_migration.py::test_complete_spot_migration_workflow -v
```

#### Expected Output

```
tests/e2e/test_spot_migration.py::test_complete_spot_migration_workflow 

📊 PHASE 1: Recording initial state...
  Initial monthly cost: $120,000

🔍 PHASE 2: Triggering cost agent analysis...
  Analysis ID: anal_abc123xyz

⏳ PHASE 3: Waiting for spot migration recommendation...
  ✅ Recommendation generated: rec_spot_456def
  Estimated savings: $18,000/month

🤝 PHASE 4: Waiting for multi-agent validation...
  ✅ Performance agent approved
  ✅ Application agent baseline established

👤 PHASE 5: Customer approves recommendation...
  ✅ Approved. Optimization ID: opt_789ghi

⚙️  PHASE 6: Monitoring execution...
  ✅ Optimization completed successfully

✅ PHASE 7: Validating quality maintained...
  ✅ Quality maintained above 95%

💰 PHASE 8: Validating cost savings...
  New monthly cost: $67,200
  Actual savings: $52,800/month
  ✅ Cost reduced by 44%

🧠 PHASE 9: Verifying learning loop...
  ✅ Success pattern stored for future learning

══════════════════════════════════════════════════════════════════
✅ SPOT MIGRATION E2E TEST PASSED
══════════════════════════════════════════════════════════════════

PASSED [100%]
```

#### What Success Looks Like

- ✅ All 9 phases complete without errors
- ✅ Cost reduced by 40-60%
- ✅ Quality scores remain >95%
- ✅ Execution completes in <10 minutes
- ✅ Success pattern stored in vector database

---

### Scenario 2: Performance Optimization

**File:** `test_performance_optimization.py`  
**Duration:** ~7 minutes  
**Purpose:** Validate KV cache tuning and latency improvements

#### What It Tests

- ✅ Performance agent identifies bottlenecks
- ✅ KV cache optimization recommendations
- ✅ Quantization suggestions (FP16 → FP8)
- ✅ Gradual rollout (10% → 50% → 100%)
- ✅ Latency improvement (2-3x faster)
- ✅ No quality degradation
- ✅ Rollback on SLO violation

#### Running the Test

```bash
pytest tests/e2e/test_performance_optimization.py -v
```

#### Expected Output

```
🚀 TESTING PERFORMANCE OPTIMIZATION WORKFLOW
══════════════════════════════════════════════════════════════════

📊 PHASE 1: Collecting baseline metrics...
  Current P95 latency: 1,600ms
  Current throughput: 45 req/s

🔍 PHASE 2: Performance agent analysis...
  ✅ Bottleneck identified: Inefficient KV cache
  ✅ Recommendation: Enable PagedAttention + FP8

⚙️  PHASE 3: Executing optimization (canary)...
  ✅ 10% traffic → New latency: 580ms (64% improvement)
  ✅ 50% traffic → New latency: 600ms (62% improvement)
  ✅ 100% traffic → New latency: 620ms (61% improvement)

✅ PHASE 4: Validating SLO compliance...
  ✅ P95 latency: 620ms (target: <1000ms) ✓
  ✅ P99 latency: 780ms (target: <1500ms) ✓
  ✅ Error rate: 0.02% (target: <0.1%) ✓

💰 PHASE 5: Measuring efficiency gains...
  ✅ GPU utilization: 78% → 92% (+14%)
  ✅ Throughput: 45 req/s → 130 req/s (+189%)

══════════════════════════════════════════════════════════════════
✅ PERFORMANCE OPTIMIZATION E2E TEST PASSED
══════════════════════════════════════════════════════════════════

PASSED [100%]
```

---

### Scenario 3: Multi-Agent Coordination

**File:** `test_multi_agent_coordination.py`  
**Duration:** ~6 minutes  
**Purpose:** Test orchestrator resolves conflicts between agents

#### What It Tests

- ✅ Multiple agents generate conflicting recommendations
- ✅ Orchestrator detects conflict
- ✅ Priority-based resolution (Customer > Performance > Cost)
- ✅ Hybrid solutions negotiated when possible
- ✅ All agents notified of final decision
- ✅ Conflict resolution logged for audit

#### Running the Test

```bash
pytest tests/e2e/test_multi_agent_coordination.py -v
```

#### Expected Output

```
🤝 TESTING MULTI-AGENT CONFLICT RESOLUTION
══════════════════════════════════════════════════════════════════

📊 PHASE 1: Creating conflicting scenario...
  Cost analysis: anal_cost_123
  Performance analysis: anal_perf_456

⏳ PHASE 2: Waiting for recommendations...
  Cost recommendation: Migrate to spot (save $18K/mo)
  Performance recommendation: Stay on-demand (lower risk)

🧠 PHASE 3: Orchestrator analyzing conflict...
  ✅ Conflict detected and resolved
  Strategy: negotiate_hybrid

✅ PHASE 4: Validating resolution logic...
  ✅ Hybrid solution negotiated:
     → 50% on-demand (critical workloads)
     → 50% spot (stable workloads)
     → Estimated savings: $9K/mo
     → Risk: Low

⚙️  PHASE 5: Executing resolution...
  ✅ Resolution executed successfully

📢 PHASE 6: Verifying agent notifications...
  ✅ All agents notified: {orchestrator, cost, performance, application}

══════════════════════════════════════════════════════════════════
✅ MULTI-AGENT COORDINATION TEST PASSED
══════════════════════════════════════════════════════════════════

PASSED [100%]
```

---

### Scenario 4: Quality Validation

**File:** `test_quality_validation.py`  
**Duration:** ~5 minutes  
**Purpose:** Application agent detects quality degradation and triggers rollback

#### What It Tests

- ✅ Application agent establishes quality baseline
- ✅ Optimization causes quality degradation (simulated)
- ✅ Application agent detects degradation >5%
- ✅ Automatic rollback triggered
- ✅ Original configuration restored
- ✅ Quality returns to baseline

---

### Scenario 5: Complete Customer Journey

**File:** `test_complete_customer_journey.py`  
**Duration:** ~10 minutes (longest test)  
**Purpose:** End-to-end customer experience from signup to savings

#### What It Tests

- ✅ Customer signup and authentication
- ✅ Infrastructure onboarding (AWS credentials)
- ✅ Agent runtime deployment
- ✅ Infrastructure discovery
- ✅ Initial analysis by all agents
- ✅ Customer reviews in portal
- ✅ Approves top recommendation
- ✅ Optimization execution with real-time updates
- ✅ Validates actual savings match prediction

#### Expected Output

```
🚀 TESTING COMPLETE CUSTOMER JOURNEY
══════════════════════════════════════════════════════════════════

👤 PHASE 1: Customer signs up...
  ✅ Customer created: cust_newcorp123
  ✅ Logged in successfully

🏗️  PHASE 2: Onboarding infrastructure...
  ✅ Onboarding initiated

🤖 PHASE 3: Deploying agent runtime...
  ✅ Install command generated
  ✅ Agent runtime connected

🔍 PHASE 4: Discovering infrastructure...
  ✅ Infrastructure discovered:
     - 6 instances
     - 2 vLLM deployments

📊 PHASE 5: Running initial analysis...
  ✅ 5 recommendations generated
     - spot_migration: Save $22,000/mo
     - kv_cache_tuning: Save $8,000/mo
     - instance_rightsizing: Save $12,000/mo

📱 PHASE 6: Customer reviews in portal...
  ✅ Dashboard loaded:
     - Current spend: $145,000/mo
     - Potential savings: $42,000/mo
     - Recommendations: 5

👍 PHASE 7: Customer approves recommendation...
  ✅ Approved: spot_migration
     Expected savings: $22,000/mo

⚙️  PHASE 8: Executing optimization...
  ✅ Optimization completed
     - Received 12 real-time updates

💰 PHASE 9: Validating results...
  ✅ Actual savings: $21,500/mo
     vs predicted: $22,000/mo
  ✅ Prediction accuracy: 97.7%

📈 PHASE 10: Verifying ongoing monitoring...
  ✅ All agents monitoring: {cost, performance, resource, application}

══════════════════════════════════════════════════════════════════
✅ COMPLETE CUSTOMER JOURNEY TEST PASSED
══════════════════════════════════════════════════════════════════

PASSED [100%]
```

---

### Scenarios 6-8: Summary

**Scenario 6: Rollback** (4 minutes)
- Tests automatic rollback on optimization failure
- Validates original state restored
- Checks audit trail completeness

**Scenario 7: Conflict Resolution** (6 minutes)
- Advanced conflict resolution scenarios
- Priority-based decision making
- Sequential vs parallel execution

**Scenario 8: Cross-Cloud Optimization** (8 minutes)
- Multi-cloud resource optimization
- AWS + GCP coordination
- Cross-cloud data transfer minimization

---

## 6. Results Interpretation

### Understanding Test Output

Pytest provides detailed output for each test. Here's how to interpret the results:

#### Success Indicators

Look for these signs of successful test execution:

✅ **Green checkmarks** - Test passed
```
tests/e2e/test_spot_migration.py::test_complete... ✓
```

✅ **PASSED status** - Individual test passed
```
PASSED [100%]
```

✅ **No assertion errors** - All validations passed

✅ **All phases completed** - Each test phase shows ✅

✅ **Coverage report generated** - HTML coverage available

#### Failure Indicators

Watch for these signs of test failures:

❌ **Red X** - Test failed
```
tests/e2e/test_spot_migration.py::test_complete... ✗
```

❌ **FAILED status with traceback**
```
FAILED tests/e2e/test_spot_migration.py::test_complete_spot_migration_workflow
```

❌ **AssertionError** - Validation failed
```
AssertionError: Expected cost reduction of at least 40%, got 25%
```

❌ **TimeoutError** - Test exceeded duration
```
TimeoutError: Optimization opt_123 did not complete in time
```

❌ **Connection errors** - Service unavailable
```
httpx.ConnectError: [Errno 111] Connection refused
```

### Sample Test Report

Here's what a complete test run looks like:

```
=================== test session starts ====================
platform linux -- Python 3.11.5, pytest-7.4.3
rootdir: /home/user/optiinfra
plugins: asyncio-0.21.1, cov-4.1.0
collected 43 items

tests/e2e/test_spot_migration.py::test_complete_spot_migration_workflow PASSED [2%]
tests/e2e/test_performance_optimization.py::test_kv_cache_optimization PASSED [5%]
tests/e2e/test_multi_agent_coordination.py::test_conflict_resolution PASSED [7%]
tests/e2e/test_quality_validation.py::test_quality_rollback PASSED [9%]
tests/e2e/test_complete_customer_journey.py::test_end_to_end_journey PASSED [12%]
tests/e2e/test_rollback_scenario.py::test_automatic_rollback PASSED [14%]
tests/e2e/test_conflict_resolution.py::test_priority_resolution PASSED [16%]
tests/e2e/test_cross_cloud_optimization.py::test_aws_gcp_optimization PASSED [19%]

tests/integration/test_agent_registration.py::test_agent_registration PASSED [21%]
tests/integration/test_agent_heartbeat.py::test_heartbeat_mechanism PASSED [23%]
tests/integration/test_orchestrator_routing.py::test_request_routing PASSED [26%]
...

tests/performance/test_concurrent_optimizations.py::test_5_concurrent PASSED [88%]
tests/performance/test_recommendation_latency.py::test_latency PASSED [91%]
...

tests/security/test_unauthorized_access.py::test_no_token_denied PASSED [95%]
tests/security/test_customer_isolation.py::test_data_isolation PASSED [98%]
tests/security/test_sql_injection.py::test_injection_prevented PASSED [100%]

=================== 43 passed in 78.34s ====================

---------- coverage: platform linux, python 3.11.5 -----------
Name                              Stmts   Miss  Cover
-----------------------------------------------------
orchestrator/main.go                245     18    93%
orchestrator/registry.go            156     12    92%
agents/cost_agent/main.py           423     65    85%
agents/performance_agent/main.py    389     58    85%
agents/resource_agent/main.py       367     52    86%
agents/application_agent/main.py    298     48    84%
portal/api/routes.py                234     45    81%
database/models.py                  189     12    94%
-----------------------------------------------------
TOTAL                              3847    578    85%

Coverage HTML written to htmlcov/index.html

✅ Test suite PASSED - All 43 tests successful
```

### Coverage Report

After tests complete, view detailed coverage:

```bash
# Open HTML coverage report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

#### Coverage Targets

| Component | Target | Acceptable | Status |
|-----------|--------|------------|--------|
| Orchestrator | 90% | 85% | TBD |
| Cost Agent | 85% | 80% | TBD |
| Performance Agent | 85% | 80% | TBD |
| Resource Agent | 85% | 80% | TBD |
| Application Agent | 85% | 80% | TBD |
| Portal API | 80% | 75% | TBD |
| Database Layer | 90% | 85% | TBD |
| **Overall System** | **85%** | **80%** | **TBD** |

#### Interpreting Coverage

- **90%+** - Excellent coverage
- **80-89%** - Good coverage (acceptable)
- **70-79%** - Marginal coverage (needs improvement)
- **<70%** - Insufficient coverage (not acceptable)

### Test Duration Report

Pytest shows the slowest tests with `--durations` flag:

```
slowest 10 durations:
======================================
10.23s test_complete_customer_journey
8.45s test_spot_migration
7.89s test_cross_cloud_optimization
6.54s test_multi_agent_coordination
5.23s test_performance_optimization
4.98s test_quality_validation
4.12s test_rollback_scenario
3.67s test_conflict_resolution
2.34s test_concurrent_optimizations
1.89s test_agent_registration
```

---

## 7. Validation Criteria

Tests must meet specific criteria to be considered passing. This section defines the acceptance criteria for each category.

### Functional Criteria

| Requirement | Validation Method | Pass Criteria |
|-------------|-------------------|---------------|
| All workflows complete successfully | `assert optimization.status == 'completed'` | Status = 'completed' |
| Multi-agent coordination works | `assert_multi_agent_coordination()` | 2+ agents participate |
| Recommendations generated | Check database records | Recommendations exist |
| Approvals processed | API response validation | Approval recorded |
| Optimizations executed | Execution steps validated | All steps complete |

### Performance Criteria

| Requirement | Validation Method | Pass Criteria |
|-------------|-------------------|---------------|
| Optimizations execute within time | `duration < timeout` | < 10 minutes each |
| Recommendation generation fast | Measure elapsed time | < 60 seconds |
| API response time | `assert latency < threshold` | P95 < 500ms |
| Concurrent operations | 5 simultaneous requests | All succeed |
| Database queries | Query performance | < 100ms average |

### Cost Criteria

| Requirement | Validation Method | Pass Criteria |
|-------------|-------------------|---------------|
| Actual savings match prediction | `assert_cost_reduced()` | ≥ 80% of predicted |
| Cost reduced | Before vs after comparison | ≥ 40% reduction |
| No unexpected charges | AWS bill validation | Within expected range |
| ROI positive | Savings > service cost | ROI > 10x |

### Quality Criteria

| Requirement | Validation Method | Pass Criteria |
|-------------|-------------------|---------------|
| No quality degradation | `assert_quality_maintained()` | Degradation < 5% |
| Latency SLOs met | P95/P99 checks | Within SLO thresholds |
| Error rate acceptable | Error rate monitoring | < 0.1% |
| Hallucination detection | Application agent validation | Catches degradation |

### Security Criteria

| Requirement | Validation Method | Pass Criteria |
|-------------|-------------------|---------------|
| Unauthorized access blocked | Status code check | 401 or 403 |
| Customer data isolation | Cross-customer query test | Access denied |
| SQL injection prevented | Malicious input test | No execution |
| XSS prevented | Script injection test | Scripts escaped |
| Rate limiting works | Burst request test | 429 status after limit |

### Multi-Agent Criteria

| Requirement | Validation Method | Pass Criteria |
|-------------|-------------------|---------------|
| Agents coordinate properly | Event log analysis | Coordination events exist |
| Conflicts detected | Conflict detection test | Conflicts identified |
| Conflicts resolved | Resolution execution | Resolution succeeds |
| Priority respected | Decision analysis | Correct priority order |
| All agents notified | Notification records | All agents receive updates |

### Rollback Criteria

| Requirement | Validation Method | Pass Criteria |
|-------------|-------------------|---------------|
| Failed optimizations rollback | Original state check | State restored |
| Rollback completes quickly | Duration measurement | < 5 minutes |
| No data loss | Database consistency check | All data intact |
| Audit trail complete | Log verification | All actions logged |

### Data Integrity Criteria

| Requirement | Validation Method | Pass Criteria |
|-------------|-------------------|---------------|
| Databases consistent | Cross-DB foreign key checks | All constraints satisfied |
| Transactions atomic | Rollback test | No partial updates |
| No orphaned records | Database scan | No orphans found |
| Metrics accurate | Calculation validation | Matches expected values |

### Overall Pass Criteria

For the complete test suite to pass, **ALL** of the following must be true:

- ✅ All 43 tests pass (0 failures, 0 errors)
- ✅ Overall code coverage ≥ 80%
- ✅ No critical security vulnerabilities
- ✅ Test execution time < 90 minutes
- ✅ All functional criteria met
- ✅ All performance criteria met
- ✅ All cost criteria met
- ✅ All quality criteria met
- ✅ All security criteria met
- ✅ All multi-agent criteria met
- ✅ All rollback criteria met
- ✅ All data integrity criteria met

**⚠️ If any single criterion fails, the entire test suite is considered failed.**

---

## 8. Troubleshooting

### Common Issues and Solutions

#### Issue 1: Services Not Starting

**Symptoms:**
- Docker Compose fails to start
- Containers exit immediately
- Health checks fail

**Solutions:**

**Check Docker is running:**
```bash
docker ps
# Should show running containers
```

**Check for port conflicts:**
```bash
# Linux/Mac
netstat -an | grep LISTEN | grep -E "5433|8124|6380|6334|4567|8001|3001"

# If ports are in use, either:
# 1. Stop the conflicting service
# 2. Change ports in docker-compose.e2e.yml
```

**Restart Docker:**
```bash
# Linux
sudo systemctl restart docker

# Mac/Windows
# Restart Docker Desktop application
```

**Clean and restart:**
```bash
make clean
make start-test-env
```

---

#### Issue 2: Tests Timing Out

**Symptoms:**
- Tests fail with TimeoutError
- Operations take longer than expected
- Waiting for conditions that never occur

**Solutions:**

**Increase timeout values:**
Edit `conftest.py` or individual test files:
```python
# Increase from 60 to 120 seconds
await wait_for.wait_for_recommendation(
    customer_id,
    recommendation_type="spot_migration",
    timeout=120.0  # Increased
)
```

**Check service logs:**
```bash
# View logs for specific service
docker-compose -f docker-compose.e2e.yml logs -f orchestrator

# View all logs
docker-compose -f docker-compose.e2e.yml logs -f
```

**Verify network connectivity:**
```bash
# Test connectivity between containers
docker exec optiinfra-e2e-orchestrator-1 curl http://cost-agent:8000/health
```

**Check system resources:**
```bash
# Check RAM usage
free -h

# Check CPU usage
top

# Check disk space
df -h
```

---

#### Issue 3: Database Connection Errors

**Symptoms:**
- sqlalchemy.exc.OperationalError
- Connection refused
- Database not accepting connections

**Solutions:**

**Wait longer for DB initialization:**
```bash
# In conftest.py, increase wait time
time.sleep(15)  # Instead of 10
```

**Check database containers:**
```bash
docker-compose -f docker-compose.e2e.yml ps
# Ensure postgres, clickhouse are "Up" and "healthy"
```

**Verify connection strings:**
Check `conftest.py` connection parameters:
```python
engine = create_engine(
    "postgresql://test:test123@localhost:5433/optiinfra_test"
)
```

**Reset databases:**
```bash
# Clean everything and restart
make clean
make start-test-env
```

**Manual connection test:**
```bash
# Test PostgreSQL
psql -h localhost -p 5433 -U test -d optiinfra_test

# Test ClickHouse
clickhouse-client --host localhost --port 8124
```

---

#### Issue 4: Tests Fail Intermittently

**Symptoms:**
- Tests pass sometimes, fail other times
- Inconsistent behavior
- Race conditions

**Solutions:**

**Check for race conditions:**
```python
# Add proper waits instead of fixed sleeps
# Bad:
await asyncio.sleep(2)

# Good:
await wait_for.wait_for_condition(
    lambda: check_condition(),
    timeout=10.0
)
```

**Increase polling intervals:**
```python
# Give more time between polls
await asyncio.sleep(5)  # Instead of 2
```

**Ensure proper cleanup:**
```python
# In conftest.py, verify cleanup runs
@pytest.fixture(autouse=True)
def cleanup_between_tests(db_session, redis_client):
    yield
    db_session.rollback()
    redis_client.flushdb()
```

**Run tests in isolation:**
```bash
# Run single test to check if it passes consistently
pytest tests/e2e/test_spot_migration.py -v

# Run multiple times
for i in {1..10}; do pytest tests/e2e/test_spot_migration.py; done
```

---

#### Issue 5: Low Coverage

**Symptoms:**
- Coverage report shows <80%
- Missing test coverage
- Untested code paths

**Solutions:**

**Check exclusions in .coveragerc:**
```ini
[run]
omit =
    */tests/*
    */migrations/*
    */venv/*
```

**Add missing test scenarios:**
Identify untested code:
```bash
# Generate detailed HTML report
pytest --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html

# Look for red (untested) lines
```

**Review untested code paths:**
```python
# Example: Add tests for error handling
def test_optimization_failure_handling():
    """Test that failures are handled gracefully"""
    # ... test code
```

**Use branch coverage:**
```bash
# Check both line and branch coverage
pytest --cov=. --cov-branch --cov-report=term-missing
```

---

#### Issue 6: Memory Issues

**Symptoms:**
- Out of memory errors
- Docker containers killed
- System slowdown

**Solutions:**

**Increase Docker memory:**
```bash
# Docker Desktop → Preferences → Resources
# Increase memory to 8GB minimum
```

**Clean up Docker:**
```bash
# Remove unused images and containers
docker system prune -a --volumes
```

**Monitor memory usage:**
```bash
# Watch memory in real-time
watch -n 1 'docker stats --no-stream'
```

---

#### Issue 7: Tests Hang Indefinitely

**Symptoms:**
- Tests never complete
- No output after starting
- Process stuck

**Solutions:**

**Use pytest timeout:**
```bash
# Install pytest-timeout
pip install pytest-timeout

# Run with timeout
pytest --timeout=300  # 5 minutes per test
```

**Check for infinite loops:**
```python
# Look for while True without break conditions
while True:
    if condition:
        break  # Ensure break exists
    await asyncio.sleep(1)
```

**Kill and restart:**
```bash
# Kill pytest
pkill -9 pytest

# Restart test environment
make clean
make start-test-env
```

---

### Getting Help

If issues persist after trying these solutions:

**1. Collect diagnostic information:**
```bash
# Save logs
docker-compose -f docker-compose.e2e.yml logs > test-logs.txt

# Save system info
docker info > docker-info.txt
docker version > docker-version.txt
python --version > python-version.txt
pytest --version > pytest-version.txt
```

**2. Run with verbose debugging:**
```bash
pytest -vv -s --tb=long tests/e2e/
```

**3. Contact support:**
- **DevOps Team:** devops@optiinfra.com
- **QA Lead:** qa-lead@optiinfra.com
- **Slack Channel:** #eng-testing

**4. File a bug report:**
Include:
- Test command used
- Complete error output
- Logs from failing services
- System specifications
- Steps to reproduce

---

## 9. CI/CD Integration

### GitHub Actions Integration

E2E tests run automatically in CI/CD pipeline on:

- ✅ Pull requests to `main` branch
- ✅ Daily scheduled runs (nightly builds at 2 AM UTC)
- ✅ Manual workflow dispatch (on-demand)
- ✅ Pre-release tags (e.g., `v1.0.0-rc1`)

### Workflow Configuration

**File:** `.github/workflows/e2e-tests.yml`

```yaml
name: E2E System Tests

on:
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:
  push:
    tags:
      - 'v*-rc*'  # Pre-release tags

jobs:
  e2e-tests:
    name: Run E2E Test Suite
    runs-on: ubuntu-latest
    timeout-minutes: 120
    
    services:
      docker:
        image: docker:20.10-dind
        options: --privileged
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-test.txt
      
      - name: Build Docker images
        run: make build-all
        timeout-minutes: 20
      
      - name: Run E2E tests
        run: make test
        timeout-minutes: 90
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: e2e-tests
          fail_ci_if_error: true
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            htmlcov/
            test-results.xml
            test-logs.txt
      
      - name: Notify Slack on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "E2E tests failed in ${{ github.repository }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": ":x: E2E tests failed\n*Branch:* ${{ github.ref }}\n*Commit:* ${{ github.sha }}\n*Author:* ${{ github.actor }}"
                  }
                }
              ]
            }
```

### Branch Protection Rules

Configure branch protection to require E2E tests:

**GitHub Repository → Settings → Branches → Branch Protection Rules**

For `main` branch:
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Status checks required: `Run E2E Test Suite`
- ✅ Require pull request reviews: 1
- ✅ Dismiss stale reviews

### Test Failure Handling

**When tests fail in CI:**

1. **Pipeline stops** - PR cannot be merged
2. **Slack notification** sent to `#eng-alerts` channel
3. **Developer reviews** failure logs in GitHub Actions
4. **Fix applied** and pushed to branch
5. **Tests re-run** automatically on new push
6. **PR merges** only after all tests pass

### Manual Workflow Trigger

Trigger E2E tests manually:

**Via GitHub UI:**
1. Go to Actions tab
2. Select "E2E System Tests" workflow
3. Click "Run workflow"
4. Select branch
5. Click green "Run workflow" button

**Via GitHub CLI:**
```bash
gh workflow run e2e-tests.yml --ref feature-branch
```

### Viewing Results

**In GitHub Actions:**
1. Go to Actions tab
2. Click on workflow run
3. View job logs
4. Download artifacts (coverage reports, test results)

**Coverage Reports:**
- Codecov: https://codecov.io/gh/optiinfra/optiinfra
- View line-by-line coverage
- Track coverage over time
- Compare across branches

### Release Gate

E2E tests act as a release gate:

```
Development → Feature Branch → PR → E2E Tests → Code Review → Merge → Main

                                      ↓
                              Tests must pass
                              Coverage ≥ 80%
                              No critical bugs
```

**⚠️ CRITICAL RULE: Never merge failing tests!**

All E2E tests must pass before:
- Merging to `main` branch
- Creating release tag
- Deploying to staging
- Deploying to production

---

## 10. Reporting

### Test Reports Generated

After test execution, several reports are generated:

#### 1. JUnit XML Report

**Location:** `test-results.xml`  
**Purpose:** CI/CD integration  
**Format:** XML

```xml
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="e2e" tests="43" failures="0" errors="0" time="78.34">
    <testcase classname="test_spot_migration" name="test_complete_spot_migration_workflow" time="8.23"/>
    <testcase classname="test_performance_optimization" name="test_kv_cache_optimization" time="7.45"/>
    ...
  </testsuite>
</testsuites>
```

**Usage:**
- Parsed by CI/CD tools
- Integrated with GitHub Actions
- Displayed in test dashboards

---

#### 2. HTML Coverage Report

**Location:** `htmlcov/index.html`  
**Purpose:** Detailed line-by-line coverage  
**Format:** Interactive HTML

**Opening the report:**
```bash
# Mac
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Windows
start htmlcov/index.html
```

**Features:**
- Color-coded coverage (green = covered, red = missed)
- File-by-file breakdown
- Line numbers with execution counts
- Branch coverage visualization
- Sortable columns

---

#### 3. Terminal Coverage Summary

**Location:** Console output  
**Purpose:** Quick coverage overview  
**Format:** Text table

```
---------- coverage: platform linux, python 3.11.5 -----------
Name                              Stmts   Miss  Cover
-----------------------------------------------------
orchestrator/main.go                245     18    93%
orchestrator/registry.go            156     12    92%
agents/cost_agent/main.py           423     65    85%
agents/performance_agent/main.py    389     58    85%
agents/resource_agent/main.py       367     52    86%
agents/application_agent/main.py    298     48    84%
portal/api/routes.py                234     45    81%
database/models.py                  189     12    94%
-----------------------------------------------------
TOTAL                              3847    578    85%
```

---

#### 4. Test Duration Report

**Location:** Pytest output  
**Purpose:** Identify slow tests  
**Format:** Text

**Viewing slowest tests:**
```bash
pytest --durations=10
```

**Output:**
```
slowest 10 test durations:
======================================
10.23s test_complete_customer_journey
8.45s test_spot_migration
7.89s test_cross_cloud_optimization
6.54s test_multi_agent_coordination
5.23s test_performance_optimization
```

---

#### 5. Failure Screenshots

**Location:** `screenshots/`  
**Purpose:** Debug UI test failures  
**Format:** PNG images

*Note: Only applicable if UI tests with Playwright/Selenium are added*

---

### Sample Complete Test Report

Here's what a full test run output looks like:

```
========================================
OptiInfra E2E System Tests
========================================
Started: 2025-10-27 14:30:00 UTC
Platform: linux, Python 3.11.5

=================== test session starts ====================
collected 43 items

E2E TESTS (8 scenarios)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tests/e2e/test_spot_migration.py::test_complete_spot_migration_workflow PASSED [2%]
tests/e2e/test_performance_optimization.py::test_kv_cache_optimization PASSED [5%]
tests/e2e/test_multi_agent_coordination.py::test_conflict_resolution PASSED [7%]
tests/e2e/test_quality_validation.py::test_quality_rollback PASSED [9%]
tests/e2e/test_complete_customer_journey.py::test_end_to_end_journey PASSED [12%]
tests/e2e/test_rollback_scenario.py::test_automatic_rollback PASSED [14%]
tests/e2e/test_conflict_resolution.py::test_priority_resolution PASSED [16%]
tests/e2e/test_cross_cloud_optimization.py::test_aws_gcp_optimization PASSED [19%]

INTEGRATION TESTS (20 tests)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tests/integration/test_agent_registration.py::test_agent_registration PASSED [21%]
tests/integration/test_agent_heartbeat.py::test_heartbeat_mechanism PASSED [23%]
tests/integration/test_orchestrator_routing.py::test_request_routing PASSED [26%]
... (17 more tests) ...

PERFORMANCE TESTS (5 tests)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tests/performance/test_concurrent_optimizations.py::test_5_concurrent PASSED [88%]
tests/performance/test_recommendation_latency.py::test_latency PASSED [91%]
... (3 more tests) ...

SECURITY TESTS (10 tests)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tests/security/test_unauthorized_access.py::test_no_token_denied PASSED [95%]
tests/security/test_customer_isolation.py::test_data_isolation PASSED [98%]
tests/security/test_sql_injection.py::test_injection_prevented PASSED [100%]

=================== 43 passed in 78.34s ====================

Coverage Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Component                    Stmts   Miss   Cover   Status
──────────────────────────────────────────────────────────
orchestrator/                 401     29     93%    ✅ PASS
agents/cost_agent/            423     65     85%    ✅ PASS
agents/performance_agent/     389     58     85%    ✅ PASS
agents/resource_agent/        367     52     86%    ✅ PASS
agents/application_agent/     298     48     84%    ✅ PASS
portal/                       234     45     81%    ✅ PASS
database/                     189     12     94%    ✅ PASS
──────────────────────────────────────────────────────────
TOTAL                        3847    578     85%    ✅ PASS

Test Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Tests:        43
Passed:             43  ✅
Failed:             0
Skipped:            0
Duration:           78.34 seconds
Coverage:           85% (target: 80%)  ✅

✅ TEST SUITE PASSED - All validation criteria met
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reports generated:
  • HTML Coverage: htmlcov/index.html
  • JUnit XML: test-results.xml
  • Logs: test-logs.txt

Finished: 2025-10-27 15:48:34 UTC
```

### Report Distribution

**After test completion:**

1. **Developers** - View HTML coverage locally
2. **QA Team** - Review test results in CI/CD
3. **DevOps** - Monitor test trends over time
4. **Management** - View coverage dashboard

### Metrics Tracked

Key metrics tracked across test runs:

- **Pass Rate** - % of tests passing
- **Coverage Trend** - Coverage over time
- **Test Duration** - Time to complete suite
- **Flaky Tests** - Tests with inconsistent results
- **Failure Rate** - % of test runs that fail

---

## Appendix: Quick Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests (complete suite) |
| `make test-e2e` | Run E2E tests only |
| `make test-integration` | Run integration tests |
| `make test-performance` | Run performance tests |
| `make test-security` | Run security tests |
| `make test-fast` | Run fast tests (skip slow E2E) |
| `make clean` | Clean up test environment |
| `make health-check` | Check all services health |
| `pytest -v` | Verbose test output |
| `pytest -vv` | Extra verbose output |
| `pytest -s` | Show print statements |
| `pytest -x` | Stop on first failure |
| `pytest -k 'spot'` | Run tests matching 'spot' |
| `pytest --lf` | Run last failed tests only |
| `pytest --ff` | Run failed first, then others |
| `pytest --durations=10` | Show 10 slowest tests |

### Directory Structure

```
optiinfra/
├── tests/
│   └── e2e/
│       ├── conftest.py                      # Fixtures
│       ├── test_spot_migration.py           # E2E scenario 1
│       ├── test_performance_optimization.py # E2E scenario 2
│       ├── test_multi_agent_coordination.py # E2E scenario 3
│       ├── test_quality_validation.py       # E2E scenario 4
│       ├── test_complete_customer_journey.py# E2E scenario 5
│       ├── test_rollback_scenario.py        # E2E scenario 6
│       ├── test_conflict_resolution.py      # E2E scenario 7
│       └── test_cross_cloud_optimization.py # E2E scenario 8
├── docker-compose.e2e.yml                   # Test environment
├── Makefile                                  # Build commands
├── pytest.ini                                # Pytest config
└── requirements-test.txt                     # Test dependencies
```

### Service Ports

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5433 | localhost:5433 |
| ClickHouse | 8124 | localhost:8124 |
| Redis | 6380 | localhost:6380 |
| Qdrant | 6334 | localhost:6334 |
| LocalStack (AWS) | 4567 | localhost:4567 |
| Orchestrator | 8001 | http://localhost:8001 |
| Portal | 3001 | http://localhost:3001 |

### Support Contacts

- **DevOps Team:** devops@optiinfra.com
- **QA Lead:** qa-lead@optiinfra.com
- **Slack Channel:** #eng-testing
- **Documentation:** https://docs.optiinfra.com/testing

### Important Links

- **GitHub Repository:** https://github.com/optiinfra/optiinfra
- **CI/CD Dashboard:** https://github.com/optiinfra/optiinfra/actions
- **Coverage Reports:** https://codecov.io/gh/optiinfra/optiinfra
- **Bug Tracker:** https://github.com/optiinfra/optiinfra/issues
- **Test Documentation:** https://docs.optiinfra.com/testing/e2e

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-27 | QA Team | Initial release |

---

**End of Document**

For questions or issues, contact the QA team or refer to the troubleshooting section.

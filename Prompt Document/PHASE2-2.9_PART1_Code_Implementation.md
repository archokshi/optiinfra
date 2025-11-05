# PHASE2-2.9 PART1: Tests (Unit + Integration) - Code Implementation Plan

**Phase**: PHASE2-2.9  
**Agent**: Performance Agent  
**Objective**: Comprehensive unit and integration testing to achieve >85% coverage  
**Estimated Time**: 35+25m (60 minutes total)  
**Priority**: HIGH  
**Dependencies**: All previous PHASE2 phases

---

## Overview

This phase focuses on achieving comprehensive test coverage (>85%) through additional unit tests and integration tests that validate end-to-end workflows across all Performance Agent components.

---

## Current Test Status

### Existing Tests (78 tests, 77% coverage)

**Unit Tests**:
- ✅ Health API (3 tests)
- ✅ Prometheus Parser (5 tests)
- ✅ vLLM Collector (2 tests)
- ✅ TGI Collector (4 tests)
- ✅ SGLang Collector (5 tests)
- ✅ Bottleneck Detector (5 tests)
- ✅ SLO Monitor (3 tests)
- ✅ Analysis Engine (3 tests)
- ✅ Analysis API (3 tests)
- ✅ KV Cache Optimizer (5 tests)
- ✅ Quantization Optimizer (3 tests)
- ✅ Batching Optimizer (5 tests)
- ✅ Optimization Engine (4 tests)
- ✅ Optimization API (3 tests)
- ✅ Workflow Models (6 tests)
- ✅ Workflow Manager (4 tests)
- ✅ Workflow API (6 tests)
- ✅ Config API (2 tests)
- ✅ Error Handlers (5 tests)

**Coverage Gaps**:
- ⚠️ Collectors: 21-22% (need more edge case tests)
- ⚠️ Optimizers: 22-25% (need more scenario tests)
- ⚠️ Workflow: 30% (complex async code)
- ⚠️ Integration: No end-to-end tests

---

## Testing Strategy

### 1. Unit Tests (Target: 85%+ coverage)
- Test individual functions and methods
- Mock external dependencies
- Cover edge cases and error scenarios
- Fast execution (<5 seconds total)

### 2. Integration Tests (Target: Key workflows)
- Test component interactions
- Minimal mocking
- Real workflow execution
- Slower execution (acceptable)

### 3. Test Categories

#### Category A: Missing Unit Tests
- Collector edge cases (timeout, invalid data, network errors)
- Optimizer edge cases (no bottlenecks, invalid config)
- Analysis engine edge cases (empty metrics, invalid thresholds)

#### Category B: Integration Tests
- End-to-end metrics collection → analysis → optimization
- Complete workflow execution (10% → 50% → 100%)
- Error recovery and rollback scenarios
- Multi-component coordination

---

## Implementation Plan

### Step 1: Additional Collector Tests (10 minutes)

#### 1.1 vLLM Collector Edge Cases
**File**: `tests/test_vllm_collector_extended.py`

```python
"""
Extended vLLM Collector Tests

Additional tests for edge cases and error scenarios.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.collectors.vllm_collector import VLLMCollector


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_timeout():
    """Test collection with timeout."""
    async with VLLMCollector(timeout=1) as collector:
        with patch('httpx.AsyncClient.get', side_effect=asyncio.TimeoutError()):
            with pytest.raises(Exception):
                await collector.collect("test", "http://localhost:8000/metrics")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_invalid_response():
    """Test collection with invalid response."""
    async with VLLMCollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = "invalid prometheus data"
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            # Should handle gracefully
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
            assert metrics is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_network_error():
    """Test collection with network error."""
    async with VLLMCollector() as collector:
        with patch('httpx.AsyncClient.get', side_effect=ConnectionError()):
            with pytest.raises(Exception):
                await collector.collect("test", "http://localhost:8000/metrics")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_metrics_empty():
    """Test extracting metrics from empty data."""
    collector = VLLMCollector()
    metrics = collector._extract_request_metrics([])
    assert metrics.success_total == 0
    assert metrics.failure_total == 0
```

#### 1.2 Similar Tests for TGI and SGLang
- Create `test_tgi_collector_extended.py`
- Create `test_sglang_collector_extended.py`
- Cover timeout, invalid data, network errors

---

### Step 2: Additional Optimizer Tests (8 minutes)

#### 2.1 Optimizer Edge Cases
**File**: `tests/test_optimizers_extended.py`

```python
"""
Extended Optimizer Tests

Additional tests for optimizer edge cases.
"""

import pytest
from src.optimization.kv_cache_optimizer import KVCacheOptimizer
from src.optimization.quantization_optimizer import QuantizationOptimizer
from src.optimization.batching_optimizer import BatchingOptimizer
from src.models.analysis import Bottleneck, BottleneckType, Severity


@pytest.mark.unit
def test_kv_cache_no_bottlenecks():
    """Test KV cache optimizer with no bottlenecks."""
    optimizer = KVCacheOptimizer()
    optimizations, config = optimizer.generate_optimizations([], "vllm", {})
    
    assert len(optimizations) == 0
    assert config is None


@pytest.mark.unit
def test_quantization_already_quantized():
    """Test quantization optimizer when already quantized."""
    optimizer = QuantizationOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.HIGH_LATENCY,
            severity=Severity.HIGH,
            description="High latency",
            metric_name="ttft",
            current_value=0.2,
            threshold_value=0.1,
            recommendation="Optimize"
        )
    ]
    
    # Already using INT8
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"quantization": "int8"}
    )
    
    assert len(optimizations) == 0
    assert config is None


@pytest.mark.unit
def test_batching_max_batch_size():
    """Test batching optimizer at maximum batch size."""
    optimizer = BatchingOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.QUEUE_BUILDUP,
            severity=Severity.HIGH,
            description="Queue buildup",
            metric_name="queue_size",
            current_value=15.0,
            threshold_value=10.0,
            recommendation="Increase batch"
        )
    ]
    
    # Already at max
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks,
        "vllm",
        {"max_batch_size": 256}
    )
    
    # Should still recommend but cap at 256
    assert len(optimizations) > 0
    if config:
        assert config.max_batch_size <= 256


@pytest.mark.unit
def test_optimizer_with_none_config():
    """Test optimizers with None config."""
    kv_optimizer = KVCacheOptimizer()
    quant_optimizer = QuantizationOptimizer()
    batch_optimizer = BatchingOptimizer()
    
    bottlenecks = []
    
    # Should handle None config gracefully
    kv_opts, _ = kv_optimizer.generate_optimizations(bottlenecks, "vllm", None)
    quant_opts, _ = quant_optimizer.generate_optimizations(bottlenecks, "vllm", None)
    batch_opts, _ = batch_optimizer.generate_optimizations(bottlenecks, "vllm", None)
    
    assert isinstance(kv_opts, list)
    assert isinstance(quant_opts, list)
    assert isinstance(batch_opts, list)
```

---

### Step 3: Integration Tests (12 minutes)

#### 3.1 End-to-End Metrics → Analysis → Optimization
**File**: `tests/integration/test_e2e_optimization.py`

```python
"""
End-to-End Optimization Integration Tests

Tests complete flow from metrics collection to optimization.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_optimization_flow():
    """Test complete flow: collect → analyze → optimize."""
    from src.collectors.vllm_collector import VLLMCollector
    from src.analysis.engine import AnalysisEngine
    from src.optimization.engine import OptimizationEngine
    
    # Mock metrics data
    mock_metrics_text = """
    # HELP vllm_request_success_total Total successful requests
    # TYPE vllm_request_success_total counter
    vllm_request_success_total 100
    
    # HELP vllm_time_to_first_token_seconds Time to first token
    # TYPE vllm_time_to_first_token_seconds histogram
    vllm_time_to_first_token_seconds_sum 15.0
    vllm_time_to_first_token_seconds_count 100
    
    # HELP vllm_num_requests_waiting Number of waiting requests
    # TYPE vllm_num_requests_waiting gauge
    vllm_num_requests_waiting 12
    """
    
    # Step 1: Collect metrics
    async with VLLMCollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = mock_metrics_text
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
    
    assert metrics is not None
    
    # Step 2: Analyze
    analysis_engine = AnalysisEngine()
    analysis_result = analysis_engine.analyze(metrics, "vllm")
    
    assert analysis_result is not None
    assert len(analysis_result.bottlenecks) > 0  # Should detect high TTFT and queue
    
    # Step 3: Generate optimizations
    optimization_engine = OptimizationEngine()
    optimization_plan = optimization_engine.generate_plan(analysis_result)
    
    assert optimization_plan is not None
    assert len(optimization_plan.optimizations) > 0
    assert optimization_plan.estimated_total_improvement is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_optimization_with_slo_targets():
    """Test optimization with custom SLO targets."""
    from src.collectors.vllm_collector import VLLMCollector
    from src.analysis.engine import AnalysisEngine
    from src.optimization.engine import OptimizationEngine
    from src.models.analysis import SLOTarget
    
    # Mock high latency metrics
    mock_metrics_text = """
    vllm_time_to_first_token_seconds_sum 20.0
    vllm_time_to_first_token_seconds_count 100
    """
    
    async with VLLMCollector() as collector:
        mock_response = AsyncMock()
        mock_response.text = mock_metrics_text
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            metrics = await collector.collect("test", "http://localhost:8000/metrics")
    
    # Analyze with strict SLO
    analysis_engine = AnalysisEngine()
    slo_targets = [
        SLOTarget(
            metric_name="ttft",
            target_value=0.1,
            comparison="less_than"
        )
    ]
    
    analysis_result = analysis_engine.analyze(metrics, "vllm", slo_targets)
    
    # Should have SLO violations
    assert len(analysis_result.slo_statuses) > 0
    assert not all(s.compliant for s in analysis_result.slo_statuses)
    
    # Generate optimizations
    optimization_engine = OptimizationEngine()
    optimization_plan = optimization_engine.generate_plan(analysis_result)
    
    # Should recommend optimizations to meet SLO
    assert len(optimization_plan.optimizations) > 0
```

#### 3.2 Complete Workflow Integration Test
**File**: `tests/integration/test_workflow_integration.py`

```python
"""
Workflow Integration Tests

Tests complete workflow execution.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_workflow_execution():
    """Test complete workflow from start to finish."""
    from src.workflows.manager import WorkflowManager
    from src.models.workflow import WorkflowRequest
    
    manager = WorkflowManager()
    
    # Mock collectors
    mock_metrics_text = """
    vllm_time_to_first_token_seconds_sum 10.0
    vllm_time_to_first_token_seconds_count 100
    """
    
    mock_response = AsyncMock()
    mock_response.text = mock_metrics_text
    mock_response.status_code = 200
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        # Start workflow
        request = WorkflowRequest(
            instance_id="test-instance",
            instance_type="vllm",
            requires_approval=False,
            auto_rollout=True,
            monitoring_duration_seconds=1  # Short for testing
        )
        
        result = await manager.start_workflow(request)
    
    # Verify workflow completed
    assert result.workflow_id is not None
    assert result.status.value in ["completed", "failed", "rolled_back"]
    
    # If completed, should have rollout history
    if result.status.value == "completed":
        assert len(result.rollout_history) == 3  # 10%, 50%, 100%
        assert result.final_health_score is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_with_approval():
    """Test workflow with approval gate."""
    from src.workflows.manager import WorkflowManager
    from src.models.workflow import WorkflowRequest, WorkflowStatus
    
    manager = WorkflowManager()
    
    # Create workflow requiring approval
    request = WorkflowRequest(
        instance_id="test-instance",
        instance_type="vllm",
        requires_approval=True,
        auto_rollout=False
    )
    
    # Note: This will hang waiting for approval in real execution
    # For testing, we'd need to mock the workflow execution
    # or test the approval mechanism separately
```

#### 3.3 API Integration Tests
**File**: `tests/integration/test_api_integration.py`

```python
"""
API Integration Tests

Tests API endpoints working together.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
def test_api_workflow_chain(client: TestClient):
    """Test chaining API calls: collect → analyze → optimize → workflow."""
    
    # Mock metrics response
    mock_metrics_text = """
    vllm_time_to_first_token_seconds_sum 15.0
    vllm_time_to_first_token_seconds_count 100
    vllm_num_requests_waiting 12
    """
    
    mock_response = AsyncMock()
    mock_response.text = mock_metrics_text
    mock_response.status_code = 200
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        # 1. Collect metrics
        collect_response = client.post(
            "/api/v1/collect/vllm",
            json={
                "instance_id": "test-instance",
                "endpoint": "http://localhost:8000/metrics"
            }
        )
        assert collect_response.status_code == 200
        
        # 2. Analyze
        analyze_response = client.post(
            "/api/v1/analyze",
            json={
                "instance_id": "test-instance",
                "instance_type": "vllm"
            }
        )
        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()
        assert "bottlenecks" in analysis_data
        
        # 3. Optimize
        optimize_response = client.post(
            "/api/v1/optimize",
            json={
                "instance_id": "test-instance",
                "instance_type": "vllm"
            }
        )
        assert optimize_response.status_code == 200
        optimization_data = optimize_response.json()
        assert "optimizations" in optimization_data
        
        # 4. Start workflow
        workflow_response = client.post(
            "/api/v1/workflows",
            json={
                "instance_id": "test-instance",
                "instance_type": "vllm",
                "requires_approval": False,
                "auto_rollout": True,
                "monitoring_duration_seconds": 1
            }
        )
        assert workflow_response.status_code == 201
        workflow_data = workflow_response.json()
        assert "workflow_id" in workflow_data
        
        # 5. Check workflow status
        workflow_id = workflow_data["workflow_id"]
        status_response = client.get(f"/api/v1/workflows/{workflow_id}")
        assert status_response.status_code == 200
```

---

### Step 4: Performance Tests (5 minutes)

#### 4.1 Load Testing
**File**: `tests/performance/test_load.py`

```python
"""
Performance/Load Tests

Tests system performance under load.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient


@pytest.mark.performance
def test_concurrent_health_checks(client: TestClient):
    """Test concurrent health check requests."""
    import concurrent.futures
    
    def make_request():
        response = client.get("/api/v1/health")
        return response.status_code
    
    # 100 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]
    
    # All should succeed
    assert all(status == 200 for status in results)


@pytest.mark.performance
def test_api_response_time(client: TestClient):
    """Test API response times."""
    import time
    
    endpoints = [
        "/api/v1/health",
        "/api/v1/config",
        "/api/v1/capabilities",
        "/api/v1/workflows"
    ]
    
    for endpoint in endpoints:
        start = time.time()
        response = client.get(endpoint)
        duration = time.time() - start
        
        assert response.status_code in [200, 404]  # 404 for workflows is ok
        assert duration < 1.0  # Should respond in < 1 second
```

---

## Success Criteria

### Coverage Targets
- **Overall Coverage**: >85% (currently 77%)
- **Collectors**: >80% (currently 21-22%)
- **Optimizers**: >80% (currently 22-25%)
- **Analysis**: >90% (currently 67-86%)
- **APIs**: >85% (currently 69-89%)
- **Workflows**: >50% (currently 30%, complex async)

### Test Counts
- **Unit Tests**: 100+ tests (currently 78)
- **Integration Tests**: 10+ tests (currently 0)
- **Performance Tests**: 5+ tests (currently 0)
- **Total**: 115+ tests

### Quality Metrics
- ✅ All tests pass
- ✅ No flaky tests
- ✅ Fast execution (unit tests < 10s)
- ✅ Clear test names and documentation
- ✅ Proper test isolation

---

## Test Organization

```
tests/
├── unit/                          # Unit tests (fast)
│   ├── test_collectors_extended.py
│   ├── test_optimizers_extended.py
│   ├── test_analysis_extended.py
│   └── ...
├── integration/                   # Integration tests (slower)
│   ├── test_e2e_optimization.py
│   ├── test_workflow_integration.py
│   └── test_api_integration.py
├── performance/                   # Performance tests
│   └── test_load.py
└── conftest.py                    # Shared fixtures
```

---

## Dependencies

### Testing Libraries
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support
- `httpx` - HTTP client for testing

### From Previous Phases
- All PHASE2 components (collectors, analysis, optimization, workflows, APIs)

---

## Next Steps

After achieving >85% coverage:
1. **PHASE2-2.10**: Documentation - Complete API docs, architecture docs
2. **PHASE2-2.11**: Deployment - Docker, Kubernetes configs
3. **PHASE2-3**: Integration with Orchestrator

---

**Status**: Ready for implementation  
**Estimated Completion**: 60 minutes  
**Target**: >85% coverage, 115+ tests

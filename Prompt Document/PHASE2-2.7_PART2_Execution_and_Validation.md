# PHASE2-2.7 PART2: LangGraph Workflow - Execution and Validation Plan

**Phase**: PHASE2-2.7  
**Agent**: Performance Agent  
**Objective**: Execute implementation and validate LangGraph workflow  
**Estimated Time**: 25 minutes  
**Priority**: HIGH

---

## Overview

This document outlines the execution steps for implementing the LangGraph workflow that orchestrates gradual rollout of performance optimizations with automatic monitoring and rollback capabilities.

---

## Execution Strategy

### Approach
1. **State-Driven**: LangGraph manages workflow state
2. **Gradual Rollout**: 10% → 50% → 100% deployment
3. **Health Monitoring**: Check health between stages
4. **Automatic Rollback**: Revert if health degrades
5. **Human-in-the-Loop**: Optional approval gate

### Priority Order
1. **Workflow Models** (High Priority)
   - State management models
   
2. **LangGraph Workflow** (High Priority)
   - State machine definition
   - Node implementations

3. **Workflow Manager** (High Priority)
   - Lifecycle management

4. **API Endpoints** (High Priority)
   - Workflow control endpoints

5. **Testing** (High Priority)
   - Comprehensive workflow tests

---

## Execution Plan

### Phase 1: Workflow Models (3 minutes)

#### Task 1.1: Create Workflow Models
**File**: `src/models/workflow.py`

**Models to create**:
- `WorkflowStatus` enum
- `RolloutStage` enum
- `RolloutStatus` model
- `WorkflowState` model
- `WorkflowRequest` model

**Validation**:
```python
from src.models.workflow import WorkflowState, WorkflowStatus
state = WorkflowState(
    workflow_id="test-123",
    instance_id="localhost:8000",
    instance_type="vllm",
    status=WorkflowStatus.PENDING
)
print(state.model_dump_json())
```

---

### Phase 2: LangGraph Workflow (10 minutes)

#### Task 2.1: Install LangGraph
```bash
pip install langgraph
```

#### Task 2.2: Create Workflow Directory
```bash
mkdir src/workflows
```

#### Task 2.3: Create Workflow Implementation
**File**: `src/workflows/optimization_workflow.py`

**Components**:
- `OptimizationWorkflow` class
- State machine graph
- Node implementations:
  - `collect_metrics`
  - `analyze_performance`
  - `generate_optimizations`
  - `await_approval`
  - `rollout_stage` (10%, 50%, 100%)
  - `monitor_stage`
  - `complete`
  - `rollback`
- Conditional routing logic

---

### Phase 3: Workflow Manager (3 minutes)

#### Task 3.1: Create Workflow Manager
**File**: `src/workflows/manager.py`

**Components**:
- `WorkflowManager` class
- `start_workflow()` method
- `get_workflow()` method
- `approve_workflow()` method
- `reject_workflow()` method
- In-memory state storage

---

### Phase 4: API Endpoints (2 minutes)

#### Task 4.1: Create Workflow API
**File**: `src/api/workflows.py`

**Endpoints**:
- `POST /api/v1/workflows` - Start workflow
- `GET /api/v1/workflows/{id}` - Get workflow status
- `POST /api/v1/workflows/{id}/approve` - Approve workflow
- `POST /api/v1/workflows/{id}/reject` - Reject workflow

#### Task 4.2: Update Main App
**File**: `src/main.py`

Add workflow router

---

### Phase 5: Testing (7 minutes)

#### Task 5.1: Create Tests
**Files**:
- `tests/test_workflow_models.py`
- `tests/test_optimization_workflow.py`
- `tests/test_workflow_manager.py`
- `tests/test_workflow_api.py`

---

## Validation Plan

### Step 1: Unit Tests

```bash
# Run workflow tests
pytest tests/test_workflow_models.py -v
pytest tests/test_optimization_workflow.py -v
pytest tests/test_workflow_manager.py -v
pytest tests/test_workflow_api.py -v

# Run all tests
pytest tests/ -v
```

---

### Step 2: Manual Workflow Testing

#### 2.1 Test Complete Workflow

**Start Workflow**:
```bash
curl -X POST http://localhost:8002/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "localhost:8000",
    "instance_type": "vllm",
    "requires_approval": false,
    "auto_rollout": true,
    "monitoring_duration_seconds": 10,
    "health_threshold": 0.9
  }'
```

**Expected Response**:
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "instance_id": "localhost:8000",
  "instance_type": "vllm",
  "status": "completed",
  "created_at": "2025-01-24T...",
  "analysis_result": {
    "bottlenecks": [...],
    "overall_health_score": 75.0
  },
  "optimization_plan": {
    "optimizations": [...],
    "estimated_total_improvement": "30-50%"
  },
  "rollout_history": [
    {
      "stage": "10%",
      "status": "success",
      "health_score_before": 75.0,
      "health_score_after": 85.0
    },
    {
      "stage": "50%",
      "status": "success",
      "health_score_before": 85.0,
      "health_score_after": 90.0
    },
    {
      "stage": "100%",
      "status": "success",
      "health_score_before": 90.0,
      "health_score_after": 95.0
    }
  ],
  "final_health_score": 95.0
}
```

---

#### 2.2 Test Workflow with Approval

**Start Workflow (Requires Approval)**:
```bash
WORKFLOW_ID=$(curl -X POST http://localhost:8002/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "localhost:8000",
    "instance_type": "vllm",
    "requires_approval": true
  }' | jq -r '.workflow_id')

echo "Workflow ID: $WORKFLOW_ID"
```

**Check Status**:
```bash
curl http://localhost:8002/api/v1/workflows/$WORKFLOW_ID
```

**Expected**: Status should be `awaiting_approval`

**Approve Workflow**:
```bash
curl -X POST http://localhost:8002/api/v1/workflows/$WORKFLOW_ID/approve \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "admin"}'
```

**Check Final Status**:
```bash
curl http://localhost:8002/api/v1/workflows/$WORKFLOW_ID
```

**Expected**: Status should progress to `completed`

---

#### 2.3 Test Rollback Scenario

**Simulate Unhealthy Instance**:
```bash
# This would require modifying the workflow to simulate health degradation
# For testing, we can mock the health check to return low scores
```

**Expected Behavior**:
- Workflow should detect health drop
- Automatically trigger rollback
- Status should be `rolled_back`
- Error message should explain reason

---

### Step 3: Integration Testing

#### 3.1 Test End-to-End Flow

**Complete Flow**:
```bash
# 1. Start workflow
WORKFLOW_ID=$(curl -X POST http://localhost:8002/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "localhost:8000",
    "instance_type": "vllm",
    "requires_approval": false
  }' | jq -r '.workflow_id')

# 2. Poll status
while true; do
  STATUS=$(curl -s http://localhost:8002/api/v1/workflows/$WORKFLOW_ID | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] || [ "$STATUS" = "rolled_back" ]; then
    break
  fi
  
  sleep 5
done

# 3. Get final result
curl http://localhost:8002/api/v1/workflows/$WORKFLOW_ID | jq
```

---

## Validation Checklist

### Functional Validation
- [ ] Workflow starts successfully
- [ ] Metrics collection works
- [ ] Analysis runs correctly
- [ ] Optimizations generated
- [ ] Approval gate works (if enabled)
- [ ] 10% rollout executes
- [ ] Health monitoring works
- [ ] 50% rollout executes
- [ ] 100% rollout executes
- [ ] Workflow completes successfully
- [ ] Rollback works on health degradation
- [ ] State persists correctly

### Code Quality
- [ ] All files have proper docstrings
- [ ] Type hints are used throughout
- [ ] Code follows Python best practices
- [ ] No linting errors

### Testing
- [ ] All unit tests pass
- [ ] Test coverage > 80%
- [ ] Integration tests work
- [ ] Workflow executes end-to-end

### Performance
- [ ] Workflow completes in reasonable time
- [ ] No memory leaks
- [ ] State management efficient

---

## Success Metrics

### Test Coverage
- **Target**: > 80% coverage for new code
- **Critical Paths**: 100% coverage
  - Workflow state machine
  - Rollout stages
  - Health monitoring
  - Rollback logic

### Performance Metrics
- **Workflow Duration**: < 20 minutes (with monitoring)
- **State Transitions**: < 1 second per transition
- **Memory Usage**: < 200 MB

---

## Troubleshooting

### Common Issues

#### Issue 1: LangGraph Import Errors
**Symptom**: `ModuleNotFoundError: No module named 'langgraph'`

**Solution**:
```bash
pip install langgraph
```

#### Issue 2: Workflow Hangs
**Symptom**: Workflow stuck in one state

**Solution**:
- Check node implementations for blocking calls
- Verify conditional routing logic
- Add timeout to monitoring stages

#### Issue 3: State Not Persisting
**Symptom**: Workflow state lost between calls

**Solution**:
- Verify MemorySaver is configured
- Check state updates in each node
- Ensure state is returned from nodes

#### Issue 4: Rollback Not Triggering
**Symptom**: Workflow continues despite low health

**Solution**:
- Check health threshold configuration
- Verify health score calculation
- Review conditional routing logic

---

## Post-Validation Steps

### After Successful Validation

1. **Run Full Test Suite**:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

2. **Check Coverage**:
```bash
start htmlcov/index.html  # Windows
```

3. **Test Workflow Scenarios**:
   - ✅ Happy path (all stages succeed)
   - ✅ Approval required
   - ✅ Approval rejected
   - ✅ Rollback at 10%
   - ✅ Rollback at 50%
   - ✅ Complete success

4. **Create Completion Report**

5. **Commit Code**:
```bash
git add .
git commit -m "feat: implement PHASE2-2.7 LangGraph Workflow"
git push origin main
```

---

## Next Steps

### Immediate
1. ✅ Validate all functionality
2. ✅ Run complete test suite
3. ✅ Test all workflow scenarios
4. ✅ Create completion report
5. ✅ Commit and push code

### Next Phase: PHASE2-2.8
**Integration Testing**: End-to-end testing of complete Performance Agent

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Workflow Models | 3 min | Pending |
| LangGraph Workflow | 10 min | Pending |
| Workflow Manager | 3 min | Pending |
| API Endpoints | 2 min | Pending |
| Testing & Validation | 7 min | Pending |
| **Total** | **25 min** | **Pending** |

---

## Deliverables

### Code Deliverables
- ✅ Workflow state models
- ✅ LangGraph workflow implementation
- ✅ Workflow manager
- ✅ API endpoints
- ✅ Comprehensive tests

### Documentation Deliverables
- ✅ Code documentation (docstrings)
- ✅ API documentation (OpenAPI)
- ✅ Workflow diagram
- ✅ Test documentation

---

## Workflow Execution Flow

### Visual Flow

```
User Request
    ↓
POST /api/v1/workflows
    ↓
┌─────────────────────────────────────────┐
│ 1. Collect Metrics (10s)                │
│    - Query vLLM/TGI/SGLang metrics      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. Analyze Performance (5s)             │
│    - Detect bottlenecks                 │
│    - Calculate health score             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. Generate Optimizations (5s)          │
│    - KV cache, quantization, batching   │
│    - Estimate improvements              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. Approval Gate (if required)          │
│    - Wait for human approval            │
│    - Can be skipped with auto_rollout   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. Rollout 10% (30s)                    │
│    - Apply config to 10% of instances   │
│    - Monitor for 5 minutes              │
│    - Check health score                 │
└─────────────────────────────────────────┘
    ↓ (if healthy)
┌─────────────────────────────────────────┐
│ 6. Rollout 50% (30s)                    │
│    - Apply config to 50% of instances   │
│    - Monitor for 5 minutes              │
│    - Check health score                 │
└─────────────────────────────────────────┘
    ↓ (if healthy)
┌─────────────────────────────────────────┐
│ 7. Rollout 100% (30s)                   │
│    - Apply config to all instances      │
│    - Final validation                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 8. Complete                             │
│    - Record final health score          │
│    - Store optimization results         │
│    - Return success                     │
└─────────────────────────────────────────┘

Total Time: ~20 minutes (with 5-min monitoring per stage)
```

---

## Notes

### Important Considerations
1. **Monitoring Duration**: Configurable per stage (default 5 minutes)
2. **Health Threshold**: Configurable (default 90%)
3. **Approval Gate**: Optional, can be disabled
4. **Rollback**: Automatic on health degradation
5. **State Persistence**: Uses LangGraph MemorySaver

### LangGraph Features Used
- **StateGraph**: Define workflow structure
- **Conditional Edges**: Dynamic routing based on state
- **MemorySaver**: Persist workflow state
- **Async Support**: Non-blocking execution
- **Human-in-the-Loop**: Approval gates

---

## Example Workflow States

### State 1: Awaiting Approval
```json
{
  "workflow_id": "abc-123",
  "status": "awaiting_approval",
  "analysis_result": {...},
  "optimization_plan": {...},
  "requires_approval": true,
  "approved": null
}
```

### State 2: Rolling Out 10%
```json
{
  "workflow_id": "abc-123",
  "status": "rolling_out",
  "current_stage": "10%",
  "rollout_history": [
    {
      "stage": "10%",
      "status": "in_progress",
      "started_at": "2025-01-24T...",
      "health_score_before": 75.0
    }
  ]
}
```

### State 3: Completed
```json
{
  "workflow_id": "abc-123",
  "status": "completed",
  "rollout_history": [
    {"stage": "10%", "status": "success", "health_score_after": 85.0},
    {"stage": "50%", "status": "success", "health_score_after": 90.0},
    {"stage": "100%", "status": "success", "health_score_after": 95.0}
  ],
  "final_health_score": 95.0,
  "total_improvement": "30-50% overall performance improvement"
}
```

### State 4: Rolled Back
```json
{
  "workflow_id": "abc-123",
  "status": "rolled_back",
  "current_stage": "50%",
  "rollout_history": [
    {"stage": "10%", "status": "success", "health_score_after": 85.0},
    {"stage": "50%", "status": "failed", "health_score_after": 70.0}
  ],
  "error_message": "Health score dropped below threshold (70.0 < 90.0), rolled back changes"
}
```

---

**Status**: Ready for execution  
**Estimated Completion**: 25 minutes  
**Next Phase**: PHASE2-2.8 - Integration Testing

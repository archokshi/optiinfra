# PHASE4-4.5 PART2: LangGraph Workflow - Execution and Validation

**Phase**: PHASE4-4.5  
**Agent**: Application Agent  
**Objective**: Execute and validate LangGraph workflow implementation  
**Estimated Time**: 15 minutes  
**Priority**: HIGH

---

## Pre-Execution Checklist

- [ ] PHASE4-4.5_PART1 documentation reviewed
- [ ] PHASE4-4.4 complete (Validation Engine working)
- [ ] Application Agent running on port 8004
- [ ] Python 3.11+ installed
- [ ] langgraph library available

---

## Execution Steps

### Step 1: Install LangGraph (2 minutes)

```bash
cd services/application-agent

# Install langgraph
pip install langgraph

# Verify installation
python -c "import langgraph; print(langgraph.__version__)"
```

### Step 2: Create Workflow Directory (1 minute)

```bash
# Create workflows directory
mkdir -p src/workflows

# Verify structure
ls -la src/
```

### Step 3: Implement Workflow State (3 minutes)

Create `src/workflows/state.py` with:
- WorkflowStatus enum
- WorkflowState TypedDict
- WorkflowResult model

### Step 4: Implement Workflow Nodes (8 minutes)

Create `src/workflows/quality_validation_workflow.py` with:
- 7 workflow nodes
- LangGraph graph construction
- Conditional routing logic
- Error handling

### Step 5: Create Workflow API (3 minutes)

Create `src/api/workflow.py` with 3 endpoints

### Step 6: Update Main Application (1 minute)

Update `src/main.py`:
```python
from .api import health, quality, regression, validation, workflow
app.include_router(workflow.router)
```

### Step 7: Create Tests (5 minutes)

Create `tests/test_workflow.py` with 5+ tests

### Step 8: Run Tests (2 minutes)

```bash
pytest tests/test_workflow.py -v
```

**Expected**: All tests passing

---

## Validation Steps

### 1. Start Application (1 minute)

```bash
python -m uvicorn src.main:app --port 8004 --reload
```

### 2. Run Approval Workflow (3 minutes)

```bash
curl -X POST http://localhost:8004/workflow/validate \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-oss-20b",
    "prompt": "What is the capital of France?",
    "response": "The capital of France is Paris."
  }'
```

**Expected Response**:
```json
{
  "request_id": "...",
  "status": "completed",
  "decision": "approve",
  "quality_metrics": {
    "overall_quality": 85.0
  },
  "validation_result": {
    "decision": "approve",
    "confidence": 0.95
  }
}
```

### 3. Run Rejection Workflow (3 minutes)

```bash
curl -X POST http://localhost:8004/workflow/validate \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-oss-20b",
    "prompt": "What is 2+2?",
    "response": "I dont know"
  }'
```

**Expected**: `decision: "reject"` due to low quality

### 4. Check Workflow Status (2 minutes)

```bash
curl http://localhost:8004/workflow/status/<request_id>
```

**Expected**:
```json
{
  "request_id": "...",
  "status": "completed",
  "current_step": "execute_approval",
  "decision": "approve"
}
```

### 5. Get Workflow History (2 minutes)

```bash
curl http://localhost:8004/workflow/history?limit=10
```

**Expected**: List of recent workflow executions

### 6. Test API Documentation (1 minute)

```bash
# Open in browser
start http://localhost:8004/docs
```

Verify 3 new workflow endpoints listed

---

## Validation Checklist

### Workflow Execution ✅
- [ ] Workflow runs end-to-end
- [ ] All nodes execute correctly
- [ ] State transitions properly
- [ ] Conditional routing works
- [ ] Error handling functional

### Decision Routing ✅
- [ ] Approve path works
- [ ] Reject path works
- [ ] Manual review path works
- [ ] Baseline creation works
- [ ] Routing logic correct

### API Endpoints ✅
- [ ] POST /workflow/validate works
- [ ] GET /workflow/status/{id} works
- [ ] GET /workflow/history works

### Tests ✅
- [ ] All 5+ tests passing
- [ ] No test failures
- [ ] Coverage > 70%

---

## Test Scenarios

### Scenario 1: High Quality Response
**Input**: Good prompt + good response  
**Expected**: Approve, confidence > 0.9, workflow completes

### Scenario 2: Low Quality Response
**Input**: Good prompt + poor response  
**Expected**: Reject, quality < 60, workflow completes

### Scenario 3: Borderline Quality
**Input**: Good prompt + mediocre response  
**Expected**: Manual review or approve, confidence < 0.8

### Scenario 4: No Baseline
**Input**: New model (no baseline)  
**Expected**: Create baseline, workflow ends early

### Scenario 5: Error Handling
**Input**: Invalid data  
**Expected**: Error captured, workflow fails gracefully

---

## Performance Validation

| Metric | Target | Validation |
|--------|--------|------------|
| Workflow execution | < 500ms | Measure with curl |
| Quality analysis | < 100ms | Check logs |
| Regression check | < 50ms | Check logs |
| Decision making | < 50ms | Check logs |
| Total latency | < 600ms | End-to-end timing |

---

## Workflow Observability

### Logging
```bash
# Check workflow logs
tail -f logs/application-agent.log | grep "workflow"
```

**Expected**: Step-by-step execution logs

### State Tracking
- [ ] State updates logged
- [ ] Transitions visible
- [ ] Errors captured
- [ ] Final state recorded

---

## Troubleshooting

### Issue 1: LangGraph Import Error
```bash
# Install langgraph
pip install langgraph
```

### Issue 2: State Type Errors
- Check TypedDict definitions
- Verify all required fields present
- Ensure type consistency

### Issue 3: Routing Errors
- Verify conditional edge logic
- Check return values from routing functions
- Ensure all paths lead to END

### Issue 4: Workflow Hangs
- Check for infinite loops
- Verify all edges defined
- Ensure END nodes reachable

---

## Integration Validation

### With Quality Monitoring
- [ ] Quality analysis integrated
- [ ] Metrics collected correctly
- [ ] Scores calculated properly

### With Regression Detection
- [ ] Baseline checked/created
- [ ] Regression detected accurately
- [ ] Alerts generated if needed

### With Validation Engine
- [ ] Decisions made correctly
- [ ] Confidence calculated
- [ ] Recommendations generated

---

## Success Criteria

- [x] All files created
- [x] LangGraph workflow working
- [x] 7 nodes functional
- [x] Conditional routing correct
- [x] 3 API endpoints working
- [x] 5+ tests passing
- [x] Workflow time < 500ms
- [x] API docs updated
- [x] Ready for PHASE4-4.6

---

**LangGraph Workflow validated and ready!** ✅

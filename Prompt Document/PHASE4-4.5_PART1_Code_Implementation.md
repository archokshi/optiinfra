# PHASE4-4.5 PART1: LangGraph Workflow - Code Implementation Plan

**Phase**: PHASE4-4.5  
**Agent**: Application Agent  
**Objective**: Implement LangGraph workflow for quality validation  
**Estimated Time**: 25 minutes implementation + 15 minutes validation = 40 minutes  
**Priority**: HIGH  
**Dependencies**: PHASE4-4.4 (Validation Engine)

---

## Overview

Implement a LangGraph-based workflow that orchestrates the complete quality validation process: quality analysis → regression detection → validation decision → execution. This provides a stateful, observable workflow for validating optimization changes.

---

## Core Features

### 1. Quality Validation Workflow
- **State Management**: Track workflow state across steps
- **Step Orchestration**: Coordinate quality, regression, and validation
- **Decision Routing**: Route based on validation decision
- **Error Handling**: Handle failures gracefully
- **Observability**: Log and track workflow execution

### 2. Workflow Steps
1. **Analyze Quality** - Analyze current quality metrics
2. **Check Baseline** - Verify baseline exists
3. **Detect Regression** - Check for quality regression
4. **Make Decision** - Approve/reject/manual review
5. **Execute Action** - Apply approved changes or rollback

### 3. State Schema
```python
class WorkflowState:
    - request_id: str
    - model_name: str
    - prompt: str
    - response: str
    - quality_metrics: QualityMetrics
    - baseline: Baseline
    - regression_result: RegressionResult
    - validation_result: ValidationResult
    - decision: ValidationDecision
    - status: WorkflowStatus
    - errors: List[str]
```

### 4. Workflow Graph
```
START
  ↓
Analyze Quality
  ↓
Check Baseline → [No Baseline] → Create Baseline → END
  ↓ [Has Baseline]
Detect Regression
  ↓
Make Decision
  ↓
[APPROVE] → Execute Approval → END
  ↓
[REJECT] → Execute Rejection → END
  ↓
[MANUAL_REVIEW] → Flag for Review → END
```

---

## Implementation Plan

### Step 1: Create Workflow State Models (5 minutes)

**File**: `src/workflows/state.py`

Models:
- `WorkflowStatus` - Workflow status enum
- `WorkflowState` - Complete workflow state
- `WorkflowResult` - Final workflow result

---

### Step 2: Implement Workflow Nodes (10 minutes)

**File**: `src/workflows/quality_validation_workflow.py`

Nodes:
- `analyze_quality_node()` - Analyze quality
- `check_baseline_node()` - Check/create baseline
- `detect_regression_node()` - Detect regression
- `make_decision_node()` - Make validation decision
- `execute_approval_node()` - Execute approved change
- `execute_rejection_node()` - Execute rejection/rollback
- `flag_for_review_node()` - Flag for manual review

---

### Step 3: Build LangGraph Workflow (5 minutes)

**File**: `src/workflows/quality_validation_workflow.py`

Graph Construction:
```python
from langgraph.graph import StateGraph

workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("analyze_quality", analyze_quality_node)
workflow.add_node("check_baseline", check_baseline_node)
workflow.add_node("detect_regression", detect_regression_node)
workflow.add_node("make_decision", make_decision_node)
workflow.add_node("execute_approval", execute_approval_node)
workflow.add_node("execute_rejection", execute_rejection_node)
workflow.add_node("flag_for_review", flag_for_review_node)

# Add edges
workflow.set_entry_point("analyze_quality")
workflow.add_edge("analyze_quality", "check_baseline")
workflow.add_conditional_edges(
    "check_baseline",
    lambda state: "create" if not state.baseline else "continue",
    {"create": END, "continue": "detect_regression"}
)
workflow.add_edge("detect_regression", "make_decision")
workflow.add_conditional_edges(
    "make_decision",
    lambda state: state.decision,
    {
        "approve": "execute_approval",
        "reject": "execute_rejection",
        "manual_review": "flag_for_review"
    }
)
workflow.add_edge("execute_approval", END)
workflow.add_edge("execute_rejection", END)
workflow.add_edge("flag_for_review", END)

# Compile
app = workflow.compile()
```

---

### Step 4: Create Workflow API (3 minutes)

**File**: `src/api/workflow.py`

Endpoints:
- `POST /workflow/validate` - Run validation workflow
- `GET /workflow/status/{id}` - Get workflow status
- `GET /workflow/history` - Get workflow history

---

### Step 5: Update Main Application (2 minutes)

**File**: `src/main.py`

- Import workflow router
- Include workflow router

---

### Step 6: Create Tests (5 minutes)

**File**: `tests/test_workflow.py`

Tests:
- `test_workflow_approve()`
- `test_workflow_reject()`
- `test_workflow_manual_review()`
- `test_workflow_no_baseline()`
- `test_workflow_error_handling()`

---

## Workflow State Schema

### WorkflowState
```python
{
  "request_id": "uuid",
  "model_name": "gpt-oss-20b",
  "prompt": "What is 2+2?",
  "response": "2+2 equals 4",
  "quality_metrics": {
    "overall_quality": 85.0,
    "relevance": {"score": 90.0},
    "coherence": {"score": 88.0},
    "hallucination": {"hallucination_rate": 5.0}
  },
  "baseline": {
    "baseline_id": "uuid",
    "metrics": {"average_quality": 83.0}
  },
  "regression_result": {
    "regression_detected": false,
    "severity": "none"
  },
  "validation_result": {
    "decision": "approve",
    "confidence": 0.95
  },
  "status": "completed",
  "errors": []
}
```

---

## Node Implementation Details

### 1. Analyze Quality Node
```python
def analyze_quality_node(state: WorkflowState) -> WorkflowState:
    """Analyze quality of response."""
    request = QualityRequest(
        prompt=state.prompt,
        response=state.response,
        model_name=state.model_name
    )
    metrics = quality_collector.collect_metrics(request)
    state.quality_metrics = metrics
    state.status = WorkflowStatus.ANALYZING
    return state
```

### 2. Check Baseline Node
```python
def check_baseline_node(state: WorkflowState) -> WorkflowState:
    """Check if baseline exists, create if not."""
    baseline = baseline_storage.get_by_model(state.model_name)
    if not baseline:
        # Create baseline
        config = BaselineConfig(
            model_name=state.model_name,
            sample_size=10
        )
        baseline = regression_detector.establish_baseline(config)
    state.baseline = baseline
    state.status = WorkflowStatus.BASELINE_CHECKED
    return state
```

### 3. Detect Regression Node
```python
def detect_regression_node(state: WorkflowState) -> WorkflowState:
    """Detect quality regression."""
    request = RegressionDetectionRequest(
        model_name=state.model_name,
        current_quality=state.quality_metrics.overall_quality
    )
    result = regression_detector.detect_regression(request)
    state.regression_result = result
    state.status = WorkflowStatus.REGRESSION_CHECKED
    return state
```

### 4. Make Decision Node
```python
def make_decision_node(state: WorkflowState) -> WorkflowState:
    """Make validation decision."""
    request = ValidationRequest(
        name=f"Validation {state.request_id}",
        model_name=state.model_name,
        baseline_quality=state.baseline.metrics.average_quality,
        new_quality=state.quality_metrics.overall_quality
    )
    result = approval_engine.validate_change(
        request,
        p_value=state.regression_result.z_score
    )
    state.validation_result = result
    state.decision = result.decision
    state.status = WorkflowStatus.DECISION_MADE
    return state
```

---

## Conditional Routing

### Baseline Check Routing
```python
def route_baseline(state: WorkflowState) -> str:
    """Route based on baseline existence."""
    if state.baseline is None:
        return "create_baseline"
    return "continue"
```

### Decision Routing
```python
def route_decision(state: WorkflowState) -> str:
    """Route based on validation decision."""
    return state.decision.value  # "approve", "reject", or "manual_review"
```

---

## Error Handling

```python
def handle_error(state: WorkflowState, error: Exception) -> WorkflowState:
    """Handle workflow errors."""
    state.errors.append(str(error))
    state.status = WorkflowStatus.FAILED
    logger.error(f"Workflow {state.request_id} failed: {error}")
    return state
```

---

## Files to Create

1. `src/workflows/__init__.py` (~5 lines)
2. `src/workflows/state.py` (~80 lines)
3. `src/workflows/quality_validation_workflow.py` (~250 lines)
4. `src/api/workflow.py` (~150 lines)
5. `tests/test_workflow.py` (~200 lines)

**Total**: ~685 lines

---

## Success Criteria

- [ ] LangGraph workflow implemented
- [ ] 7 workflow nodes functional
- [ ] State management working
- [ ] Conditional routing correct
- [ ] Error handling robust
- [ ] 3 API endpoints functional
- [ ] 5+ tests passing
- [ ] Workflow execution < 500ms

---

**Ready for implementation!**

# PHASE2-2.5 PART2: Analysis Engine - Execution and Validation Plan

**Phase**: PHASE2-2.5  
**Agent**: Performance Agent  
**Objective**: Execute implementation and validate analysis engine  
**Estimated Time**: 20 minutes  
**Priority**: HIGH

---

## Overview

This document outlines the execution steps for implementing the Analysis Engine that detects bottlenecks and monitors SLOs.

---

## Execution Strategy

### Approach
1. **Modular Design**: Separate bottleneck detection, SLO monitoring, and analysis engine
2. **Configurable Thresholds**: Allow custom threshold configuration
3. **Multi-Instance Support**: Support vLLM, TGI, and SGLang
4. **Actionable Insights**: Generate specific recommendations

### Priority Order
1. **Analysis Models** (High Priority)
   - Bottleneck and SLO models
   
2. **Bottleneck Detector** (High Priority)
   - Detection logic for all instance types

3. **SLO Monitor** (High Priority)
   - SLO compliance checking

4. **Analysis Engine** (High Priority)
   - Orchestrate detection and monitoring

5. **API Endpoints** (High Priority)
   - Analysis endpoints

6. **Testing** (High Priority)
   - Comprehensive tests

---

## Execution Plan

### Phase 1: Analysis Models (3 minutes)

#### Task 1.1: Create Analysis Models
**File**: `src/models/analysis.py`

**Models to create**:
- `BottleneckType` enum
- `Severity` enum
- `Bottleneck` model
- `SLOTarget` model
- `SLOStatus` model
- `AnalysisResult` model
- `AnalysisRequest` model

**Validation**:
```python
from src.models.analysis import AnalysisResult, Bottleneck
result = AnalysisResult(
    instance_id="test",
    instance_type="vllm",
    bottlenecks=[],
    slo_statuses=[],
    overall_health_score=95.0,
    recommendations=[]
)
print(result.model_dump_json())
```

---

### Phase 2: Bottleneck Detector (5 minutes)

#### Task 2.1: Create Bottleneck Detector
**File**: `src/analysis/bottleneck_detector.py`

**Components**:
- `BottleneckDetector` class
- Default thresholds
- Detection methods:
  - `detect_vllm_bottlenecks()`
  - `detect_tgi_bottlenecks()`
  - `detect_sglang_bottlenecks()`
- Severity calculation

**Create directory**:
```bash
mkdir src/analysis
```

---

### Phase 3: SLO Monitor (4 minutes)

#### Task 3.1: Create SLO Monitor
**File**: `src/analysis/slo_monitor.py`

**Components**:
- `SLOMonitor` class
- `check_slos()` method
- Metric extraction
- Compliance checking
- Deviation calculation

---

### Phase 4: Analysis Engine (3 minutes)

#### Task 4.1: Create Analysis Engine
**File**: `src/analysis/engine.py`

**Components**:
- `AnalysisEngine` class
- `analyze()` method
- Health score calculation
- Recommendation generation

---

### Phase 5: API Endpoints (2 minutes)

#### Task 5.1: Create Analysis API
**File**: `src/api/analysis.py`

**Endpoints**:
- `POST /api/v1/analyze` - Analyze instance

#### Task 5.2: Update Main App
**File**: `src/main.py`

Add analysis router

---

### Phase 6: Testing (3 minutes)

#### Task 6.1: Create Tests
**Files**:
- `tests/test_bottleneck_detector.py`
- `tests/test_slo_monitor.py`
- `tests/test_analysis_engine.py`
- `tests/test_analysis_api.py`

---

## Validation Plan

### Step 1: Unit Tests

```bash
# Run analysis tests
pytest tests/test_bottleneck_detector.py -v
pytest tests/test_slo_monitor.py -v
pytest tests/test_analysis_engine.py -v
pytest tests/test_analysis_api.py -v

# Run all tests
pytest tests/ -v
```

---

### Step 2: Manual API Testing

#### 2.1 Test Bottleneck Detection

**Request**:
```bash
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "localhost:8000",
    "instance_type": "vllm",
    "slo_targets": [
      {
        "name": "P95 TTFT",
        "metric": "request_metrics.time_to_first_token_seconds",
        "target_value": 0.1,
        "comparison": "<",
        "description": "95th percentile TTFT under 100ms"
      }
    ]
  }'
```

**Expected Response**:
```json
{
  "instance_id": "localhost:8000",
  "instance_type": "vllm",
  "timestamp": "2025-01-24T...",
  "bottlenecks": [
    {
      "type": "high_latency",
      "severity": "medium",
      "description": "Time to First Token exceeds threshold",
      "metric_name": "time_to_first_token_seconds",
      "current_value": 0.15,
      "threshold_value": 0.1,
      "recommendation": "Consider reducing batch size or enabling prefix caching",
      "timestamp": "2025-01-24T..."
    }
  ],
  "slo_statuses": [
    {
      "target": {
        "name": "P95 TTFT",
        "metric": "request_metrics.time_to_first_token_seconds",
        "target_value": 0.1,
        "comparison": "<"
      },
      "current_value": 0.15,
      "is_compliant": false,
      "deviation_percent": 50.0,
      "timestamp": "2025-01-24T..."
    }
  ],
  "overall_health_score": 75.0,
  "recommendations": [
    "Consider reducing batch size or enabling prefix caching",
    "Address P95 TTFT SLO violation: current 0.15, target 0.10"
  ]
}
```

---

### Step 3: Integration Testing

#### 3.1 Test with Different Instance Types

**vLLM**:
```bash
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "localhost:8000", "instance_type": "vllm"}'
```

**TGI**:
```bash
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "localhost:8080", "instance_type": "tgi"}'
```

**SGLang**:
```bash
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "localhost:30000", "instance_type": "sglang"}'
```

---

## Validation Checklist

### Functional Validation
- [ ] Bottleneck detection works for vLLM
- [ ] Bottleneck detection works for TGI
- [ ] Bottleneck detection works for SGLang
- [ ] SLO monitoring tracks compliance
- [ ] Health score calculation is accurate
- [ ] Recommendations are generated
- [ ] API endpoint works correctly

### Code Quality
- [ ] All files have proper docstrings
- [ ] Type hints are used throughout
- [ ] Code follows Python best practices
- [ ] No linting errors

### Testing
- [ ] All unit tests pass
- [ ] Test coverage > 80%
- [ ] Tests cover error cases

### Performance
- [ ] Analysis completes in < 1 second
- [ ] No memory leaks

---

## Success Metrics

### Test Coverage
- **Target**: > 80% coverage for new code
- **Critical Paths**: 100% coverage
  - Bottleneck detection
  - SLO monitoring
  - Analysis engine

### Performance Metrics
- **Analysis Time**: < 1 second
- **Memory Usage**: < 100 MB

---

## Troubleshooting

### Common Issues

#### Issue 1: Import Errors
**Symptom**: `ModuleNotFoundError`

**Solution**:
```bash
# Verify files exist
ls src/analysis/
ls src/models/analysis.py
```

#### Issue 2: Metric Not Found
**Symptom**: Metric extraction returns None

**Solution**:
- Check metric path syntax
- Verify metric exists in snapshot
- Add debug logging

#### Issue 3: Incorrect Severity
**Symptom**: Severity calculation is wrong

**Solution**:
- Review threshold values
- Check severity calculation logic
- Adjust thresholds

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

3. **Create Completion Report**

4. **Commit Code**:
```bash
git add .
git commit -m "feat: implement PHASE2-2.5 Analysis Engine"
git push origin main
```

---

## Next Steps

### Immediate
1. ✅ Validate all functionality
2. ✅ Run complete test suite
3. ✅ Create completion report
4. ✅ Commit and push code

### Next Phase: PHASE2-2.6
**Optimization Recommendations**: Generate optimization strategies based on analysis

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Analysis Models | 3 min | Pending |
| Bottleneck Detector | 5 min | Pending |
| SLO Monitor | 4 min | Pending |
| Analysis Engine | 3 min | Pending |
| API Endpoints | 2 min | Pending |
| Testing & Validation | 3 min | Pending |
| **Total** | **20 min** | **Pending** |

---

## Deliverables

### Code Deliverables
- ✅ Analysis models (Pydantic)
- ✅ Bottleneck detector
- ✅ SLO monitor
- ✅ Analysis engine
- ✅ API endpoints
- ✅ Comprehensive tests

### Documentation Deliverables
- ✅ Code documentation (docstrings)
- ✅ API documentation (OpenAPI)
- ✅ Test documentation

---

## Notes

### Important Considerations
1. **Threshold Configuration**: Allow custom thresholds
2. **Multi-Instance Support**: Handle all three types
3. **Actionable Recommendations**: Specific, not generic
4. **Health Score**: Balanced calculation
5. **SLO Flexibility**: Support various metrics and comparisons

### Analysis Engine Features
- **Real-time**: Immediate bottleneck detection
- **Configurable**: Custom thresholds and SLOs
- **Actionable**: Specific recommendations
- **Comprehensive**: Multiple bottleneck types

---

**Status**: Ready for execution  
**Estimated Completion**: 20 minutes  
**Next Phase**: PHASE2-2.6 - Optimization Recommendations

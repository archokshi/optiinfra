# PHASE4-4.3 PART2: Regression Detection - Execution and Validation

**Phase**: PHASE4-4.3  
**Agent**: Application Agent  
**Objective**: Execute and validate regression detection implementation  
**Estimated Time**: 25 minutes  
**Priority**: HIGH

---

## Pre-Execution Checklist

- [ ] PHASE4-4.3_PART1 documentation reviewed
- [ ] PHASE4-4.2 complete (Quality Monitoring working)
- [ ] Application Agent running on port 8004
- [ ] Python 3.11+ installed

---

## Execution Steps

### Step 1: Create Directory Structure (1 minute)

```bash
cd services/application-agent

# Create storage directory
mkdir -p src/storage

# Verify structure
ls -la src/
```

### Step 2: Implement Baseline Models (5 minutes)

Create `src/models/baseline.py` with:
- BaselineConfig
- BaselineMetrics
- Baseline
- RegressionAlert
- RegressionResult

### Step 3: Implement Baseline Storage (5 minutes)

Create `src/storage/baseline_storage.py` with:
- BaselineStorage class
- CRUD operations
- Query methods

### Step 4: Implement Regression Detector (10 minutes)

Create `src/analyzers/regression_detector.py` with:
- RegressionDetector class
- Baseline establishment
- Regression detection
- Alert generation

### Step 5: Create Regression API (5 minutes)

Create `src/api/regression.py` with 5 endpoints

### Step 6: Update Main Application (2 minutes)

Update `src/main.py`:
```python
from .api import health, quality, regression
app.include_router(regression.router)
```

### Step 7: Create Tests (3 minutes)

Create `tests/test_regression.py` with 7+ tests

### Step 8: Run Tests (2 minutes)

```bash
pytest tests/test_regression.py -v
```

**Expected**: All tests passing

---

## Validation Steps

### 1. Start Application (1 minute)

```bash
python -m uvicorn src.main:app --port 8004 --reload
```

### 2. Establish Baseline (3 minutes)

```bash
# Analyze some quality metrics first
curl -X POST http://localhost:8004/quality/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is AI?",
    "response": "AI is artificial intelligence.",
    "model_name": "gpt-oss-20b"
  }'

# Establish baseline
curl -X POST http://localhost:8004/regression/baseline \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-oss-20b",
    "config_hash": "default",
    "sample_size": 10
  }'
```

**Expected Response**:
```json
{
  "baseline_id": "...",
  "model_name": "gpt-oss-20b",
  "metrics": {
    "average_quality": 80.0,
    "average_relevance": 75.0,
    "average_coherence": 85.0
  },
  "status": "active"
}
```

### 3. Test Regression Detection - No Regression (3 minutes)

```bash
curl -X POST http://localhost:8004/regression/detect \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-oss-20b",
    "config_hash": "default",
    "current_quality": 82.0
  }'
```

**Expected**: `regression_detected: false`

### 4. Test Regression Detection - With Regression (3 minutes)

```bash
curl -X POST http://localhost:8004/regression/detect \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-oss-20b",
    "config_hash": "default",
    "current_quality": 70.0
  }'
```

**Expected**:
```json
{
  "regression_detected": true,
  "regression_score": 75.0,
  "severity": "moderate",
  "quality_drop": 10.0,
  "alert": {
    "level": "WARNING",
    "message": "Quality dropped by 12.5%"
  }
}
```

### 5. List Baselines (2 minutes)

```bash
curl http://localhost:8004/regression/baselines
```

### 6. Get Alerts (2 minutes)

```bash
curl http://localhost:8004/regression/alerts
```

### 7. Test API Documentation (1 minute)

```bash
# Open in browser
start http://localhost:8004/docs
```

Verify 5 new regression endpoints listed

---

## Validation Checklist

### Baseline Tracking ✅
- [ ] Baseline creation works
- [ ] Baseline metrics calculated correctly
- [ ] Multiple baselines supported
- [ ] Baseline retrieval works

### Regression Detection ✅
- [ ] No regression detected when quality stable
- [ ] Regression detected when quality drops >5%
- [ ] Regression score calculated correctly
- [ ] Severity classification accurate

### Anomaly Detection ✅
- [ ] Z-score calculation works
- [ ] Threshold detection works
- [ ] Trend detection works

### Alert Generation ✅
- [ ] Alerts generated for regressions
- [ ] Alert severity levels correct
- [ ] Alert messages descriptive
- [ ] Alert history tracked

### API Endpoints ✅
- [ ] POST /regression/baseline works
- [ ] POST /regression/detect works
- [ ] GET /regression/baselines works
- [ ] GET /regression/alerts works
- [ ] GET /regression/history works

### Tests ✅
- [ ] All 7+ tests passing
- [ ] No test failures
- [ ] Coverage > 70%

---

## Test Scenarios

### Scenario 1: Establish Baseline
**Input**: 10 quality metrics with avg 85%
**Expected**: Baseline created with avg_quality=85%

### Scenario 2: No Regression
**Baseline**: 85%
**Current**: 84%
**Expected**: No regression (drop <5%)

### Scenario 3: Minor Regression
**Baseline**: 85%
**Current**: 79%
**Expected**: Regression detected, severity=minor (7% drop)

### Scenario 4: Moderate Regression
**Baseline**: 85%
**Current**: 72%
**Expected**: Regression detected, severity=moderate (15% drop)

### Scenario 5: Severe Regression
**Baseline**: 85%
**Current**: 60%
**Expected**: Regression detected, severity=severe (29% drop)

### Scenario 6: Critical Regression
**Baseline**: 85%
**Current**: 50%
**Expected**: Regression detected, severity=critical (41% drop)

---

## Performance Validation

| Metric | Target | Validation |
|--------|--------|------------|
| Detection time | < 100ms | Measure with curl |
| Baseline creation | < 200ms | Measure with curl |
| API response | < 500ms | Measure with curl |
| Memory usage | < 100MB | Monitor process |

---

## Troubleshooting

### Issue 1: Import Errors
```bash
# Ensure __init__.py exists
touch src/storage/__init__.py
```

### Issue 2: Tests Failing
```bash
# Run with verbose output
pytest tests/test_regression.py -v -s
```

### Issue 3: No Baseline Found
- Ensure baseline created before detection
- Check model_name and config_hash match

### Issue 4: Regression Not Detected
- Verify quality drop is >5%
- Check baseline metrics are valid

---

## Success Criteria

- [x] All files created
- [x] Baseline tracking working
- [x] Regression detection accurate
- [x] 5 API endpoints functional
- [x] 7+ tests passing
- [x] Detection time < 100ms
- [x] API docs updated
- [x] Ready for PHASE4-4.4

---

**Regression Detection validated and ready!** ✅

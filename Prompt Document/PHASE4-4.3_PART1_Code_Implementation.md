# PHASE4-4.3 PART1: Regression Detection - Code Implementation Plan

**Phase**: PHASE4-4.3  
**Agent**: Application Agent  
**Objective**: Implement regression detection with baseline tracking and anomaly detection  
**Estimated Time**: 30 minutes implementation + 25 minutes validation = 55 minutes  
**Priority**: HIGH  
**Dependencies**: PHASE4-4.2 (Quality Monitoring)

---

## Overview

Implement automated regression detection to identify quality degradation by tracking baselines, detecting anomalies, and generating alerts when quality drops below acceptable thresholds.

---

## Core Features

### 1. Baseline Tracking
- Establish quality baselines per model/configuration
- Track baseline metrics over time
- Support multiple baseline types (rolling, fixed, adaptive)
- Baseline persistence and retrieval

### 2. Anomaly Detection
- Statistical anomaly detection (Z-score, IQR)
- Trend-based anomaly detection
- Threshold-based detection (>5% drop)
- Configurable sensitivity levels

### 3. Regression Scoring
- Calculate regression severity (0-100)
- Classify regression types (minor, moderate, severe, critical)
- Track regression duration and frequency
- Historical regression tracking

### 4. Alert Generation
- Generate alerts for quality drops
- Alert severity levels (INFO, WARNING, CRITICAL)
- Alert deduplication
- Alert history tracking

---

## Implementation Plan

### Step 1: Create Baseline Models (5 minutes)

**File**: `src/models/baseline.py`

Models:
- `BaselineConfig` - Baseline configuration
- `BaselineMetrics` - Baseline quality metrics
- `Baseline` - Complete baseline with metadata
- `RegressionAlert` - Regression alert
- `RegressionResult` - Regression detection result

---

### Step 2: Create Baseline Storage (5 minutes)

**File**: `src/storage/baseline_storage.py`

Features:
- In-memory baseline storage
- CRUD operations for baselines
- Query baselines by model/config
- Baseline versioning

---

### Step 3: Implement Regression Detector (10 minutes)

**File**: `src/analyzers/regression_detector.py`

Core Methods:
- `establish_baseline()` - Create new baseline
- `detect_regression()` - Detect quality regression
- `calculate_regression_score()` - Score regression severity
- `generate_alert()` - Generate regression alert
- `_detect_anomaly()` - Statistical anomaly detection
- `_calculate_z_score()` - Z-score calculation
- `_detect_trend()` - Trend-based detection

Detection Methods:
- **Z-Score**: Statistical deviation detection
- **Threshold**: Absolute threshold comparison (>5% drop)
- **Trend**: Moving average trend analysis
- **IQR**: Interquartile range outlier detection

---

### Step 4: Create Regression API (5 minutes)

**File**: `src/api/regression.py`

Endpoints:
- `POST /regression/baseline` - Establish baseline
- `POST /regression/detect` - Detect regression
- `GET /regression/baselines` - List baselines
- `GET /regression/alerts` - Get alerts
- `GET /regression/history` - Get regression history

---

### Step 5: Update Main Application (2 minutes)

**File**: `src/main.py`

- Import regression router
- Include regression router

---

### Step 6: Create Tests (3 minutes)

**File**: `tests/test_regression.py`

Tests:
- `test_establish_baseline()`
- `test_detect_regression()`
- `test_no_regression()`
- `test_minor_regression()`
- `test_severe_regression()`
- `test_list_baselines()`
- `test_get_alerts()`

---

## Data Models

### Baseline
```python
{
  "baseline_id": "uuid",
  "model_name": "gpt-oss-20b",
  "config_hash": "abc123",
  "metrics": {
    "average_quality": 85.5,
    "average_relevance": 82.0,
    "average_coherence": 88.0,
    "average_hallucination": 5.0
  },
  "sample_size": 100,
  "created_at": "2025-10-26T...",
  "status": "active"
}
```

### Regression Result
```python
{
  "regression_detected": true,
  "regression_score": 75.0,
  "severity": "moderate",
  "quality_drop": 12.5,
  "baseline_quality": 85.5,
  "current_quality": 73.0,
  "alert": {
    "level": "WARNING",
    "message": "Quality dropped by 12.5%"
  }
}
```

---

## Regression Detection Logic

### Threshold-Based (Primary)
```python
quality_drop = baseline_quality - current_quality
drop_percentage = (quality_drop / baseline_quality) * 100

if drop_percentage > 5:
    regression_detected = True
```

### Z-Score (Statistical)
```python
z_score = (current_quality - mean) / std_dev

if abs(z_score) > 2:  # 2 standard deviations
    anomaly_detected = True
```

### Severity Classification
- **Minor**: 5-10% drop
- **Moderate**: 10-20% drop
- **Severe**: 20-30% drop
- **Critical**: >30% drop

---

## Files to Create

1. `src/models/baseline.py` (~120 lines)
2. `src/storage/baseline_storage.py` (~150 lines)
3. `src/analyzers/regression_detector.py` (~300 lines)
4. `src/api/regression.py` (~180 lines)
5. `tests/test_regression.py` (~200 lines)

**Total**: ~950 lines

---

## Success Criteria

- [ ] Baseline tracking works
- [ ] Regression detection accurate
- [ ] Anomaly detection functional
- [ ] Alert generation working
- [ ] 5 API endpoints functional
- [ ] 7+ tests passing
- [ ] Detection latency < 100ms

---

**Ready for implementation!**

# PHASE1-1.9 PART1: Recommendation Engine - Code Implementation

**Phase:** Cost Agent - Week 2  
**Objective:** Implement intelligent Recommendation Engine with ML-based predictions and scoring  
**Priority:** HIGH  
**Estimated Effort:** 2-2.5 hours  
**Date:** October 22, 2025

---

## 📋 OVERVIEW

The Recommendation Engine is an intelligent system that generates, scores, and prioritizes cost optimization recommendations based on:
1. **Historical Analysis** - Learn from past patterns and trends
2. **ML-Based Predictions** - Forecast future costs and usage
3. **Intelligent Scoring** - Rank recommendations by ROI and risk
4. **Contextual Awareness** - Consider business constraints and priorities

**Key Differences from Previous Components:**
- **PHASE1-1.6 (Workflows):** Executes specific optimizations
- **PHASE1-1.7 (Analysis Engine):** Detects problems (idle, anomalies)
- **PHASE1-1.8 (LLM Integration):** Adds natural language insights
- **PHASE1-1.9 (Recommendation Engine):** Intelligently prioritizes and predicts outcomes

**Expected Impact:** 25-50% improvement in recommendation accuracy and adoption rate

---

## 🎯 OBJECTIVES

### Primary Goals
1. **Recommendation Generation:**
   - Generate recommendations from analysis results
   - Combine multiple data sources (idle, anomalies, trends)
   - Apply business rules and constraints
   - Deduplicate and consolidate recommendations

2. **ML-Based Cost Prediction:**
   - Predict future costs (7, 30, 90 days)
   - Forecast savings from recommendations
   - Identify cost trends and patterns
   - Detect seasonality and anomalies

3. **Intelligent Scoring:**
   - Score recommendations by ROI
   - Factor in implementation risk
   - Consider business impact
   - Prioritize by urgency

4. **Historical Trend Analysis:**
   - Analyze cost trends over time
   - Identify recurring patterns
   - Track recommendation effectiveness
   - Learn from past outcomes

### Success Criteria
- ✅ Accurate cost predictions (< 10% error)
- ✅ Intelligent recommendation scoring (ROI-based)
- ✅ Historical trend analysis (30+ days)
- ✅ Integration with Analysis Engine and LLM
- ✅ 85%+ test coverage

---

## 🏗️ ARCHITECTURE

### Recommendation Engine Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Recommendation Engine                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. generate_recommendations                                 │
│     ├─> From idle resources                                 │
│     ├─> From anomalies                                      │
│     ├─> From cost trends                                    │
│     └─> From historical patterns                            │
│                                                              │
│  2. predict_costs (ML-based)                                 │
│     ├─> Time series forecasting                             │
│     ├─> Trend analysis                                      │
│     ├─> Seasonality detection                               │
│     └─> Confidence intervals                                │
│                                                              │
│  3. score_recommendations                                    │
│     ├─> Calculate ROI                                       │
│     ├─> Assess implementation risk                          │
│     ├─> Evaluate business impact                            │
│     └─> Prioritize by urgency                               │
│                                                              │
│  4. analyze_historical_trends                                │
│     ├─> Cost trends over time                               │
│     ├─> Usage patterns                                      │
│     ├─> Recommendation effectiveness                        │
│     └─> Savings realized                                    │
│                                                              │
│  5. consolidate_recommendations                              │
│     ├─> Deduplicate similar recommendations                 │
│     ├─> Group related recommendations                       │
│     ├─> Resolve conflicts                                   │
│     └─> Apply business rules                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Analysis Results → Generate Recs → Score Recs → Predict Costs → Prioritize → Output
      ↓                ↓              ↓              ↓              ↓
  Historical      ML Model       ROI Calc      Forecasts      Final Recs
   Trends
```

---

## 📦 IMPLEMENTATION PLAN

### Phase 1: Recommendation Generation Module
**File:** `src/recommendations/generator.py`

**Functions:**

1. `generate_recommendations(analysis_report: Dict, historical_data: Dict) -> List[Recommendation]`
   - Generate recommendations from idle resources
   - Generate recommendations from anomalies
   - Generate recommendations from cost trends
   - Apply business rules and filters
   - Deduplicate and consolidate

2. `generate_from_idle_resources(idle_resources: List[Dict]) -> List[Recommendation]`
   - Terminate recommendations for critical/high idle
   - Hibernate recommendations for medium idle
   - Right-size recommendations for low idle
   - Calculate potential savings

3. `generate_from_anomalies(anomalies: List[Dict]) -> List[Recommendation]`
   - Cost spike mitigation recommendations
   - Usage optimization recommendations
   - Configuration fix recommendations
   - Security remediation recommendations

4. `generate_from_trends(cost_history: List[Dict]) -> List[Recommendation]`
   - Spot instance migration (if steady workload)
   - Reserved instance purchase (if predictable usage)
   - Auto-scaling configuration (if variable usage)
   - Storage optimization (if growing storage costs)

5. `consolidate_recommendations(recommendations: List[Recommendation]) -> List[Recommendation]`
   - Remove duplicates
   - Merge similar recommendations
   - Resolve conflicts (e.g., terminate vs right-size)
   - Apply priority rules

**Recommendation Types:**
- **Terminate** - Stop idle resources
- **Hibernate** - Pause low-usage resources
- **Right-Size** - Reduce instance size
- **Spot Migration** - Move to spot instances
- **RI Purchase** - Buy reserved instances
- **Auto-Scale** - Configure auto-scaling
- **Storage Optimization** - Optimize storage tiers
- **Configuration Fix** - Fix misconfigurations

---

### Phase 2: ML-Based Cost Prediction Module
**File:** `src/recommendations/predictor.py`

**Functions:**

1. `predict_future_costs(cost_history: List[Dict], forecast_days: int = 30) -> CostForecast`
   - Time series forecasting (ARIMA, Prophet, or simple moving average)
   - Predict costs for next 7, 30, 90 days
   - Calculate confidence intervals
   - Detect trends and seasonality

2. `predict_savings(recommendation: Recommendation, cost_history: List[Dict]) -> SavingsForecast`
   - Estimate savings from recommendation
   - Calculate ROI timeline
   - Factor in implementation costs
   - Provide confidence level

3. `detect_cost_trends(cost_history: List[Dict]) -> TrendAnalysis`
   - Identify upward/downward trends
   - Calculate growth rate
   - Detect inflection points
   - Identify cost drivers

4. `detect_seasonality(cost_history: List[Dict]) -> SeasonalityAnalysis`
   - Identify daily patterns
   - Identify weekly patterns
   - Identify monthly patterns
   - Forecast seasonal peaks

5. `calculate_confidence_intervals(forecast: List[float], confidence: float = 0.95) -> Tuple[List[float], List[float]]`
   - Calculate upper and lower bounds
   - Use historical variance
   - Adjust for forecast horizon

**ML Models (Simple Implementations):**
```python
# For MVP, use simple statistical methods
# Can upgrade to ML models later

# Moving Average Forecast
def moving_average_forecast(data, window=7):
    return np.mean(data[-window:])

# Linear Trend Forecast
def linear_trend_forecast(data, days_ahead):
    x = np.arange(len(data))
    y = np.array(data)
    slope, intercept = np.polyfit(x, y, 1)
    future_x = np.arange(len(data), len(data) + days_ahead)
    return slope * future_x + intercept

# Exponential Smoothing (Simple)
def exponential_smoothing(data, alpha=0.3):
    result = [data[0]]
    for i in range(1, len(data)):
        result.append(alpha * data[i] + (1 - alpha) * result[i-1])
    return result[-1]
```

---

### Phase 3: Recommendation Scoring Module
**File:** `src/recommendations/scorer.py`

**Functions:**

1. `score_recommendations(recommendations: List[Recommendation], context: Dict) -> List[ScoredRecommendation]`
   - Calculate ROI score
   - Calculate risk score
   - Calculate urgency score
   - Calculate business impact score
   - Compute final priority score

2. `calculate_roi_score(recommendation: Recommendation) -> float`
   - ROI = (Annual Savings - Implementation Cost) / Implementation Cost
   - Normalize to 0-100 scale
   - Factor in confidence level
   - Adjust for payback period

3. `calculate_risk_score(recommendation: Recommendation) -> float`
   - Implementation complexity (0-100)
   - Potential downtime risk
   - Rollback difficulty
   - Dependencies on other systems

4. `calculate_urgency_score(recommendation: Recommendation) -> float`
   - Cost impact (higher = more urgent)
   - Security impact (critical = urgent)
   - Compliance impact
   - Time sensitivity

5. `calculate_business_impact_score(recommendation: Recommendation, context: Dict) -> float`
   - Affected services/applications
   - User impact
   - Business criticality
   - SLA considerations

6. `compute_priority_score(roi: float, risk: float, urgency: float, impact: float) -> float`
   - Weighted combination of scores
   - Default weights: ROI (40%), Risk (20%), Urgency (25%), Impact (15%)
   - Configurable weights per customer
   - Returns 0-100 score

**Scoring Formula:**
```python
priority_score = (
    roi_score * 0.40 +
    (100 - risk_score) * 0.20 +  # Lower risk = higher score
    urgency_score * 0.25 +
    impact_score * 0.15
)
```

---

### Phase 4: Historical Trend Analysis Module
**File:** `src/recommendations/trend_analyzer.py`

**Functions:**

1. `analyze_cost_trends(customer_id: str, days: int = 30) -> TrendAnalysis`
   - Fetch historical cost data from ClickHouse
   - Calculate daily/weekly/monthly trends
   - Identify cost drivers
   - Compare to baseline

2. `analyze_usage_trends(customer_id: str, days: int = 30) -> UsageTrends`
   - CPU/memory utilization trends
   - Network traffic trends
   - Storage growth trends
   - Request volume trends

3. `analyze_recommendation_effectiveness(customer_id: str) -> EffectivenessReport`
   - Track implemented recommendations
   - Measure actual vs predicted savings
   - Calculate success rate
   - Identify patterns in successful recommendations

4. `identify_recurring_patterns(cost_history: List[Dict]) -> List[Pattern]`
   - Daily patterns (business hours vs off-hours)
   - Weekly patterns (weekday vs weekend)
   - Monthly patterns (month-end spikes)
   - Seasonal patterns (holiday traffic)

5. `compare_to_baseline(current_metrics: Dict, baseline_metrics: Dict) -> ComparisonReport`
   - Calculate percentage changes
   - Identify significant deviations
   - Highlight improvements or regressions
   - Generate insights

---

### Phase 5: Pydantic Models
**File:** `src/models/recommendation_engine.py`

**Models:**

1. **Recommendation**
```python
class Recommendation(BaseModel):
    recommendation_id: str
    customer_id: str
    recommendation_type: str  # terminate, hibernate, right-size, spot, ri, etc.
    resource_id: Optional[str]
    resource_type: Optional[str]
    region: str
    
    # Description
    title: str
    description: str
    rationale: str
    
    # Savings
    monthly_savings: float
    annual_savings: float
    implementation_cost: float
    payback_period_days: int
    
    # Risk assessment
    risk_level: str  # low, medium, high
    risk_factors: List[str]
    rollback_plan: Optional[str]
    
    # Implementation
    implementation_steps: List[str]
    estimated_time_minutes: int
    requires_approval: bool
    
    # Metadata
    created_at: datetime
    expires_at: Optional[datetime]
    source: str  # idle_detection, anomaly, trend_analysis
    confidence: float  # 0.0-1.0
```

2. **ScoredRecommendation**
```python
class ScoredRecommendation(BaseModel):
    recommendation: Recommendation
    
    # Scores (0-100)
    roi_score: float
    risk_score: float
    urgency_score: float
    business_impact_score: float
    priority_score: float  # Final weighted score
    
    # Ranking
    rank: int
    category: str  # quick_win, strategic, long_term
    
    # Context
    scoring_context: Dict[str, Any]
    scored_at: datetime
```

3. **CostForecast**
```python
class CostForecast(BaseModel):
    customer_id: str
    forecast_start_date: date
    forecast_end_date: date
    
    # Forecast data
    daily_forecast: List[float]
    weekly_forecast: List[float]
    monthly_forecast: List[float]
    
    # Confidence intervals
    daily_lower_bound: List[float]
    daily_upper_bound: List[float]
    confidence_level: float  # e.g., 0.95
    
    # Trends
    trend_direction: str  # increasing, decreasing, stable
    growth_rate_percent: float
    
    # Metadata
    model_used: str  # moving_average, linear_trend, exponential_smoothing
    forecast_accuracy: Optional[float]  # Based on historical validation
    generated_at: datetime
```

4. **SavingsForecast**
```python
class SavingsForecast(BaseModel):
    recommendation_id: str
    
    # Savings forecast
    monthly_savings: float
    annual_savings: float
    three_year_savings: float
    
    # Timeline
    savings_start_date: date
    full_savings_date: date  # When full savings realized
    
    # Confidence
    confidence_level: float
    confidence_interval: Tuple[float, float]
    
    # Assumptions
    assumptions: List[str]
    risk_factors: List[str]
```

5. **TrendAnalysis**
```python
class TrendAnalysis(BaseModel):
    customer_id: str
    analysis_period_days: int
    analysis_date: datetime
    
    # Cost trends
    total_cost_trend: str  # increasing, decreasing, stable
    cost_growth_rate: float  # Percentage
    cost_volatility: float  # Standard deviation
    
    # By resource type
    cost_by_resource_type: Dict[str, float]
    fastest_growing_resource: str
    largest_cost_driver: str
    
    # Patterns
    daily_pattern: Optional[Dict[str, float]]
    weekly_pattern: Optional[Dict[str, float]]
    monthly_pattern: Optional[Dict[str, float]]
    
    # Insights
    key_findings: List[str]
    recommendations: List[str]
```

6. **RecommendationEngineRequest**
```python
class RecommendationEngineRequest(BaseModel):
    customer_id: str
    analysis_report: Dict[str, Any]  # From Analysis Engine
    
    # Options
    include_predictions: bool = True
    include_trends: bool = True
    forecast_days: int = 30
    max_recommendations: int = 50
    min_monthly_savings: float = 10.0
    
    # Scoring weights (must sum to 1.0)
    roi_weight: float = 0.40
    risk_weight: float = 0.20
    urgency_weight: float = 0.25
    impact_weight: float = 0.15
    
    # Filters
    excluded_resource_types: List[str] = []
    excluded_regions: List[str] = []
    min_confidence: float = 0.5
```

7. **RecommendationEngineResponse**
```python
class RecommendationEngineResponse(BaseModel):
    request_id: str
    customer_id: str
    timestamp: datetime
    
    # Recommendations
    total_recommendations: int
    scored_recommendations: List[ScoredRecommendation]
    
    # Forecasts
    cost_forecast: Optional[CostForecast]
    total_potential_savings: float
    
    # Trends
    trend_analysis: Optional[TrendAnalysis]
    
    # Summary
    quick_wins: List[ScoredRecommendation]  # High ROI, low risk
    strategic_initiatives: List[ScoredRecommendation]  # High ROI, medium risk
    long_term_opportunities: List[ScoredRecommendation]  # Lower ROI, strategic value
    
    # Metadata
    processing_time_seconds: float
    success: bool
    error_message: Optional[str]
```

---

### Phase 6: Recommendation Engine Core
**File:** `src/recommendations/engine.py`

**Main Class:**
```python
class RecommendationEngine:
    def __init__(
        self,
        metrics_client: Optional[ClickHouseMetricsClient] = None
    ):
        self.generator = RecommendationGenerator()
        self.predictor = CostPredictor()
        self.scorer = RecommendationScorer()
        self.trend_analyzer = TrendAnalyzer(metrics_client)
        self.metrics_client = metrics_client
    
    async def generate_recommendations(
        self,
        request: RecommendationEngineRequest
    ) -> RecommendationEngineResponse:
        """
        Main entry point for recommendation generation.
        
        Steps:
        1. Generate recommendations from analysis report
        2. Fetch historical data
        3. Analyze trends
        4. Predict future costs
        5. Score recommendations
        6. Prioritize and categorize
        7. Return response
        """
        
    async def _fetch_historical_data(
        self,
        customer_id: str,
        days: int
    ) -> Dict[str, Any]:
        """Fetch historical cost and usage data"""
        
    def _categorize_recommendations(
        self,
        scored_recommendations: List[ScoredRecommendation]
    ) -> Dict[str, List[ScoredRecommendation]]:
        """Categorize into quick wins, strategic, long-term"""
```

---

### Phase 7: API Endpoints
**File:** `src/api/recommendation_routes.py`

**Endpoints:**

1. **POST /api/v1/recommendations/generate**
   - Generate recommendations from analysis report
   - Request body: `RecommendationEngineRequest`
   - Response: `RecommendationEngineResponse`

2. **GET /api/v1/recommendations/{customer_id}**
   - Get all recommendations for customer
   - Query params: status, type, min_savings
   - Response: List of recommendations

3. **GET /api/v1/recommendations/{recommendation_id}**
   - Get specific recommendation details
   - Response: Full recommendation with scoring

4. **POST /api/v1/recommendations/{recommendation_id}/implement**
   - Mark recommendation as implemented
   - Track actual savings for learning

5. **GET /api/v1/forecasts/{customer_id}**
   - Get cost forecast for customer
   - Query params: days (7, 30, 90)
   - Response: `CostForecast`

6. **GET /api/v1/trends/{customer_id}**
   - Get trend analysis for customer
   - Query params: days
   - Response: `TrendAnalysis`

---

### Phase 8: ClickHouse Metrics Enhancement
**File:** `src/database/clickhouse_metrics.py`

**New Tables:**

```sql
-- Recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    timestamp DateTime,
    recommendation_id String,
    customer_id String,
    recommendation_type String,
    resource_id String,
    resource_type String,
    region String,
    
    monthly_savings Float64,
    annual_savings Float64,
    implementation_cost Float64,
    
    roi_score Float64,
    risk_score Float64,
    urgency_score Float64,
    priority_score Float64,
    
    status String,  -- pending, implemented, rejected, expired
    created_at DateTime,
    implemented_at Nullable(DateTime),
    
    actual_savings Nullable(Float64)
) ENGINE = MergeTree()
ORDER BY (timestamp, customer_id, recommendation_id)
TTL timestamp + INTERVAL 365 DAY;

-- Cost forecasts table
CREATE TABLE IF NOT EXISTS cost_forecasts (
    timestamp DateTime,
    customer_id String,
    forecast_date Date,
    forecast_days_ahead UInt16,
    
    predicted_cost Float64,
    lower_bound Float64,
    upper_bound Float64,
    confidence_level Float64,
    
    actual_cost Nullable(Float64),
    prediction_error Nullable(Float64),
    
    model_used String
) ENGINE = MergeTree()
ORDER BY (timestamp, customer_id, forecast_date)
TTL timestamp + INTERVAL 180 DAY;
```

**New Methods:**
- `insert_recommendation(recommendation: Dict) -> None`
- `update_recommendation_status(recommendation_id: str, status: str) -> None`
- `insert_cost_forecast(forecast: Dict) -> None`
- `get_recommendation_effectiveness(customer_id: str) -> Dict`
- `get_forecast_accuracy(customer_id: str) -> float`

---

### Phase 9: Prometheus Metrics Enhancement
**File:** `src/monitoring/prometheus_metrics.py`

**New Metrics:**

```python
# Counters
recommendations_generated_total = Counter(
    'recommendations_generated_total',
    'Total recommendations generated',
    ['customer_id', 'recommendation_type', 'category']
)

recommendations_implemented_total = Counter(
    'recommendations_implemented_total',
    'Total recommendations implemented',
    ['customer_id', 'recommendation_type']
)

# Histograms
recommendation_savings_dollars = Histogram(
    'recommendation_savings_dollars',
    'Recommendation savings distribution',
    ['customer_id', 'recommendation_type'],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

recommendation_priority_score = Histogram(
    'recommendation_priority_score',
    'Recommendation priority score distribution',
    ['customer_id', 'category'],
    buckets=[0, 20, 40, 60, 80, 100]
)

forecast_accuracy_percent = Histogram(
    'forecast_accuracy_percent',
    'Cost forecast accuracy',
    ['customer_id', 'forecast_days'],
    buckets=[70, 75, 80, 85, 90, 95, 100]
)

# Gauges
total_potential_savings = Gauge(
    'total_potential_savings',
    'Total potential savings from recommendations',
    ['customer_id']
)

active_recommendations = Gauge(
    'active_recommendations',
    'Number of active recommendations',
    ['customer_id', 'category']
)
```

---

## 🔒 SECURITY & VALIDATION

### Input Validation
```python
# Customer ID
customer_id: str = Field(
    ...,
    pattern=r'^[a-zA-Z0-9_-]{1,64}$'
)

# Forecast days
forecast_days: int = Field(
    default=30,
    ge=1,
    le=365
)

# Weights validation
@validator('roi_weight', 'risk_weight', 'urgency_weight', 'impact_weight')
def validate_weights(cls, v, values):
    total = v + values.get('roi_weight', 0) + values.get('risk_weight', 0) + \
            values.get('urgency_weight', 0) + values.get('impact_weight', 0)
    if abs(total - 1.0) > 0.01:
        raise ValueError("Weights must sum to 1.0")
    return v
```

---

## 🧪 TESTING STRATEGY

### Test File
**File:** `tests/test_recommendation_engine.py`

### Test Categories

1. **Recommendation Generation Tests** (8 tests)
   - test_generate_from_idle_resources
   - test_generate_from_anomalies
   - test_generate_from_trends
   - test_consolidate_recommendations
   - test_deduplication
   - test_conflict_resolution
   - test_business_rules_application
   - test_empty_input_handling

2. **Cost Prediction Tests** (6 tests)
   - test_moving_average_forecast
   - test_linear_trend_forecast
   - test_exponential_smoothing
   - test_confidence_intervals
   - test_seasonality_detection
   - test_forecast_accuracy_validation

3. **Scoring Tests** (8 tests)
   - test_roi_score_calculation
   - test_risk_score_calculation
   - test_urgency_score_calculation
   - test_business_impact_score
   - test_priority_score_computation
   - test_custom_weights
   - test_score_normalization
   - test_edge_cases

4. **Trend Analysis Tests** (6 tests)
   - test_cost_trend_analysis
   - test_usage_trend_analysis
   - test_pattern_identification
   - test_baseline_comparison
   - test_recommendation_effectiveness
   - test_historical_data_fetching

5. **Integration Tests** (4 tests)
   - test_end_to_end_recommendation_flow
   - test_with_analysis_engine_output
   - test_with_llm_enhancement
   - test_api_endpoints

6. **Validation Tests** (4 tests)
   - test_request_validation
   - test_weights_validation
   - test_recommendation_validation
   - test_forecast_validation

**Target:** 36+ tests, 85%+ coverage

---

## 📊 SUCCESS METRICS

### Technical Metrics
- ✅ 85%+ test coverage
- ✅ All tests passing
- ✅ API response time < 10s
- ✅ Forecast accuracy > 90%
- ✅ Error rate < 1%

### Business Metrics
- ✅ Recommendation adoption rate > 60%
- ✅ Average ROI > 300%
- ✅ Savings accuracy within 15%
- ✅ Quick wins identified (> 30% of recommendations)

---

## 📝 IMPLEMENTATION STEPS

### Step 1: Create Recommendation Generator (25 min)
- Implement `generator.py`
- Add recommendation generation logic
- Add consolidation logic

### Step 2: Create Cost Predictor (30 min)
- Implement `predictor.py`
- Add forecasting algorithms
- Add trend detection

### Step 3: Create Recommendation Scorer (25 min)
- Implement `scorer.py`
- Add scoring algorithms
- Add prioritization logic

### Step 4: Create Trend Analyzer (20 min)
- Implement `trend_analyzer.py`
- Add historical analysis
- Add pattern detection

### Step 5: Create Pydantic Models (25 min)
- Implement `recommendation_engine.py` (models)
- Add all validation models

### Step 6: Create Engine Core (25 min)
- Implement `engine.py`
- Integrate all components
- Add error handling

### Step 7: Create API Endpoints (20 min)
- Implement `recommendation_routes.py`
- Add all endpoints
- Add validation

### Step 8: Enhance Metrics (15 min)
- Update `clickhouse_metrics.py`
- Update `prometheus_metrics.py`

### Step 9: Create Tests (30 min)
- Implement `test_recommendation_engine.py`
- Create 36+ tests

### Step 10: Run and Validate (10 min)
- Run all tests
- Fix failures
- Validate integration

**Total Estimated Time:** ~2.5 hours

---

## 🎯 DELIVERABLES

### Code Files
1. ✅ `src/recommendations/generator.py` (~400 lines)
2. ✅ `src/recommendations/predictor.py` (~450 lines)
3. ✅ `src/recommendations/scorer.py` (~350 lines)
4. ✅ `src/recommendations/trend_analyzer.py` (~400 lines)
5. ✅ `src/recommendations/engine.py` (~300 lines)
6. ✅ `src/models/recommendation_engine.py` (~400 lines)
7. ✅ `src/api/recommendation_routes.py` (~300 lines)
8. ✅ `src/database/clickhouse_metrics.py` (enhanced, +150 lines)
9. ✅ `src/monitoring/prometheus_metrics.py` (enhanced, +100 lines)
10. ✅ `tests/test_recommendation_engine.py` (~900 lines)

### Documentation
1. ✅ PHASE1-1.9_PART1_Code_Implementation.md (this file)
2. ✅ PHASE1-1.9_PART2_Execution_and_Validation.md

**Total New Code:** ~3,750 lines

---

## 📖 EXAMPLE USAGE

```python
from src.recommendations.engine import RecommendationEngine
from src.models.recommendation_engine import RecommendationEngineRequest

# Initialize engine
engine = RecommendationEngine()

# Create request
request = RecommendationEngineRequest(
    customer_id="customer-123",
    analysis_report=analysis_engine_output,
    include_predictions=True,
    include_trends=True,
    forecast_days=30,
    max_recommendations=50,
    min_monthly_savings=10.0
)

# Generate recommendations
response = await engine.generate_recommendations(request)

# Results
print(f"Total Recommendations: {response.total_recommendations}")
print(f"Potential Savings: ${response.total_potential_savings:,.2f}/month")

# Quick wins
for rec in response.quick_wins[:5]:
    print(f"- {rec.recommendation.title}")
    print(f"  Savings: ${rec.recommendation.monthly_savings:,.2f}/month")
    print(f"  Priority Score: {rec.priority_score:.1f}")
    print(f"  ROI: {rec.roi_score:.1f}%")
```

---

**Document Version:** 1.0  
**Last Updated:** October 22, 2025  
**Next:** PHASE1-1.9_PART2_Execution_and_Validation.md

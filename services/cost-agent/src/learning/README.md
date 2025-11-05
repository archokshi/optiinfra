# Learning Loop

The Learning Loop is the **continuous improvement engine** that learns from recommendation outcomes to improve future recommendations.

## 🎯 Overview

The Learning Loop closes the feedback loop by:
1. **Tracking Outcomes** - Monitor execution results and actual savings
2. **Storing Knowledge** - Use Qdrant vector DB for semantic memory
3. **Analyzing Feedback** - Learn from successes and failures
4. **Improving Recommendations** - Apply learnings to future recommendations

## 📦 Components

### 1. OutcomeTracker (`outcome_tracker.py`)
Tracks execution outcomes and measures actual savings.

```python
from src.learning.outcome_tracker import OutcomeTracker

tracker = OutcomeTracker()

# Track an outcome
outcome = await tracker.track_execution_outcome(
    execution_id="exec-123",
    recommendation_id="rec-456",
    outcome_data={
        "success": True,
        "actual_savings": 52.00,
        "predicted_savings": 50.00,
        "execution_duration_seconds": 120.0
    }
)
```

### 2. KnowledgeStore (`knowledge_store.py`)
Stores outcomes in Qdrant vector database for semantic search.

```python
from src.learning.knowledge_store import KnowledgeStore

store = KnowledgeStore(
    qdrant_url="http://localhost:6333",
    openai_api_key="sk-..."
)

# Store outcome
vector_id = await store.store_recommendation_outcome(
    recommendation=recommendation_data,
    outcome=outcome_data
)

# Find similar cases
similar = await store.find_similar_cases(
    recommendation=current_recommendation,
    limit=10
)
```

### 3. FeedbackAnalyzer (`feedback_analyzer.py`)
Analyzes patterns and generates insights.

```python
from src.learning.feedback_analyzer import FeedbackAnalyzer

analyzer = FeedbackAnalyzer(
    outcome_tracker=tracker,
    knowledge_store=store
)

# Analyze success patterns
patterns = await analyzer.analyze_success_patterns(
    recommendation_type="terminate",
    lookback_days=90
)

# Generate insights
insights = await analyzer.generate_learning_insights(
    lookback_days=30
)
```

### 4. ImprovementEngine (`improvement_engine.py`)
Applies learnings to improve recommendations.

```python
from src.learning.improvement_engine import ImprovementEngine

engine = ImprovementEngine()

# Adjust scoring weights
weights = await engine.adjust_scoring_weights(insights)

# Refine predictions
model = await engine.refine_cost_predictions(
    recommendation_type="terminate",
    historical_data=outcomes
)
```

### 5. LearningLoop (`learning_loop.py`)
Orchestrates the complete learning process.

```python
from src.learning.learning_loop import LearningLoop

loop = LearningLoop()

# Process an outcome
result = await loop.process_execution_outcome(
    execution_id="exec-123",
    recommendation_id="rec-456",
    outcome_data=outcome_data
)

# Run learning cycle
cycle_result = await loop.run_learning_cycle(force=True)

# Get metrics
metrics = await loop.get_learning_metrics()
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install qdrant-client openai
```

### 2. Start Qdrant (Optional)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Initialize Collections

```bash
python scripts/init_qdrant.py --url http://localhost:6333
```

### 4. Use the Learning Loop

```python
from src.learning.learning_loop import LearningLoop

# Create instance
loop = LearningLoop()

# Process outcomes automatically
result = await loop.process_execution_outcome(
    execution_id="exec-123",
    recommendation_id="rec-456",
    outcome_data={
        "success": True,
        "actual_savings": 52.00,
        "predicted_savings": 50.00,
        "execution_duration_seconds": 120.0,
        "recommendation_type": "terminate"
    }
)

print(f"Outcome processed: {result.outcome_id}")
print(f"Stored in Qdrant: {result.stored_in_qdrant}")
print(f"Insights generated: {result.insights_generated}")
```

## 📊 API Endpoints

### Track Outcome
```bash
POST /api/v1/learning/track-outcome
{
  "execution_id": "exec-123",
  "recommendation_id": "rec-456",
  "success": true,
  "actual_savings": 52.00,
  "predicted_savings": 50.00
}
```

### Get Metrics
```bash
GET /api/v1/learning/metrics
```

### Get Insights
```bash
GET /api/v1/learning/insights?lookback_days=30&limit=10
```

### Find Similar Cases
```bash
GET /api/v1/learning/similar-cases/rec-123?limit=10
```

### Run Learning Cycle
```bash
POST /api/v1/learning/run-cycle?force=true
```

## 🧪 Testing

### Run Automated Tests
```bash
# All tests
python -m pytest tests/test_learning_loop.py -v

# Specific test class
python -m pytest tests/test_learning_loop.py::TestOutcomeTracker -v

# With coverage
python -m pytest tests/test_learning_loop.py --cov=src.learning
```

### Run Manual Tests
```bash
python test_learning_manual.py
```

## 📈 Expected Impact

- **30-60% improvement** in recommendation accuracy over 3 months
- **Reduced false positives** through pattern learning
- **Better savings predictions** through historical analysis
- **Lower execution failures** through risk assessment

## 🔧 Configuration

### Environment Variables
```bash
# Qdrant
QDRANT_URL=http://localhost:6333

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

# PostgreSQL (optional)
DATABASE_URL=postgresql://user:pass@localhost/optiinfra
```

### Settings
```python
# In src/learning/knowledge_store.py
COLLECTION_NAME = "recommendation_outcomes"
EMBEDDING_SIZE = 1536  # OpenAI text-embedding-3-small
```

## 🐛 Troubleshooting

### Qdrant Connection Failed
```
Error: [WinError 10061] No connection could be made
```
**Solution:** Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`

### OpenAI API Key Missing
```
Warning: No OpenAI API key, using mock embedding
```
**Solution:** Set `OPENAI_API_KEY` environment variable

### Tests Failing
```
FAILED tests/test_learning_loop.py::test_xxx
```
**Solution:** Tests work without Qdrant. Check test output for specific errors.

## 📚 Documentation

- **PHASE1-1.11_PART1_Code_Implementation.md** - Implementation guide
- **PHASE1-1.11_PART2_Execution_and_Validation.md** - Testing guide
- **PHASE1-1.11_VALIDATION_REPORT.md** - Validation results

## 🤝 Contributing

1. Write tests for new features
2. Follow existing code patterns
3. Update documentation
4. Run all tests before committing

## 📝 License

Part of OptiInfra Cost Agent - Internal Use Only

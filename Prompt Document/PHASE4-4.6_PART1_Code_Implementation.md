# PHASE4-4.6 PART1: LLM Integration - Code Implementation Plan

**Phase**: PHASE4-4.6  
**Agent**: Application Agent  
**Objective**: Integrate Groq LLM for advanced quality scoring and analysis  
**Estimated Time**: 30 minutes implementation + 25 minutes validation = 55 minutes  
**Priority**: HIGH ⭐  
**Dependencies**: PHASE4-4.5 (LangGraph Workflow)

---

## Overview

Integrate Groq's LLM (gpt-oss-20b) to enhance quality analysis with AI-powered scoring, semantic understanding, and intelligent recommendations. This adds a layer of LLM-based analysis on top of the existing rule-based quality metrics.

---

## Core Features

### 1. Groq Client Integration
- Initialize Groq client with API key
- Configure gpt-oss-20b model
- Handle API errors and retries
- Rate limiting and timeout handling

### 2. LLM-Based Quality Scoring
- **Semantic Relevance**: LLM evaluates if response truly answers the question
- **Contextual Coherence**: LLM checks logical flow and consistency
- **Factual Accuracy**: LLM identifies potential hallucinations or errors
- **Overall Assessment**: LLM provides holistic quality score

### 3. Prompt Engineering
- Quality analysis prompts
- Scoring prompts (0-100 scale)
- Explanation generation prompts
- Improvement suggestion prompts

### 4. Hybrid Scoring System
- Combine rule-based scores (existing)
- Combine LLM-based scores (new)
- Weighted average for final score
- Confidence intervals

---

## Implementation Plan

### Step 1: Create LLM Client (8 minutes)

**File**: `src/llm/llm_client.py`

Features:
- Groq client initialization
- API key management from environment
- Error handling and retries
- Response parsing

```python
class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "gpt-oss-20b"
        self.client = Groq(api_key=self.api_key)
    
    async def generate(self, prompt: str) -> str:
        """Generate LLM response."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
```

---

### Step 2: Create Quality Scoring Prompts (7 minutes)

**File**: `src/llm/prompts.py`

Prompt Templates:
- `RELEVANCE_PROMPT` - Evaluate relevance (0-100)
- `COHERENCE_PROMPT` - Evaluate coherence (0-100)
- `HALLUCINATION_PROMPT` - Detect hallucinations (0-100)
- `OVERALL_QUALITY_PROMPT` - Overall assessment
- `IMPROVEMENT_PROMPT` - Suggest improvements

Example:
```python
RELEVANCE_PROMPT = """
Evaluate how well this response answers the given prompt.

Prompt: {prompt}
Response: {response}

Rate the relevance on a scale of 0-100:
- 0-20: Completely irrelevant
- 21-40: Somewhat related but misses the point
- 41-60: Partially relevant
- 61-80: Mostly relevant
- 81-100: Highly relevant and directly answers

Provide only a number between 0-100.
"""
```

---

### Step 3: Implement LLM Quality Analyzer (10 minutes)

**File**: `src/analyzers/llm_quality_analyzer.py`

Core Methods:
- `analyze_relevance()` - LLM-based relevance scoring
- `analyze_coherence()` - LLM-based coherence scoring
- `detect_hallucination()` - LLM-based hallucination detection
- `analyze_overall_quality()` - Comprehensive analysis
- `suggest_improvements()` - Generate improvement suggestions

Features:
- Async LLM calls
- Score parsing and validation
- Error handling
- Caching for efficiency

---

### Step 4: Enhance Quality Collector (5 minutes)

**File**: `src/collectors/quality_collector.py` (modify)

Enhancements:
- Add LLM-based scoring alongside rule-based
- Combine scores with weighted average
- Add LLM insights to metrics
- Optional LLM analysis flag

```python
async def collect_quality_metrics(self, request: QualityRequest) -> QualityMetrics:
    # Existing rule-based analysis
    rule_based_scores = self._rule_based_analysis(request)
    
    # New LLM-based analysis (optional)
    if request.use_llm:
        llm_scores = await llm_analyzer.analyze(request)
        # Combine: 70% rule-based + 30% LLM
        final_scores = self._combine_scores(rule_based_scores, llm_scores)
    else:
        final_scores = rule_based_scores
    
    return final_scores
```

---

### Step 5: Create LLM API Endpoints (3 minutes)

**File**: `src/api/llm.py`

Endpoints:
- `POST /llm/analyze` - LLM-based quality analysis
- `POST /llm/score` - Get LLM quality score
- `POST /llm/suggest` - Get improvement suggestions

---

### Step 6: Update Configuration (2 minutes)

**Files**: 
- `src/core/config.py` - Add LLM settings
- `.env.example` - Add GROQ_API_KEY

```python
# config.py
groq_api_key: str = Field(default="", env="GROQ_API_KEY")
groq_model: str = Field(default="gpt-oss-20b", env="GROQ_MODEL")
llm_enabled: bool = Field(default=True, env="LLM_ENABLED")
llm_weight: float = Field(default=0.3, env="LLM_WEIGHT")  # 30% LLM, 70% rules
```

---

### Step 7: Create Tests (5 minutes)

**File**: `tests/test_llm.py`

Tests:
- `test_llm_client_initialization()`
- `test_llm_relevance_scoring()`
- `test_llm_coherence_scoring()`
- `test_llm_hallucination_detection()`
- `test_hybrid_scoring()`
- `test_llm_api_endpoints()`

---

## Prompt Templates

### Relevance Scoring Prompt
```
Evaluate how well this response answers the given prompt.

Prompt: {prompt}
Response: {response}

Rate the relevance on a scale of 0-100 where:
- 0-20: Completely irrelevant or off-topic
- 21-40: Somewhat related but misses key points
- 41-60: Partially relevant, addresses some aspects
- 61-80: Mostly relevant, covers main points
- 81-100: Highly relevant, directly and completely answers

Provide ONLY a number between 0-100.
```

### Coherence Scoring Prompt
```
Evaluate the logical coherence and consistency of this response.

Response: {response}

Rate the coherence on a scale of 0-100 where:
- 0-20: Incoherent, contradictory, or nonsensical
- 21-40: Poor structure, some contradictions
- 41-60: Acceptable structure, minor inconsistencies
- 61-80: Good structure, logical flow
- 81-100: Excellent structure, perfectly coherent

Provide ONLY a number between 0-100.
```

### Hallucination Detection Prompt
```
Analyze this response for potential hallucinations or factual errors.

Prompt: {prompt}
Response: {response}

Rate the factual accuracy on a scale of 0-100 where:
- 0-20: Contains major hallucinations or false information
- 21-40: Several questionable or unverified claims
- 41-60: Some minor inaccuracies
- 61-80: Mostly accurate with minor issues
- 81-100: Completely accurate, no hallucinations

Provide ONLY a number between 0-100.
```

### Overall Quality Prompt
```
Provide a comprehensive quality assessment of this response.

Prompt: {prompt}
Response: {response}

Consider:
1. Relevance to the prompt
2. Logical coherence
3. Factual accuracy
4. Completeness
5. Clarity

Rate the overall quality on a scale of 0-100.
Provide ONLY a number between 0-100.
```

---

## Hybrid Scoring Formula

```python
# Weighted combination
final_score = (rule_based_score * 0.7) + (llm_score * 0.3)

# With confidence
if llm_confidence > 0.8:
    weight_llm = 0.4  # Increase LLM weight if confident
else:
    weight_llm = 0.2  # Decrease if uncertain

final_score = (rule_based_score * (1 - weight_llm)) + (llm_score * weight_llm)
```

---

## Error Handling

### API Errors
```python
try:
    response = await llm_client.generate(prompt)
except GroqAPIError as e:
    logger.error(f"Groq API error: {e}")
    # Fallback to rule-based only
    return rule_based_scores
except RateLimitError:
    logger.warning("Rate limit hit, using cache")
    return cached_scores
```

### Invalid Responses
```python
def parse_score(response: str) -> float:
    """Parse LLM score response."""
    try:
        score = float(response.strip())
        return max(0, min(100, score))  # Clamp to 0-100
    except ValueError:
        logger.warning(f"Invalid score: {response}")
        return None  # Use rule-based fallback
```

---

## Files to Create/Modify

### Create (4 files, ~600 lines)
1. `src/llm/__init__.py` (~5 lines)
2. `src/llm/llm_client.py` (~150 lines)
3. `src/llm/prompts.py` (~100 lines)
4. `src/analyzers/llm_quality_analyzer.py` (~200 lines)
5. `src/api/llm.py` (~150 lines)
6. `tests/test_llm.py` (~200 lines)

### Modify (2 files)
1. `src/collectors/quality_collector.py` - Add LLM integration
2. `src/core/config.py` - Add LLM settings
3. `.env.example` - Add GROQ_API_KEY

**Total**: ~805 lines

---

## Success Criteria

- [ ] Groq client initialized successfully
- [ ] LLM prompts generate valid responses
- [ ] Scores parsed correctly (0-100 range)
- [ ] Hybrid scoring combines rule-based + LLM
- [ ] API endpoints functional
- [ ] 6+ tests passing
- [ ] LLM analysis time < 2 seconds
- [ ] Fallback to rule-based on errors

---

## Environment Variables

```bash
# .env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=gpt-oss-20b
LLM_ENABLED=true
LLM_WEIGHT=0.3
LLM_TIMEOUT=5
```

---

**Ready for implementation!**

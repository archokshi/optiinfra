# OptiInfra LLM Integration Architecture

## 🎯 Total LLM Integration Points: 5

---

## 📊 Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM INTEGRATION POINTS                    │
└─────────────────────────────────────────────────────────────┘

1. Cost Agent          → Groq API (Recommendations & Insights)
2. Performance Agent   → Groq API (Bottleneck Analysis)
3. Resource Agent      → Groq API (Optimization Suggestions)
4. Application Agent   → Groq API (Quality Baseline & Regression)
5. Data Collector      → Groq API (Real-time Quality Monitoring)
   └─ Phase 6.5 Addition ⭐
```

---

## 🔍 Detailed Breakdown

### 1️⃣ **Cost Agent** (Port 8001)
**Location:** `services/cost-agent/src/llm/`

**Purpose:** AI-powered cost optimization recommendations

**LLM Use Cases:**
- **Insight Generation:** Analyze cost data and generate business insights
- **Recommendation Enhancement:** Add context and reasoning to technical recommendations
- **Executive Summaries:** Generate C-suite friendly summaries
- **Natural Language Queries:** Answer questions about cost data

**Example:**
```
Technical Data: "Instance i-123 idle 95% of time, costs $52/month"
↓ LLM Enhancement ↓
Business Insight: "This idle instance represents $624 annual waste. 
Recommendation: Terminate or downsize to t3.micro for 70% savings."
```

**Files:**
- `src/llm/llm_client.py` - Groq API client
- `src/llm/llm_integration.py` - Integration layer
- `src/llm/insight_generator.py` - Insight generation
- `src/llm/prompt_templates.py` - Prompt templates

---

### 2️⃣ **Performance Agent** (Port 8002)
**Location:** `services/performance-agent/src/llm/`

**Purpose:** AI-powered performance analysis and optimization

**LLM Use Cases:**
- **Bottleneck Analysis:** Identify root causes of performance issues
- **Optimization Suggestions:** Generate tuning recommendations
- **Anomaly Explanation:** Explain why performance degraded
- **Configuration Recommendations:** Suggest optimal configs

**Example:**
```
Technical Data: "P95 latency spiked from 200ms to 2000ms"
↓ LLM Analysis ↓
Root Cause: "KV cache misconfiguration after model update. 
Context length increased but cache size not adjusted.
Recommendation: Increase KV cache from 2048 to 4096."
```

**Files:**
- `src/llm/llm_client.py` - Groq API client
- `src/llm/llm_integration.py` - Integration layer

---

### 3️⃣ **Resource Agent** (Port 8003)
**Location:** `services/resource-agent/src/llm/`

**Purpose:** AI-powered resource optimization

**LLM Use Cases:**
- **Utilization Analysis:** Explain GPU/CPU utilization patterns
- **Scaling Recommendations:** Suggest when to scale up/down
- **Resource Consolidation:** Identify consolidation opportunities
- **Capacity Planning:** Predict future resource needs

**Example:**
```
Technical Data: "GPU utilization: 45%, Memory: 60%, CPU: 30%"
↓ LLM Analysis ↓
Insight: "GPU underutilized. Workload is memory-bound, not compute-bound.
Recommendation: Switch to memory-optimized instance (r6g) for 40% cost savings."
```

**Files:**
- `src/llm/llm_client.py` - Groq API client
- `src/llm/prompt_templates.py` - Prompt templates

---

### 4️⃣ **Application Agent** (Port 8004)
**Location:** `services/application-agent/src/llm/`

**Purpose:** AI-powered quality monitoring and regression detection

**LLM Use Cases:**
- **Quality Baseline:** Establish quality benchmarks
- **Regression Detection:** Detect quality drops after changes
- **A/B Test Analysis:** Compare quality between variants
- **Approval/Rejection:** Decide if changes are safe to deploy

**Example:**
```
Scenario: New quantized model deployed
↓ LLM Analysis ↓
Before: Quality = 87%, Hallucination = 2%
After:  Quality = 75%, Hallucination = 8%
Decision: ❌ REJECT - Quality dropped 12% (threshold: 5%)
Action: Auto-rollback initiated
```

**Files:**
- `src/llm/llm_client.py` - Groq API client
- `src/llm/prompts.py` - Prompt templates

---

### 5️⃣ **Data Collector** (Port 8005) ⭐ **Phase 6.5 Addition**
**Location:** `services/data-collector/src/collectors/application/groq_client.py`

**Purpose:** Real-time quality monitoring during data collection

**Why This Exists:**
This is a **DIFFERENT use case** from the Application Agent!

**Key Differences:**

| Aspect | Data Collector LLM | Application Agent LLM |
|--------|-------------------|----------------------|
| **When** | During data collection (every 15 min) | On-demand analysis |
| **What** | Analyze individual LLM interactions | Aggregate quality trends |
| **Output** | Raw quality scores per interaction | Quality baselines & regressions |
| **Storage** | ClickHouse (time-series) | PostgreSQL (analysis results) |
| **Purpose** | Collect metrics | Make decisions |

**LLM Use Cases:**
1. **Quality Scoring:** Analyze each LLM interaction for quality
   - Coherence, relevance, accuracy, completeness
   
2. **Hallucination Detection:** Check each response for false information
   - Hallucination score, confidence, reasoning
   
3. **Toxicity Checking:** Ensure responses are safe
   - Toxicity, hate speech, violence, profanity

**Example Flow:**
```
Customer's vLLM Instance
  ↓ (generates responses)
Data Collector (every 15 min)
  ↓ (collects interactions)
Groq API (analyzes each interaction)
  ↓ (returns scores)
ClickHouse (stores metrics)
  ↓ (time-series data)
Application Agent (reads from ClickHouse)
  ↓ (analyzes trends)
Decision: Quality baseline established
```

**Files:**
- `src/collectors/application/groq_client.py` - Groq API client
  - `analyze_quality()` - Quality scoring
  - `detect_hallucination()` - Hallucination detection
  - `check_toxicity()` - Toxicity checking

---

## 🤔 Why Data Collector Has LLM Integration?

### **The Problem:**
In Phase 6.5, we needed to collect **application quality metrics** from customer's LLM deployments. But how do you measure "quality" of an LLM response?

### **The Solution:**
Use **another LLM** (Groq) to analyze the quality of customer's LLM outputs!

### **Why Not Just Use Application Agent?**
The Application Agent is for **analysis and decision-making**, not data collection:

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA FLOW                                 │
└─────────────────────────────────────────────────────────────┘

Step 1: DATA COLLECTION (Data Collector + Groq)
  Customer vLLM → Data Collector → Groq API → ClickHouse
  
  What happens:
  - Collect LLM interactions every 15 minutes
  - Send each interaction to Groq for analysis
  - Get quality/hallucination/toxicity scores
  - Store raw scores in ClickHouse
  
Step 2: ANALYSIS & DECISIONS (Application Agent)
  ClickHouse → Application Agent → Decisions
  
  What happens:
  - Read quality scores from ClickHouse
  - Establish quality baselines
  - Detect regressions (quality drops)
  - Approve/reject changes
  - Trigger rollbacks if needed
```

### **Analogy:**
Think of it like a factory:

- **Data Collector + Groq** = Quality Inspector
  - Inspects each product (LLM response)
  - Records measurements (quality scores)
  - Happens continuously during production
  
- **Application Agent** = Quality Manager
  - Reviews inspection reports
  - Sets quality standards
  - Makes decisions (pass/fail)
  - Stops production if quality drops

---

## 📈 LLM Integration by Phase

### **Phase 0-5: Agent LLM Integration**
- ✅ Cost Agent (PHASE1-1.8)
- ✅ Performance Agent (PHASE2-2.12)
- ✅ Resource Agent (PHASE3)
- ✅ Application Agent (PHASE4-4.6)

**Purpose:** AI-powered recommendations and analysis

### **Phase 6.5: Data Collection LLM Integration** ⭐
- ✅ Data Collector (PHASE6.5)

**Purpose:** Real-time quality monitoring during data collection

**Why Added:**
- Needed to collect application quality metrics
- Can't measure quality without LLM analysis
- Provides raw data for Application Agent to analyze

---

## 🔄 How They Work Together

### **Example: Detecting Quality Regression**

```
┌─────────────────────────────────────────────────────────────┐
│  SCENARIO: Customer deploys new quantized model             │
└─────────────────────────────────────────────────────────────┘

BEFORE DEPLOYMENT:
  1. Data Collector collects interactions (every 15 min)
     ↓ Groq API analyzes each interaction
     ↓ Quality scores: 0.87, 0.89, 0.85, 0.88
     ↓ Stored in ClickHouse
  
  2. Application Agent reads from ClickHouse
     ↓ Calculates baseline: 87% quality
     ↓ Stores baseline in PostgreSQL

AFTER DEPLOYMENT:
  1. Data Collector collects new interactions
     ↓ Groq API analyzes each interaction
     ↓ Quality scores: 0.75, 0.73, 0.76, 0.74
     ↓ Stored in ClickHouse
  
  2. Application Agent reads from ClickHouse
     ↓ Calculates current: 75% quality
     ↓ Compares: 75% vs 87% baseline
     ↓ Drop: 12% (threshold: 5%)
     ↓ Decision: ❌ REJECT
     ↓ Action: Auto-rollback

RESULT:
  - Data Collector provided the raw measurements
  - Application Agent made the decision
  - Both used Groq, but for different purposes
```

---

## 🎯 Summary

### **5 LLM Integration Points:**

1. **Cost Agent** - Cost optimization recommendations
2. **Performance Agent** - Performance analysis and tuning
3. **Resource Agent** - Resource optimization suggestions
4. **Application Agent** - Quality decisions and regression detection
5. **Data Collector** - Real-time quality measurement ⭐

### **Why 5 and Not 4?**

The Data Collector is a **separate concern**:
- **Agents** = Decision makers (use LLM for analysis)
- **Data Collector** = Data gatherer (use LLM for measurement)

### **All Use Same Model:**
- ✅ Model: `openai/gpt-oss-20b`
- ✅ Provider: Groq
- ✅ API Key: Same across all services
- ✅ Configuration: Standardized

---

## 🔧 Configuration

All 5 integration points use the same configuration:

```bash
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=openai/gpt-oss-20b
LLM_ENABLED=true
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3
```

**Benefits:**
- Single API key to manage
- Consistent behavior across all services
- Easier to monitor and debug
- Unified cost tracking

---

## 📊 LLM Usage Patterns

### **Data Collector (High Frequency)**
- Frequency: Every 15 minutes
- Volume: ~6-10 API calls per collection
- Purpose: Continuous monitoring
- Cost: Higher (more frequent)

### **Agents (On-Demand)**
- Frequency: When triggered by user or event
- Volume: Variable (depends on usage)
- Purpose: Analysis and decisions
- Cost: Lower (less frequent)

---

**Total LLM Integration Points: 5**
- 4 Agents (decision makers)
- 1 Data Collector (data gatherer)

All validated and working with Groq API! ✅

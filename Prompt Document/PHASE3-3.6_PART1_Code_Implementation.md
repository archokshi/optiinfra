# PHASE3-3.6 PART1: LangGraph Workflow - Code Implementation Plan

**Phase**: PHASE3-3.6  
**Agent**: Resource Agent  
**Objective**: Implement LangGraph workflow for intelligent resource optimization orchestration  
**Estimated Time**: 40+25m (65 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE3-3.1 to PHASE3-3.5

---

## Overview

This phase implements a **LangGraph-based workflow** that orchestrates resource optimization decisions using LLM-powered analysis. The workflow integrates GPU metrics, system metrics, LMCache status, and analysis results to generate intelligent optimization recommendations.

---

## LangGraph Workflow Architecture

### Workflow States

1. **Collect Metrics** - Gather GPU, system, and LMCache metrics
2. **Analyze Resources** - Run analysis engine
3. **Generate Insights** - Use LLM to generate recommendations
4. **Execute Actions** - Apply optimization actions (future)
5. **Monitor Results** - Track optimization outcomes (future)

### Decision Flow

```
START → Collect Metrics → Analyze Resources → Generate Insights → END
                ↓                ↓                    ↓
           [GPU/System]    [Bottlenecks]      [LLM Recommendations]
```

---

## Implementation Plan

### Step 1: LLM Client (10 minutes)

Create `src/llm/llm_client.py` - Groq API client using gpt-oss-20b model (same as Cost Agent).

**Key Components:**
- Groq API integration
- Retry logic with tenacity
- Error handling
- Response validation

### Step 2: Prompt Templates (8 minutes)

Create `src/llm/prompt_templates.py` - Templates for resource optimization prompts.

**Templates:**
- System prompt for resource optimization
- Metrics analysis prompt
- Recommendation generation prompt
- Action planning prompt

### Step 3: Workflow Models (5 minutes)

Create `src/models/workflow.py` - Pydantic models for workflow state and results.

**Models:**
- `WorkflowState` - Current workflow state
- `WorkflowResult` - Final workflow output
- `OptimizationAction` - Recommended actions

### Step 4: LangGraph Workflow (12 minutes)

Create `src/workflow/optimizer.py` - Main LangGraph workflow implementation.

**Components:**
- State graph definition
- Node implementations (collect, analyze, generate)
- Edge conditions
- Workflow execution

### Step 5: API Endpoint (3 minutes)

Create `src/api/optimize.py` - Endpoint to trigger optimization workflow.

**Endpoints:**
- `POST /optimize/run` - Run optimization workflow
- `GET /optimize/status` - Get workflow status

### Step 6: Testing (5 minutes)

Create tests for workflow components.

---

## File Structure

```
resource-agent/
├── src/
│   ├── llm/
│   │   ├── __init__.py (NEW)
│   │   ├── llm_client.py (NEW)
│   │   └── prompt_templates.py (NEW)
│   ├── workflow/
│   │   ├── __init__.py (NEW)
│   │   └── optimizer.py (NEW)
│   ├── models/
│   │   └── workflow.py (NEW)
│   └── api/
│       └── optimize.py (NEW)
└── tests/
    ├── test_llm_client.py (NEW)
    └── test_workflow.py (NEW)
```

---

## Success Criteria

- [ ] LLM client connects to Groq API
- [ ] Workflow executes all states
- [ ] LLM generates relevant recommendations
- [ ] API endpoints functional
- [ ] Tests pass (8+ tests)
- [ ] Integration with existing components

---

**Ready to build intelligent resource optimization!** 🚀

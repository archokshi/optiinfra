# OptiInfra - Project Context & Design Document
## AI-Assisted Development Guide for Windsurf

**Version:** 1.0  
**Date:** October 16, 2025  
**Purpose:** Context for AI-assisted code generation  

---

## 🎯 PROJECT OVERVIEW

### What We're Building

**OptiInfra** is a multi-agent AI platform that automatically optimizes LLM infrastructure to:
- **Cut costs by 50%** (spot instances, right-sizing, reserved instances)
- **Improve performance 3x** (latency optimization, KV cache tuning)
- **Ensure quality** (detect regressions before production)

### The Problem We Solve

Companies running LLM infrastructure (vLLM, TGI, SGLang) waste **$50K-$500K per month** due to:
- Suboptimal configurations (40% waste)
- Idle GPU time (50% underutilization)
- Over-provisioning (fear of outages)
- Manual optimization (20 hrs/week engineering time)

### Our Solution

**4 intelligent agents** working together:
1. **Cost Agent** - Optimize cloud spending
2. **Performance Agent** - Improve latency/throughput
3. **Resource Agent** - Maximize GPU/CPU utilization
4. **Application Agent** - Monitor quality, prevent regressions

All coordinated by a **Go-based orchestrator**.

---

## 🏗️ HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOMER PORTAL                           │
│                  (Next.js 14 Dashboard)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Go)                         │
│  • Agent Registry & Discovery                                │
│  • Request Routing (by capability, load balancing)           │
│  • Multi-Agent Coordination                                  │
│  • Conflict Resolution (priority: Customer > Perf > Cost)    │
│  • Change Approval Workflow                                  │
└───┬──────────┬──────────┬──────────┬──────────────────────┘
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐
│  COST  │ │  PERF   │ │ RESOURCE │ │ APPLICATION  │
│ AGENT  │ │ AGENT   │ │  AGENT   │ │    AGENT     │
└───┬────┘ └────┬────┘ └─────┬────┘ └──────┬───────┘
    │           │            │              │
    └───────────┴────────────┴──────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │         DATA LAYER                     │
    │  • PostgreSQL (primary data)           │
    │  • ClickHouse (time-series metrics)    │
    │  • Qdrant (vector DB for LLM memory)   │
    │  • Redis (cache, pub/sub)              │
    └────────────────────────────────────────┘
```

---

## 🤖 AGENT DETAILS

### 1. Cost Agent (Python/FastAPI + LangGraph)

**Purpose:** Reduce cloud spending

**What It Does:**
- Collects cost data from AWS/GCP/Azure
- Analyzes spending patterns
- Generates recommendations (spot migration, right-sizing, RIs)
- Executes optimizations with approval
- Learns from outcomes

**Key Workflows:**
- Spot Instance Migration (30-40% savings)
- Reserved Instance Recommendations (40-60% savings)
- Instance Right-Sizing (20-30% savings)

**Tech Stack:** FastAPI, LangGraph, SQLAlchemy, boto3, OpenAI/Anthropic

---

### 2. Performance Agent (Python/FastAPI + LangGraph)

**Purpose:** Improve latency and throughput

**What It Does:**
- Collects performance metrics from vLLM/TGI/SGLang
- Identifies bottlenecks
- Generates optimizations (KV cache, quantization, batching)
- Tests in staging, gradual rollout
- Monitors for SLO violations

**Key Optimizations:**
- KV Cache tuning
- Quantization (FP16 → FP8 → INT8)
- Batch size optimization
- Model parallelism

**Tech Stack:** FastAPI, LangGraph, Prometheus client

---

### 3. Resource Agent (Python/FastAPI + LangGraph)

**Purpose:** Maximize GPU/CPU/memory utilization

**What It Does:**
- Collects GPU metrics (nvidia-smi)
- Collects CPU/memory metrics (psutil)
- Identifies underutilized resources
- Recommends scaling or consolidation
- Integrates with KVOptkit

**Key Workflows:**
- Auto-scaling (predictive)
- Resource consolidation
- KV cache optimization

**Tech Stack:** FastAPI, LangGraph, nvidia-smi, psutil, KVOptkit

---

### 4. Application Agent (Python/FastAPI + LangGraph)

**Purpose:** Monitor quality, prevent regressions

**What It Does:**
- Monitors LLM output quality
- Detects hallucinations and toxic content
- Establishes quality baselines
- Validates optimization changes (A/B testing)
- Auto-rollback if quality drops > 5%

**Key Features:**
- Quality metrics scoring
- Regression detection
- Approval/rejection of changes
- A/B testing

**Tech Stack:** FastAPI, LangGraph, Quality scoring models

---

## 🧠 ORCHESTRATOR (Go)

**Purpose:** Coordinate all agents

**Responsibilities:**
1. Agent Registry (health monitoring)
2. Request Routing
3. Conflict Resolution
4. Change Approval Workflow
5. Rollback Mechanism
6. Event Publishing (Redis pub/sub)

**Why Go?** Performance, concurrency, low resource usage

**Tech Stack:** Gin, gRPC, Redis, PostgreSQL

---

## 💾 DATA ARCHITECTURE

### PostgreSQL (Primary Database)
- Customers, Agents, Events
- Cost/Performance/Resource/Quality metrics
- Recommendations, Optimizations, Approvals

### ClickHouse (Time-Series)
- High-frequency metrics (1-sec to 1-min granularity)
- Materialized views (hourly, daily aggregations)
- 30-90 day retention

### Qdrant (Vector Database)
- LLM memory and learning
- Past decisions → outcomes
- Similarity search for recommendations

### Redis
- Agent registry backup
- API caching (1-hour TTL)
- Rate limiting
- Event pub/sub

---

## 🔄 WORKFLOW EXAMPLE: Spot Migration

```
1. COST AGENT: Analyze instances → Find savings opportunity
2. COST AGENT: Generate recommendation → LLM assesses risk
3. ORCHESTRATOR: Coordinate agents
   ├─ PERFORMANCE AGENT: "Is this safe?" → Yes
   ├─ RESOURCE AGENT: "Will this work?" → Yes
   └─ APPLICATION AGENT: "Establish baseline" → Done
4. CUSTOMER: Approve in portal
5. COST AGENT: Execute migration
   ├─ Create spot instance
   ├─ Gradual rollout (10% → 50% → 100%)
   └─ Terminate on-demand
6. APPLICATION AGENT: Monitor quality → 0.5% drop (OK)
7. COST AGENT: Record outcome → Store in Qdrant
8. ORCHESTRATOR: Close workflow → Notify customer
```

---

## 🎨 CUSTOMER PORTAL (Next.js 14)

**Pages:**
- Overview (all agents status)
- Cost Dashboard
- Performance Dashboard
- Resource Dashboard
- Application Dashboard
- Recommendations (approve/reject)
- Execution History

**Features:**
- Real-time updates (WebSocket)
- Charts (Recharts)
- Approval workflow
- Dark mode

**Tech Stack:** Next.js 14, TypeScript, TailwindCSS, Recharts, WebSocket

---

## 🔐 SECURITY & PRODUCTION

### Authentication
- OAuth 2.0 (Google, GitHub)
- JWT tokens
- Role-based access control

### API Security
- Rate limiting (Redis)
- API key authentication
- Input validation
- SQL injection prevention
- CORS configuration

### Deployment
- Kubernetes
- Horizontal Pod Autoscaler
- Health checks
- Resource limits

### CI/CD
- GitHub Actions
- Automated testing
- Docker builds
- Security scanning

### Monitoring
- Prometheus + Grafana
- Alerting (Slack)

---

## 🛠️ TECHNOLOGY STACK

| Component | Technology | Why? |
|-----------|------------|------|
| Orchestrator | Go + Gin | Performance, concurrency |
| Agents | Python + FastAPI | Rapid dev, ML libraries |
| Workflows | LangGraph | State machines |
| Portal | Next.js 14 + TS | Modern React, SSR |
| Primary DB | PostgreSQL | Reliability, ACID |
| Metrics DB | ClickHouse | Time-series perf |
| Vector DB | Qdrant | LLM memory |
| Cache | Redis | Speed, pub/sub |
| LLM | OpenAI/Anthropic | Decision-making |
| Container | Docker | Consistency |
| Orchestration | Kubernetes | Production |
| CI/CD | GitHub Actions | Automation |
| Monitoring | Prometheus/Grafana | Observability |

---

## 📊 DEVELOPMENT PHASES (70 Prompts)

### PILOT (Week 0) - 5 prompts
Validate AI-assisted development approach

### Foundation (Week 1) - 15 prompts
Build infrastructure (databases, orchestrator, monitoring)

### Cost Agent (Week 2-3) - 17 prompts
Complete cost optimization

### Performance Agent (Week 4-5) - 11 prompts
Performance optimization

### Resource Agent (Week 6-7) - 10 prompts
Resource optimization

### Application Agent (Week 8-9) - 9 prompts
Quality monitoring

### Portal & Production (Week 10) - 8 prompts
Production-ready system

---

## 🎯 KEY PRINCIPLES

### 1. Production-Ready Code
- No placeholders or TODOs
- Complete error handling
- Comprehensive logging
- Input validation
- Security considerations

### 2. Testing
- 80%+ code coverage
- Unit + Integration + E2E tests
- Mock fixtures
- Deterministic tests

### 3. Documentation
- Docstrings for all functions
- README for each component
- API documentation
- Architecture diagrams
- Troubleshooting guides

### 4. Consistency
- Follow language conventions
- Consistent naming
- Consistent error handling
- Consistent logging

### 5. Performance
- Async/await
- Connection pooling
- Caching
- Query optimization
- Resource limits

### 6. Security
- Input sanitization
- Injection prevention
- Rate limiting
- Authentication/authorization

---

## 📝 CODE PATTERNS

### FastAPI Agent
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Agent")

class Request(BaseModel):
    customer_id: str

@app.post("/endpoint")
async def handler(req: Request):
    try:
        result = await process(req)
        return result
    except Exception as e:
        raise HTTPException(500, detail=str(e))
```

### LangGraph Workflow
```python
from langgraph.graph import StateGraph
from typing import TypedDict

class State(TypedDict):
    data: dict

def node(state: State):
    return {"result": "processed"}

workflow = StateGraph(State)
workflow.add_node("process", node)
```

### Go Orchestrator
```go
package main

import "github.com/gin-gonic/gin"

func RouteRequest(c *gin.Context) {
    var req Request
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    result := process(req)
    c.JSON(200, result)
}
```

---

## 🎯 SUCCESS METRICS

### Technical
- 80%+ test coverage
- < 500ms API latency (P95)
- 99.9% uptime
- Zero critical vulnerabilities

### Business
- 40-50% cost savings
- 2-3x performance improvement
- < 2% quality degradation
- 2-3 weeks to first savings

### Development
- 70 prompts executed
- < 10% manual fixes
- 11 weeks timeline
- 4 decision gates passed

---

**This context helps Windsurf AI generate high-quality, consistent, production-ready code throughout all 70 prompts.**

**Let's build OptiInfra! 🚀**
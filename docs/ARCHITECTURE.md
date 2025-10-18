# OptiInfra Architecture

## Overview

OptiInfra uses a **multi-agent architecture** where specialized AI agents work together to optimize LLM infrastructure across cost, performance, resource utilization, and application quality.

## System Architecture

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

## Components

### 1. Customer Portal (Next.js 14)
- **Technology**: Next.js 14, TypeScript, TailwindCSS, shadcn/ui
- **Purpose**: Web interface for monitoring and approvals
- **Features**:
  - Real-time dashboards for all agents
  - Recommendation approval workflow
  - Execution history
  - WebSocket for live updates

### 2. Orchestrator (Go)
- **Technology**: Go, Gin, gRPC, PostgreSQL, Redis
- **Purpose**: Central coordination service
- **Responsibilities**:
  - Agent registry and health monitoring
  - Request routing to appropriate agents
  - Multi-agent workflow coordination
  - Conflict resolution between agents
  - Change approval management
  - Event publishing (Redis pub/sub)

### 3. Cost Agent (Python/FastAPI)
- **Technology**: Python, FastAPI, LangGraph, boto3, SQLAlchemy
- **Purpose**: Optimize cloud spending
- **Capabilities**:
  - Spot instance migration
  - Reserved instance recommendations
  - Instance right-sizing
  - Cost anomaly detection
  - Budget forecasting

### 4. Performance Agent (Python/FastAPI)
- **Technology**: Python, FastAPI, LangGraph, Prometheus
- **Purpose**: Improve latency and throughput
- **Capabilities**:
  - KV cache tuning
  - Quantization optimization
  - Batch size optimization
  - Model parallelism configuration
  - Performance anomaly detection

### 5. Resource Agent (Python/FastAPI)
- **Technology**: Python, FastAPI, LangGraph, nvidia-smi, psutil
- **Purpose**: Maximize resource utilization
- **Capabilities**:
  - Auto-scaling (predictive)
  - Resource consolidation
  - GPU utilization monitoring
  - KV cache optimization (KVOptkit)
  - Resource anomaly detection

### 6. Application Agent (Python/FastAPI)
- **Technology**: Python, FastAPI, LangGraph, Quality scoring models
- **Purpose**: Monitor quality and prevent regressions
- **Capabilities**:
  - LLM output quality monitoring
  - Hallucination detection
  - Toxic content detection
  - Quality baseline establishment
  - A/B testing validation
  - Auto-rollback on degradation

## Data Layer

### PostgreSQL
- **Purpose**: Primary relational database
- **Stores**:
  - Customer accounts
  - Agent registry
  - Recommendations
  - Optimizations
  - Approvals
  - Events

### ClickHouse
- **Purpose**: Time-series metrics database
- **Stores**:
  - Cost metrics (1-min granularity)
  - Performance metrics (1-sec granularity)
  - Resource metrics (1-sec granularity)
  - Quality metrics (per-request)
- **Features**:
  - Materialized views for aggregations
  - 30-90 day retention
  - High-speed queries

### Qdrant
- **Purpose**: Vector database for LLM memory
- **Stores**:
  - Past decisions and outcomes
  - Similar scenario lookups
  - Agent learning data
- **Features**:
  - Semantic similarity search
  - Fast retrieval for LLM context

### Redis
- **Purpose**: Cache and pub/sub
- **Uses**:
  - Agent registry backup
  - API response caching (1-hour TTL)
  - Rate limiting
  - Event pub/sub for real-time updates

## Communication Patterns

### Synchronous (HTTP/gRPC)
- Portal → Orchestrator: REST API
- Orchestrator → Agents: gRPC
- Agents → Databases: Direct connections

### Asynchronous (Pub/Sub)
- Orchestrator → Portal: WebSocket
- Agents → Orchestrator: Redis pub/sub
- Event notifications: Redis pub/sub

## Workflow Example: Spot Instance Migration

1. **Cost Agent**: Analyzes instances → Finds savings opportunity
2. **Cost Agent**: Generates recommendation → LLM assesses risk
3. **Orchestrator**: Coordinates agents
   - Performance Agent: "Is this safe?" → Yes
   - Resource Agent: "Will this work?" → Yes
   - Application Agent: "Establish baseline" → Done
4. **Customer**: Approves in portal
5. **Cost Agent**: Executes migration
   - Create spot instance
   - Gradual rollout (10% → 50% → 100%)
   - Terminate on-demand
6. **Application Agent**: Monitors quality → 0.5% drop (OK)
7. **Cost Agent**: Records outcome → Stores in Qdrant
8. **Orchestrator**: Closes workflow → Notifies customer

## Conflict Resolution

When agents have conflicting recommendations:

**Priority Order**:
1. **Customer preferences** (highest)
2. **Application quality** (no degradation > 5%)
3. **Performance SLOs** (latency, throughput)
4. **Cost optimization** (lowest)

**Resolution Process**:
1. Orchestrator detects conflict
2. Applies priority rules
3. Requests agent re-evaluation
4. Escalates to customer if unresolvable

## Security

- **Authentication**: OAuth 2.0, JWT tokens
- **Authorization**: Role-based access control (RBAC)
- **API Security**: Rate limiting, input validation
- **Data Encryption**: TLS in transit, encryption at rest
- **Secrets Management**: Environment variables, secret stores

## Scalability

- **Horizontal scaling**: All services are stateless
- **Load balancing**: Orchestrator routes to least-loaded agent
- **Database sharding**: ClickHouse for time-series data
- **Caching**: Redis for frequently accessed data
- **Auto-scaling**: Kubernetes HPA based on CPU/memory

## Monitoring

- **Metrics**: Prometheus + Grafana
- **Logging**: Structured logs (JSON)
- **Tracing**: Distributed tracing (future)
- **Alerting**: Slack/PagerDuty integration

## Deployment

- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Environments**: Development, Staging, Production

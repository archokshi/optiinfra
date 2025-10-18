# OptiInfra Cost Agent

Python FastAPI-based agent for cloud cost optimization.

## Features

- FastAPI web framework
- **LangGraph AI workflows** for intelligent cost optimization
- Structured JSON logging
- Health check endpoint
- Automatic orchestrator registration
- Docker support
- Comprehensive tests (89% coverage)

## Capabilities

- **Spot Migration**: Migrate on-demand instances to spot instances (30-40% savings)
- **Reserved Instances**: Recommend RI purchases (40-60% savings)
- **Right-Sizing**: Identify over-provisioned instances (20-30% savings)
- **AI Workflow Optimization**: LangGraph-powered analysis and recommendations

## LangGraph Workflows

The Cost Agent uses LangGraph for AI-powered workflow orchestration with two main workflows:

### 1. Cost Optimization Workflow

```
START → Analyze → Recommend → Summarize → END
```

1. **Analyze Node**: Detects waste and inefficiencies in cloud resources
2. **Recommend Node**: Generates actionable optimization recommendations
3. **Summarize Node**: Creates executive summary of findings

### 2. Spot Migration Workflow (PILOT-05)

```
START → Analyze → Coordinate → Execute → Monitor → END
```

1. **Analyze Node**: Identifies EC2 spot migration opportunities
2. **Coordinate Node**: Gets approval from Performance, Resource, and Application agents
3. **Execute Node**: Performs gradual rollout (10% → 50% → 100%)
4. **Monitor Node**: Tracks quality metrics and triggers rollback if needed

### Spot Migration Demo (PILOT-05)

The spot migration workflow demonstrates end-to-end cost optimization with:
- Real AWS EC2 instance analysis (simulated)
- Spot opportunity identification with savings calculation
- Multi-agent coordination (Performance, Resource, Application agents)
- Gradual rollout strategy (10% → 50% → 100%)
- Quality monitoring with automatic rollback
- Success reporting with final savings

**Run the Interactive Demo:**
```bash
python demos/spot_migration_demo.py
```

**Or use the API:**
```bash
curl -X POST http://localhost:8001/spot-migration \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "demo-customer-001",
    "auto_approve": true
  }'
```

**Expected Results:**
- Analyzes 10 EC2 instances
- Identifies 6-8 spot opportunities
- Achieves 30-40% cost savings ($2,000-$3,000/month)
- Maintains quality within 5% degradation threshold
- Completes migration in 3 phases

### Using the Analysis Endpoint

**Request:**
```bash
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "resources": [
      {
        "resource_id": "i-1234567890abcdef0",
        "resource_type": "ec2",
        "provider": "aws",
        "region": "us-east-1",
        "cost_per_month": 150.00,
        "utilization": 0.25,
        "tags": {"environment": "production"}
      }
    ]
  }'
```

**Response:**
```json
{
  "request_id": "req-abc123",
  "timestamp": "2025-10-18T10:00:00Z",
  "resources_analyzed": 1,
  "total_waste_detected": 75.00,
  "total_potential_savings": 75.00,
  "recommendations": [
    {
      "recommendation_id": "rec-xyz789",
      "recommendation_type": "right_sizing",
      "resource_id": "i-1234567890abcdef0",
      "description": "Right-size resource to match utilization",
      "estimated_savings": 75.00,
      "confidence_score": 0.85,
      "implementation_steps": ["..."]
    }
  ],
  "summary": "Cost Optimization Analysis Summary...",
  "workflow_status": "complete"
}
```

### Workflow State Management

The workflow uses TypedDict for state management:
- **Resources**: Input cloud resources to analyze
- **Analysis Results**: Detected waste and inefficiencies
- **Recommendations**: Generated optimization actions
- **Summary**: Executive summary of findings

### Future Enhancements

- LLM integration for intelligent recommendations
- Conditional workflow branching
- Workflow persistence and history
- Multi-agent coordination

## Development

### Prerequisites

- Python 3.11+
- Docker (optional)

### Running Locally

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --port 8001
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# View coverage
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## API Endpoints

### POST /spot-migration

Execute spot migration workflow with gradual rollout.

**Request:**
```json
{
  "customer_id": "customer-123",
  "instance_ids": null,
  "auto_approve": true
}
```

**Response:**
```json
{
  "request_id": "spot-20251018120000",
  "customer_id": "customer-123",
  "timestamp": "2025-10-18T12:00:00Z",
  "instances_analyzed": 10,
  "opportunities_found": 6,
  "total_savings": 2450.00,
  "opportunities": [...],
  "performance_approval": {...},
  "resource_approval": {...},
  "application_approval": {...},
  "execution_10_percent": {...},
  "execution_50_percent": {...},
  "execution_100_percent": {...},
  "workflow_status": "complete",
  "final_savings": 2450.00,
  "success": true
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T10:00:00Z",
  "version": "0.1.0",
  "agent_id": "cost-agent-001",
  "agent_type": "cost",
  "uptime_seconds": 120.5
}
```

### GET /

Service information endpoint.

**Response:**
```json
{
  "service": "OptiInfra Cost Agent",
  "version": "0.1.0",
  "status": "running",
  "capabilities": [
    "spot_migration",
    "reserved_instances",
    "right_sizing"
  ]
}
```

## Configuration

Environment variables:

- `PORT` - Port to listen on (default: 8001)
- `ENVIRONMENT` - Environment name (default: development)
- `LOG_LEVEL` - Log level (default: INFO)
- `ORCHESTRATOR_URL` - Orchestrator URL (default: http://localhost:8080)
- `AGENT_ID` - Agent identifier (default: cost-agent-001)

## Docker

```bash
# Build image
docker build -t optiinfra-cost-agent .

# Run container
docker run -p 8001:8001 optiinfra-cost-agent

# Or use docker-compose (from project root)
docker-compose up cost-agent
```

## Project Status

**PILOT-05 Complete** ✅
- Spot migration workflow implemented
- Multi-agent coordination working
- Gradual rollout with quality monitoring
- Comprehensive test coverage (37 tests passing)
- Interactive demo available

## Next Steps

- Integrate with real AWS APIs (currently simulated)
- Add LLM-powered recommendation intelligence
- Implement workflow persistence and history
- Add support for other cloud providers (Azure, GCP)
- Expand to other optimization types (Reserved Instances, Right-Sizing)

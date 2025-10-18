# OptiInfra Cost Agent

Python FastAPI-based agent for cloud cost optimization.

## Features

- FastAPI web framework
- Structured JSON logging
- Health check endpoint
- Automatic orchestrator registration
- Docker support
- Comprehensive tests (80%+ coverage)

## Capabilities

- **Spot Migration**: Migrate on-demand instances to spot instances (30-40% savings)
- **Reserved Instances**: Recommend RI purchases (40-60% savings)
- **Right-Sizing**: Identify over-provisioned instances (20-30% savings)

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

## Next Steps

After this pilot phase:
- Add cloud provider collectors (Week 2)
- Add LangGraph workflows (Week 2)
- Add analysis engine (Week 2)
- Add LLM integration (Week 2)
- Add execution engine (Week 2)

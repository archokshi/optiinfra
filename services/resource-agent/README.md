# Resource Agent

**AI-powered resource optimization agent for LLM infrastructure**

## Overview

The Resource Agent maximizes GPU/CPU/memory utilization through:
- Auto-scaling (predictive)
- Resource consolidation
- KV cache optimization (via KVOptkit)
- GPU utilization monitoring
- Resource anomaly detection

## Architecture

```
resource-agent/
├── src/
│   ├── api/             # FastAPI endpoints
│   ├── workflows/       # LangGraph workflows
│   ├── collectors/      # Resource metrics collectors
│   ├── analyzers/       # Resource analysis logic
│   └── executors/       # Optimization executors
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── requirements.txt
├── Dockerfile
└── README.md
```

## Technology Stack

- **Framework**: FastAPI
- **Workflows**: LangGraph
- **Monitoring**: nvidia-smi, psutil
- **Database**: SQLAlchemy (PostgreSQL)
- **LLM**: OpenAI/Anthropic
- **Testing**: pytest

## Development

### Prerequisites
- Python 3.11+
- Docker (for local testing)

### Setup
```bash
cd services/resource-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run locally
```bash
uvicorn src.main:app --reload --port 8003
```

### Run tests
```bash
pytest tests/ -v --cov=src
```

## API Endpoints

### Health Check
```
GET /health
```

### Resource Analysis
```
POST /api/v1/analyze
```

### Recommendations
```
GET  /api/v1/recommendations
POST /api/v1/recommendations/:id/approve
```

### Optimizations
```
GET  /api/v1/optimizations
POST /api/v1/optimizations
```

## Configuration

Environment variables:
- `RESOURCE_AGENT_PORT` - HTTP server port (default: 8003)
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key

## Deployment

See [Deployment Guide](../../docs/DEPLOYMENT.md) for production deployment instructions.
